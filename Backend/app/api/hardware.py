"""
Hardware API: lets the dashboard and the agent read/drive the Arduino alert.

    GET  /hardware/status          connection + current LED state
    POST /hardware/alert           {"level": "CRITICAL"}  or  {"level": "HIGH"}
    POST /hardware/ping            check the board answers
    POST /hardware/reconnect       retry the USB connection
    GET  /hardware/button-acks     operator button presses (optional ?since=<iso time>)
    POST /hardware/simulate-button demo helper when no board is attached
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.hardware.alert_service import get_alert_service

router = APIRouter(prefix="/hardware", tags=["hardware"])


class AlertRequest(BaseModel):
    level: str          # NORMAL | WARNING | CRITICAL | CLEAR  or  LOW | MEDIUM | HIGH
    reason: Optional[str] = None


@router.get("/status")
def hardware_status():
    return get_alert_service().status()


@router.post("/alert")
def set_alert(req: AlertRequest):
    try:
        result = get_alert_service().set_alert(req.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if req.reason:
        result["reason"] = req.reason
    if not result["ok"]:
        raise HTTPException(status_code=503, detail=result)
    return result


@router.post("/ping")
def ping():
    svc = get_alert_service()
    return {"ok": svc.ping(), "simulated": svc.simulated}


@router.post("/reconnect")
def reconnect():
    return get_alert_service().reconnect()


@router.get("/button-acks")
def button_acks(since: Optional[str] = None):
    return get_alert_service().button_acks(since)


@router.post("/simulate-button")
def simulate_button():
    return get_alert_service().simulate_button_press()