
import pytest

from app.defense.threat_classification import ThreatClassification
from app.defense.risk_mapping import RiskLevel
from app.defense.recommendation_rules import (
    RecommendedAction,
    get_recommended_action,
)


@pytest.mark.parametrize(
    "classification, risk_level, expected",
    [
        (ThreatClassification.BENIGN, RiskLevel.LOW, RecommendedAction.MONITOR),
        (ThreatClassification.BENIGN, RiskLevel.CRITICAL, RecommendedAction.MONITOR),

        (ThreatClassification.SUSPICIOUS, RiskLevel.LOW, RecommendedAction.MONITOR),
        (ThreatClassification.SUSPICIOUS, RiskLevel.MEDIUM, RecommendedAction.MONITOR),
        (ThreatClassification.SUSPICIOUS, RiskLevel.HIGH, RecommendedAction.INVESTIGATE),
        (ThreatClassification.SUSPICIOUS, RiskLevel.CRITICAL, RecommendedAction.INVESTIGATE),

        (ThreatClassification.MALICIOUS, RiskLevel.LOW, RecommendedAction.INVESTIGATE),
        (ThreatClassification.MALICIOUS, RiskLevel.MEDIUM, RecommendedAction.INVESTIGATE),
        (ThreatClassification.MALICIOUS, RiskLevel.HIGH, RecommendedAction.SIMULATED_BLOCK),
        (ThreatClassification.MALICIOUS, RiskLevel.CRITICAL, RecommendedAction.SIMULATED_BLOCK),

        (ThreatClassification.UNKNOWN, RiskLevel.HIGH, RecommendedAction.INVESTIGATE),
        (ThreatClassification.MALICIOUS, RiskLevel.UNKNOWN, RecommendedAction.INVESTIGATE),
    ],
)
def test_recommendation_rules(classification, risk_level, expected):
    assert get_recommended_action(classification, risk_level) == expected


def test_invalid_classification_fails_safe():
    result = get_recommended_action("invalid", RiskLevel.HIGH)
    assert result == RecommendedAction.INVESTIGATE


def test_invalid_risk_level_fails_safe():
    result = get_recommended_action(ThreatClassification.MALICIOUS, "invalid")
    assert result == RecommendedAction.INVESTIGATE
