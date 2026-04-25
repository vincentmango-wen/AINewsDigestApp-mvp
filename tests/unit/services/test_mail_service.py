from __future__ import annotations

from dataclasses import replace

import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.services.mail_service import MailService


class DummySmtpClient:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.calls: list[tuple[str, str, str]] = []

    def send(self, subject: str, body: str, to_address: str) -> None:
        self.calls.append((subject, body, to_address))


def build_settings() -> Settings:
    return Settings(
        category="AI",
        THE_NEWS_API_TOKEN="token",
        openai_api_key="openai-key",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="app-password",
        mail_from_address="user@example.com",
        mail_to_address="to@example.com",
        db_path=__import__("pathlib").Path("/tmp/app.db"),
        log_path=__import__("pathlib").Path("/tmp/app.log"),
    )


def test_send_mail_raises_configuration_error_when_smtp_host_is_missing() -> None:
    settings = replace(build_settings(), smtp_host="")
    service = MailService(settings=settings)

    with pytest.raises(ConfigurationError, match="SMTP_HOST"):
        service.send_mail("件名", "本文")


def test_send_mail_raises_configuration_error_when_smtp_password_is_missing() -> None:
    settings = replace(build_settings(), smtp_password=" ")
    service = MailService(settings=settings)

    with pytest.raises(ConfigurationError, match="SMTP_PASSWORD"):
        service.send_mail("件名", "本文")


def test_send_mail_uses_smtp_client_when_settings_are_complete() -> None:
    created_clients: list[DummySmtpClient] = []

    def smtp_client_factory(**kwargs) -> DummySmtpClient:
        client = DummySmtpClient(**kwargs)
        created_clients.append(client)
        return client

    service = MailService(settings=build_settings(), smtp_client_factory=smtp_client_factory)

    service.send_mail("件名", "本文")

    client = created_clients[0]
    assert client.kwargs["host"] == "smtp.gmail.com"
    assert client.kwargs["password"] == "app-password"
    assert client.calls == [("件名", "本文", "to@example.com")]
