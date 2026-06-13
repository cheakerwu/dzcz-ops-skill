"""Tests for error definitions."""
import pytest
from dzcz_merchant_ops.core.errors import (
    ErrorSeverity,
    BrowserError,
    LoginExpiredError,
    PageLoadError,
    ElementNotFoundError,
    CircuitBreakerOpenError,
    DeadlockError,
    LockError,
)


def test_error_severity_enum():
    """Test ErrorSeverity enum values."""
    assert ErrorSeverity.TRANSIENT.value == "transient"
    assert ErrorSeverity.PERMANENT.value == "permanent"
    assert ErrorSeverity.CRITICAL.value == "critical"


def test_browser_error_base():
    """Test BrowserError base class."""
    error = BrowserError("test error", ErrorSeverity.TRANSIENT, retryable=True)
    assert str(error) == "test error"
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_login_expired_error():
    """Test LoginExpiredError."""
    error = LoginExpiredError("profile123")
    assert "profile123" in str(error)
    assert error.severity == ErrorSeverity.PERMANENT
    assert error.retryable is False


def test_page_load_error():
    """Test PageLoadError."""
    error = PageLoadError("https://example.com", 30.0)
    assert "https://example.com" in str(error)
    assert "30.0" in str(error)
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_element_not_found_error():
    """Test ElementNotFoundError."""
    error = ElementNotFoundError("#button", 10.0)
    assert "#button" in str(error)
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_circuit_breaker_open_error():
    """Test CircuitBreakerOpenError."""
    error = CircuitBreakerOpenError("Circuit breaker is open")
    assert str(error) == "Circuit breaker is open"


def test_deadlock_error():
    """Test DeadlockError."""
    error = DeadlockError("Deadlock detected")
    assert str(error) == "Deadlock detected"


def test_lock_error():
    """Test LockError."""
    error = LockError("Lock acquisition failed")
    assert str(error) == "Lock acquisition failed"
