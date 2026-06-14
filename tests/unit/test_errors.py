"""Tests for error definitions."""
import pytest
from dzcz_merchant_ops.core.errors import (
    ErrorSeverity,
    BrowserError,
    InfrastructureError,
    LoginExpiredError,
    PageLoadError,
    ElementNotFoundError,
    CircuitBreakerOpenError,
    DeadlockError,
    LockError,
)


# --- ErrorSeverity ---

def test_error_severity_enum():
    """Test ErrorSeverity enum values."""
    assert ErrorSeverity.TRANSIENT.value == "transient"
    assert ErrorSeverity.PERMANENT.value == "permanent"
    assert ErrorSeverity.CRITICAL.value == "critical"


# --- BrowserError hierarchy ---

def test_browser_error_base():
    """Test BrowserError base class."""
    error = BrowserError("test error", ErrorSeverity.TRANSIENT, retryable=True)
    assert str(error) == "test error"
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_browser_error_is_exception():
    """BrowserError must be catchable as Exception."""
    with pytest.raises(Exception):
        raise BrowserError("boom", ErrorSeverity.CRITICAL)


def test_login_expired_error():
    """Test LoginExpiredError -- should be TRANSIENT and retryable."""
    error = LoginExpiredError("profile123")
    assert "profile123" in str(error)
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_login_expired_error_is_browser_error():
    """LoginExpiredError must be catchable as BrowserError."""
    with pytest.raises(BrowserError):
        raise LoginExpiredError("p1")


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


# --- InfrastructureError hierarchy ---

def test_infrastructure_error_base():
    """Test InfrastructureError base class defaults."""
    error = InfrastructureError("infra down")
    assert str(error) == "infra down"
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_infrastructure_error_is_exception():
    """InfrastructureError must be catchable as Exception."""
    with pytest.raises(Exception):
        raise InfrastructureError("boom")


def test_circuit_breaker_open_error():
    """Test CircuitBreakerOpenError defaults."""
    error = CircuitBreakerOpenError()
    assert str(error) == "Circuit breaker is open"
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_circuit_breaker_open_error_custom_message():
    """Test CircuitBreakerOpenError with custom message."""
    error = CircuitBreakerOpenError("service X circuit open")
    assert str(error) == "service X circuit open"


def test_circuit_breaker_is_infrastructure_error():
    """CircuitBreakerOpenError must be catchable as InfrastructureError."""
    with pytest.raises(InfrastructureError):
        raise CircuitBreakerOpenError()


def test_deadlock_error():
    """Test DeadlockError defaults."""
    error = DeadlockError()
    assert str(error) == "Deadlock detected"
    assert error.severity == ErrorSeverity.CRITICAL
    assert error.retryable is False


def test_deadlock_error_custom_message():
    """Test DeadlockError with custom message."""
    error = DeadlockError("table lock contention")
    assert str(error) == "table lock contention"


def test_deadlock_is_infrastructure_error():
    """DeadlockError must be catchable as InfrastructureError."""
    with pytest.raises(InfrastructureError):
        raise DeadlockError()


def test_lock_error():
    """Test LockError defaults."""
    error = LockError()
    assert str(error) == "Lock operation failed"
    assert error.severity == ErrorSeverity.TRANSIENT
    assert error.retryable is True


def test_lock_error_custom_message():
    """Test LockError with custom message."""
    error = LockError("Lock acquisition failed")
    assert str(error) == "Lock acquisition failed"


def test_lock_error_is_infrastructure_error():
    """LockError must be catchable as InfrastructureError."""
    with pytest.raises(InfrastructureError):
        raise LockError()


# --- Edge-case / inheritance tests ---

def test_all_infrastructure_errors_share_severity_and_retryable():
    """All InfrastructureError subclasses carry severity and retryable attrs."""
    errors = [CircuitBreakerOpenError(), DeadlockError(), LockError()]
    for err in errors:
        assert isinstance(err.severity, ErrorSeverity)
        assert isinstance(err.retryable, bool)


def test_all_browser_errors_share_severity_and_retryable():
    """All BrowserError subclasses carry severity and retryable attrs."""
    errors = [LoginExpiredError("p"), PageLoadError("u", 1.0),
              ElementNotFoundError("s", 1.0)]
    for err in errors:
        assert isinstance(err.severity, ErrorSeverity)
        assert isinstance(err.retryable, bool)


def test_infrastructure_and_browser_are_separate_hierarchies():
    """InfrastructureError is NOT a subclass of BrowserError."""
    assert not issubclass(InfrastructureError, BrowserError)
    assert not issubclass(BrowserError, InfrastructureError)
