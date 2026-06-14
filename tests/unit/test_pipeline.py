"""Tests for pipeline engine."""
import pytest
from unittest.mock import AsyncMock, patch

from dzcz_merchant_ops.core.pipeline import Pipeline
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError, ErrorSeverity
from dzcz_merchant_ops.core.retry import RetryPolicy
from dzcz_merchant_ops.core.recovery import RecoveryManager


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


def create_no_recovery_manager():
    """Create a recovery manager that doesn't recover anything."""
    manager = RecoveryManager()
    manager.strategies = []  # No strategies = no recovery
    return manager


# --- Existing tests ---


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
    recovery_manager = create_no_recovery_manager()
    pipeline = Pipeline(steps, retry_policy=retry_policy, recovery_manager=recovery_manager)
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


# --- Constructor validation tests ---


def test_pipeline_rejects_non_list_steps():
    """Test Pipeline raises TypeError if steps is not a list."""
    with pytest.raises(TypeError, match="steps must be a list"):
        Pipeline("not a list")  # type: ignore[arg-type]


def test_pipeline_rejects_non_retry_policy():
    """Test Pipeline raises TypeError if retry_policy is wrong type."""
    with pytest.raises(TypeError, match="retry_policy must be a RetryPolicy"):
        Pipeline([], retry_policy="invalid")  # type: ignore[arg-type]


# --- Mutation safety tests ---


def test_pipeline_does_not_mutate_input_list():
    """Pipeline should store a copy of the steps list, not the original."""
    step = MockStep(step_name="step1")
    original_list = [step]
    pipeline = Pipeline(original_list)

    # Mutating the original list should not affect the pipeline
    original_list.append(MockStep(step_name="extra"))
    assert len(pipeline.steps) == 1


@pytest.mark.asyncio
async def test_pipeline_does_not_permanently_mutate_step_retry_policy():
    """Pipeline-level retry policy should not permanently change step's policy."""
    step = MockStep(success=True, step_name="step1")
    original_policy = step.retry_policy

    pipeline_retry = RetryPolicy(max_retries=5, base_delay=0.01)
    pipeline = Pipeline([step], retry_policy=pipeline_retry)

    context = Context(profile_id="test", workflow="test", inputs={})
    await pipeline.execute(context)

    # After execution, step should have its original policy restored
    assert step.retry_policy is original_policy


# --- Retry behavior tests ---


@pytest.mark.asyncio
async def test_retry_delays_are_applied():
    """Verify asyncio.sleep is called with correct delays during retries."""
    step = MockStep(success=False, retryable=True, step_name="step1")
    retry_policy = RetryPolicy(max_retries=2, base_delay=1.0, jitter=False)
    recovery_manager = create_no_recovery_manager()
    pipeline = Pipeline([step], retry_policy=retry_policy, recovery_manager=recovery_manager)

    context = Context(profile_id="test", workflow="test", inputs={})

    with patch("dzcz_merchant_ops.core.step.asyncio.sleep",
               new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(BrowserError):
            await pipeline.execute(context)

        # Should have slept twice (between 3 attempts)
        assert mock_sleep.call_count == 2
        # First retry delay: base_delay * exponential_base^0 = 1.0
        assert mock_sleep.call_args_list[0].args[0] == pytest.approx(1.0)
        # Second retry delay: base_delay * exponential_base^1 = 2.0
        assert mock_sleep.call_args_list[1].args[0] == pytest.approx(2.0)


# --- Edge case tests ---


@pytest.mark.asyncio
async def test_pipeline_zero_retries():
    """With max_retries=0, a retryable error should still fail immediately."""
    step = MockStep(success=False, retryable=True, step_name="step1")
    retry_policy = RetryPolicy(max_retries=0, base_delay=0.01)
    recovery_manager = create_no_recovery_manager()
    pipeline = Pipeline([step], retry_policy=retry_policy, recovery_manager=recovery_manager)

    context = Context(profile_id="test", workflow="test", inputs={})

    with pytest.raises(BrowserError):
        await pipeline.execute(context)

    # Only 1 attempt (no retries)
    assert step.execution_count == 1


@pytest.mark.asyncio
async def test_pipeline_non_browser_error_propagates():
    """Non-BrowserError exceptions should propagate without retry."""
    step = MockStep(success=True, step_name="step1")

    # Override execute to raise a non-BrowserError
    async def broken_execute(context: Context) -> Context:
        raise ValueError("unexpected error")

    step.execute = broken_execute  # type: ignore[assignment]

    pipeline = Pipeline([step])
    context = Context(profile_id="test", workflow="test", inputs={})

    with pytest.raises(ValueError, match="unexpected error"):
        await pipeline.execute(context)
