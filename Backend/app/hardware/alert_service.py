"""
Arduino 101 alert service.

Talks to the NemoShield firmware (nemoshield_uno.ino) over USB serial.

Protocol (9600 baud, one command per line, '\n' terminated)
    Backend -> Arduino     Arduino -> Backend
    NORMAL                 ACK:NORMAL
    WARNING                ACK:WARNING
    CRITICAL               ACK:CRITICAL
    CLEAR                  ACK:CLEAR
    PING                   ACK:PING
    STATUS                 STATUS:<NORMAL|WARNING|CRITICAL>
    (unknown)              ERR:UNKNOWN
    Unsolicited from Arduino
        READY              sent once after boot (may be missed on Arduino 101, native USB)
        BUTTON_ACK         operator pressed the physical button (buzzer is muted on the board)

If the Arduino is unplugged or not found, the service falls back to simulate
mode so the rest of the backend and the demo keep working.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Optional

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - lets the backend start without pyserial
    serial = None
    list_ports = None

from app.config import ARDUINO_BAUD, ARDUINO_PORT, ARDUINO_SIMULATE

log = logging.getLogger("nemoshield.hardware")

COMMANDS = ("NORMAL", "WARNING", "CRITICAL", "CLEAR")
SEVERITY_TO_COMMAND = {"LOW": "NORMAL", "MEDIUM": "WARNING", "HIGH": "CRITICAL"}
# CLEAR puts the board back in NORMAL
COMMAND_TO_STATE = {"NORMAL": "NORMAL", "WARNING": "WARNING", "CRITICAL": "CRITICAL", "CLEAR": "NORMAL"}

HEARTBEAT_SECONDS = 5.0
REPLY_TIMEOUT_SECONDS = 2.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HardwareError(RuntimeError):
    pass


class ArduinoAlertService:
    def __init__(self, port: Optional[str] = None, baud: int = 9600, simulate: bool = False):
        self.requested_port = port
        self.port: Optional[str] = None
        self.baud = baud
        self.force_simulate = simulate

        self.simulated = simulate
        self.connected = False
        self.state = "NORMAL"
        self.last_ack: Optional[str] = None
        self.last_ack_at: Optional[str] = None
        self.last_error: Optional[str] = None

        self._ser = None
        self._io_lock = threading.Lock()      # one command/reply exchange at a time
        self._state_lock = threading.Lock()
        self._replies: "queue.Queue[str]" = queue.Queue()
        self._button_acks: deque = deque(maxlen=200)
        self._button_listeners: list[Callable[[dict], None]] = []
        self._stop = threading.Event()
        self._reader_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> dict:
        """Connect (or fall back to simulate mode) and start the heartbeat."""
        if not self.force_simulate:
            try:
                self._connect()
            except Exception as e:  # never crash the backend because of hardware
                self.last_error = str(e)
                log.warning("Arduino unavailable, using simulate mode: %s", e)
                self.simulated = True
        if self._heartbeat_thread is None:
            self._heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True, name="arduino-heartbeat")
            self._heartbeat_thread.start()
        return self.status()

    def stop(self) -> None:
        self._stop.set()
        self._close_serial()

    def reconnect(self) -> dict:
        self._close_serial()
        self.force_simulate = False
        try:
            self._connect()
        except Exception as e:
            self.last_error = str(e)
            self.simulated = True
        return self.status()

    # ------------------------------------------------------------------ public API

    def set_alert(self, level: str) -> dict:
        """
        Set the physical alert.
        `level` may be a command (NORMAL/WARNING/CRITICAL/CLEAR)
        or a severity (LOW/MEDIUM/HIGH).
        """
        cmd = str(level).strip().upper()
        cmd = SEVERITY_TO_COMMAND.get(cmd, cmd)
        if cmd not in COMMANDS:
            raise ValueError(f"Unknown alert level '{level}'. Use {list(COMMANDS)} or {list(SEVERITY_TO_COMMAND)}.")

        if self.simulated:
            self._record_ack(cmd)
            return self._result(cmd, ok=True)

        try:
            self._exchange(cmd, expect=f"ACK:{cmd}")
            self._record_ack(cmd)
            return self._result(cmd, ok=True)
        except Exception as e:
            self.last_error = str(e)
            log.error("Arduino command %s failed: %s", cmd, e)
            # one reconnect attempt, then report failure (caller decides what to do)
            try:
                self._close_serial()
                self._connect()
                self._exchange(cmd, expect=f"ACK:{cmd}")
                self._record_ack(cmd)
                return self._result(cmd, ok=True)
            except Exception as e2:
                self.last_error = str(e2)
                self.connected = False
                return self._result(cmd, ok=False, error=str(e2))

    def ping(self) -> bool:
        if self.simulated:
            return True
        try:
            self._exchange("PING", expect="ACK:PING")
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def status(self) -> dict:
        available_ports = self.available_ports()
        with self._state_lock:
            last_button = self._button_acks[-1] if self._button_acks else None
            return {
                "connected": self.connected,
                "simulated": self.simulated,
                "port": self.port,
                "requested_port": self.requested_port,
                "available_ports": available_ports,
                "baud": self.baud,
                "state": self.state,
                "last_ack": self.last_ack,
                "last_ack_at": self.last_ack_at,
                "button_ack_count": len(self._button_acks),
                "last_button_ack_at": last_button["at"] if last_button else None,
                "last_error": self.last_error,
            }

    def button_acks(self, since: Optional[str] = None) -> list[dict]:
        with self._state_lock:
            items = list(self._button_acks)
        if since:
            items = [a for a in items if a["at"] > since]
        return items

    def on_button_ack(self, callback: Callable[[dict], None]) -> None:
        """Register a function called (from a background thread) on every BUTTON_ACK."""
        self._button_listeners.append(callback)

    def simulate_button_press(self) -> dict:
        """For demos/tests without hardware."""
        return self._handle_button_ack(source="simulated")

    # ------------------------------------------------------------------ internals

    @staticmethod
    def available_ports() -> list[dict[str, str]]:
        if list_ports is None:
            return []
        return [
            {
                "device": port.device,
                "description": port.description,
            }
            for port in list_ports.comports()
        ]

    @staticmethod
    def find_port() -> Optional[str]:
        if list_ports is None:
            return None
        for p in list_ports.comports():
            text = f"{p.device} {p.description} {p.manufacturer or ''}".lower()
            if any(
                marker in text
                for marker in ("arduino", "genuino", "usbmodem", "ttyacm")
            ):
                return p.device
        return None

    def _connect(self) -> None:
        if serial is None:
            raise HardwareError("pyserial is not installed (pip install pyserial)")
        port = self.requested_port or self.find_port()
        if not port:
            raise HardwareError(
                "No Arduino-compatible serial port was detected. "
                "Connect the board or set ARDUINO_PORT in Backend/.env."
            )

        self._ser = serial.Serial(port, self.baud, timeout=0.2, write_timeout=1)
        self.port = port
        self._drain_replies()
        if self._reader_thread is None or not self._reader_thread.is_alive():
            self._reader_thread = threading.Thread(target=self._reader, daemon=True, name="arduino-reader")
            self._reader_thread.start()

        # Boards that reset on open need ~2 s; Arduino 101 (native USB) does not reset.
        # Keep pinging until it answers instead of waiting for READY.
        deadline = time.time() + 6
        while time.time() < deadline:
            try:
                self._exchange("PING", expect="ACK:PING", timeout=0.6)
                break
            except Exception:
                continue
        else:
            self._close_serial()
            raise HardwareError(f"Arduino on {port} did not answer PING (wrong port, wrong sketch, or Serial Monitor open?)")

        self.connected = True
        self.simulated = False
        self.last_error = None
        # Sync the board with our known state
        try:
            reply = self._exchange("STATUS", expect=None)
            if reply.startswith("STATUS:"):
                self.state = reply.split(":", 1)[1]
        except Exception:
            pass
        log.info("Arduino connected on %s", port)

    def _close_serial(self) -> None:
        ser, self._ser = self._ser, None
        self.connected = False
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass

    def _drain_replies(self) -> None:
        while not self._replies.empty():
            try:
                self._replies.get_nowait()
            except queue.Empty:
                break

    def _exchange(self, cmd: str, expect: Optional[str], timeout: float = REPLY_TIMEOUT_SECONDS) -> str:
        """Send one command and wait for its reply. Raises on timeout or ERR."""
        with self._io_lock:
            ser = self._ser
            if ser is None:
                raise HardwareError("Serial port not open")
            self._drain_replies()
            ser.write((cmd + "\n").encode("ascii"))
            ser.flush()
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    reply = self._replies.get(timeout=0.05)
                except queue.Empty:
                    continue
                if reply.startswith("ERR"):
                    raise HardwareError(f"Arduino rejected {cmd}: {reply}")
                if expect is None or reply == expect:
                    return reply
            raise HardwareError(f"No reply to {cmd} within {timeout:.1f}s")

    def _reader(self) -> None:
        while not self._stop.is_set():
            ser = self._ser
            if ser is None:
                time.sleep(0.2)
                continue
            try:
                raw = ser.readline()
            except Exception as e:
                self.last_error = f"read error: {e}"
                self.connected = False
                time.sleep(0.5)
                continue
            if not raw:
                continue
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            if line == "BUTTON_ACK":
                self._handle_button_ack(source="arduino")
            elif line == "READY":
                log.info("Arduino reported READY (board rebooted, state reset to NORMAL)")
                with self._state_lock:
                    self.state = "NORMAL"
            else:
                self._replies.put(line)

    def _handle_button_ack(self, source: str) -> dict:
        event = {"type": "BUTTON_ACK", "at": _now(), "state_when_pressed": self.state, "source": source}
        with self._state_lock:
            self._button_acks.append(event)
        log.info("Operator acknowledged alert via button (%s)", source)
        for cb in list(self._button_listeners):
            try:
                cb(event)
            except Exception as e:
                log.error("button listener failed: %s", e)
        return event

    def _heartbeat(self) -> None:
        while not self._stop.wait(HEARTBEAT_SECONDS):
            if self.simulated and self.force_simulate:
                continue
            if self._ser is None:
                # try to recover a dropped connection quietly
                try:
                    self._connect()
                except Exception as e:
                    self.last_error = str(e)
                    self.simulated = True
                continue
            self.connected = self.ping()

    def _record_ack(self, cmd: str) -> None:
        with self._state_lock:
            self.state = COMMAND_TO_STATE[cmd]
            self.last_ack = f"ACK:{cmd}"
            self.last_ack_at = _now()

    def _result(self, cmd: str, ok: bool, error: Optional[str] = None) -> dict:
        res = {
            "ok": ok,
            "command": cmd,
            "ack": f"ACK:{cmd}" if ok else None,
            "hardware_state": self.state,
            "simulated": self.simulated,
        }
        if error:
            res["error"] = error
        return res


# ---------------------------------------------------------------------- singleton

_service: Optional[ArduinoAlertService] = None
_service_lock = threading.Lock()


def get_alert_service() -> ArduinoAlertService:
    global _service
    with _service_lock:
        if _service is None:
            _service = ArduinoAlertService(port=ARDUINO_PORT or None, baud=ARDUINO_BAUD, simulate=ARDUINO_SIMULATE)
        return _service
