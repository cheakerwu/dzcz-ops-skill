"""Tests for recovery strategies."""
import pytest
from dzcz_merchant_ops.core.recovery import (
    RecoveryStrategy,
    RetryWithDelayStrategy,
    LoginRecoveryStrategy,
    PageLoadRecoveryStrategy,
    RecoveryManager
)
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import (
    BrowserError,
    LoginExpiredError,
    PageLoadError,
    ErrorSeverity
)


@pytest.fixture
def context():
    return Context(
        profile_id="test_user",
        workflow="test",
        inputs={}
    )


def test_retry_strategy_can_recover():
    """Test retry strategy can recover from transient errors."""
    strategy = RetryWithDelayStrategy()
    error = BrowserError("test", ErrorSeverity.TRANSIENT, retryable=True)
    assert strategy.can_recover(error) is True


def test_retry_strategy_cannot_recover_permanent():
    """Test retry strategy cannot recover from permanent errors."""
    strategy = RetryWithDelayStrategy()
    error = BrowserError("test", ErrorSeverity.PERMANENT, retryable=False)
    assert strategy.can_recover(error) is False


def test_login_recovery_strategy():
    """Test login recovery strategy."""
    strategy = LoginRecoveryStrategy()
    error = LoginExpiredError("test", platform="bilibili")
    assert strategy.can_recover(error) is True


def test_login_recovery_strategy_requires_intervention():
    """Test login recovery raises error when intervention required."""
    import asyncio
    strategy = LoginRecoveryStrategy()
    error = LoginExpiredError("test", requires_intervention=True)

    context = Context(profile_id="test", workflow="test", inputs={})

    with pytest.raises(LoginExpiredError):
        asyncio.run(strategy.recover(context, error))


@pytest.mark.asyncio
async def test_login_recovery_auto_relogin(context):
    """Test login recovery sets relogin flag."""
    strategy = LoginRecoveryStrategy()
    error = LoginExpiredError("test", requires_intervention=False)
    result = await strategy.recover(context, error)
    assert result.state.get("requires_relogin") is True


def test_page_load_recovery_strategy():
    """Test page load recovery strategy."""
    strategy = PageLoadRecoveryStrategy()
    error = PageLoadError("http://test.com", 30.0)
    assert strategy.can_recover(error) is True


@pytest.mark.asyncio
async def test_page_load_recovery_sets_reload(context):
    """Test page load recovery sets reload flag."""
    strategy = PageLoadRecoveryStrategy()
    error = PageLoadError("http://test.com", 30.0)
    result = await strategy.recover(context, error)
    assert result.state.get("requires_reload") is True


@pytest.mark.asyncio
async def test_recovery_manager(context):
    """Test recovery manager attempts multiple strategies."""
    manager = RecoveryManager()
    error = BrowserError("test", ErrorSeverity.TRANSIENT, retryable=True)
    result = await manager.attempt_recovery(context, error)
    assert result is not None


@pytest.mark.asyncio
async def test_recovery_manager_no_recovery(context):
    """Test recovery manager returns None when no strategy works."""
    manager = RecoveryManager()
    error = Exception("Unknown error")
    result = await manager.attempt_recovery(context, error)
    assert result is None


def test_add_strategy():
    """Test adding custom strategy."""
    manager = RecoveryManager()
    initial_count = len(manager.strategies)

    class CustomStrategy(RecoveryStrategy):
        def can_recover(self, error):
            return True

    manager.add_strategy(CustomStrategy())
    assert len(manager.strategies) == initial_count + 1
