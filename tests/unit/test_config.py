from __future__ import annotations

import pytest

from app.core.config import get_settings, reset_settings_cache
from app.core.exceptions import ConfigurationError


def set_valid_env(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("CATEGORY", "AI")
    monkeypatch.setenv("THE_NEWS_API_TOKEN", "new-token")
    monkeypatch.setenv("NEWS_API_KEY", "legacy-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("MAIL_TO_ADDRESS", "to@example.com")
    monkeypatch.delenv("MAIL_FROM_ADDRESS", raising=False)
    monkeypatch.delenv("DB_PATH", raising=False)
    monkeypatch.delenv("LOG_PATH", raising=False)
    monkeypatch.delenv("FETCH_LIMIT", raising=False)
    monkeypatch.delenv("SELECTION_LIMIT", raising=False)
    monkeypatch.delenv("SCHEDULE_HOUR", raising=False)
    monkeypatch.delenv("SCHEDULE_MINUTE", raising=False)
    reset_settings_cache()


def test_get_settings_uses_the_news_api_token_when_present(monkeypatch) -> None:
    set_valid_env(monkeypatch)

    settings = get_settings()

    assert settings.THE_NEWS_API_TOKEN == "new-token"
    reset_settings_cache()


def test_get_settings_falls_back_to_legacy_news_api_key(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.delenv("THE_NEWS_API_TOKEN", raising=False)
    reset_settings_cache()

    settings = get_settings()

    assert settings.THE_NEWS_API_TOKEN == "legacy-token"
    reset_settings_cache()


def test_get_settings_raises_when_required_category_is_missing(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.delenv("CATEGORY", raising=False)
    reset_settings_cache()

    with pytest.raises(ConfigurationError, match="必須環境変数が未設定です: CATEGORY"):
        get_settings()

    reset_settings_cache()


def test_get_settings_raises_when_required_openai_key_is_missing(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_settings_cache()

    with pytest.raises(ConfigurationError, match="必須環境変数が未設定です: OPENAI_API_KEY"):
        get_settings()

    reset_settings_cache()


def test_get_settings_raises_when_category_is_too_short(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.setenv("CATEGORY", "A")
    reset_settings_cache()

    with pytest.raises(ConfigurationError, match="CATEGORY は2文字以上50文字以内で指定してください"):
        get_settings()

    reset_settings_cache()


def test_get_settings_raises_when_category_contains_invalid_characters(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.setenv("CATEGORY", "AI!")
    reset_settings_cache()

    with pytest.raises(
        ConfigurationError,
        match="CATEGORY には日本語、英字、数字、半角スペース、'-'、'_' のみ使用できます",
    ):
        get_settings()

    reset_settings_cache()


def test_get_settings_normalizes_category_whitespace(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.setenv("CATEGORY", "  AI   Agents  ")
    reset_settings_cache()

    settings = get_settings()

    assert settings.category == "AI Agents"
    reset_settings_cache()


def test_get_settings_raises_when_smtp_port_is_not_an_integer(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "abc")
    reset_settings_cache()

    with pytest.raises(ConfigurationError, match="SMTP_PORT は整数で指定してください"):
        get_settings()

    reset_settings_cache()


def test_get_settings_raises_when_mail_to_address_is_invalid(monkeypatch) -> None:
    set_valid_env(monkeypatch)
    monkeypatch.setenv("MAIL_TO_ADDRESS", "invalid-address")
    reset_settings_cache()

    with pytest.raises(
        ConfigurationError,
        match="MAIL_TO_ADDRESS は有効なメールアドレス形式で指定してください",
    ):
        get_settings()

    reset_settings_cache()
