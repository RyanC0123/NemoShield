
import os
import subprocess

import pytest

from app.defense.firewall_safety import (
    FirewallSafetyError,
    FirewallSafetyGuard,
)
from app.defense.recommendation_rules import RecommendedAction
from app.defense.simulated_response import SimulatedResponseService


@pytest.mark.parametrize(
    "action",
    [
        RecommendedAction.MONITOR,
        RecommendedAction.INVESTIGATE,
        RecommendedAction.SIMULATED_BLOCK,
    ],
)
def test_allowed_simulation_actions(action):
    assert FirewallSafetyGuard.validate_action(action) is None


@pytest.mark.parametrize(
    "action",
    [
        "block",
        "iptables",
        "nftables",
        "cloud_block",
        None,
        123,
    ],
)
def test_real_or_invalid_actions_rejected(action):
    with pytest.raises(FirewallSafetyError):
        FirewallSafetyGuard.validate_action(action)


def test_simulation_never_invokes_system_commands(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("System execution is forbidden")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "call", forbidden)
    monkeypatch.setattr(subprocess, "check_call", forbidden)
    monkeypatch.setattr(subprocess, "check_output", forbidden)

    monkeypatch.setattr(os, "system", forbidden)
    monkeypatch.setattr(os, "popen", forbidden)

    service = SimulatedResponseService()

    for action in RecommendedAction:
        response = service.simulate(
            action,
            "event-safety-001",
        )

        assert response["executed"] is False
        assert response["status"] == "simulated"


def test_real_block_action_is_rejected():
    service = SimulatedResponseService()

    with pytest.raises(ValueError):
        service.simulate(
            "block",
            "event-001",
        )
