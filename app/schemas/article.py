"""Article-related schemas."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal

SummaryStatus = Literal["pending", "success", "failed"]


@dataclass(frozen=True, slots=True)
class ArticleFetchResult:
    title: str
    description: str | None
    url: str
    published_at: str
    source_name: str | None
    category: str


@dataclass(frozen=True, slots=True)
class Article:
    article_id: int
    url: str
    title: str
    description: str | None
    source_name: str | None
    published_at: str
    category: str
    summary: str | None
    summary_status: SummaryStatus
    fetched_at: str
    last_sent_run_id: int | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Article":
        return cls(
            article_id=row["id"],
            url=row["url"],
            title=row["title"],
            description=row["description"],
            source_name=row["source_name"],
            published_at=row["published_at"],
            category=row["category"],
            summary=row["summary"],
            summary_status=row["summary_status"],
            fetched_at=row["fetched_at"],
            last_sent_run_id=row["last_sent_run_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(frozen=True, slots=True)
class SaveArticlesResult:
    created_count: int
    skipped_count: int
