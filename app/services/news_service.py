"""News fetching business rules."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.schemas.article import ArticleFetchResult


class NewsFetcher(Protocol):
    def fetch_news(self, category: str, page_size: int) -> list[ArticleFetchResult]:
        ...


class NewsService:
    def __init__(self, news_client: NewsFetcher) -> None:
        self._news_client = news_client

    def fetch_latest_articles(self, category: str, limit: int) -> list[ArticleFetchResult]:
        articles = self._news_client.fetch_news(category, limit)
        return [article for article in articles if self._is_valid_article(article)]

    def _is_valid_article(self, article: ArticleFetchResult) -> bool:
        if article.title is None or article.url is None or article.published_at is None:
            return False
        return self._is_valid_iso8601(article.published_at)

    @staticmethod
    def _is_valid_iso8601(value: str) -> bool:
        normalized = value.strip()
        if normalized == "":
            return False

        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"

        try:
            datetime.fromisoformat(normalized)
        except ValueError:
            return False
        return True
