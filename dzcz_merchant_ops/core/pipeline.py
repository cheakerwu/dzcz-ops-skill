"""Pipeline engine for executing workflow steps."""
from typing import List, Optional

from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.retry import RetryPolicy
from dzcz_merchant_ops.core.recovery import RecoveryManager

__all__ = ["Pipeline"]


class Pipeline:
    """Pipeline engine for executing workflow steps.

    Steps are executed sequentially. If a step fails and is retryable,
    it will be retried according to the retry policy.
    """

    def __init__(self, steps: List[Step],
                 retry_policy: Optional[RetryPolicy] = None,
                 recovery_manager: Optional[RecoveryManager] = None):
        """Initialize pipeline with steps.

        Args:
            steps: List of steps to execute
            retry_policy: Default retry policy for all steps
            recovery_manager: Manager for error recovery strategies

        Raises:
            TypeError: If steps is not a list or retry_policy is not a RetryPolicy
        """
        if not isinstance(steps, list):
            raise TypeError(
                f"steps must be a list, got {type(steps).__name__}"
            )
        if retry_policy is not None and not isinstance(retry_policy, RetryPolicy):
            raise TypeError(
                f"retry_policy must be a RetryPolicy or None, "
                f"got {type(retry_policy).__name__}"
            )

        # Store a shallow copy to avoid mutating the caller's list
        self.steps: List[Step] = list(steps)
        self.retry_policy = retry_policy
        self.recovery_manager = recovery_manager or RecoveryManager()

    async def execute(self, context: Context) -> Context:
        """Execute all steps in the pipeline.

        Args:
            context: Initial execution context

        Returns:
            Final context after all steps executed

        Raises:
            BrowserError: If any step fails
        """
        for step in self.steps:
            # Temporarily override retry policy if pipeline-level policy is set
            original_policy = step.retry_policy
            if self.retry_policy is not None:
                step.retry_policy = self.retry_policy
            try:
                context = await step.execute_with_retry(context)
            except Exception as e:
                # Attempt recovery
                recovered_context = await self.recovery_manager.attempt_recovery(
                    context, e
                )
                if recovered_context is not None:
                    context = recovered_context
                    # Retry the step
                    context = await step.execute_with_retry(context)
                else:
                    raise
            finally:
                # Restore original policy to avoid side effects
                step.retry_policy = original_policy

        return context
