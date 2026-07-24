class SentryBaseException(Exception):
    """Base exception for all Sentry-related errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AIServiceError(SentryBaseException):
    """Raised when the AI service (e.g., Gemma) fails."""
    pass

class DatabaseError(SentryBaseException):
    """Raised when a database operation fails."""
    pass

class WebhookError(SentryBaseException):
    """Raised when webhook processing fails."""
    pass

class ValidationError(SentryBaseException):
    """Raised when data validation fails."""
    pass
