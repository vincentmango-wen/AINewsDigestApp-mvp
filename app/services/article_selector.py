"""Article selection logic."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.schemas.article import Article


class ArticleSelector:
    def select_top_articles(self, articles: Iterable[Article], limit: int) -> list[Article]:
        if limit <= 0:
            return []

        valid_articles = [article for article in articles if article.published_at.strip() != ""]
        sorted_articles = sorted(
            valid_articles,
            key=lambda article: self._parse_published_at(article.published_at),
            reverse=True,
        )
        return sorted_articles[:limit]

    @staticmethod
    def _parse_published_at(value: str) -> datetime:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        return datetime.fromisoformat(normalized)
