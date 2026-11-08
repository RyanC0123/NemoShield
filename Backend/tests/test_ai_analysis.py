
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from openai import APITimeoutError

from app.agent.analysis_service import AIAnalysisService
from app.agent.nemotron_client import NemotronClient
from app.models.security_event import SecurityEvent


EventType = SecurityEvent.model_fields["event_type"].annotation
Severity = SecurityEvent.model_fields["severity"].annotation


def make_event(event_type=EventType.BRUTE_FORCE):
    return SecurityEvent(
        event_id="EVT-0001",
        timestamp=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        destination_ip="10.0.0.5",
        event_type=event_type,
        severity=Severity.HIGH,
    )


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.prompts = []

    def generate_response(self, prompt):
        self.prompts.append(prompt)

        if self.error:
            raise self.error

        return self.response

    def generate_response_with_tools(
        self,
        prompt,
        tool_handler,
    ):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        event_id = "EVT-0001"
        tool_result = tool_handler(
            "lookup_related_events",
            {"event_id": event_id},
        )
        return self.response, [
            {
                "name": "lookup_related_events",
                "arguments": {"event_id": event_id},
                "result": {
                    "event_count": tool_result["event_count"],
                    "event_ids": tool_result["event_ids"],
                },
                "status": "completed",
            }
        ]


@pytest.mark.parametrize(
    "event_type, expected",
    [
        (EventType.NORMAL_TRAFFIC, "benign"),
        (EventType.SUSPICIOUS_LOGIN, "suspicious"),
        (EventType.PORT_SCAN, "suspicious"),
        (EventType.BRUTE_FORCE, "malicious"),
    ]
)
def test_mock_scenarios(event_type, expected):
    service = AIAnalysisService(mock_mode=True)
    result = service.analyze(make_event(event_type))

    assert result["classification"] == expected
    assert isinstance(result["risk_score"], int)
    assert 0 <= result["risk_score"] <= 100
    assert result["reason"]
    assert result["recommended_action"]


def test_mock_is_deterministic():
    service = AIAnalysisService(mock_mode=True)
    event = make_event()

    assert service.analyze(event) == service.analyze(event)


def test_valid_ai_response():
    response = json.dumps({
        "classification": "malicious",
        "risk_score": 90,
        "reason": "Repeated authentication attempts.",
        "recommended_action": "Review authentication logs."
    })

    fake = FakeClient(response=response)
    service = AIAnalysisService(ai_client=fake)

    result = service.analyze(make_event())

    assert result["classification"] == "malicious"
    assert result["risk_score"] == 90
    assert "brute_force" in fake.prompts[0]


def test_analysis_returns_read_only_tool_trace():
    response = json.dumps({
        "classification": "suspicious",
        "risk_score": 65,
        "reason": "Related activity needs review.",
        "recommended_action": "Review authentication logs.",
    })
    service = AIAnalysisService(ai_client=FakeClient(response=response))

    result, tool_calls = service.analyze_with_trace(make_event())

    assert result["classification"] == "suspicious"
    assert tool_calls[0]["name"] == "lookup_related_events"
    assert tool_calls[0]["status"] == "completed"
    assert tool_calls[0]["result"]["event_count"] == 0


def test_nemotron_client_runs_and_traces_read_only_tool_call():
    class ToolMessage:
        tool_calls = [
            SimpleNamespace(
                id="call-1",
                function=SimpleNamespace(
                    name="lookup_related_events",
                    arguments='{"event_id":"EVT-0001"}',
                ),
            )
        ]

        @staticmethod
        def model_dump(exclude_none=True):
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "lookup_related_events",
                            "arguments": '{"event_id":"EVT-0001"}',
                        },
                    }
                ],
            }

    responses = iter(
        [
            SimpleNamespace(
                choices=[SimpleNamespace(message=ToolMessage())]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"ok":true}')
                    )
                ]
            ),
        ]
    )
    requests = []

    class Completions:
        def create(self, **kwargs):
            requests.append(kwargs)
            return next(responses)

    client = NemotronClient.__new__(NemotronClient)
    client.client = SimpleNamespace(
        chat=SimpleNamespace(completions=Completions())
    )
    client.model = "test-model"
    executed = []

    answer, traces = client.generate_response_with_tools(
        "Analyze EVT-0001",
        lambda name, arguments: (
            executed.append((name, arguments))
            or {"event_count": 0, "event_ids": [], "events": []}
        ),
    )

    assert answer == '{"ok":true}'
    assert executed == [
        ("lookup_related_events", {"event_id": "EVT-0001"})
    ]
    assert traces[0]["status"] == "completed"
    assert requests[0]["tool_choice"] == "required"
    assert requests[1]["messages"][-1]["role"] == "tool"
    assert requests[1]["tool_choice"] == "none"


def test_invalid_json():
    fake = FakeClient(response="invalid json")
    service = AIAnalysisService(ai_client=fake)

    result = service.analyze(make_event())

    assert result["classification"] == "unknown"
    assert result["risk_score"] is None


def test_invalid_risk_score():
    response = json.dumps({
        "classification": "malicious",
        "risk_score": 150,
        "reason": "Invalid score",
        "recommended_action": "Review logs"
    })

    fake = FakeClient(response=response)
    service = AIAnalysisService(ai_client=fake)

    result = service.analyze(make_event())

    assert result["classification"] == "unknown"
    assert result["risk_score"] is None


def test_model_error():
    fake = FakeClient(error=RuntimeError("Model unavailable"))
    service = AIAnalysisService(ai_client=fake)

    result = service.analyze(make_event())

    assert result["classification"] == "unknown"
    assert "unavailable" in result["reason"]


def test_timeout():
    request = __import__("httpx").Request(
        "POST", "https://example.com"
    )
    error = APITimeoutError(request=request)

    fake = FakeClient(error=error)
    service = AIAnalysisService(ai_client=fake)

    result = service.analyze(make_event())

    assert result["classification"] == "unknown"
    assert result["risk_score"] is None
    assert "timed out" in result["reason"]
