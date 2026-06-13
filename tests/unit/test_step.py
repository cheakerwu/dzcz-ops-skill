"""Tests for step base class."""
import pytest
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError, ErrorSeverity
from dzcz_merchant_ops.core.retry import RetryPolicy


class MockStep(Step):
    """Mock step for testing."""

    def __init__(self, success: bool = True, retryable: bool = False,
                 execution_count: int = 0):
        super().__init__()
        self.success = success
        self.retryable = retryable
        self.execution_count = execution_count
        self._attempts = 0

    async def execute(self, context: Context) -> Context:
        """Execute mock step."""
        self._attempts += 1
        self.execution_count = self._attempts

        if not self.success:
            raise BrowserError(
                "Mock error",
                severity=ErrorSeverity.TRANSIENT,
                retryable=self.retryable
            )

        context.update_state("step_executed", True)
        return context


@pytest.mark.asyncio
async def test_step_execute_success():
    """Test successful step execution."""
    step = MockStep(success=True)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await step.execute(context)
    assert result.get_state("step_executed") is True


@pytest.mark.asyncio
async def test_step_execute_with_retry_success():
    """Test step execution with retry on success."""
    step = MockStep(success=True)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await step.execute_with_retry(context)
    assert result.get_state("step_executed") is True
    assert step.execution_count == 1


@pytest.mark.asyncio
async def test_step_execute_with_retry_failure():
    """Test step execution with retry on failure."""
    step = MockStep(success=False, retryable=True)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    retry_policy = RetryPolicy(max_retries=2, base_delay=0.01)
    step.retry_policy = retry_policy

    with pytest.raises(BrowserError):
        await step.execute_with_retry(context)

    # Should have tried 3 times (1 initial + 2 retries)
    assert step.execution_count == 3


@pytest.mark.asyncio
async def test_step_execute_non_retryable_error():
    """Test step execution with non-retryable error."""
    step = MockStep(success=False, retryable=False)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    retry_policy = RetryPolicy(max_retries=2, base_delay=0.01)
    step.retry_policy = retry_policy

    with pytest.raises(BrowserError):
        await step.execute_with_retry(context)

    # Should have tried only once (non-retryable)
    assert step.execution_count == 1
