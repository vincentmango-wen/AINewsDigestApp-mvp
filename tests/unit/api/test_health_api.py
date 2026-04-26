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


def test_openapi_metadata_exposes_title_version_description_and_paths() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert body["info"] == {
        "title": "FocusDigest",
        "version": "v1",
        "description": (
            "FocusDigest MVP API. "
            "ローカル検証用途として、ヘルスチェック、ダイジェスト手動実行、"
            "最新実行結果取得を提供します。"
        ),
    }
    assert "/api/v1/health" in body["paths"]
    assert "/api/v1/jobs/digest/run" in body["paths"]
    assert "/api/v1/jobs/digest/runs/latest" in body["paths"]
