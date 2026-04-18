"""Application exception types."""


class AppError(Exception):
    """Base application error."""


class ConfigurationError(AppError):
    """Raised when required settings are missing or invalid."""
