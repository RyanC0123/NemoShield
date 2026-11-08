
from datetime import datetime
from uuid import UUID

import pytest

from app.defense.simulated_response import SimulatedResponseService
from app.defense.recommendation_rules import RecommendedAction


@pytest.fixture
def service():
    return SimulatedResponseService()


@pytest.mark.parametrize(
    "action",
    [
        RecommendedAction.MONITOR,
        RecommendedAction.INVESTIGATE,
        RecommendedAction.SIMULATED_BLOCK,
    ],
)
def test_simulated_response_record(service, action):
    result = service.simulate(action, "event-001")

    assert result["event_id"] == "event-001"
    assert result["action"] == action.value
    assert result["status"] == "simulated"
    assert result["executed"] is False
    assert result["message"]

    UUID(result["response_id"])
    datetime.fromisoformat(result["timestamp"])


def test_response_ids_are_unique(service):
    first = service.simulate(
        RecommendedAction.MONITOR,
        "event-001",
    )

    second = service.simulate(
        RecommendedAction.MONITOR,
        "event-001",
    )

    assert first["response_id"] != second["response_id"]


def test_invalid_action_rejected(service):
    with pytest.raises(ValueError):
        service.simulate("real_block", "event-001")


@pytest.mark.parametrize(
    "event_id",
    ["", "   ", None, 123],
)
def test_invalid_event_id_rejected(service, event_id):
    with pytest.raises(ValueError):
        service.simulate(
            RecommendedAction.MONITOR,
            event_id,
        )


def test_simulated_block_never_executes(service):
    result = service.simulate(
        RecommendedAction.SIMULATED_BLOCK,
        "event-attack-001",
    )

    assert result["executed"] is False
    assert result["status"] == "simulated"
    assert "No firewall changes" in result["message"]
