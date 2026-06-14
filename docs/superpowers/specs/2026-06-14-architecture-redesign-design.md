# DZCZ Merchant Ops 架构重设计

## 概述

本文档描述了 dzcz-merchant-ops 项目的架构重设计方案。目标是改进系统稳定性、增强 Hermes 集成，并为迁移到 macOS 进行真实商户测试做准备。

**关键约束**：
- Bilibili 仅用于测试验证，不是真实工作流
- 真实工作流（美团、抖音等）需要在 macOS 上进行测试
- 稳定性优先：错误处理、重试机制、并发锁、配置文件管理、日志监控

## 设计目标

1. **稳定性优先** - 确保错误处理、重试机制、锁机制可靠
2. **管道模式架构** - 任务按步骤执行，每步可重试、可跳过
3. **并发调度支持** - 支持多浏览器进程、多配置文件并发
4. **跨平台兼容** - Windows 开发，macOS 生产测试
5. **测试与生产隔离** - 明确区分测试工作流和真实工作流

## 架构设计

### 整体结构

```
dzcz-merchant-ops/
├── core/                    # 核心模块
│   ├── pipeline.py         # 管道引擎
│   ├── step.py             # 步骤基类
│   ├── context.py          # 执行上下文
│   └── errors.py           # 错误定义
├── steps/                   # 具体步骤实现
│   ├── browser.py          # 浏览器操作步骤
│   ├── profile.py          # 配置文件步骤
│   └── artifact.py         # 工件捕获步骤
├── workflows/               # 工作流定义
│   ├── test/               # 测试工作流
│   │   └── bilibili/       # Bilibili 测试工作流
│   └── production/         # 真实工作流
│       ├── meituan/        # 美团
│       └── douyin/         # 抖音
├── scheduler/               # 任务调度
│   ├── scheduler.py        # 调度器
│   ├── lock.py             # 锁机制
│   └── queue.py            # 任务队列
├── monitor/                 # 监控和日志
│   ├── logger.py           # 结构化日志
│   ├── metrics.py          # 指标收集
│   └── reporter.py         # 报告生成
├── config/                  # 配置管理
│   ├── config.py           # 配置加载
│   └── platform.py         # 平台特定配置
└── tests/                   # 测试
    ├── unit/               # 单元测试
    └── integration/        # 集成测试
```

### 管道引擎

管道引擎是系统的核心，负责执行工作流的各个步骤。

```python
class Pipeline:
    def __init__(self, steps: List[Step]):
        self.steps = steps
    
    def execute(self, context: Context) -> Result:
        """执行管道，每步可重试"""
        for step in self.steps:
            context = step.execute_with_retry(context)
        return context.result

class Step(ABC):
    @abstractmethod
    def execute(self, context: Context) -> Context:
        """执行单个步骤"""
        pass
    
    def execute_with_retry(self, context: Context) -> Context:
        """带重试的执行"""
        for attempt in range(self.max_retries):
            try:
                return self.execute(context)
            except RetryableError as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)
```

### 执行上下文

```python
@dataclass
class Context:
    profile_id: str
    workflow: str
    inputs: Dict[str, Any]
    state: Dict[str, Any]  # 步骤间共享状态
    artifacts: List[str]   # 生成的工件路径
    logger: Logger
```

## 并发调度系统

### 调度器架构

```
┌─────────────────────────────────────────────────────────┐
│                    TaskScheduler                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   TaskQueue  │  │  LockManager│  │ ProcessPool │     │
│  │  (优先级队列) │  │  (锁管理器)  │  │ (进程池)    │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────────────────────────────────────────┐   │
│  │              TaskDispatcher                      │   │
│  │  - 从队列取任务                                  │   │
│  │  - 检查锁状态                                    │   │
│  │  - 分配到空闲进程                                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 锁机制

```python
class LockManager:
    """管理全局锁和配置文件锁"""
    
    def __init__(self):
        self.global_lock = asyncio.Lock()
        self.profile_locks: Dict[str, asyncio.Lock] = {}
        self.lock_owners: Dict[str, str] = {}
    
    async def acquire_profile_lock(self, profile_id: str, task_id: str) -> bool:
        """获取配置文件锁"""
        if profile_id not in self.profile_locks:
            self.profile_locks[profile_id] = asyncio.Lock()
        
        lock = self.profile_locks[profile_id]
        if lock.locked():
            if self.lock_owners.get(profile_id) == task_id:
                raise DeadlockError(f"Task {task_id} already holds lock for {profile_id}")
            return False
        
        await lock.acquire()
        self.lock_owners[profile_id] = task_id
        return True
    
    def release_profile_lock(self, profile_id: str, task_id: str):
        """释放配置文件锁"""
        if self.lock_owners.get(profile_id) != task_id:
            raise LockError(f"Task {task_id} does not hold lock for {profile_id}")
        
        self.profile_locks[profile_id].release()
        del self.lock_owners[profile_id]
```

### 多进程调度

```python
class ProcessPool:
    """管理多个浏览器进程"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workers: Dict[str, Worker] = {}
        self.available_workers: asyncio.Queue = asyncio.Queue()
    
    async def get_worker(self) -> Worker:
        """获取空闲的 worker"""
        return await self.available_workers.get()
    
    def release_worker(self, worker: Worker):
        """释放 worker"""
        self.available_workers.put_nowait(worker)

class Worker:
    """单个浏览器进程 worker"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.current_task: Optional[str] = None
        self.current_profile: Optional[str] = None
        self.browser_process: Optional[subprocess.Popen] = None
    
    async def execute_task(self, task: Task, pipeline: Pipeline) -> Result:
        """执行任务"""
        self.current_task = task.task_id
        self.current_profile = task.profile_id
        
        try:
            self.browser_process = await self._start_browser(task.profile_id)
            context = Context(
                profile_id=task.profile_id,
                workflow=task.workflow,
                inputs=task.inputs,
                worker=self
            )
            result = await pipeline.execute(context)
            return result
        finally:
            await self._cleanup()
            self.current_task = None
            self.current_profile = None
```

## 错误处理和重试机制

### 错误分类

```python
class ErrorSeverity(Enum):
    """错误严重程度"""
    TRANSIENT = "transient"    # 瞬时错误，可重试
    PERMANENT = "permanent"    # 永久错误，不可重试
    CRITICAL = "critical"      # 严重错误，需要人工干预

class BrowserError(Exception):
    """浏览器操作错误基类"""
    def __init__(self, message: str, severity: ErrorSeverity, 
                 retryable: bool = False):
        super().__init__(message)
        self.severity = severity
        self.retryable = retryable

class LoginExpiredError(BrowserError):
    """登录过期错误"""
    def __init__(self, profile_id: str):
        super().__init__(
            f"Login expired for profile {profile_id}",
            severity=ErrorSeverity.PERMANENT,
            retryable=False
        )

class PageLoadError(BrowserError):
    """页面加载错误"""
    def __init__(self, url: str, timeout: float):
        super().__init__(
            f"Page load timeout for {url} after {timeout}s",
            severity=ErrorSeverity.TRANSIENT,
            retryable=True
        )
```

### 重试策略

```python
@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay
```

### 断路器模式

```python
class CircuitBreaker:
    """断路器，防止频繁调用失败的服务"""
    
    def __init__(self, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"
    
    async def execute(self, func, *args, **kwargs):
        """通过断路器执行函数"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise
```

## 日志和监控

### 结构化日志

```python
@dataclass
class TaskLog:
    """任务日志"""
    task_id: str
    profile_id: str
    workflow: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    steps: List[StepLog]
    artifacts: List[str]
    error: Optional[str]

@dataclass
class StepLog:
    """步骤日志"""
    step_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    attempt: int
    error: Optional[str]
    metrics: Dict[str, Any]
```

### 指标收集

```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
    
    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        """设置仪表盘值"""
        self.gauges[name] = value
    
    def record_histogram(self, name: str, value: float):
        """记录直方图值"""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            "counters": self.counters.copy(),
            "gauges": self.gauges.copy(),
            "histograms": {}
        }
        
        for name, values in self.histograms.items():
            if values:
                summary["histograms"][name] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else None
                }
        
        return summary
```

## 跨平台兼容性

### 平台抽象层

```python
class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    @abstractmethod
    def get_browser_path(self) -> str:
        """获取浏览器可执行文件路径"""
        pass
    
    @abstractmethod
    def get_profile_dir(self, profile_id: str) -> Path:
        """获取配置文件目录"""
        pass
    
    @abstractmethod
    def get_state_dir(self) -> Path:
        """获取状态目录"""
        pass
    
    @abstractmethod
    def get_temp_dir(self) -> Path:
        """获取临时目录"""
        pass

class WindowsAdapter(PlatformAdapter):
    """Windows 平台适配器"""
    
    def get_browser_path(self) -> str:
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    def get_profile_dir(self, profile_id: str) -> Path:
        return Path(os.environ.get("APPDATA")) / "dzcz-merchant-ops" / "profiles" / profile_id
    
    def get_state_dir(self) -> Path:
        return Path(os.environ.get("APPDATA")) / "dzcz-merchant-ops"
    
    def get_temp_dir(self) -> Path:
        return Path(os.environ.get("TEMP"))

class MacOSAdapter(PlatformAdapter):
    """macOS 平台适配器"""
    
    def get_browser_path(self) -> str:
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    def get_profile_dir(self, profile_id: str) -> Path:
        return Path.home() / ".dzcz-merchant-ops" / "profiles" / profile_id
    
    def get_state_dir(self) -> Path:
        return Path.home() / ".dzcz-merchant-ops"
    
    def get_temp_dir(self) -> Path:
        return Path("/tmp")
```

### 配置文件迁移

```python
class ProfileMigrator:
    """配置文件迁移器"""
    
    def __init__(self, source_adapter: PlatformAdapter, 
                 target_adapter: PlatformAdapter):
        self.source = source_adapter
        self.target = target_adapter
    
    async def migrate_profile(self, profile_id: str) -> MigrationResult:
        """迁移配置文件"""
        source_dir = self.source.get_profile_dir(profile_id)
        target_dir = self.target.get_profile_dir(profile_id)
        
        if not source_dir.exists():
            return MigrationResult(
                success=False,
                error=f"Source profile not found: {source_dir}"
            )
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            await self._copy_profile(source_dir, target_dir)
            await self._update_registry(profile_id, target_dir)
            
            return MigrationResult(
                success=True,
                source_path=str(source_dir),
                target_path=str(target_dir)
            )
        except Exception as e:
            return MigrationResult(
                success=False,
                error=str(e)
            )
```

## 工作流管理

### 工作流分类

```python
class WorkflowType(Enum):
    """工作流类型"""
    TEST = "test"          # 测试工作流 - 用于验证系统功能
    PRODUCTION = "production"  # 真实工作流 - 用于实际商户操作

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    platform: str
    workflow_type: WorkflowType
    description: str
    inputs: List[WorkflowInput]
    steps: List[str]
    
    # 测试工作流特有字段
    test_purpose: Optional[str] = None
    test_scope: Optional[str] = None
    
    # 真实工作流特有字段
    production_ready: bool = False
    validation_required: bool = True
```

### 测试工作流

```python
TEST_WORKFLOWS = {
    "bilibili.video.like": WorkflowDefinition(
        name="bilibili.video.like",
        platform="bilibili",
        workflow_type=WorkflowType.TEST,
        description="测试视频点赞功能",
        test_purpose="验证配置文件管理、浏览器操作、工件捕获",
        test_scope="系统功能验证",
        inputs=[
            WorkflowInput(name="video_url", type="string", required=True)
        ],
        steps=[
            "open_browser",
            "navigate_to_video",
            "check_login_status",
            "click_like_button",
            "take_screenshot",
            "close_browser"
        ]
    ),
    "bilibili.dm.send": WorkflowDefinition(
        name="bilibili.dm.send",
        platform="bilibili",
        workflow_type=WorkflowType.TEST,
        description="测试私信发送功能",
        test_purpose="验证表单填写、消息发送、错误处理",
        test_scope="系统功能验证",
        inputs=[
            WorkflowInput(name="dm_url", type="string", required=True),
            WorkflowInput(name="message", type="string", required=True)
        ],
        steps=[
            "open_browser",
            "navigate_to_dm",
            "check_login_status",
            "fill_message_form",
            "send_message",
            "take_screenshot",
            "close_browser"
        ]
    )
}
```

### 真实工作流（示例）

```python
PRODUCTION_WORKFLOWS = {
    "meituan.order.manage": WorkflowDefinition(
        name="meituan.order.manage",
        platform="meituan",
        workflow_type=WorkflowType.PRODUCTION,
        description="美团订单管理",
        production_ready=False,
        validation_required=True,
        inputs=[
            WorkflowInput(name="order_id", type="string", required=True),
            WorkflowInput(name="action", type="string", required=True, 
                         enum=["accept", "reject", "complete"])
        ],
        steps=[
            "open_browser",
            "navigate_to_order",
            "check_login_status",
            "perform_action",
            "take_screenshot",
            "close_browser"
        ]
    ),
    "douyin.video.publish": WorkflowDefinition(
        name="douyin.video.publish",
        platform="douyin",
        workflow_type=WorkflowType.PRODUCTION,
        description="抖音视频发布",
        production_ready=False,
        validation_required=True,
        inputs=[
            WorkflowInput(name="video_path", type="string", required=True),
            WorkflowInput(name="title", type="string", required=True),
            WorkflowInput(name="description", type="string", required=False)
        ],
        steps=[
            "open_browser",
            "navigate_to_upload",
            "check_login_status",
            "upload_video",
            "fill_video_info",
            "publish_video",
            "take_screenshot",
            "close_browser"
        ]
    )
}
```

### 工作流验证

```python
class WorkflowValidator:
    """工作流验证器"""
    
    def __init__(self, workflow_manager: WorkflowManager):
        self.workflow_manager = workflow_manager
    
    async def validate_for_production(self, workflow_name: str) -> ValidationReport:
        """验证工作流是否可以用于生产"""
        workflow = self.workflow_manager.get_workflow(workflow_name)
        
        if workflow.workflow_type == WorkflowType.TEST:
            return ValidationReport(
                success=False,
                error="Cannot validate test workflows for production"
            )
        
        # 1. 检查工作流定义是否完整
        if not self._validate_definition(workflow):
            return ValidationReport(
                success=False,
                error="Workflow definition is incomplete"
            )
        
        # 2. 运行测试工作流验证系统功能
        test_result = await self._run_test_validation(workflow.platform)
        if not test_result.success:
            return ValidationReport(
                success=False,
                error=f"Test validation failed: {test_result.error}"
            )
        
        # 3. 运行真实工作流的端到端测试
        e2e_result = await self._run_e2e_validation(workflow)
        if not e2e_result.success:
            return ValidationReport(
                success=False,
                error=f"E2E validation failed: {e2e_result.error}"
            )
        
        return ValidationReport(
            success=True,
            message="Workflow is ready for production"
        )
```

## 测试策略

### 单元测试

使用 pytest 和 pytest-asyncio 进行异步测试。

```python
import pytest
from pytest_asyncio import asyncio_mode

@pytest.mark.asyncio
async def test_pipeline_execute_success():
    """测试管道成功执行"""
    steps = [MockStep(success=True), MockStep(success=True)]
    pipeline = Pipeline(steps)
    context = Context(profile_id="test", workflow="test", inputs={})
    
    result = await pipeline.execute(context)
    
    assert result.status == "success"
    assert len(result.steps) == 2

@pytest.mark.asyncio
async def test_pipeline_execute_retry():
    """测试管道重试机制"""
    steps = [MockStep(success=False, retryable=True), MockStep(success=True)]
    pipeline = Pipeline(steps, retry_policy=RetryPolicy(max_retries=2))
    context = Context(profile_id="test", workflow="test", inputs={})
    
    result = await pipeline.execute(context)
    
    assert result.status == "success"
    assert steps[0].execution_count == 3

@pytest.mark.asyncio
async def test_acquire_release_lock():
    """测试获取和释放锁"""
    lock_manager = LockManager()
    
    acquired = await lock_manager.acquire_profile_lock("profile1", "task1")
    assert acquired is True
    
    lock_manager.release_profile_lock("profile1", "task1")

@pytest.mark.asyncio
async def test_deadlock_detection():
    """测试死锁检测"""
    lock_manager = LockManager()
    
    await lock_manager.acquire_profile_lock("profile1", "task1")
    
    with pytest.raises(DeadlockError):
        await lock_manager.acquire_profile_lock("profile1", "task1")
```

### 集成测试

```python
import pytest
from pytest_asyncio import asyncio_mode

@pytest.mark.asyncio
async def test_video_like_workflow():
    """测试视频点赞工作流"""
    profile_id = await create_test_profile()
    
    task = Task(
        workflow="bilibili.video.like",
        profile_id=profile_id,
        inputs={"video_url": "https://www.bilibili.com/video/BV..."}
    )
    
    scheduler = TaskScheduler()
    await scheduler.submit_task(task)
    
    result = await wait_for_task_completion(task.task_id)
    
    assert result.status == "success"
    assert "screenshot" in result.artifacts

@pytest.mark.asyncio
async def test_concurrent_tasks():
    """测试并发任务"""
    profiles = [await create_test_profile() for _ in range(3)]
    
    tasks = [
        Task(workflow="bilibili.video.like", profile_id=profile_id, inputs={})
        for profile_id in profiles
    ]
    
    scheduler = TaskScheduler()
    for task in tasks:
        await scheduler.submit_task(task)
    
    results = await asyncio.gather(*[
        wait_for_task_completion(task.task_id)
        for task in tasks
    ])
    
    for result in results:
        assert result.status == "success"
```

## 实施计划

### 阶段 1：核心模块重构（稳定性优先）

1. **错误处理和重试机制**
   - 定义错误分类和严重程度
   - 实现重试策略和断路器
   - 为现有代码补充错误处理

2. **锁机制优化**
   - 实现配置文件锁
   - 添加死锁检测
   - 优化锁粒度

3. **日志和监控**
   - 实现结构化日志
   - 添加指标收集
   - 实现报告生成

### 阶段 2：管道引擎实现

1. **管道引擎核心**
   - 实现 Pipeline 和 Step 基类
   - 实现执行上下文
   - 实现步骤重试机制

2. **步骤实现**
   - 实现浏览器操作步骤
   - 实现配置文件步骤
   - 实现工件捕获步骤

### 阶段 3：并发调度系统

1. **任务调度器**
   - 实现任务队列
   - 实现任务调度器
   - 实现进程池管理

2. **并发控制**
   - 实现多进程调度
   - 优化锁机制
   - 实现任务优先级

### 阶段 4：跨平台兼容

1. **平台抽象层**
   - 实现平台适配器
   - 实现配置文件迁移
   - 测试跨平台兼容性

2. **macOS 迁移**
   - 在 macOS 上测试
   - 优化平台特定问题
   - 准备真实商户测试

### 阶段 5：工作流管理

1. **工作流管理器**
   - 实现工作流定义
   - 实现工作流验证
   - 区分测试和生产工作流

2. **真实工作流实现**
   - 实现美团工作流
   - 实现抖音工作流
   - 进行生产验证

## 风险和缓解措施

### 技术风险

1. **浏览器自动化稳定性**
   - 风险：浏览器进程崩溃、页面加载超时
   - 缓解：实现断路器、重试机制、超时控制

2. **并发冲突**
   - 风险：多个任务同时操作同一配置文件
   - 缓解：实现配置文件锁、死锁检测

3. **跨平台兼容性**
   - 风险：Windows 和 macOS 行为差异
   - 缓解：平台抽象层、充分测试

### 项目风险

1. **范围蔓延**
   - 风险：需求不断扩展，项目延期
   - 缓解：明确边界，分阶段实施

2. **测试覆盖不足**
   - 风险：生产环境出现问题
   - 缓解：单元测试 + 集成测试，测试工作流验证

## 成功标准

1. **稳定性**
   - 错误处理覆盖率 > 90%
   - 重试成功率 > 80%
   - 无死锁情况

2. **性能**
   - 支持 4 个并发任务
   - 任务平均执行时间 < 5 分钟

3. **可维护性**
   - 代码覆盖率 > 80%
   - 文档完整性 > 90%

4. **跨平台**
   - Windows 和 macOS 功能一致
   - 配置文件迁移成功率 > 95%

## 附录

### 参考资料

- [agent-browser 文档](https://github.com/anthropics/agent-browser)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [设计模式：管道模式](https://en.wikipedia.org/wiki/Pipeline_(software))

### 术语表

- **管道（Pipeline）**：按顺序执行的步骤序列
- **步骤（Step）**：管道中的单个操作单元
- **配置文件（Profile）**：浏览器登录状态和配置
- **工作流（Workflow）**：定义一系列步骤的业务流程
- **工件（Artifact）**：任务执行过程中生成的文件（截图、日志等）
