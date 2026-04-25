"""SMTP client for plain text mail delivery."""

from __future__ import annotations

import smtplib
import socket
import ssl
from email.message import EmailMessage

from app.core.exceptions import MailSendError

DEFAULT_TIMEOUT_SECONDS = 20.0


class SmtpClient:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        smtp_factory: type[smtplib.SMTP] = smtplib.SMTP,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._timeout = timeout
        self._smtp_factory = smtp_factory

    def send(self, subject: str, body: str, to_address: str) -> None:
        normalized_subject = subject.strip()
        normalized_body = body.strip()
        normalized_to_address = to_address.strip()

        if normalized_subject == "":
            raise MailSendError("メール件名が空です")
        if normalized_body == "":
            raise MailSendError("メール本文が空です")
        if normalized_to_address == "":
            raise MailSendError("送信先メールアドレスが空です")

        message = EmailMessage()
        message["From"] = self._from_address
        message["To"] = normalized_to_address
        message["Subject"] = normalized_subject
        message.set_content(normalized_body)

        try:
            with self._smtp_factory(self._host, self._port, timeout=self._timeout) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                smtp.login(self._username, self._password)
                smtp.send_message(message)
        except smtplib.SMTPAuthenticationError as exc:
            raise MailSendError("SMTP 認証に失敗しました") from exc
        except smtplib.SMTPException as exc:
            raise MailSendError("SMTP 送信に失敗しました") from exc
        except (socket.timeout, TimeoutError) as exc:
            raise MailSendError("SMTP 通信がタイムアウトしました") from exc
        except OSError as exc:
            raise MailSendError("SMTP 接続に失敗しました") from exc
