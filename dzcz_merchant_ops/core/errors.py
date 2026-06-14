"""Error definitions for dzcz-merchant-ops."""
from enum import Enum


__all__ = [
    "ErrorSeverity",
    "BrowserError",
    "InfrastructureError",
    "LoginExpiredError",
    "PageLoadError",
    "ElementNotFoundError",
    "CircuitBreakerOpenError",
    "DeadlockError",
    "LockError",
]


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


class InfrastructureError(Exception):
    """Base class for infrastructure-level errors (circuit breaker, locks, etc.)."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.TRANSIENT,
                 retryable: bool = True):
        super().__init__(message)
        self.severity = severity
        self.retryable = retryable


class LoginExpiredError(BrowserError):
    """Login expired error.

    Login expiry is transient and retryable because the session can be
    refreshed or the user can re-authenticate to recover.
    """

    def __init__(self, message: str = "", profile_id: str = "",
                 platform: str = "", requires_intervention: bool = False):
        if not message:
            message = f"Login expired for profile {profile_id}"
        super().__init__(
            message,
            severity=ErrorSeverity.TRANSIENT,
            retryable=True
        )
        self.profile_id = profile_id
        self.platform = platform
        self.requires_intervention = requires_intervention


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


class CircuitBreakerOpenError(InfrastructureError):
    """Circuit breaker is open error."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message, severity=ErrorSeverity.TRANSIENT, retryable=True)


class DeadlockError(InfrastructureError):
    """Deadlock detected error."""

    def __init__(self, message: str = "Deadlock detected"):
        super().__init__(message, severity=ErrorSeverity.CRITICAL, retryable=False)


class LockError(InfrastructureError):
    """Lock operation error."""

    def __init__(self, message: str = "Lock operation failed"):
        super().__init__(message, severity=ErrorSeverity.TRANSIENT, retryable=True)
