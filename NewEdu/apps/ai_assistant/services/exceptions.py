class AIError(Exception):
    """Base exception for all AI-related errors in NEWEDU."""
    pass

class AIConfigurationError(AIError):
    """Raised when AI API keys or models are missing or invalidly configured."""
    pass

class AIServiceUnavailable(AIError):
    """Raised when the AI provider's service is down or unreachable."""
    pass

class AIRateLimitExceeded(AIError):
    """Raised when the application hits provider rate limits (429)."""
    pass

class AITimeoutError(AIError):
    """Raised when the AI provider takes too long to respond."""
    pass

class AIInvalidResponse(AIError):
    """Raised when the AI returns a malformed response that cannot be parsed."""
    pass

class AIValidationError(AIError):
    """Raised when the AI's response does not match the required Pydantic schema or business rules."""
    pass
