"""APScheduler registration logic."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logging import get_logger


class DigestScheduler:
    def __init__(self) -> None:
        self._logger = get_logger("scheduler")
        self._scheduler = BackgroundScheduler()

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def start(self) -> None:
        if self._scheduler.running:
            return

        self._scheduler.start()
        self._logger.info("スケジューラを起動しました", extra={"run_id": "-"})

    def shutdown(self) -> None:
        if not self._scheduler.running:
            return

        self._scheduler.shutdown(wait=False)
        self._logger.info("スケジューラを停止しました", extra={"run_id": "-"})

    def register_jobs(self) -> None:
        """Register scheduled jobs.

        T501 only starts the scheduler. Job registration is added in T502.
        """
