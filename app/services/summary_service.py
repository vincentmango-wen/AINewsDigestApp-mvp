"""Summary generation service."""

from __future__ import annotations

from typing import Protocol

from app.core.exceptions import ExternalApiError
from app.schemas.article import Article


class SummaryGenerator(Protocol):
    def summarize(self, title: str, description: str | None) -> str:
        ...


class SummaryRepository(Protocol):
    def update_summary(
        self,
        article_id: int,
        *,
        summary: str | None,
        summary_status: str,
    ) -> Article:
        ...


class SummaryService:
    def __init__(
        self,
        *,
        openai_client: SummaryGenerator,
        article_repository: SummaryRepository,
    ) -> None:
        self._openai_client = openai_client
        self._article_repository = article_repository

    def summarize_articles(self, run_id: int, articles: list[Article]) -> list[Article]:
        del run_id

        summarized_articles: list[Article] = []

        for article in articles:
            if article.title.strip() == "":
                continue

            try:
                summary = self._openai_client.summarize(article.title, article.description)
                if summary.strip() == "":
                    raise ExternalApiError("要約結果が空です")
                updated_article = self._article_repository.update_summary(
                    article.article_id,
                    summary=summary,
                    summary_status="success",
                )
            except ExternalApiError:
                self._article_repository.update_summary(
                    article.article_id,
                    summary=None,
                    summary_status="failed",
                )
                continue

            summarized_articles.append(updated_article)

        return summarized_articles
