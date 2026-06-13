"""Error definitions for dzcz-merchant-ops."""
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    TRANSIENT = "transient"    # Transient errors, can be retried
    PERMANENT = "permanent"    # Permanent errors, cannot be retried
    CRITICAL = "critical"      # Critical errors, require manual intervention


class BrowserError(Exception):
    """Base class for browser operation errors."""

    def __init__(self, message: str, severity: ErrorSeverity,
                 retryable: bool = False):
        super().__init__(message)
        self.severity = severity
        self.retryable = retryable


class LoginExpiredError(BrowserError):
    """Login expired error."""

    def __init__(self, profile_id: str):
        super().__init__(
            f"Login expired for profile {profile_id}",
            severity=ErrorSeverity.PERMANENT,
            retryable=False
        )


class PageLoadError(BrowserError):
    """Page load timeout error."""

    def __init__(self, url: str, timeout: float):
        super().__init__(
            f"Page load timeout for {url} after {timeout}s",
            severity=ErrorSeverity.TRANSIENT,
            retryable=True
        )


class ElementNotFoundError(BrowserError):
    """Element not found error."""

    def __init__(self, selector: str, timeout: float):
        super().__init__(
            f"Element {selector} not found after {timeout}s",
            severity=ErrorSeverity.TRANSIENT,
            retryable=True
        )


class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open error."""
    pass


class DeadlockError(Exception):
    """Deadlock detected error."""
    pass


class LockError(Exception):
    """Lock operation error."""
    pass
