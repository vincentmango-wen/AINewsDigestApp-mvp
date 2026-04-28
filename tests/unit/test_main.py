from __future__ import annotations

from pathlib import Path

from apscheduler.triggers.cron import CronTrigger
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings
from app.schedulers.digest_scheduler import DAILY_DIGEST_JOB_ID


class StubLogger:
    def info(self, *_args, **_kwargs) -> None:
        pass


class StubDigestScheduler:
    def __init__(self) -> None:
        self.registered = False
        self.started = False
        self.stopped = False

    def register_jobs(self) -> None:
        self.registered = True

    def start(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.stopped = True


def test_lifespan_starts_and_stops_digest_scheduler(monkeypatch) -> None:
    stub_scheduler = StubDigestScheduler()

    monkeypatch.setattr("app.main.configure_logging", lambda: StubLogger())
    monkeypatch.setattr("app.main.initialize_database", lambda: None)
    monkeypatch.setattr("app.main.build_digest_scheduler", lambda: stub_scheduler)

    with TestClient(app):
        assert stub_scheduler.registered is True
        assert stub_scheduler.started is True
        assert app.state.digest_scheduler is stub_scheduler
        assert stub_scheduler.stopped is False

    assert stub_scheduler.stopped is True


def test_build_digest_scheduler_registers_one_job_with_configured_schedule(monkeypatch) -> None:
    settings = Settings(
        category="AI",
        THE_NEWS_API_TOKEN="token",
        openai_api_key="openai-key",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="app-password",
        mail_from_address="user@example.com",
        mail_to_address="to@example.com",
        db_path=Path("/tmp/app.db"),
        log_path=Path("/tmp/app.log"),
        schedule_hour=9,
        schedule_minute=30,
    )

    monkeypatch.setattr("app.main.get_settings", lambda: settings)

    from app.main import build_digest_scheduler

    scheduler = build_digest_scheduler()
    scheduler.register_jobs()
    jobs = scheduler.get_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == DAILY_DIGEST_JOB_ID
    assert isinstance(jobs[0].trigger, CronTrigger)
    assert str(jobs[0].trigger) == "cron[hour='9', minute='30']"
    scheduler.shutdown()


class StubDigestService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, triggered_by: str) -> None:
        self.calls.append(triggered_by)


def test_run_scheduled_digest_uses_digest_service_with_scheduler_trigger(monkeypatch) -> None:
    settings = object()
    stub_service = StubDigestService()
    build_calls: list[object] = []

    def fake_build_digest_service(received_settings: object) -> StubDigestService:
        build_calls.append(received_settings)
        return stub_service

    monkeypatch.setattr("app.main.build_digest_service", fake_build_digest_service)

    from app.main import run_scheduled_digest

    run_scheduled_digest(settings)  # type: ignore[arg-type]

    assert build_calls == [settings]
    assert stub_service.calls == ["scheduler"]
