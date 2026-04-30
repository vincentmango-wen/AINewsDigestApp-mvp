"""Application settings loader."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError

BASE_DIR: Final = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH: Final = BASE_DIR / "data" / "app.db"
DEFAULT_LOG_PATH: Final = BASE_DIR / "logs" / "app.log"
DEFAULT_FETCH_LIMIT: Final = 20
DEFAULT_SELECTION_LIMIT: Final = 5
DEFAULT_SCHEDULE_HOUR: Final = 17
DEFAULT_SCHEDULE_MINUTE: Final = 30
CATEGORY_PATTERN: Final = re.compile(
    r"^[A-Za-z0-9_\- \u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF々ー]+$"
)
EMAIL_PATTERN: Final = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Settings:
    category: str
    THE_NEWS_API_TOKEN: str
    openai_api_key: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    mail_from_address: str
    mail_to_address: str
    db_path: Path
    log_path: Path
    fetch_limit: int = DEFAULT_FETCH_LIMIT
    selection_limit: int = DEFAULT_SELECTION_LIMIT
    schedule_hour: int = DEFAULT_SCHEDULE_HOUR
    schedule_minute: int = DEFAULT_SCHEDULE_MINUTE


def _read_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value


def _require_env(name: str) -> str:
    value = _read_env(name)
    if value is None or value.strip() == "":
        raise ConfigurationError(f"必須環境変数が未設定です: {name}")
    return value.strip()


def _require_any_env(*names: str) -> str:
    for name in names:
        value = _read_env(name)
        if value is not None and value.strip() != "":
            return value.strip()
    joined_names = ", ".join(names)
    raise ConfigurationError(f"必須環境変数が未設定です: {joined_names}")


def _normalize_category(raw_value: str) -> str:
    if "\n" in raw_value or "\r" in raw_value:
        raise ConfigurationError("CATEGORY に改行は使用できません")

    normalized = re.sub(r" {2,}", " ", raw_value.strip())
    if normalized == "":
        raise ConfigurationError("CATEGORY は空文字にできません")
    if len(normalized) < 2 or len(normalized) > 50:
        raise ConfigurationError("CATEGORY は2文字以上50文字以内で指定してください")
    if not CATEGORY_PATTERN.fullmatch(normalized):
        raise ConfigurationError(
            "CATEGORY には日本語、英字、数字、半角スペース、'-'、'_' のみ使用できます"
        )
    if re.fullmatch(r"[-_ ]+", normalized):
        raise ConfigurationError("CATEGORY には文字または数字を含めてください")
    return normalized


def _parse_email(name: str, raw_value: str) -> str:
    value = raw_value.strip()
    if not EMAIL_PATTERN.fullmatch(value):
        raise ConfigurationError(f"{name} は有効なメールアドレス形式で指定してください")
    return value


def _parse_int(name: str, raw_value: str) -> int:
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} は整数で指定してください") from exc


def _ensure_positive(name: str, value: int) -> int:
    if value <= 0:
        raise ConfigurationError(f"{name} は1以上で指定してください")
    return value


def _resolve_path(raw_value: str | None, default_path: Path) -> Path:
    if raw_value is None or raw_value.strip() == "":
        return default_path
    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        return BASE_DIR / path
    return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env", override=True)

    category = _normalize_category(_require_env("CATEGORY"))
    THE_NEWS_API_TOKEN = _require_any_env("THE_NEWS_API_TOKEN", "NEWS_API_KEY")
    openai_api_key = _require_env("OPENAI_API_KEY")
    smtp_host = _require_env("SMTP_HOST")
    smtp_port = _parse_int("SMTP_PORT", _require_env("SMTP_PORT"))
    smtp_username = _parse_email("SMTP_USERNAME", _require_env("SMTP_USERNAME"))
    smtp_password = _require_env("SMTP_PASSWORD")
    mail_from_address = _parse_email(
        "MAIL_FROM_ADDRESS",
        _read_env("MAIL_FROM_ADDRESS", smtp_username) or smtp_username,
    )
    mail_to_address = _parse_email("MAIL_TO_ADDRESS", _require_env("MAIL_TO_ADDRESS"))

    fetch_limit = _ensure_positive(
        "FETCH_LIMIT", _parse_int("FETCH_LIMIT", _read_env("FETCH_LIMIT", str(DEFAULT_FETCH_LIMIT)))
    )
    selection_limit = _ensure_positive(
        "SELECTION_LIMIT",
        _parse_int("SELECTION_LIMIT", _read_env("SELECTION_LIMIT", str(DEFAULT_SELECTION_LIMIT))),
    )
    schedule_hour = _parse_int(
        "SCHEDULE_HOUR", _read_env("SCHEDULE_HOUR", str(DEFAULT_SCHEDULE_HOUR))
    )
    schedule_minute = _parse_int(
        "SCHEDULE_MINUTE", _read_env("SCHEDULE_MINUTE", str(DEFAULT_SCHEDULE_MINUTE))
    )

    if schedule_hour < 0 or schedule_hour > 23:
        raise ConfigurationError("SCHEDULE_HOUR は0から23の範囲で指定してください")
    if schedule_minute < 0 or schedule_minute > 59:
        raise ConfigurationError("SCHEDULE_MINUTE は0から59の範囲で指定してください")
    if smtp_port < 1 or smtp_port > 65535:
        raise ConfigurationError("SMTP_PORT は1から65535の範囲で指定してください")

    db_path = _resolve_path(_read_env("DB_PATH"), DEFAULT_DB_PATH)
    log_path = _resolve_path(_read_env("LOG_PATH"), DEFAULT_LOG_PATH)

    return Settings(
        category=category,
        THE_NEWS_API_TOKEN=THE_NEWS_API_TOKEN,
        openai_api_key=openai_api_key,
        smtp_host=smtp_host.strip(),
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        mail_from_address=mail_from_address,
        mail_to_address=mail_to_address,
        db_path=db_path,
        log_path=log_path,
        fetch_limit=fetch_limit,
        selection_limit=selection_limit,
        schedule_hour=schedule_hour,
        schedule_minute=schedule_minute,
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
