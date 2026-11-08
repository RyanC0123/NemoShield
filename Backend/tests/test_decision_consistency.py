
import json

import pytest

from app.defense.decision_engine import DecisionEngine
from app.defense.decision_pipeline import DecisionPipeline
from app.defense.decision_logging import DecisionLoggingService


@pytest.fixture
def engine():
    return DecisionEngine()


@pytest.fixture
def pipeline(tmp_path):
    logger = DecisionLoggingService(
        tmp_path / "decisions.jsonl"
    )
    return DecisionPipeline(logger)


@pytest.mark.parametrize(
    "analysis, expected_action",
    [
        (
            {"classification": "benign", "risk_score": 10},
            "monitor",
        ),
        (
            {"classification": "suspicious", "risk_score": 40},
            "monitor",
        ),
        (
            {"classification": "suspicious", "risk_score": 80},
            "investigate",
        ),
        (
            {"classification": "malicious", "risk_score": 40},
            "investigate",
        ),
        (
            {"classification": "malicious", "risk_score": 95},
            "simulated_block",
        ),
        (
            {"classification": "unknown", "risk_score": 95},
            "investigate",
        ),
        (
            {"classification": "malicious", "risk_score": None},
            "investigate",
        ),
    ],
)
def test_deterministic_decisions(engine, analysis, expected_action):
    first = engine.decide(analysis)

    for _ in range(10):
        assert engine.decide(analysis) == first

    assert first["action"] == expected_action


def test_invalid_classification_fails_safe(engine):
    result = engine.decide({
        "classification": "unexpected",
        "risk_score": 95,
    })

    assert result["classification"] == "unknown"
    assert result["action"] == "investigate"


def test_pipeline_creates_audit_log(pipeline):
    event = {
        "event_id": "event-001",
        "source_ip": "192.0.2.10",
    }

    analysis = {
        "classification": "malicious",
        "risk_score": 95,
        "reason": "Repeated failed login attempts",
    }

    result = pipeline.process(event, analysis)

    assert result["event"] == event
    assert result["analysis"] == analysis
    assert result["decision"]["classification"] == "malicious"
    assert result["decision"]["risk_level"] == "critical"
    assert result["decision"]["action"] == "simulated_block"

    response = result["decision"]["response"]

    assert response["status"] == "simulated"
    assert response["executed"] is False

    log_path = pipeline.logging_service.log_path

    assert log_path.exists()

    stored = json.loads(
        log_path.read_text(encoding="utf-8").splitlines()[0]
    )

    assert stored == result


def test_repeated_pipeline_decisions_are_consistent(pipeline):
    event = {"event_id": "event-002"}

    analysis = {
        "classification": "suspicious",
        "risk_score": 85,
    }

    first = pipeline.process(event, analysis)
    second = pipeline.process(event, analysis)

    for key in ("classification", "risk_level", "action"):
        assert first["decision"][key] == second["decision"][key]

    assert first["decision"]["response"]["executed"] is False
    assert second["decision"]["response"]["executed"] is False


@pytest.mark.parametrize(
    "invalid_event",
    [{}, {"event_id": ""}, {"event_id": None}],
)
def test_pipeline_rejects_invalid_event(pipeline, invalid_event):
    with pytest.raises(ValueError):
        pipeline.process(
            invalid_event,
            {"classification": "benign", "risk_score": 5},
        )
