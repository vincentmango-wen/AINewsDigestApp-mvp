"""Mail build and send service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from app.clients.smtp_client import SmtpClient
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, MailBuildError
from app.schemas.article import Article


class MailService:
    def __init__(
        self,
        *,
        settings: Settings,
        smtp_client_factory: Callable[..., SmtpClient] = SmtpClient,
    ) -> None:
        self._settings = settings
        self._smtp_client_factory = smtp_client_factory

    def build_message(
        self,
        articles: list[Article],
        *,
        target_date: date | datetime | None = None,
    ) -> tuple[str, str] | None:
        if not articles:
            return None

        resolved_date = self._resolve_target_date(target_date)
        subject = f"{self._settings.category}ニュースダイジェスト {resolved_date.isoformat()}"
        if subject.strip() == "":
            raise MailBuildError("メール件名の生成に失敗しました")

        body_parts: list[str] = []
        for article in articles:
            title = article.title.strip()
            url = article.url.strip()
            summary = (article.summary or "").strip()

            if title == "" or url == "" or summary == "":
                raise MailBuildError("メール本文の生成に必要な記事データが不足しています")

            body_parts.append(f"タイトル: {title}\n要約: {summary}\nURL: {url}")

        body = "\n\n".join(body_parts).strip()
        if body == "":
            raise MailBuildError("メール本文の生成に失敗しました")

        return subject, body

    def send_mail(self, subject: str, body: str) -> None:
        self._validate_smtp_settings()
        if subject.strip() == "":
            raise MailBuildError("メール件名の生成に失敗しました")
        if body.strip() == "":
            raise MailBuildError("メール本文の生成に失敗しました")
        smtp_client = self._smtp_client_factory(
            host=self._settings.smtp_host,
            port=self._settings.smtp_port,
            username=self._settings.smtp_username,
            password=self._settings.smtp_password,
            from_address=self._settings.mail_from_address,
        )
        smtp_client.send(subject, body, self._settings.mail_to_address)

    def _validate_smtp_settings(self) -> None:
        required_values = {
            "SMTP_HOST": self._settings.smtp_host,
            "SMTP_PASSWORD": self._settings.smtp_password,
            "SMTP_USERNAME": self._settings.smtp_username,
            "MAIL_FROM_ADDRESS": self._settings.mail_from_address,
            "MAIL_TO_ADDRESS": self._settings.mail_to_address,
        }
        for name, value in required_values.items():
            if value.strip() == "":
                raise ConfigurationError(f"必須環境変数が未設定です: {name}")

    @staticmethod
    def _resolve_target_date(value: date | datetime | None) -> date:
        if value is None:
            return date.today()
        if isinstance(value, datetime):
            return value.date()
        return value
