from __future__ import annotations

import smtplib
import socket

import pytest

from app.clients.smtp_client import SmtpClient
from app.core.exceptions import MailSendError


class DummySMTP:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        *,
        login_error: Exception | None = None,
        send_error: Exception | None = None,
        starttls_error: Exception | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.login_error = login_error
        self.send_error = send_error
        self.starttls_error = starttls_error
        self.login_args: tuple[str, str] | None = None
        self.sent_message = None
        self.started_tls = False

    def __enter__(self) -> "DummySMTP":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def ehlo(self) -> None:
        return None

    def starttls(self, *, context) -> None:
        if self.starttls_error is not None:
            raise self.starttls_error
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        if self.login_error is not None:
            raise self.login_error
        self.login_args = (username, password)

    def send_message(self, message) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent_message = message


def test_send_delivers_plain_text_mail() -> None:
    smtp_instances: list[DummySMTP] = []

    def smtp_factory(host: str, port: int, timeout: float | None = None) -> DummySMTP:
        smtp = DummySMTP(host, port, timeout)
        smtp_instances.append(smtp)
        return smtp

    client = SmtpClient(
        host="smtp.gmail.com",
        port=587,
        username="user@example.com",
        password="app-password",
        from_address="user@example.com",
        smtp_factory=smtp_factory,
    )

    client.send("件名", "本文です", "to@example.com")

    smtp = smtp_instances[0]
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 587
    assert smtp.started_tls is True
    assert smtp.login_args == ("user@example.com", "app-password")
    assert smtp.sent_message["To"] == "to@example.com"
    assert smtp.sent_message["Subject"] == "件名"
    assert "本文です" in smtp.sent_message.get_content()


def test_send_raises_when_body_is_empty() -> None:
    client = SmtpClient(
        host="smtp.gmail.com",
        port=587,
        username="user@example.com",
        password="app-password",
        from_address="user@example.com",
    )

    with pytest.raises(MailSendError, match="本文が空"):
        client.send("件名", "   ", "to@example.com")


def test_send_converts_authentication_error() -> None:
    def smtp_factory(host: str, port: int, timeout: float | None = None) -> DummySMTP:
        return DummySMTP(
            host,
            port,
            timeout,
            login_error=smtplib.SMTPAuthenticationError(535, b"auth failed"),
        )

    client = SmtpClient(
        host="smtp.gmail.com",
        port=587,
        username="user@example.com",
        password="wrong-password",
        from_address="user@example.com",
        smtp_factory=smtp_factory,
    )

    with pytest.raises(MailSendError, match="認証に失敗"):
        client.send("件名", "本文です", "to@example.com")


def test_send_converts_timeout_error() -> None:
    def smtp_factory(host: str, port: int, timeout: float | None = None) -> DummySMTP:
        return DummySMTP(
            host,
            port,
            timeout,
            starttls_error=socket.timeout("timed out"),
        )

    client = SmtpClient(
        host="smtp.gmail.com",
        port=587,
        username="user@example.com",
        password="app-password",
        from_address="user@example.com",
        smtp_factory=smtp_factory,
    )

    with pytest.raises(MailSendError, match="タイムアウト"):
        client.send("件名", "本文です", "to@example.com")
