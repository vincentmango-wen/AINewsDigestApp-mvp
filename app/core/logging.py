"""Logging setup for FocusDigest."""

from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Final

from app.core.config import get_settings

LOGGER_NAME: Final = "focusdigest"
DEFAULT_LOG_LEVEL: Final = logging.INFO
LOG_FORMAT: Final = (
    "%(asctime)s %(levelname)s %(name)s run_id=%(run_id)s %(message)s"
)
DATE_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
DEFAULT_RUN_ID: Final = "-"


class RunIdFilter(logging.Filter):
    """Ensure all log records include a run_id field."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = DEFAULT_RUN_ID
        return True


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


def _build_stream_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(DEFAULT_LOG_LEVEL)
    handler.setFormatter(_build_formatter())
    handler.addFilter(RunIdFilter())
    return handler


def _build_file_handler(log_path: Path) -> logging.Handler:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.setLevel(DEFAULT_LOG_LEVEL)
    handler.setFormatter(_build_formatter())
    handler.addFilter(RunIdFilter())
    return handler


def configure_logging() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(DEFAULT_LOG_LEVEL)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    stream_handler = _build_stream_handler()
    logger.addHandler(stream_handler)

    try:
        file_handler = _build_file_handler(settings.log_path)
    except OSError as exc:
        logger.error(
            "ログファイルの初期化に失敗したため、標準出力のみで継続します: %s",
            exc,
            extra={"run_id": DEFAULT_RUN_ID},
        )
        return logger

    logger.addHandler(file_handler)
    logger.info(
        "ロガーを初期化しました。ログファイル: %s",
        settings.log_path,
        extra={"run_id": DEFAULT_RUN_ID},
    )
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
