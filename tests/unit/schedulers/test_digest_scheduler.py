from __future__ import annotations

from app.schedulers.digest_scheduler import DigestScheduler


def test_digest_scheduler_start_and_shutdown_manage_running_state() -> None:
    scheduler = DigestScheduler()

    assert scheduler.running is False

    scheduler.start()

    assert scheduler.running is True

    scheduler.shutdown()

    assert scheduler.running is False
