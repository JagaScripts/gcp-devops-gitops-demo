"""Unit tests for the HTTP microservice."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Iterator

import pytest

from app.main import create_server


@pytest.fixture()
def live_server_url() -> Iterator[str]:
    server = create_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_health_endpoint_returns_200_json(live_server_url: str) -> None:
    with urllib.request.urlopen(f"{live_server_url}/health", timeout=3) as resp:
        assert resp.status == 200
        assert "application/json" in resp.headers.get("Content-Type", "")
        payload = json.loads(resp.read().decode("utf-8"))

    assert payload["status"] == "ok"
    assert payload["service"] == "gcp-devops-demo"
    assert "version" in payload
    assert "timestamp" in payload


def test_root_endpoint_lists_available_endpoints(live_server_url: str) -> None:
    with urllib.request.urlopen(f"{live_server_url}/", timeout=3) as resp:
        assert resp.status == 200
        payload = json.loads(resp.read().decode("utf-8"))

    assert "/health" in payload["endpoints"]


def test_unknown_route_returns_404_json(live_server_url: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(f"{live_server_url}/does-not-exist", timeout=3)

    assert exc_info.value.code == 404
    body = json.loads(exc_info.value.read().decode("utf-8"))
    assert body["error"] == "not_found"
    assert body["path"] == "/does-not-exist"
