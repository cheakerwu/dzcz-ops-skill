"""Pipeline engine for executing workflow steps."""
from typing import List, Optional

from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.retry import RetryPolicy

__all__ = ["Pipeline"]


class Pipeline:
    """Pipeline engine for executing workflow steps.

    Steps are executed sequentially. If a step fails and is retryable,
    it will be retried according to the retry policy.
    """

    def __init__(self, steps: List[Step],
                 retry_policy: Optional[RetryPolicy] = None):
        """Initialize pipeline with steps.

        Args:
            steps: List of steps to execute
            retry_policy: Default retry policy for all steps
        """
        self.steps = steps
        self.retry_policy = retry_policy

        # Apply pipeline retry policy to all steps if provided
        if retry_policy:
            for step in self.steps:
                step.retry_policy = retry_policy

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
            context = await step.execute_with_retry(context)

        return context
