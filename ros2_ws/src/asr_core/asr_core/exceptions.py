"""Project-level custom exception hierarchy."""

class AsrError(Exception):
    """Base ASR exception."""


class AsrConfigurationError(AsrError):
    """Raised when backend configuration is invalid."""


class AsrCredentialError(AsrError):
    """Raised when cloud credentials are missing or invalid."""


class AsrInferenceError(AsrError):
    """Raised on inference/runtime backend failure."""
