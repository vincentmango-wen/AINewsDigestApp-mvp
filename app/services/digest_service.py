"""Digest workflow orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import ClassVar, Protocol

from app.core.config import Settings
from app.core.exceptions import JobAlreadyRunningError
from app.schemas.article import Article, ArticleFetchResult, SaveArticlesResult
from app.schemas.digest_run import DigestRun, TriggeredBy


class NewsServiceProtocol(Protocol):
    def fetch_latest_articles(self, category: str, limit: int) -> list[ArticleFetchResult]:
        ...


class ArticleRepositoryProtocol(Protocol):
    def save_articles(self, articles: list[ArticleFetchResult]) -> SaveArticlesResult:
        ...

    def get_recent_articles(self, category: str, limit: int) -> list[Article]:
        ...

    def mark_sent(self, article_ids: list[int], run_id: int) -> int:
        ...


class SummaryServiceProtocol(Protocol):
    def summarize_articles(self, run_id: int, articles: list[Article]) -> list[Article]:
        ...


class MailServiceProtocol(Protocol):
    def build_message(self, articles: list[Article]) -> tuple[str, str] | None:
        ...

    def send_mail(self, subject: str, body: str) -> None:
        ...


class RunHistoryServiceProtocol(Protocol):
    def start_run(self, triggered_by: TriggeredBy) -> DigestRun:
        ...

    def finish_run(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: str,
    ) -> DigestRun:
        ...

    def fail_run(
        self,
        run_id: int,
        error_message: str,
        *,
        fetched_count: int = 0,
        selected_count: int = 0,
        summarized_count: int = 0,
    ) -> DigestRun:
        ...


@dataclass(frozen=True, slots=True)
class DigestExecutionResult:
    run: DigestRun
    saved_articles: SaveArticlesResult
    selected_articles: list[Article]
    summarized_articles: list[Article]


class DigestService:
    _run_lock: ClassVar[Lock] = Lock()

    def __init__(
        self,
        *,
        settings: Settings,
        news_service: NewsServiceProtocol,
        article_repository: ArticleRepositoryProtocol,
        article_selector,
        summary_service: SummaryServiceProtocol,
        mail_service: MailServiceProtocol,
        run_history_service: RunHistoryServiceProtocol,
    ) -> None:
        self._settings = settings
        self._news_service = news_service
        self._article_repository = article_repository
        self._article_selector = article_selector
        self._summary_service = summary_service
        self._mail_service = mail_service
        self._run_history_service = run_history_service

    def run(self, triggered_by: TriggeredBy) -> DigestExecutionResult:
        if not self._run_lock.acquire(blocking=False):
            raise JobAlreadyRunningError("ダイジェスト処理は既に実行中です")

        digest_run = self._run_history_service.start_run(triggered_by)
        fetched_articles: list[ArticleFetchResult] = []
        saved_articles = SaveArticlesResult(created_count=0, skipped_count=0)
        selected_articles: list[Article] = []
        summarized_articles: list[Article] = []

        try:
            fetched_articles = self._news_service.fetch_latest_articles(
                self._settings.category,
                self._settings.fetch_limit,
            )
            saved_articles = self._article_repository.save_articles(fetched_articles)
            recent_articles = self._article_repository.get_recent_articles(
                self._settings.category,
                self._settings.selection_limit,
            )
            selected_articles = self._article_selector.select_top_articles(
                recent_articles,
                self._settings.selection_limit,
            )

            if not selected_articles:
                finished_run = self._run_history_service.finish_run(
                    digest_run.run_id,
                    fetched_count=len(fetched_articles),
                    selected_count=0,
                    summarized_count=0,
                    email_status="skipped",
                )
                return DigestExecutionResult(
                    run=finished_run,
                    saved_articles=saved_articles,
                    selected_articles=[],
                    summarized_articles=[],
                )

            summarized_articles = self._summary_service.summarize_articles(
                digest_run.run_id,
                selected_articles,
            )

            if not summarized_articles:
                finished_run = self._run_history_service.finish_run(
                    digest_run.run_id,
                    fetched_count=len(fetched_articles),
                    selected_count=len(selected_articles),
                    summarized_count=0,
                    email_status="skipped",
                )
                return DigestExecutionResult(
                    run=finished_run,
                    saved_articles=saved_articles,
                    selected_articles=selected_articles,
                    summarized_articles=[],
                )

            message = self._mail_service.build_message(summarized_articles)
            if message is None:
                finished_run = self._run_history_service.finish_run(
                    digest_run.run_id,
                    fetched_count=len(fetched_articles),
                    selected_count=len(selected_articles),
                    summarized_count=len(summarized_articles),
                    email_status="skipped",
                )
                return DigestExecutionResult(
                    run=finished_run,
                    saved_articles=saved_articles,
                    selected_articles=selected_articles,
                    summarized_articles=summarized_articles,
                )

            subject, body = message
            self._mail_service.send_mail(subject, body)
            self._article_repository.mark_sent(
                [article.article_id for article in summarized_articles],
                digest_run.run_id,
            )

            finished_run = self._run_history_service.finish_run(
                digest_run.run_id,
                fetched_count=len(fetched_articles),
                selected_count=len(selected_articles),
                summarized_count=len(summarized_articles),
                email_status="success",
            )
            return DigestExecutionResult(
                run=finished_run,
                saved_articles=saved_articles,
                selected_articles=selected_articles,
                summarized_articles=summarized_articles,
            )
        except Exception as exc:
            self._run_history_service.fail_run(
                digest_run.run_id,
                str(exc),
                fetched_count=len(fetched_articles),
                selected_count=len(selected_articles),
                summarized_count=len(summarized_articles),
            )
            raise
        finally:
            self._run_lock.release()
