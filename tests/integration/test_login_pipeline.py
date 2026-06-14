"""Integration test for login pipeline."""
import pytest
from dzcz_merchant_ops.core.pipeline import Pipeline
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.errors import LoginExpiredError
from dzcz_merchant_ops.core.recovery import RecoveryManager


class MockLoginStep(Step):
    """Mock login step that fails once then succeeds."""

    def __init__(self):
        super().__init__()
        self.attempt = 0

    @property
    def name(self):
        return "mock_login"

    async def execute(self, context):
        self.attempt += 1
        if self.attempt == 1:
            raise LoginExpiredError("First attempt fails")
        return context.with_state("login_status", "success")


class MockNormalStep(Step):
    """Mock normal step that always succeeds."""

    @property
    def name(self):
        return "mock_normal"

    async def execute(self, context):
        return context.with_state("normal_step", "done")


@pytest.mark.asyncio
async def test_pipeline_with_login_recovery():
    """Test pipeline recovers from login error."""
    step = MockLoginStep()
    pipeline = Pipeline([step])

    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await pipeline.execute(context)
    assert result.state.get("login_status") == "success"
    assert step.attempt == 2


@pytest.mark.asyncio
async def test_pipeline_multiple_steps():
    """Test pipeline executes multiple steps."""
    login_step = MockLoginStep()
    normal_step = MockNormalStep()
    pipeline = Pipeline([login_step, normal_step])

    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await pipeline.execute(context)
    assert result.state.get("login_status") == "success"
    assert result.state.get("normal_step") == "done"


@pytest.mark.asyncio
async def test_pipeline_with_custom_recovery():
    """Test pipeline with custom recovery manager."""
    from dzcz_merchant_ops.core.recovery import RecoveryStrategy

    class CustomRecovery(RecoveryStrategy):
        def can_recover(self, error):
            return isinstance(error, LoginExpiredError)

        async def recover(self, context, error):
            # Custom recovery just returns context, step will retry
            return context

    manager = RecoveryManager()
    manager.add_strategy(CustomRecovery())

    step = MockLoginStep()
    pipeline = Pipeline([step], recovery_manager=manager)

    context = Context(
        profile_id="test",
        workflow="test",
        inputs={}
    )

    result = await pipeline.execute(context)
    # Step retries after recovery and succeeds
    assert result.state.get("login_status") == "success"
    assert step.attempt == 2
