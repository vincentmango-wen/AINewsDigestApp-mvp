"""Application exception types."""

from __future__ import annotations


class AppError(Exception):
    """Base application error with API metadata."""

    error_code = "INTERNAL_SERVER_ERROR"
    status_code = 500

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class ConfigurationError(AppError):
    """Raised when required settings are missing or invalid."""

    error_code = "CONFIGURATION_ERROR"
    status_code = 400


class DatabaseError(AppError):
    """Raised when database access fails."""

    error_code = "DATABASE_ERROR"
    status_code = 500


class ExternalApiError(AppError):
    """Raised when an external API call fails."""

    error_code = "EXTERNAL_API_ERROR"
    status_code = 500


class MailBuildError(AppError):
    """Raised when mail subject or body cannot be built."""

    error_code = "MAIL_BUILD_ERROR"
    status_code = 500


class MailSendError(AppError):
    """Raised when SMTP delivery fails."""

    error_code = "MAIL_SEND_ERROR"
    status_code = 500


class JobAlreadyRunningError(AppError):
    """Raised when a digest job is already running."""

    error_code = "JOB_ALREADY_RUNNING"
    status_code = 409


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    error_code = "NOT_FOUND"
    status_code = 404
