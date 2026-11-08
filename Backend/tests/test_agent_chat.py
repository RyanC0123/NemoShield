
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_agent_chat_success():
    with patch(
        "app.api.agent_routes.NemotronClient"
    ) as mock_client:
        mock_client.return_value.generate_response.return_value = (
            "A firewall filters network traffic."
        )

        with TestClient(app) as client:
            response = client.post(
                "/api/agent/chat",
                json={"message": "What is a firewall?"}
            )

    assert response.status_code == 200
    assert response.json() == {
        "response": "A firewall filters network traffic."
    }


def test_agent_chat_empty_message():
    with TestClient(app) as client:
        response = client.post(
            "/api/agent/chat",
            json={"message": ""}
        )

    assert response.status_code == 422
