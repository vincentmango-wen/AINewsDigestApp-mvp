"""Repository for articles table access."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager

from app.core.exceptions import DatabaseError, NotFoundError
from app.db.connection import get_connection
from app.schemas.article import (
    Article,
    ArticleFetchResult,
    SaveArticlesResult,
    SummaryStatus,
)

SELECT_ARTICLE_COLUMNS = """
SELECT
    id,
    url,
    title,
    description,
    source_name,
    published_at,
    category,
    summary,
    summary_status,
    fetched_at,
    last_sent_run_id
FROM articles
"""


class ArticleRepository:
    def __init__(
        self,
        connection_factory: Callable[[], AbstractContextManager[sqlite3.Connection]] = get_connection,
    ) -> None:
        self._connection_factory = connection_factory

    def save_articles(self, articles: Sequence[ArticleFetchResult]) -> SaveArticlesResult:
        if not articles:
            return SaveArticlesResult(created_count=0, skipped_count=0)

        created_count = 0
        skipped_count = 0

        try:
            with self._connection_factory() as connection:
                for article in articles:
                    cursor = connection.execute(
                        """
                        INSERT OR IGNORE INTO articles (
                            url,
                            title,
                            description,
                            source_name,
                            published_at,
                            category
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            article.url,
                            article.title,
                            article.description,
                            article.source_name,
                            article.published_at,
                            article.category,
                        ),
                    )
                    if cursor.rowcount == 1:
                        created_count += 1
                    else:
                        skipped_count += 1

                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError("記事の保存に失敗しました") from exc

        return SaveArticlesResult(
            created_count=created_count,
            skipped_count=skipped_count,
        )

    def get_recent_articles(self, category: str, limit: int) -> list[Article]:
        try:
            with self._connection_factory() as connection:
                rows = connection.execute(
                    f"""
                    {SELECT_ARTICLE_COLUMNS}
                    WHERE category = ?
                    ORDER BY published_at DESC, id DESC
                    LIMIT ?
                    """,
                    (category, limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError("最新記事の取得に失敗しました") from exc

        return [Article.from_row(row) for row in rows]

    def update_summary(
        self,
        article_id: int,
        *,
        summary: str | None,
        summary_status: SummaryStatus,
    ) -> Article:
        try:
            with self._connection_factory() as connection:
                cursor = connection.execute(
                    """
                    UPDATE articles
                    SET
                        summary = ?,
                        summary_status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (summary, summary_status, article_id),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError("対象の記事が存在しません")

                article = self._get_by_id(connection, article_id)
                connection.commit()
        except NotFoundError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError("記事要約の更新に失敗しました") from exc

        if article is None:
            raise DatabaseError("更新後の記事取得に失敗しました")

        return article

    def mark_sent(self, article_ids: Sequence[int], run_id: int) -> int:
        if not article_ids:
            return 0

        placeholders = ", ".join("?" for _ in article_ids)
        parameters = [run_id, *article_ids]

        try:
            with self._connection_factory() as connection:
                cursor = connection.execute(
                    f"""
                    UPDATE articles
                    SET
                        last_sent_run_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                    """,
                    parameters,
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError("配信済み記事の更新に失敗しました") from exc

        return cursor.rowcount

    def _get_by_id(
        self,
        connection: sqlite3.Connection,
        article_id: int,
    ) -> Article | None:
        row = connection.execute(
            f"""
            {SELECT_ARTICLE_COLUMNS}
            WHERE id = ?
            """,
            (article_id,),
        ).fetchone()
        if row is None:
            return None
        return Article.from_row(row)
