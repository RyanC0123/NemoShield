
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


def map_risk_level(risk_score: Optional[float]) -> RiskLevel:
    """
    Convert a risk score (0-100) to a risk level.
    Invalid or missing scores return UNKNOWN.
    """

    if risk_score is None:
        return RiskLevel.UNKNOWN

    if isinstance(risk_score, bool):
        return RiskLevel.UNKNOWN

    if not isinstance(risk_score, (int, float)):
        return RiskLevel.UNKNOWN

    if not (0 <= risk_score <= 100):
        return RiskLevel.UNKNOWN

    if risk_score < 25:
        return RiskLevel.LOW

    if risk_score < 50:
        return RiskLevel.MEDIUM

    if risk_score < 75:
        return RiskLevel.HIGH

    return RiskLevel.CRITICAL
