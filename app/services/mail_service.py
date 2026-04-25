"""Mail build and send service."""

from __future__ import annotations

from collections.abc import Callable

from app.clients.smtp_client import SmtpClient
from app.core.config import Settings
from app.core.exceptions import ConfigurationError


class MailService:
    def __init__(
        self,
        *,
        settings: Settings,
        smtp_client_factory: Callable[..., SmtpClient] = SmtpClient,
    ) -> None:
        self._settings = settings
        self._smtp_client_factory = smtp_client_factory

    def send_mail(self, subject: str, body: str) -> None:
        self._validate_smtp_settings()
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
