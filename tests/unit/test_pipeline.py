"""Tests for pipeline engine."""
import pytest
from dzcz_merchant_ops.core.pipeline import Pipeline
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError, ErrorSeverity
from dzcz_merchant_ops.core.retry import RetryPolicy


class MockStep(Step):
    """Mock step for testing."""

    def __init__(self, success: bool = True, retryable: bool = False,
                 execution_count: int = 0, step_name: str = "mock"):
        super().__init__()
        self.success = success
        self.retryable = retryable
        self.execution_count = execution_count
        self.step_name = step_name
        self._attempts = 0

    async def execute(self, context: Context) -> Context:
        """Execute mock step."""
        self._attempts += 1
        self.execution_count = self._attempts

        if not self.success:
            raise BrowserError(
                f"Mock error in {self.step_name}",
                severity=ErrorSeverity.TRANSIENT,
                retryable=self.retryable
            )

        context.update_state(f"{self.step_name}_executed", True)
        return context


@pytest.mark.asyncio
async def test_pipeline_execute_success():
    """Test successful pipeline execution."""
    steps = [
        MockStep(success=True, step_name="step1"),
        MockStep(success=True, step_name="step2"),
        MockStep(success=True, step_name="step3"),
    ]
    pipeline = Pipeline(steps)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await pipeline.execute(context)

    assert result.get_state("step1_executed") is True
    assert result.get_state("step2_executed") is True
    assert result.get_state("step3_executed") is True


@pytest.mark.asyncio
async def test_pipeline_execute_stops_on_failure():
    """Test pipeline stops on first failure."""
    steps = [
        MockStep(success=True, step_name="step1"),
        MockStep(success=False, retryable=False, step_name="step2"),
        MockStep(success=True, step_name="step3"),
    ]
    pipeline = Pipeline(steps)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    with pytest.raises(BrowserError):
        await pipeline.execute(context)

    # step1 should have executed, step2 failed, step3 not reached
    assert steps[0].execution_count == 1
    assert steps[1].execution_count == 1
    assert steps[2].execution_count == 0


@pytest.mark.asyncio
async def test_pipeline_execute_with_retry():
    """Test pipeline execution with retry on failure."""
    steps = [
        MockStep(success=True, step_name="step1"),
        MockStep(success=False, retryable=True, step_name="step2"),
        MockStep(success=True, step_name="step3"),
    ]

    retry_policy = RetryPolicy(max_retries=2, base_delay=0.01)
    pipeline = Pipeline(steps, retry_policy=retry_policy)
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    with pytest.raises(BrowserError):
        await pipeline.execute(context)

    # step1 executed once, step2 failed 3 times (1 + 2 retries), step3 not reached
    assert steps[0].execution_count == 1
    assert steps[1].execution_count == 3
    assert steps[2].execution_count == 0


@pytest.mark.asyncio
async def test_pipeline_empty():
    """Test pipeline with no steps."""
    pipeline = Pipeline([])
    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await pipeline.execute(context)
    assert result.profile_id == "test"
