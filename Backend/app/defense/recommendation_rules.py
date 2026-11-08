
from enum import Enum

from app.defense.threat_classification import ThreatClassification
from app.defense.risk_mapping import RiskLevel


class RecommendedAction(str, Enum):
    MONITOR = "monitor"
    INVESTIGATE = "investigate"
    SIMULATED_BLOCK = "simulated_block"


def get_recommended_action(
    classification: ThreatClassification,
    risk_level: RiskLevel,
) -> RecommendedAction:
    """
    Determine a safe recommended action using fixed rules.

    This function only returns a recommendation.
    It never performs any firewall operation.
    """

    if not isinstance(classification, ThreatClassification):
        return RecommendedAction.INVESTIGATE

    if not isinstance(risk_level, RiskLevel):
        return RecommendedAction.INVESTIGATE

    if (
        classification == ThreatClassification.UNKNOWN
        or risk_level == RiskLevel.UNKNOWN
    ):
        return RecommendedAction.INVESTIGATE

    if classification == ThreatClassification.BENIGN:
        return RecommendedAction.MONITOR

    if classification == ThreatClassification.SUSPICIOUS:
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return RecommendedAction.INVESTIGATE

        return RecommendedAction.MONITOR

    if classification == ThreatClassification.MALICIOUS:
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return RecommendedAction.SIMULATED_BLOCK

        return RecommendedAction.INVESTIGATE

    return RecommendedAction.INVESTIGATE
