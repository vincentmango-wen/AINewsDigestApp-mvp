"""Repository for digest_runs table access."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import AbstractContextManager

from app.core.exceptions import DatabaseError, NotFoundError
from app.db.connection import get_connection
from app.schemas.digest_run import DigestRun, EmailStatus, TriggeredBy

SELECT_DIGEST_RUN_COLUMNS = """
SELECT
    id,
    triggered_by,
    started_at,
    finished_at,
    fetched_count,
    selected_count,
    summarized_count,
    email_status,
    error_message
FROM digest_runs
"""


class DigestRunRepository:
    def __init__(
        self,
        connection_factory: Callable[[], AbstractContextManager[sqlite3.Connection]] = get_connection,
    ) -> None:
        self._connection_factory = connection_factory

    def create_run(self, triggered_by: TriggeredBy) -> DigestRun:
        try:
            with self._connection_factory() as connection:
                cursor = connection.execute(
                    "INSERT INTO digest_runs (triggered_by) VALUES (?)",
                    (triggered_by,),
                )
                digest_run = self._get_by_id(connection, cursor.lastrowid)
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError("実行履歴の作成に失敗しました") from exc

        if digest_run is None:
            raise DatabaseError("作成した実行履歴の取得に失敗しました")

        return digest_run

    def update_result(
        self,
        run_id: int,
        *,
        fetched_count: int,
        selected_count: int,
        summarized_count: int,
        email_status: EmailStatus,
        error_message: str | None = None,
    ) -> DigestRun:
        try:
            with self._connection_factory() as connection:
                cursor = connection.execute(
                    """
                    UPDATE digest_runs
                    SET
                        finished_at = CURRENT_TIMESTAMP,
                        fetched_count = ?,
                        selected_count = ?,
                        summarized_count = ?,
                        email_status = ?,
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        fetched_count,
                        selected_count,
                        summarized_count,
                        email_status,
                        error_message,
                        run_id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError("対象の実行履歴が存在しません")

                digest_run = self._get_by_id(connection, run_id)
                connection.commit()
        except NotFoundError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError("実行履歴の更新に失敗しました") from exc

        if digest_run is None:
            raise DatabaseError("更新後の実行履歴の取得に失敗しました")

        return digest_run

    def get_latest(self) -> DigestRun | None:
        try:
            with self._connection_factory() as connection:
                row = connection.execute(
                    f"""
                    {SELECT_DIGEST_RUN_COLUMNS}
                    ORDER BY started_at DESC, id DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError("最新の実行履歴の取得に失敗しました") from exc

        if row is None:
            return None

        return DigestRun.from_row(row)

    def _get_by_id(
        self,
        connection: sqlite3.Connection,
        run_id: int | None,
    ) -> DigestRun | None:
        if run_id is None:
            return None

        row = connection.execute(
            f"""
            {SELECT_DIGEST_RUN_COLUMNS}
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return DigestRun.from_row(row)
