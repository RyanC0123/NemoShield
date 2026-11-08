
from fastapi.testclient import TestClient

from app.main import app


def test_internal_server_error():
    def raise_unexpected_error():
        raise RuntimeError("Sensitive internal test error")

    app.add_api_route(
        "/api/test-internal-error",
        raise_unexpected_error,
        methods=["GET"],
        include_in_schema=False,
    )

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = client.get("/api/test-internal-error")

    assert response.status_code == 500

    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred",
        }
    }

    assert "Sensitive internal test error" not in response.text
