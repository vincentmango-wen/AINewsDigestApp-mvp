from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, MailBuildError
from app.schemas.article import Article
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


def build_article(
    article_id: int,
    *,
    title: str = "記事タイトル",
    summary: str | None = "要約本文です。",
    url: str = "https://example.com/articles/1",
) -> Article:
    return Article(
        article_id=article_id,
        url=url,
        title=title,
        description="説明文",
        source_name="Example News",
        published_at="2026-04-26T09:00:00Z",
        category="AI",
        summary=summary,
        summary_status="success",
        fetched_at="2026-04-26T09:00:00Z",
        last_sent_run_id=None,
        created_at="2026-04-26T09:00:00Z",
        updated_at="2026-04-26T09:00:00Z",
    )


def test_build_message_returns_subject_and_body() -> None:
    service = MailService(settings=build_settings())

    message = service.build_message(
        [build_article(1), build_article(2, title="記事2", summary="要約2です。", url="https://example.com/articles/2")],
        target_date=date(2026, 4, 26),
    )

    assert message is not None
    subject, body = message
    assert subject == "AIニュースダイジェスト 2026-04-26"
    assert "タイトル: 記事タイトル" in body
    assert "要約: 要約本文です。" in body
    assert "URL: https://example.com/articles/1" in body
    assert "タイトル: 記事2" in body


def test_build_message_returns_none_when_articles_are_empty() -> None:
    service = MailService(settings=build_settings())

    message = service.build_message([])

    assert message is None


def test_build_message_raises_when_required_article_data_is_missing() -> None:
    service = MailService(settings=build_settings())

    with pytest.raises(MailBuildError, match="記事データが不足"):
        service.build_message([build_article(1, url=" ")], target_date=date(2026, 4, 26))


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
