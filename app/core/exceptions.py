class ApplicationError(Exception):
    """Base application exception."""


class ConversationNotFoundError(ApplicationError):
    """Raised when a conversation cannot be found for the given brand."""


class BackendUnavailableError(ApplicationError):
    """Raised when the backend candidate search cannot be completed."""
