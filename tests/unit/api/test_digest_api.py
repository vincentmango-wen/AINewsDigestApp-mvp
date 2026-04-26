from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.digest import get_digest_service, get_run_history_service
from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, DatabaseError, JobAlreadyRunningError
from app.main import app
from app.schemas.article import SaveArticlesResult
from app.schemas.digest_run import DigestRun
from app.services.digest_service import DigestExecutionResult


def build_digest_run(*, email_status: str = "success", error_message: str | None = None) -> DigestRun:
    return DigestRun(
        run_id=12,
        triggered_by="manual",
        started_at="2026-04-18T08:00:00+09:00",
        finished_at="2026-04-18T08:01:42+09:00",
        fetched_count=20,
        selected_count=5,
        summarized_count=4,
        email_status=email_status,
        error_message=error_message,
        created_at="2026-04-18T08:00:00+09:00",
        updated_at="2026-04-18T08:01:42+09:00",
    )


class StubDigestService:
    def __init__(
        self,
        *,
        result: DigestExecutionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def run(self, triggered_by: str) -> DigestExecutionResult:
        self.calls.append(triggered_by)
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


class StubRunHistoryService:
    def __init__(
        self,
        *,
        latest_run: DigestRun | None = None,
        error: Exception | None = None,
    ) -> None:
        self._latest_run = latest_run
        self._error = error
        self.calls = 0

    def get_latest_run(self) -> DigestRun | None:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._latest_run


def build_success_result() -> DigestExecutionResult:
    digest_run = build_digest_run()
    return DigestExecutionResult(
        run=digest_run,
        saved_articles=SaveArticlesResult(created_count=20, skipped_count=0),
        selected_articles=[],
        summarized_articles=[],
    )


def test_run_digest_returns_success_response() -> None:
    stub_service = StubDigestService(result=build_success_result())
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 200
    assert stub_service.calls == ["manual"]
    assert response.json() == {
        "success": True,
        "data": {
            "run_id": 12,
            "triggered_by": "manual",
            "started_at": "2026-04-18T08:00:00+09:00",
            "finished_at": "2026-04-18T08:01:42+09:00",
            "fetched_count": 20,
            "selected_count": 5,
            "summarized_count": 4,
            "email_status": "success",
            "error_message": None,
        },
        "message": "ダイジェスト処理が完了しました",
    }
    app.dependency_overrides.clear()


def test_run_digest_accepts_empty_json_body() -> None:
    stub_service = StubDigestService(result=build_success_result())
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run", json={})

    assert response.status_code == 200
    assert stub_service.calls == ["manual"]
    app.dependency_overrides.clear()


def test_run_digest_rejects_non_empty_json_body() -> None:
    stub_service = StubDigestService(result=build_success_result())
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run", json={"unexpected": True})

    assert response.status_code == 400
    assert stub_service.calls == []
    assert response.json() == {
        "success": False,
        "error_code": "VALIDATION_ERROR",
        "message": "リクエストボディは空または空JSONのみ許可されています",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_400_for_configuration_error() -> None:
    stub_service = StubDigestService(error=ConfigurationError("必須設定が不足しています"))
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error_code": "CONFIGURATION_ERROR",
        "message": "必須設定が不足しています",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_400_for_settings_resolution_error() -> None:
    def raise_configuration_error() -> None:
        raise ConfigurationError("必須設定が不足しています")

    app.dependency_overrides[get_settings] = raise_configuration_error
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error_code": "CONFIGURATION_ERROR",
        "message": "必須設定が不足しています",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_409_for_running_job() -> None:
    stub_service = StubDigestService(error=JobAlreadyRunningError("ダイジェスト処理は既に実行中です"))
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "error_code": "JOB_ALREADY_RUNNING",
        "message": "ダイジェスト処理は既に実行中です",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_500_for_processing_error() -> None:
    stub_service = StubDigestService(error=DatabaseError("実行履歴の更新に失敗しました"))
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error_code": "DATABASE_ERROR",
        "message": "実行履歴の更新に失敗しました",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_400_for_request_validation_error() -> None:
    stub_service = StubDigestService(result=build_success_result())
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app)

    response = client.post("/api/v1/jobs/digest/run", json=[])

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "error_code": "VALIDATION_ERROR",
        "message": "入力値が不正です",
    }
    app.dependency_overrides.clear()


def test_run_digest_returns_500_for_unexpected_error() -> None:
    stub_service = StubDigestService(error=RuntimeError("unexpected"))
    app.dependency_overrides[get_digest_service] = lambda: stub_service
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post("/api/v1/jobs/digest/run")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "サーバー内部エラーが発生しました",
    }
    app.dependency_overrides.clear()


def test_get_latest_digest_run_returns_success_response() -> None:
    stub_service = StubRunHistoryService(latest_run=build_digest_run())
    app.dependency_overrides[get_run_history_service] = lambda: stub_service
    client = TestClient(app)

    response = client.get("/api/v1/jobs/digest/runs/latest")

    assert response.status_code == 200
    assert stub_service.calls == 1
    assert response.json() == {
        "success": True,
        "data": {
            "run_id": 12,
            "triggered_by": "manual",
            "started_at": "2026-04-18T08:00:00+09:00",
            "finished_at": "2026-04-18T08:01:42+09:00",
            "fetched_count": 20,
            "selected_count": 5,
            "summarized_count": 4,
            "email_status": "success",
            "error_message": None,
        },
        "message": "成功",
    }
    app.dependency_overrides.clear()


def test_get_latest_digest_run_returns_404_when_no_history_exists() -> None:
    stub_service = StubRunHistoryService(latest_run=None)
    app.dependency_overrides[get_run_history_service] = lambda: stub_service
    client = TestClient(app)

    response = client.get("/api/v1/jobs/digest/runs/latest")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error_code": "NOT_FOUND",
        "message": "直近の実行履歴が存在しません",
    }
    app.dependency_overrides.clear()


def test_get_latest_digest_run_returns_500_for_repository_error() -> None:
    stub_service = StubRunHistoryService(error=DatabaseError("最新の実行履歴の取得に失敗しました"))
    app.dependency_overrides[get_run_history_service] = lambda: stub_service
    client = TestClient(app)

    response = client.get("/api/v1/jobs/digest/runs/latest")

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error_code": "DATABASE_ERROR",
        "message": "最新の実行履歴の取得に失敗しました",
    }
    app.dependency_overrides.clear()
