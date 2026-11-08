
import math

import pytest

from app.defense.risk_mapping import RiskLevel, map_risk_level


@pytest.mark.parametrize(
    "score, expected",
    [
        (0, RiskLevel.LOW),
        (24, RiskLevel.LOW),
        (25, RiskLevel.MEDIUM),
        (49, RiskLevel.MEDIUM),
        (50, RiskLevel.HIGH),
        (74, RiskLevel.HIGH),
        (75, RiskLevel.CRITICAL),
        (100, RiskLevel.CRITICAL),
        (37.5, RiskLevel.MEDIUM),
    ],
)
def test_risk_level_mapping(score, expected):
    assert map_risk_level(score) == expected


@pytest.mark.parametrize(
    "score",
    [
        None,
        -1,
        101,
        "high",
        True,
        False,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_invalid_risk_score(score):
    assert map_risk_level(score) == RiskLevel.UNKNOWN
