from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


def test_get_health_returns_common_success_response() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "成功"
    assert body["data"]["status"] == "ok"
    assert body["data"]["app_name"] == "FocusDigest"
    datetime.fromisoformat(body["data"]["timestamp"])
