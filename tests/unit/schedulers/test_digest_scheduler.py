from __future__ import annotations

from apscheduler.triggers.cron import CronTrigger
import pytest

from app.schedulers.digest_scheduler import DAILY_DIGEST_JOB_ID, DigestScheduler


def test_digest_scheduler_start_and_shutdown_manage_running_state() -> None:
    scheduler = DigestScheduler()

    assert scheduler.running is False

    scheduler.start()

    assert scheduler.running is True

    scheduler.shutdown()

    assert scheduler.running is False


def test_digest_scheduler_registers_one_daily_job_at_0800() -> None:
    scheduler = DigestScheduler()

    scheduler.register_jobs()

    jobs = scheduler.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == DAILY_DIGEST_JOB_ID
    assert isinstance(jobs[0].trigger, CronTrigger)
    assert str(jobs[0].trigger) == "cron[hour='8', minute='0']"


def test_digest_scheduler_does_not_duplicate_registered_job() -> None:
    scheduler = DigestScheduler()

    scheduler.register_jobs()
    scheduler.register_jobs()

    jobs = scheduler.get_jobs()

    assert len(jobs) == 1


def test_digest_scheduler_runs_digest_job_with_scheduler_trigger() -> None:
    calls: list[str] = []

    def run_digest_job() -> None:
        calls.append("called")

    scheduler = DigestScheduler(run_digest_job=run_digest_job)

    scheduler._run_scheduled_digest()

    assert calls == ["called"]


def test_digest_scheduler_reraises_digest_job_errors() -> None:
    def run_digest_job() -> None:
        raise RuntimeError("boom")

    scheduler = DigestScheduler(run_digest_job=run_digest_job)

    with pytest.raises(RuntimeError, match="boom"):
        scheduler._run_scheduled_digest()
