"""Run history update service."""

from __future__ import annotations

from typing import Protocol

from app.schemas.digest_run import DigestRun, EmailStatus, TriggeredBy


class RunHistoryRepository(Protocol):
    def create_run(self, triggered_by: TriggeredBy) -> DigestRun:
        ...

    def update_result(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: EmailStatus,
        error_message: str | None = None,
    ) -> DigestRun:
        ...

    def get_latest(self) -> DigestRun | None:
        ...


class RunHistoryService:
    def __init__(self, digest_run_repository: RunHistoryRepository) -> None:
        self._digest_run_repository = digest_run_repository

    def start_run(self, triggered_by: TriggeredBy) -> DigestRun:
        return self._digest_run_repository.create_run(triggered_by)

    def finish_run(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: EmailStatus,
    ) -> DigestRun:
        return self._digest_run_repository.update_result(
            run_id,
            fetched_count=fetched_count,
            selected_count=selected_count,
            summarized_count=summarized_count,
            email_status=email_status,
            error_message=None,
        )

    def fail_run(self, run_id: int, error_message: str) -> DigestRun:
        return self._digest_run_repository.update_result(
            run_id,
            fetched_count=0,
            selected_count=0,
            summarized_count=0,
            email_status="failed",
            error_message=error_message,
        )

    def get_latest_run(self) -> DigestRun | None:
        return self._digest_run_repository.get_latest()
