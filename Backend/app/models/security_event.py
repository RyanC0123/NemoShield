
from datetime import datetime
from enum import Enum
import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    field_validator,
)


class EventType(str, Enum):
    NORMAL_TRAFFIC = "normal_traffic"
    SUSPICIOUS_LOGIN = "suspicious_login"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    event_id: str = Field(min_length=1)
    timestamp: datetime
    source_ip: IPvAnyAddress
    destination_ip: IPvAnyAddress
    event_type: EventType
    severity: Severity

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, value: str) -> str:
        if not re.fullmatch(r"EVT-[0-9]{4}", value):
            raise ValueError(
                "event_id must follow EVT-0001 format"
            )
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "timestamp must include timezone information"
            )
        return value
  