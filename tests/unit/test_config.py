from __future__ import annotations

from app.core.config import get_settings, reset_settings_cache


def test_get_settings_uses_the_news_api_token_when_present(monkeypatch) -> None:
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
    reset_settings_cache()

    settings = get_settings()

    assert settings.THE_NEWS_API_TOKEN == "new-token"
    reset_settings_cache()


def test_get_settings_falls_back_to_legacy_news_api_key(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("CATEGORY", "AI")
    monkeypatch.delenv("THE_NEWS_API_TOKEN", raising=False)
    monkeypatch.setenv("NEWS_API_KEY", "legacy-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("MAIL_TO_ADDRESS", "to@example.com")
    reset_settings_cache()

    settings = get_settings()

    assert settings.THE_NEWS_API_TOKEN == "legacy-token"
    reset_settings_cache()
