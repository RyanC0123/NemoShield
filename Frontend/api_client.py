"""HTTP client for the NemoShield backend API."""
import json
import os
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class APIError(RuntimeError):
    """A backend request failed or returned an invalid response."""


def request_json(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    payload: Optional[dict[str, Any]] = None,
) -> Any:
    base_url = os.getenv(
        "NEMOSHIELD_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")
    query = f"?{urlencode(params)}" if params else ""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{base_url}{path}{query}",
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method=method,
    )

    try:
        with urlopen(request, timeout=10) as response:
            response_body = response.read()
    except HTTPError as exc:
        response_body = exc.read()
        try:
            error_data = json.loads(response_body)
        except json.JSONDecodeError:
            error_message = f"Backend returned HTTP {exc.code}."
        else:
            error_message = (
                error_data.get("error", {}).get("message")
                or error_data.get("detail")
                or f"Backend returned HTTP {exc.code}."
            )
        raise APIError(f"{path}: {error_message}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise APIError(
            f"Could not reach NemoShield API at {base_url} for {path}: {exc}"
        ) from exc

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise APIError(
            f"NemoShield API returned invalid JSON for {path}."
        ) from exc


def api_get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    return request_json("GET", path, params=params)


def api_post(path: str, payload: Optional[dict[str, Any]] = None) -> Any:
    return request_json("POST", path, payload=payload)
