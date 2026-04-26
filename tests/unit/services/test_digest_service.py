from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import JobAlreadyRunningError, MailSendError
from app.schemas.article import Article, ArticleFetchResult, SaveArticlesResult
from app.schemas.digest_run import DigestRun
from app.services.digest_service import DigestService


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
        db_path=Path("/tmp/app.db"),
        log_path=Path("/tmp/app.log"),
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


def build_article(index: int, *, summary: str | None = None, summary_status: str = "pending") -> Article:
    return Article(
        article_id=index,
        url=f"https://example.com/articles/{index}",
        title=f"記事{index}",
        description=f"説明{index}",
        source_name="Example News",
        published_at=f"2026-04-26T0{index}:00:00Z",
        category="AI",
        summary=summary,
        summary_status=summary_status,
        fetched_at="2026-04-26T00:00:00Z",
        last_sent_run_id=None,
        created_at="2026-04-26T00:00:00Z",
        updated_at="2026-04-26T00:00:00Z",
    )


def build_digest_run(run_id: int, *, email_status: str = "skipped", error_message: str | None = None) -> DigestRun:
    return DigestRun(
        run_id=run_id,
        triggered_by="manual",
        started_at="2026-04-26T00:00:00Z",
        finished_at="2026-04-26T00:10:00Z" if error_message or email_status != "skipped" else None,
        fetched_count=0,
        selected_count=0,
        summarized_count=0,
        email_status=email_status,
        error_message=error_message,
        created_at="2026-04-26T00:00:00Z",
        updated_at="2026-04-26T00:10:00Z",
    )


class DummyNewsService:
    def __init__(self, articles: list[ArticleFetchResult]) -> None:
        self.articles = articles
        self.calls: list[tuple[str, int]] = []

    def fetch_latest_articles(self, category: str, limit: int) -> list[ArticleFetchResult]:
        self.calls.append((category, limit))
        return self.articles


class ReentrantNewsService(DummyNewsService):
    def __init__(self, articles: list[ArticleFetchResult]) -> None:
        super().__init__(articles)
        self.on_fetch: callable | None = None
        self._triggered = False

    def fetch_latest_articles(self, category: str, limit: int) -> list[ArticleFetchResult]:
        if not self._triggered and self.on_fetch is not None:
            self._triggered = True
            self.on_fetch()
        return super().fetch_latest_articles(category, limit)


class DummyArticleRepository:
    def __init__(self, selected_articles: list[Article]) -> None:
        self.selected_articles = selected_articles
        self.saved_batches: list[list[ArticleFetchResult]] = []
        self.marked_sent: list[tuple[list[int], int]] = []

    def save_articles(self, articles: list[ArticleFetchResult]) -> SaveArticlesResult:
        self.saved_batches.append(articles)
        return SaveArticlesResult(created_count=len(articles), skipped_count=0)

    def get_recent_articles(self, category: str, limit: int) -> list[Article]:
        return self.selected_articles

    def mark_sent(self, article_ids: list[int], run_id: int) -> int:
        self.marked_sent.append((article_ids, run_id))
        return len(article_ids)


class DummyArticleSelector:
    def __init__(self, selected_articles: list[Article]) -> None:
        self.selected_articles = selected_articles
        self.calls: list[tuple[list[Article], int]] = []

    def select_top_articles(self, articles: list[Article], limit: int) -> list[Article]:
        self.calls.append((articles, limit))
        return self.selected_articles


class DummySummaryService:
    def __init__(self, summarized_articles: list[Article]) -> None:
        self.summarized_articles = summarized_articles
        self.calls: list[tuple[int, list[Article]]] = []

    def summarize_articles(self, run_id: int, articles: list[Article]) -> list[Article]:
        self.calls.append((run_id, articles))
        return self.summarized_articles


class DummyMailService:
    def __init__(self, message: tuple[str, str] | None, *, send_error: Exception | None = None) -> None:
        self.message = message
        self.send_error = send_error
        self.build_calls: list[list[Article]] = []
        self.send_calls: list[tuple[str, str]] = []

    def build_message(self, articles: list[Article]) -> tuple[str, str] | None:
        self.build_calls.append(articles)
        return self.message

    def send_mail(self, subject: str, body: str) -> None:
        self.send_calls.append((subject, body))
        if self.send_error is not None:
            raise self.send_error


class DummyRunHistoryService:
    def __init__(self) -> None:
        self.start_calls: list[str] = []
        self.finish_calls: list[dict[str, object]] = []
        self.fail_calls: list[dict[str, object]] = []

    def start_run(self, triggered_by: str) -> DigestRun:
        self.start_calls.append(triggered_by)
        return build_digest_run(1)

    def finish_run(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: str,
    ) -> DigestRun:
        call = {
            "run_id": run_id,
            "fetched_count": fetched_count,
            "selected_count": selected_count,
            "summarized_count": summarized_count,
            "email_status": email_status,
        }
        self.finish_calls.append(call)
        return replace(
            build_digest_run(run_id, email_status=email_status),
            fetched_count=fetched_count,
            selected_count=selected_count,
            summarized_count=summarized_count,
            finished_at="2026-04-26T00:10:00Z",
        )

    def fail_run(
        self,
        run_id: int,
        error_message: str,
        *,
        fetched_count: int = 0,
        selected_count: int = 0,
        summarized_count: int = 0,
    ) -> DigestRun:
        call = {
            "run_id": run_id,
            "error_message": error_message,
            "fetched_count": fetched_count,
            "selected_count": selected_count,
            "summarized_count": summarized_count,
        }
        self.fail_calls.append(call)
        return replace(
            build_digest_run(run_id, email_status="failed", error_message=error_message),
            fetched_count=fetched_count,
            selected_count=selected_count,
            summarized_count=summarized_count,
            finished_at="2026-04-26T00:10:00Z",
        )


def test_run_completes_full_digest_flow_successfully() -> None:
    fetched = [build_fetch_result(1), build_fetch_result(2)]
    selected = [build_article(1), build_article(2)]
    summarized = [
        build_article(1, summary="要約1", summary_status="success"),
        build_article(2, summary="要約2", summary_status="success"),
    ]
    service = DigestService(
        settings=build_settings(),
        news_service=DummyNewsService(fetched),
        article_repository=DummyArticleRepository(selected),
        article_selector=DummyArticleSelector(selected),
        summary_service=DummySummaryService(summarized),
        mail_service=DummyMailService(("件名", "本文")),
        run_history_service=DummyRunHistoryService(),
    )

    result = service.run("manual")

    assert result.run.email_status == "success"
    assert result.run.fetched_count == 2
    assert result.run.selected_count == 2
    assert result.run.summarized_count == 2


def test_run_skips_email_when_all_summaries_fail() -> None:
    fetched = [build_fetch_result(1), build_fetch_result(2)]
    selected = [build_article(1), build_article(2)]
    run_history = DummyRunHistoryService()
    mail_service = DummyMailService(("件名", "本文"))
    service = DigestService(
        settings=build_settings(),
        news_service=DummyNewsService(fetched),
        article_repository=DummyArticleRepository(selected),
        article_selector=DummyArticleSelector(selected),
        summary_service=DummySummaryService([]),
        mail_service=mail_service,
        run_history_service=run_history,
    )

    result = service.run("manual")

    assert result.run.email_status == "skipped"
    assert result.run.summarized_count == 0
    assert mail_service.build_calls == []
    assert run_history.finish_calls[0]["email_status"] == "skipped"


def test_run_marks_failed_when_smtp_send_fails() -> None:
    fetched = [build_fetch_result(1)]
    selected = [build_article(1)]
    summarized = [build_article(1, summary="要約1", summary_status="success")]
    run_history = DummyRunHistoryService()
    mail_service = DummyMailService(("件名", "本文"), send_error=MailSendError("SMTP 認証に失敗しました"))
    article_repository = DummyArticleRepository(selected)
    service = DigestService(
        settings=build_settings(),
        news_service=DummyNewsService(fetched),
        article_repository=article_repository,
        article_selector=DummyArticleSelector(selected),
        summary_service=DummySummaryService(summarized),
        mail_service=mail_service,
        run_history_service=run_history,
    )

    with pytest.raises(MailSendError, match="SMTP 認証に失敗しました"):
        service.run("manual")

    assert run_history.fail_calls[0]["summarized_count"] == 1
    assert run_history.fail_calls[0]["error_message"] == "SMTP 認証に失敗しました"
    assert article_repository.marked_sent == []


def test_run_allows_sequential_reruns_with_duplicate_articles() -> None:
    fetched = [build_fetch_result(1)]
    selected = [build_article(1)]
    summarized = [build_article(1, summary="要約1", summary_status="success")]
    repository = DummyArticleRepository(selected)
    service = DigestService(
        settings=build_settings(),
        news_service=DummyNewsService(fetched),
        article_repository=repository,
        article_selector=DummyArticleSelector(selected),
        summary_service=DummySummaryService(summarized),
        mail_service=DummyMailService(("件名", "本文")),
        run_history_service=DummyRunHistoryService(),
    )

    first = service.run("manual")
    second = service.run("manual")

    assert first.run.email_status == "success"
    assert second.run.email_status == "success"
    assert len(repository.saved_batches) == 2


def test_run_rejects_overlapping_execution() -> None:
    fetched = [build_fetch_result(1)]
    selected = [build_article(1)]
    summarized = [build_article(1, summary="要約1", summary_status="success")]
    news_service = ReentrantNewsService(fetched)
    service = DigestService(
        settings=build_settings(),
        news_service=news_service,
        article_repository=DummyArticleRepository(selected),
        article_selector=DummyArticleSelector(selected),
        summary_service=DummySummaryService(summarized),
        mail_service=DummyMailService(("件名", "本文")),
        run_history_service=DummyRunHistoryService(),
    )

    def trigger_nested_run() -> None:
        with pytest.raises(JobAlreadyRunningError, match="既に実行中"):
            service.run("manual")

    news_service.on_fetch = trigger_nested_run

    result = service.run("manual")

    assert result.run.email_status == "success"
