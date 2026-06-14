"""集成测试 - 验证点赞工作流完整流程"""
import asyncio
from dzcz_merchant_ops.core.pipeline import Pipeline
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.retry import RetryPolicy
from dzcz_merchant_ops.monitor.logger import StructuredLogger
from dzcz_merchant_ops.scheduler.lock import LockManager


class MockStep(Step):
    """模拟步骤"""
    def __init__(self, name: str, should_fail: bool = False):
        super().__init__()
        self._name = name
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: Context) -> Context:
        print(f"  [EXEC] {self._name}")
        if self._should_fail:
            raise Exception(f"Mock failure in {self._name}")
        ctx = context.with_state("step", self._name)
        return ctx.with_state("status", "done")


async def test_like_workflow():
    """测试点赞工作流"""
    print("\n=== Integration Test: Like Workflow ===\n")

    # 1. 创建上下文
    ctx = Context(
        profile_id="test_user",
        workflow="bilibili_like",
        inputs={"video_url": "https://bilibili.com/video/test123"}
    )
    print(f"[1] Context created: profile={ctx.profile_id}")

    # 2. 创建步骤
    steps = [
        MockStep("login"),
        MockStep("navigate"),
        MockStep("like"),
        MockStep("verify"),
    ]
    print(f"[2] Steps created: {[s.name for s in steps]}")

    # 3. 创建重试策略
    retry = RetryPolicy(max_retries=2, base_delay=0.1)
    print(f"[3] RetryPolicy: max_retries={retry.max_retries}")

    # 4. 创建管道并执行
    pipeline = Pipeline(steps, retry_policy=retry)
    result = await pipeline.execute(ctx)
    print(f"[4] Pipeline executed: state={result.state}")

    # 5. 验证结果
    assert result.state.get("step") == "verify", f"Expected 'verify', got {result.state.get('step')}"
    assert result.state.get("status") == "done"
    print("[5] Assertions PASSED")

    # 6. 测试日志记录
    logger = StructuredLogger(task_id="integration_test", profile_id="test_user", log_file="test.log")
    logger.log_step_start("test_step")
    logger.log_step_end("test_step", "success")
    print(f"[6] Logger: {len(logger.step_logs)} steps logged")

    # 7. 测试锁管理器
    lock_mgr = LockManager()
    acquired = await lock_mgr.acquire_profile_lock("test_user", "task1")
    assert acquired == True
    print(f"[7] Lock acquired: {acquired}")

    lock_mgr.release_profile_lock("test_user", "task1")
    print("[8] Lock released")

    print("\n=== ALL INTEGRATION TESTS PASSED ===\n")


if __name__ == "__main__":
    asyncio.run(test_like_workflow())
