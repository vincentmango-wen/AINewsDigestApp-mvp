from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


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
