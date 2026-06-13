"""Base class for workflow steps."""
from abc import ABC, abstractmethod
import asyncio
from typing import Optional

from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError
from dzcz_merchant_ops.core.retry import RetryPolicy


class Step(ABC):
    """Base class for workflow steps.

    All workflow steps should inherit from this class and
    implement the execute method.
    """

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        """Initialize step with optional retry policy.

        Args:
            retry_policy: Retry policy for this step
        """
        self.retry_policy = retry_policy or RetryPolicy()

    @abstractmethod
    async def execute(self, context: Context) -> Context:
        """Execute the step.

        Args:
            context: Current execution context

        Returns:
            Updated context

        Raises:
            BrowserError: If step execution fails
        """
        pass

    async def execute_with_retry(self, context: Context) -> Context:
        """Execute step with retry logic.

        Args:
            context: Current execution context

        Returns:
            Updated context

        Raises:
            BrowserError: If step execution fails after all retries
        """
        last_error = None

        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                return await self.execute(context)
            except BrowserError as e:
                last_error = e

                # Don't retry if error is not retryable
                if not e.retryable:
                    raise

                # Don't retry if this was the last attempt
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

        raise last_error
