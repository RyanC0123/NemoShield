
from typing import Any

from app.defense.threat_classification import ThreatClassification
from app.defense.risk_mapping import map_risk_level
from app.defense.recommendation_rules import get_recommended_action


class DecisionEngine:
    """
    Converts AI analysis into deterministic security decisions.

    No firewall operations are performed.
    """

    def decide(self, analysis: dict[str, Any]) -> dict[str, str]:
        if not isinstance(analysis, dict):
            raise ValueError("analysis must be a dictionary")

        raw_classification = analysis.get(
            "classification", "unknown"
        )

        try:
            classification = ThreatClassification(
                raw_classification
            )
        except (ValueError, TypeError):
            classification = ThreatClassification.UNKNOWN

        risk_level = map_risk_level(
            analysis.get("risk_score")
        )

        action = get_recommended_action(
            classification,
            risk_level,
        )

        return {
            "classification": classification.value,
            "risk_level": risk_level.value,
            "action": action.value,
        }
