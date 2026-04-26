"""APScheduler registration logic."""

from __future__ import annotations

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.logging import get_logger

DAILY_DIGEST_JOB_ID = "daily_digest"


class DigestScheduler:
    def __init__(self, *, schedule_hour: int = 8, schedule_minute: int = 0) -> None:
        self._logger = get_logger("scheduler")
        self._scheduler = BackgroundScheduler()
        self._schedule_hour = schedule_hour
        self._schedule_minute = schedule_minute

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def get_jobs(self) -> list[Job]:
        return self._scheduler.get_jobs()

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
        self._logger.info("スケジューラジョブ登録を開始します", extra={"run_id": "-"})

        if self._scheduler.get_job(DAILY_DIGEST_JOB_ID) is None:
            self._scheduler.add_job(
                self._run_scheduled_digest,
                trigger=CronTrigger(hour=self._schedule_hour, minute=self._schedule_minute),
                id=DAILY_DIGEST_JOB_ID,
                replace_existing=False,
            )

        self._logger.info(
            "スケジューラジョブ登録が完了しました: id=%s hour=%s minute=%s",
            DAILY_DIGEST_JOB_ID,
            self._schedule_hour,
            self._schedule_minute,
            extra={"run_id": "-"},
        )

    def _run_scheduled_digest(self) -> None:
        """Placeholder for T503, which wires the digest execution."""
