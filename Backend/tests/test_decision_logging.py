
import json
from datetime import datetime
from uuid import UUID

import pytest

from app.defense.decision_logging import DecisionLoggingService


@pytest.fixture
def logger(tmp_path):
    return DecisionLoggingService(
        tmp_path / "logs" / "decisions.jsonl"
    )


@pytest.fixture
def sample_data():
    event = {
        "event_id": "event-001",
        "source_ip": "192.0.2.10",
    }

    analysis = {
        "classification": "malicious",
        "risk_score": 95,
        "reason": "Repeated failed login attempts",
    }

    decision = {
        "risk_level": "critical",
        "action": "simulated_block",
        "executed": False,
    }

    return event, analysis, decision


def test_log_decision_creates_file(logger, sample_data):
    event, analysis, decision = sample_data

    record = logger.log_decision(
        event, analysis, decision
    )

    assert logger.log_path.exists()
    assert record["event"] == event
    assert record["analysis"] == analysis
    assert record["decision"] == decision

    UUID(record["decision_id"])
    datetime.fromisoformat(record["timestamp"])


def test_log_decision_writes_valid_json(logger, sample_data):
    event, analysis, decision = sample_data

    logger.log_decision(event, analysis, decision)

    lines = logger.log_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored = json.loads(lines[0])

    assert stored["event"]["event_id"] == "event-001"
    assert stored["analysis"]["classification"] == "malicious"
    assert stored["decision"]["action"] == "simulated_block"
    assert stored["decision"]["executed"] is False


def test_multiple_decisions_are_appended(logger, sample_data):
    event, analysis, decision = sample_data

    logger.log_decision(event, analysis, decision)
    logger.log_decision(event, analysis, decision)

    lines = logger.log_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["decision_id"] != second["decision_id"]


@pytest.mark.parametrize(
    "invalid_event, invalid_analysis, invalid_decision",
    [
        (None, {}, {}),
        ({}, None, {}),
        ({}, {}, None),
        ("invalid", {}, {}),
        ({}, "invalid", {}),
        ({}, {}, "invalid"),
    ],
)
def test_invalid_log_inputs(
    logger,
    invalid_event,
    invalid_analysis,
    invalid_decision,
):
    with pytest.raises(ValueError):
        logger.log_decision(
            invalid_event,
            invalid_analysis,
            invalid_decision,
        )


def test_log_does_not_modify_input(logger, sample_data):
    event, analysis, decision = sample_data

    original_event = event.copy()
    original_analysis = analysis.copy()
    original_decision = decision.copy()

    logger.log_decision(event, analysis, decision)

    assert event == original_event
    assert analysis == original_analysis
    assert decision == original_decision
