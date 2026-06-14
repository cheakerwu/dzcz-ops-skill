"""Error recovery strategies."""
from typing import Optional
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError, LoginExpiredError, ErrorSeverity


class RecoveryStrategy:
    """Base class for error recovery strategies."""

    def can_recover(self, error: Exception) -> bool:
        """Check if this strategy can recover from the error."""
        return False

    async def recover(self, context: Context, error: Exception) -> Context:
        """Attempt to recover from error."""
        raise NotImplementedError


class RetryWithDelayStrategy(RecoveryStrategy):
    """Recover by retrying with delay."""

    def __init__(self, delay_seconds: float = 5.0,
                 max_attempts: int = 3):
        self.delay_seconds = delay_seconds
        self.max_attempts = max_attempts

    def can_recover(self, error: Exception) -> bool:
        if isinstance(error, BrowserError):
            return error.retryable and error.severity == ErrorSeverity.TRANSIENT
        return False

    async def recover(self, context: Context, error: Exception) -> Context:
        """Recover by waiting and retrying."""
        import asyncio
        await asyncio.sleep(self.delay_seconds)
        return context


class LoginRecoveryStrategy(RecoveryStrategy):
    """Recover from login errors."""

    def can_recover(self, error: Exception) -> bool:
        return isinstance(error, LoginExpiredError)

    async def recover(self, context: Context, error: Exception) -> Context:
        """Recover by triggering re-login."""
        if isinstance(error, LoginExpiredError) and error.requires_intervention:
            # Cannot auto-recover, need manual intervention
            raise error
        # For other login errors, can attempt auto-relogin
        return context.with_state("requires_relogin", True)


class PageLoadRecoveryStrategy(RecoveryStrategy):
    """Recover from page load errors."""

    def can_recover(self, error: Exception) -> bool:
        from dzcz_merchant_ops.core.errors import PageLoadError
        return isinstance(error, PageLoadError)

    async def recover(self, context: Context, error: Exception) -> Context:
        """Recover by reloading page."""
        return context.with_state("requires_reload", True)


class RecoveryManager:
    """Manage error recovery strategies."""

    def __init__(self):
        self.strategies: list[RecoveryStrategy] = [
            LoginRecoveryStrategy(),
            PageLoadRecoveryStrategy(),
            RetryWithDelayStrategy(),
        ]

    def add_strategy(self, strategy: RecoveryStrategy) -> None:
        """Add a recovery strategy."""
        self.strategies.insert(0, strategy)

    async def attempt_recovery(self, context: Context,
                              error: Exception) -> Optional[Context]:
        """Attempt to recover from error using available strategies."""
        for strategy in self.strategies:
            if strategy.can_recover(error):
                return await strategy.recover(context, error)
        return None
