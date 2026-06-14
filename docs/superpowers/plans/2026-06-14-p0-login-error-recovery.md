# P0 优先级：登录流程适配与错误恢复机制

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现真实商家后台的登录流程适配和错误恢复机制，支持短信/验证码/二维码等复杂登录场景，确保业务操作的可靠性。

**Architecture:** 扩展现有 Pipeline 架构，添加登录检测步骤、人工介入机制、错误恢复策略。

---

## 任务列表

### Task 1: 登录状态检测步骤

**Files:**
- Create: `dzcz_merchant_ops/steps/__init__.py`
- Create: `dzcz_merchant_ops/steps/login.py`
- Create: `tests/unit/test_login_step.py`

- [ ] **Step 1: 创建步骤模块初始化**

```python
# dzcz_merchant_ops/steps/__init__.py
"""Workflow steps module."""
from dzcz_merchant_ops.steps.login import LoginDetectionStep, LoginMethod

__all__ = ["LoginDetectionStep", "LoginMethod"]
```

- [ ] **Step 2: 编写登录检测步骤**

```python
# dzcz_merchant_ops/steps/login.py
"""Login detection and handling steps."""
import asyncio
from enum import Enum
from typing import Optional, Dict, Any
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import LoginExpiredError


class LoginMethod(Enum):
    """Supported login methods."""
    PASSWORD = "password"
    SMS = "sms"
    QR_CODE = "qr_code"
    TWO_FACTOR = "two_factor"


class LoginDetectionStep(Step):
    """Detect login status and handle login flows."""

    def __init__(self, platform: str, selectors: Dict[str, str]):
        """
        Args:
            platform: Platform name (bilibili, meituan, douyin)
            selectors: CSS selectors for login detection
        """
        super().__init__()
        self.platform = platform
        self.selectors = selectors

    @property
    def name(self) -> str:
        return f"login_detection_{self.platform}"

    async def execute(self, context: Context) -> Context:
        """Execute login detection."""
        # 1. Check if already logged in
        is_logged_in = await self._check_login_status(context)
        if is_logged_in:
            return context.with_state("login_status", "logged_in")

        # 2. Detect login method required
        login_method = await self._detect_login_method(context)

        # 3. Handle based on method
        if login_method == LoginMethod.PASSWORD:
            return await self._handle_password_login(context)
        elif login_method == LoginMethod.SMS:
            return await self._handle_sms_login(context)
        elif login_method == LoginMethod.QR_CODE:
            return await self._handle_qr_login(context)
        else:
            raise LoginExpiredError(
                f"Unsupported login method: {login_method}",
                platform=self.platform
            )

    async def _check_login_status(self, context: Context) -> bool:
        """Check if user is already logged in."""
        # Placeholder - actual implementation depends on platform
        return False

    async def _detect_login_method(self, context: Context) -> LoginMethod:
        """Detect which login method is required."""
        # Placeholder - actual implementation depends on platform
        return LoginMethod.PASSWORD

    async def _handle_password_login(self, context: Context) -> Context:
        """Handle password-based login."""
        # Password login requires manual intervention
        raise LoginExpiredError(
            "Password login required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )

    async def _handle_sms_login(self, context: Context) -> Context:
        """Handle SMS verification login."""
        # SMS login requires manual intervention
        raise LoginExpiredError(
            "SMS verification required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )

    async def _handle_qr_login(self, context: Context) -> Context:
        """Handle QR code login."""
        # QR code requires manual scan
        raise LoginExpiredError(
            "QR code scan required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )
```

- [ ] **Step 3: 编写登录检测步骤测试**

```python
# tests/unit/test_login_step.py
"""Tests for login detection step."""
import pytest
from dzcz_merchant_ops.steps.login import LoginDetectionStep, LoginMethod
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import LoginExpiredError


@pytest.fixture
def context():
    return Context(
        profile_id="test_user",
        workflow="test",
        inputs={}
    )


def test_login_method_enum():
    """Test LoginMethod enum values."""
    assert LoginMethod.PASSWORD.value == "password"
    assert LoginMethod.SMS.value == "sms"
    assert LoginMethod.QR_CODE.value == "qr_code"


def test_login_detection_step_name():
    """Test step name generation."""
    step = LoginDetectionStep(platform="bilibili", selectors={})
    assert step.name == "login_detection_bilibili"


@pytest.mark.asyncio
async def test_login_detection_requires_intervention(context):
    """Test that login detection raises error for manual intervention."""
    step = LoginDetectionStep(platform="bilibili", selectors={})
    with pytest.raises(LoginExpiredError) as exc_info:
        await step.execute(context)
    assert exc_info.value.requires_intervention is True
```

- [ ] **Step 4: 更新 LoginExpiredError 支持 requires_intervention**

```python
# dzcz_merchant_ops/core/errors.py - 添加 requires_intervention 属性
class LoginExpiredError(BrowserError):
    """Raised when login session has expired."""

    def __init__(self, message: str, platform: str = "", 
                 requires_intervention: bool = False):
        super().__init__(
            message,
            ErrorSeverity.TRANSIENT,
            retryable=True
        )
        self.platform = platform
        self.requires_intervention = requires_intervention
```

- [ ] **Step 5: 运行测试**

```bash
pytest tests/unit/test_login_step.py -v
```

---

### Task 2: 人工介入机制

**Files:**
- Create: `dzcz_merchant_ops/core/intervention.py`
- Create: `tests/unit/test_intervention.py`

- [ ] **Step 1: 编写人工介入管理器**

```python
# dzcz_merchant_ops/core/intervention.py
"""Manual intervention handling for complex scenarios."""
import asyncio
from typing import Optional, Callable, Any
from dzcz_merchant_ops.core.context import Context


class InterventionRequest:
    """Request for manual intervention."""

    def __init__(self, step_name: str, message: str, 
                 timeout_seconds: int = 300):
        self.step_name = step_name
        self.message = message
        self.timeout_seconds = timeout_seconds
        self.response: Optional[Any] = None
        self.event = asyncio.Event()

    async def wait_for_response(self) -> Any:
        """Wait for manual intervention response."""
        try:
            await asyncio.wait_for(
                self.event.wait(),
                timeout=self.timeout_seconds
            )
            return self.response
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Intervention timeout after {self.timeout_seconds}s"
            )

    def provide_response(self, response: Any) -> None:
        """Provide response to intervention request."""
        self.response = response
        self.event.set()


class InterventionManager:
    """Manage manual intervention requests."""

    def __init__(self):
        self.pending_requests: dict[str, InterventionRequest] = {}

    def request_intervention(self, step_name: str, message: str,
                           timeout_seconds: int = 300) -> InterventionRequest:
        """Create intervention request."""
        request = InterventionRequest(step_name, message, timeout_seconds)
        self.pending_requests[step_name] = request
        return request

    def provide_response(self, step_name: str, response: Any) -> None:
        """Provide response to pending request."""
        if step_name in self.pending_requests:
            self.pending_requests[step_name].provide_response(response)
            del self.pending_requests[step_name]

    def get_pending_requests(self) -> list[InterventionRequest]:
        """Get list of pending intervention requests."""
        return list(self.pending_requests.values())
```

- [ ] **Step 2: 编写人工介入测试**

```python
# tests/unit/test_intervention.py
"""Tests for intervention manager."""
import pytest
import asyncio
from dzcz_merchant_ops.core.intervention import InterventionManager


@pytest.mark.asyncio
async def test_intervention_request_response():
    """Test intervention request and response flow."""
    manager = InterventionManager()
    request = manager.request_intervention(
        "login_step",
        "Please scan QR code",
        timeout_seconds=5
    )

    # Simulate response after delay
    async def provide_response():
        await asyncio.sleep(0.1)
        manager.provide_response("login_step", "scanned")

    asyncio.create_task(provide_response())
    response = await request.wait_for_response()
    assert response == "scanned"


@pytest.mark.asyncio
async def test_intervention_timeout():
    """Test intervention timeout."""
    manager = InterventionManager()
    request = manager.request_intervention(
        "login_step",
        "Please scan QR code",
        timeout_seconds=1
    )

    with pytest.raises(TimeoutError):
        await request.wait_for_response()
```

---

### Task 3: 错误恢复策略

**Files:**
- Create: `dzcz_merchant_ops/core/recovery.py`
- Create: `tests/unit/test_recovery.py`

- [ ] **Step 1: 编写错误恢复策略**

```python
# dzcz_merchant_ops/core/recovery.py
"""Error recovery strategies."""
from typing import Optional, Callable, Any
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import BrowserError, ErrorSeverity


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
        from dzcz_merchant_ops.core.errors import LoginExpiredError
        return isinstance(error, LoginExpiredError)

    async def recover(self, context: Context, error: Exception) -> Context:
        """Recover by triggering re-login."""
        from dzcz_merchant_ops.core.errors import LoginExpiredError
        if isinstance(error, LoginExpiredError) and error.requires_intervention:
            # Cannot auto-recover, need manual intervention
            raise error
        # For other login errors, can attempt auto-relogin
        return context.with_state("requires_relogin", True)


class RecoveryManager:
    """Manage error recovery strategies."""

    def __init__(self):
        self.strategies: list[RecoveryStrategy] = [
            LoginRecoveryStrategy(),
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
```

- [ ] **Step 2: 编写错误恢复测试**

```python
# tests/unit/test_recovery.py
"""Tests for recovery strategies."""
import pytest
from dzcz_merchant_ops.core.recovery import (
    RetryWithDelayStrategy,
    LoginRecoveryStrategy,
    RecoveryManager
)
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import (
    BrowserError,
    LoginExpiredError,
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


@pytest.mark.asyncio
async def test_recovery_manager(context):
    """Test recovery manager attempts multiple strategies."""
    manager = RecoveryManager()
    error = BrowserError("test", ErrorSeverity.TRANSIENT, retryable=True)
    result = await manager.attempt_recovery(context, error)
    assert result is not None
```

---

### Task 4: 集成登录流程到 Pipeline

**Files:**
- Update: `dzcz_merchant_ops/core/pipeline.py`
- Create: `tests/integration/test_login_pipeline.py`

- [ ] **Step 1: 扩展 Pipeline 支持错误恢复**

```python
# dzcz_merchant_ops/core/pipeline.py - 添加 recovery_manager 支持
from dzcz_merchant_ops.core.recovery import RecoveryManager

class Pipeline:
    """Pipeline engine for executing workflow steps."""

    def __init__(self, steps, retry_policy=None, recovery_manager=None):
        self.steps = list(steps)
        self.retry_policy = retry_policy
        self.recovery_manager = recovery_manager or RecoveryManager()

    async def execute(self, context: Context) -> Context:
        """Execute all steps in the pipeline."""
        for step in self.steps:
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
                step.retry_policy = original_policy
        return context
```

- [ ] **Step 2: 编写集成测试**

```python
# tests/integration/test_login_pipeline.py
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
```

---

## 验证清单

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] 错误恢复机制工作正常
- [ ] 人工介入机制可用
- [ ] 文档已更新

---

## 下一步

完成 P0 后，可继续：
- P1: 真实商家后台工作流（美团/抖音）
- P1: 监控告警系统
- P2: 反爬策略优化
