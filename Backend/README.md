# NemoShield Backend

## Run locally

From the project root:

```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

## Ingest normalized events

`POST /api/events` accepts a validated `SecurityEvent` and persists it in
`Backend/data/ingested_events.jsonl`. Ingested events appear in the event list,
dashboard summary, alerts, analysis, and trend views. Event IDs must be unique
and use the `EVT-0001` format; timestamps must include a timezone. Repeating an
identical event is safe and does not create a duplicate.

This is a generic normalized-event webhook, not a vendor collector. An
integration or collector must translate its source events into this schema and
POST them to the endpoint.

Configure a private token in `Backend/.env` before accepting events:

```dotenv
NEMOSHIELD_INGEST_TOKEN=<long-random-secret>
```

Send that token in the `Authorization: Bearer` header. For example:

```bash
curl -X POST http://127.0.0.1:8000/api/events \
  -H "Authorization: Bearer $NEMOSHIELD_INGEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT-9001",
    "timestamp": "2026-11-08T12:00:00Z",
    "source_ip": "192.0.2.90",
    "destination_ip": "198.51.100.90",
    "event_type": "suspicious_login",
    "severity": "high"
  }'
```

The backend binds to loopback in the local run command above. Only expose the
ingestion API to a trusted collector over a protected network; do not put the
ingestion token in frontend code or browser requests.

## Arduino

Leave `ARDUINO_PORT` empty to auto-detect an Arduino-compatible serial device,
or set it to the port shown by Arduino IDE. The backend retries detection while
running, so a board connected after startup can be found. `ARDUINO_BAUD`
defaults to 9600.

Upload `nemoshield_uno_7525.ino` to the board. The firmware and backend use the
same line-based serial protocol. Use a data-capable USB cable and close Arduino
IDE's Serial Monitor before connecting from NemoShield. The Arduino Monitor
page lists serial ports macOS can currently see. A listed port confirms USB
enumeration only; the backend's ping must also succeed to verify the firmware.
If the board is unavailable, the application reports simulation mode instead
of claiming hardware control.

## AI validation

Set `NVIDIA_API_KEY` in `Backend/.env`. The frontend displays whether a key is
configured and offers an explicit connection-test action. The test makes a
small request to Nemotron only when clicked. Set `NEMOSHIELD_AI_MOCK_MODE=true`
to use deterministic mock analysis instead of live model calls.

Live analysis uses Nemotron function calling for a required, read-only lookup
of up to five recent events from the same source IP. The call and a minimized
result summary are persisted in investigation traces. No exposed tool changes
firewall rules or otherwise modifies the system.

## Persisted operations

- `POST /api/alerts/{alert_id}/acknowledge` records an acknowledgment.
- `GET /api/decisions` lists decision records from `data/decisions.jsonl`.
- `GET /api/traces` lists analysis and decision workflow traces from
  `data/investigation_traces.jsonl`.
- Firewall decisions remain recommendation-only: `simulated_block` does not
  modify firewall rules and always reports `executed: false`.

When an operator explicitly runs `POST /api/analyze-and-decide`, the resulting
recommendation also updates the Arduino alert: `monitor` sets NORMAL (green),
`investigate` sets WARNING (yellow blink), and `simulated_block` sets CRITICAL
(red blink and buzzer). This only controls the indicator board; it never blocks
network traffic. Hardware acknowledgment and whether the command was simulated
are included in the decision record. Use `POST /hardware/alert` with
`{"level":"CLEAR"}` to stop an active alert and return the board to NORMAL.