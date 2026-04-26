from __future__ import annotations

from app.schemas.digest_run import DigestRun
from app.services.run_history_service import RunHistoryService


def build_digest_run(
    run_id: int,
    *,
    triggered_by: str = "manual",
    finished_at: str | None = None,
    fetched_count: int = 0,
    selected_count: int = 0,
    summarized_count: int = 0,
    email_status: str = "skipped",
    error_message: str | None = None,
) -> DigestRun:
    return DigestRun(
        run_id=run_id,
        triggered_by=triggered_by,
        started_at="2026-04-26T09:00:00Z",
        finished_at=finished_at,
        fetched_count=fetched_count,
        selected_count=selected_count,
        summarized_count=summarized_count,
        email_status=email_status,
        error_message=error_message,
        created_at="2026-04-26T09:00:00Z",
        updated_at="2026-04-26T09:00:00Z",
    )


class DummyDigestRunRepository:
    def __init__(self) -> None:
        self.created_triggered_by: list[str] = []
        self.updated_calls: list[dict[str, object]] = []
        self.latest_run: DigestRun | None = None

    def create_run(self, triggered_by: str) -> DigestRun:
        self.created_triggered_by.append(triggered_by)
        return build_digest_run(1, triggered_by=triggered_by)

    def update_result(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: str,
        error_message: str | None = None,
    ) -> DigestRun:
        self.updated_calls.append(
            {
                "run_id": run_id,
                "fetched_count": fetched_count,
                "selected_count": selected_count,
                "summarized_count": summarized_count,
                "email_status": email_status,
                "error_message": error_message,
            }
        )
        return build_digest_run(
            run_id,
            finished_at="2026-04-26T09:05:00Z",
            fetched_count=fetched_count,
            selected_count=selected_count,
            summarized_count=summarized_count,
            email_status=email_status,
            error_message=error_message,
        )

    def get_latest(self) -> DigestRun | None:
        return self.latest_run


def test_start_run_creates_digest_run() -> None:
    repository = DummyDigestRunRepository()
    service = RunHistoryService(repository)

    run = service.start_run("manual")

    assert repository.created_triggered_by == ["manual"]
    assert run.triggered_by == "manual"


def test_finish_run_updates_counts_and_email_status() -> None:
    repository = DummyDigestRunRepository()
    service = RunHistoryService(repository)

    run = service.finish_run(
        1,
        fetched_count=3,
        selected_count=2,
        summarized_count=2,
        email_status="success",
    )

    assert repository.updated_calls == [
        {
            "run_id": 1,
            "fetched_count": 3,
            "selected_count": 2,
            "summarized_count": 2,
            "email_status": "success",
            "error_message": None,
        }
    ]
    assert run.email_status == "success"
    assert run.finished_at == "2026-04-26T09:05:00Z"


def test_fail_run_marks_run_as_failed_with_error_message_and_counts() -> None:
    repository = DummyDigestRunRepository()
    service = RunHistoryService(repository)

    run = service.fail_run(
        1,
        "ニュース取得に失敗しました",
        fetched_count=3,
        selected_count=2,
        summarized_count=1,
    )

    assert repository.updated_calls == [
        {
            "run_id": 1,
            "fetched_count": 3,
            "selected_count": 2,
            "summarized_count": 1,
            "email_status": "failed",
            "error_message": "ニュース取得に失敗しました",
        }
    ]
    assert run.email_status == "failed"
    assert run.error_message == "ニュース取得に失敗しました"


def test_get_latest_run_returns_latest_digest_run() -> None:
    repository = DummyDigestRunRepository()
    repository.latest_run = build_digest_run(2, triggered_by="scheduler")
    service = RunHistoryService(repository)

    run = service.get_latest_run()

    assert run is not None
    assert run.run_id == 2
    assert run.triggered_by == "scheduler"
