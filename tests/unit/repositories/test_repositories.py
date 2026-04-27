from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.db.connection import SCHEMA_PATH
from app.repositories.article_repository import ArticleRepository
from app.repositories.digest_run_repository import DigestRunRepository
from app.schemas.article import ArticleFetchResult


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


def build_article(
    *,
    url: str,
    title: str = "AI News",
    description: str | None = "Summary",
    published_at: str = "2026-04-18T08:00:00+09:00",
    source_name: str | None = "Example",
    category: str = "AI",
) -> ArticleFetchResult:
    return ArticleFetchResult(
        title=title,
        description=description,
        url=url,
        published_at=published_at,
        source_name=source_name,
        category=category,
    )


def test_digest_run_repository_creates_updates_and_gets_latest_run(tmp_path) -> None:
    db_path = tmp_path / "repository.db"
    initialize_test_db(db_path)
    repository = DigestRunRepository(connection_factory=lambda: connection_factory(db_path))

    created_run = repository.create_run("manual")
    updated_run = repository.update_result(
        created_run.run_id,
        fetched_count=20,
        selected_count=5,
        summarized_count=4,
        email_status="success",
    )
    latest_run = repository.get_latest()

    assert created_run.triggered_by == "manual"
    assert updated_run.run_id == created_run.run_id
    assert updated_run.finished_at is not None
    assert updated_run.fetched_count == 20
    assert updated_run.selected_count == 5
    assert updated_run.summarized_count == 4
    assert updated_run.email_status == "success"
    assert latest_run is not None
    assert latest_run.run_id == created_run.run_id


def test_article_repository_prevents_duplicate_urls_and_returns_recent_articles(tmp_path) -> None:
    db_path = tmp_path / "repository.db"
    initialize_test_db(db_path)
    repository = ArticleRepository(connection_factory=lambda: connection_factory(db_path))

    result = repository.save_articles(
        [
            build_article(url="https://example.com/a1", published_at="2026-04-18T08:00:00+09:00"),
            build_article(url="https://example.com/a1", published_at="2026-04-18T07:59:00+09:00"),
            build_article(url="https://example.com/a2", published_at="2026-04-18T08:01:00+09:00"),
        ]
    )
    recent_articles = repository.get_recent_articles("AI", 5)

    assert result.created_count == 2
    assert result.skipped_count == 1
    assert [article.url for article in recent_articles] == [
        "https://example.com/a2",
        "https://example.com/a1",
    ]


def test_article_repository_updates_summary_and_marks_sent(tmp_path) -> None:
    db_path = tmp_path / "repository.db"
    initialize_test_db(db_path)
    article_repository = ArticleRepository(connection_factory=lambda: connection_factory(db_path))
    run_repository = DigestRunRepository(connection_factory=lambda: connection_factory(db_path))

    save_result = article_repository.save_articles([build_article(url="https://example.com/a1")])
    assert save_result.created_count == 1

    article = article_repository.get_recent_articles("AI", 1)[0]
    updated_article = article_repository.update_summary(
        article.article_id,
        summary="要約済み",
        summary_status="success",
    )

    digest_run = run_repository.create_run("scheduler")
    marked_count = article_repository.mark_sent([article.article_id], digest_run.run_id)
    sent_article = article_repository.get_recent_articles("AI", 1)[0]

    assert updated_article.summary == "要約済み"
    assert updated_article.summary_status == "success"
    assert marked_count == 1
    assert sent_article.last_sent_run_id == digest_run.run_id
