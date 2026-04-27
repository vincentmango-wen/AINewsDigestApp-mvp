from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import ExternalApiError, MailSendError
from app.db.connection import SCHEMA_PATH
from app.repositories.article_repository import ArticleRepository
from app.repositories.digest_run_repository import DigestRunRepository
from app.schemas.article import Article, ArticleFetchResult
from app.services.article_selector import ArticleSelector
from app.services.digest_service import DigestService
from app.services.mail_service import MailService
from app.services.run_history_service import RunHistoryService
from app.services.summary_service import SummaryService


@contextmanager
def connection_factory(db_path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connection
    finally:
        connection.close()


def initialize_test_db(db_path: Path) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(schema_sql)
        connection.commit()
    finally:
        connection.close()


def build_settings(db_path: Path) -> Settings:
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
        db_path=db_path,
        log_path=db_path.with_suffix(".log"),
        fetch_limit=20,
        selection_limit=5,
    )


def build_fetch_result(index: int) -> ArticleFetchResult:
    return ArticleFetchResult(
        title=f"記事{index}",
        description=f"説明{index}",
        url=f"https://example.com/articles/{index}",
        published_at=f"2026-04-26T0{index}:00:00Z",
        source_name="Example News",
        category="AI",
    )


class StubNewsService:
    def __init__(self, articles: list[ArticleFetchResult]) -> None:
        self._articles = articles

    def fetch_latest_articles(self, category: str, limit: int) -> list[ArticleFetchResult]:
        assert category == "AI"
        assert limit == 20
        return self._articles


class StubOpenAIClient:
    def __init__(self, responses: dict[str, str | Exception]) -> None:
        self._responses = responses

    def summarize(self, title: str, description: str | None) -> str:
        del description
        response = self._responses[title]
        if isinstance(response, Exception):
            raise response
        return response


class RecordingSmtpClient:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.calls: list[tuple[str, str, str]] = []

    def send(self, subject: str, body: str, to_address: str) -> None:
        self.calls.append((subject, body, to_address))


class FailingSmtpClient(RecordingSmtpClient):
    def send(self, subject: str, body: str, to_address: str) -> None:
        super().send(subject, body, to_address)
        raise MailSendError("SMTP 認証に失敗しました")


def build_digest_service(
    *,
    db_path: Path,
    fetched_articles: list[ArticleFetchResult],
    openai_responses: dict[str, str | Exception],
    smtp_client_factory,
) -> tuple[DigestService, ArticleRepository, DigestRunRepository, list[RecordingSmtpClient]]:
    settings = build_settings(db_path)
    article_repository = ArticleRepository(connection_factory=lambda: connection_factory(db_path))
    digest_run_repository = DigestRunRepository(connection_factory=lambda: connection_factory(db_path))
    created_smtp_clients: list[RecordingSmtpClient] = []

    def capture_smtp_client(**kwargs):
        client = smtp_client_factory(**kwargs)
        created_smtp_clients.append(client)
        return client

    service = DigestService(
        settings=settings,
        news_service=StubNewsService(fetched_articles),
        article_repository=article_repository,
        article_selector=ArticleSelector(),
        summary_service=SummaryService(
            openai_client=StubOpenAIClient(openai_responses),
            article_repository=article_repository,
        ),
        mail_service=MailService(
            settings=settings,
            smtp_client_factory=capture_smtp_client,
        ),
        run_history_service=RunHistoryService(digest_run_repository),
    )
    return service, article_repository, digest_run_repository, created_smtp_clients


def test_run_persists_success_status_and_marks_articles_as_sent(tmp_path: Path) -> None:
    db_path = tmp_path / "digest-success.db"
    initialize_test_db(db_path)
    service, article_repository, digest_run_repository, smtp_clients = build_digest_service(
        db_path=db_path,
        fetched_articles=[build_fetch_result(1), build_fetch_result(2)],
        openai_responses={"記事1": "要約1", "記事2": "要約2"},
        smtp_client_factory=RecordingSmtpClient,
    )

    result = service.run("manual")
    latest_run = digest_run_repository.get_latest()
    recent_articles = article_repository.get_recent_articles("AI", 5)

    assert result.run.email_status == "success"
    assert latest_run is not None
    assert latest_run.email_status == "success"
    assert latest_run.summarized_count == 2
    assert [article.summary_status for article in recent_articles] == ["success", "success"]
    assert [article.last_sent_run_id for article in recent_articles] == [result.run.run_id, result.run.run_id]
    assert smtp_clients[0].kwargs["host"] == "smtp.gmail.com"
    assert smtp_clients[0].calls[0][2] == "to@example.com"


def test_run_persists_skipped_status_when_all_summaries_fail(tmp_path: Path) -> None:
    db_path = tmp_path / "digest-skipped.db"
    initialize_test_db(db_path)
    service, article_repository, digest_run_repository, smtp_clients = build_digest_service(
        db_path=db_path,
        fetched_articles=[build_fetch_result(1), build_fetch_result(2)],
        openai_responses={
            "記事1": ExternalApiError("OpenAI failed"),
            "記事2": ExternalApiError("OpenAI failed"),
        },
        smtp_client_factory=RecordingSmtpClient,
    )

    result = service.run("manual")
    latest_run = digest_run_repository.get_latest()
    recent_articles = article_repository.get_recent_articles("AI", 5)

    assert result.run.email_status == "skipped"
    assert latest_run is not None
    assert latest_run.email_status == "skipped"
    assert latest_run.summarized_count == 0
    assert [article.summary_status for article in recent_articles] == ["failed", "failed"]
    assert [article.last_sent_run_id for article in recent_articles] == [None, None]
    assert smtp_clients == []


def test_run_persists_failed_status_when_smtp_send_fails(tmp_path: Path) -> None:
    db_path = tmp_path / "digest-failed.db"
    initialize_test_db(db_path)
    service, article_repository, digest_run_repository, smtp_clients = build_digest_service(
        db_path=db_path,
        fetched_articles=[build_fetch_result(1)],
        openai_responses={"記事1": "要約1"},
        smtp_client_factory=FailingSmtpClient,
    )

    with pytest.raises(MailSendError, match="SMTP 認証に失敗しました"):
        service.run("manual")

    latest_run = digest_run_repository.get_latest()
    recent_articles = article_repository.get_recent_articles("AI", 5)

    assert latest_run is not None
    assert latest_run.email_status == "failed"
    assert latest_run.error_message == "SMTP 認証に失敗しました"
    assert latest_run.summarized_count == 1
    assert isinstance(smtp_clients[0], FailingSmtpClient)
    assert len(smtp_clients[0].calls) == 1
    assert recent_articles[0].summary_status == "success"
    assert recent_articles[0].last_sent_run_id is None

