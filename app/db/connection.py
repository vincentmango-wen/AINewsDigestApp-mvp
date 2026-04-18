"""SQLite connection helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

SQLITE_TIMEOUT_SECONDS = 30.0
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _ensure_db_directory(db_path: Path) -> None:
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseError(
            f"データベース保存先ディレクトリの作成に失敗しました: {db_path.parent}"
        ) from exc


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")


def create_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_path = settings.db_path

    _ensure_db_directory(db_path)

    try:
        connection = sqlite3.connect(
            database=db_path,
            timeout=SQLITE_TIMEOUT_SECONDS,
        )
    except sqlite3.Error as exc:
        raise DatabaseError(f"SQLite への接続に失敗しました: {db_path}") from exc

    try:
        _configure_connection(connection)
    except sqlite3.Error as exc:
        connection.close()
        raise DatabaseError("SQLite 接続の初期設定に失敗しました") from exc

    return connection


def initialize_database() -> None:
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise DatabaseError(f"スキーマ定義ファイルの読込に失敗しました: {SCHEMA_PATH}") from exc

    try:
        with get_connection() as connection:
            connection.executescript(schema_sql)
            connection.commit()
    except sqlite3.Error as exc:
        raise DatabaseError("データベース初期化に失敗しました") from exc


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = create_connection()
    try:
        yield connection
    finally:
        connection.close()
