from types import SimpleNamespace

import app.hardware.alert_service as hardware_module
from app.hardware.alert_service import ArduinoAlertService


def make_port(device, description, manufacturer=None):
    return SimpleNamespace(
        device=device,
        description=description,
        manufacturer=manufacturer,
    )


def test_auto_detection_selects_arduino_port(monkeypatch):
    ports = [
        make_port("/dev/cu.Bluetooth-Incoming-Port", "Bluetooth"),
        make_port("/dev/cu.usbmodem1401", "USB Serial", "Arduino LLC"),
    ]
    monkeypatch.setattr(
        hardware_module,
        "list_ports",
        SimpleNamespace(comports=lambda: ports),
    )

    assert ArduinoAlertService.find_port() == "/dev/cu.usbmodem1401"


def test_auto_detection_does_not_select_unrelated_serial_device(monkeypatch):
    ports = [
        make_port("/dev/cu.wlan-debug", "Wireless Debug"),
        make_port("/dev/cu.Bluetooth-Incoming-Port", "Bluetooth"),
    ]
    monkeypatch.setattr(
        hardware_module,
        "list_ports",
        SimpleNamespace(comports=lambda: ports),
    )

    assert ArduinoAlertService.find_port() is None


def test_status_lists_detected_serial_ports(monkeypatch):
    port = make_port("/dev/cu.usbmodem1401", "Arduino 101")
    monkeypatch.setattr(
        hardware_module,
        "list_ports",
        SimpleNamespace(comports=lambda: [port]),
    )
    service = ArduinoAlertService()

    assert service.status()["available_ports"] == [
        {
            "device": "/dev/cu.usbmodem1401",
            "description": "Arduino 101",
        }
    ]
