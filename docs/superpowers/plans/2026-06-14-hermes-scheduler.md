# Hermes 智能调度系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现基于 Hermes 的智能任务调度系统，支持多平台多账号任务编排、资源管理

**Architecture:** Hermes 层负责调度和任务队列，dzcz-merchant-ops 层负责执行单个任务，通过 SQLite 持久化任务状态

**Tech Stack:** Python 3.10+, SQLite, pytest

---

## 文件结构映射

### 新增文件
- `dzcz_merchant_ops/hermes/__init__.py` - 模块初始化
- `dzcz_merchant_ops/hermes/task_queue.py` - 任务队列
- `dzcz_merchant_ops/hermes/resource_manager.py` - 资源管理器
- `dzcz_merchant_ops/hermes/scheduler.py` - 调度器
- `tests/unit/test_task_queue.py` - 任务队列测试
- `tests/unit/test_resource_manager.py` - 资源管理器测试
- `tests/unit/test_scheduler.py` - 调度器测试

### 修改文件
- `dzcz_merchant_ops/cli.py` - 集成调度器命令

---

## 实施任务

### Task 1: 任务队列

**Files:**
- Create: `dzcz_merchant_ops/hermes/__init__.py`
- Create: `dzcz_merchant_ops/hermes/task_queue.py`
- Create: `tests/unit/test_task_queue.py`

- [ ] **Step 1: 创建 hermes 模块初始化**

```python
# dzcz_merchant_ops/hermes/__init__.py
"""Hermes scheduler module."""
from dzcz_merchant_ops.hermes.task_queue import TaskQueue, TaskStatus

__all__ = ["TaskQueue", "TaskStatus"]
```

- [ ] **Step 2: 编写任务队列测试**

```python
# tests/unit/test_task_queue.py
"""Tests for task queue."""
import pytest
import json
from pathlib import Path
from dzcz_merchant_ops.hermes.task_queue import TaskQueue, TaskStatus


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary data directory."""
    return tmp_path


@pytest.fixture
def queue(tmp_data_dir):
    """Create TaskQueue instance."""
    return TaskQueue(tmp_data_dir)


def test_create_task(queue):
    """Test creating a task."""
    task_id = queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )
    assert task_id is not None
    assert len(task_id) > 0


def test_get_task(queue):
    """Test getting a task by ID."""
    task_id = queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    task = queue.get_task(task_id)
    assert task is not None
    assert task["task_id"] == task_id
    assert task["user_id"] == "user1"
    assert task["platform"] == "bilibili"
    assert task["status"] == TaskStatus.PENDING.value


def test_get_pending_tasks(queue):
    """Test getting pending tasks."""
    # Create multiple tasks
    queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test1"},
        priority=2,
    )
    queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test2"},
        priority=1,
    )

    pending = queue.get_pending_tasks()
    assert len(pending) == 2
    # Should be ordered by priority (1 = highest)
    assert pending[0]["priority"] == 1
    assert pending[1]["priority"] == 2


def test_update_task_status(queue):
    """Test updating task status."""
    task_id = queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    # Update to running
    queue.update_task_status(task_id, TaskStatus.RUNNING)
    task = queue.get_task(task_id)
    assert task["status"] == TaskStatus.RUNNING.value
    assert task["started_at"] is not None

    # Update to completed
    queue.update_task_status(task_id, TaskStatus.COMPLETED, result={"ok": True})
    task = queue.get_task(task_id)
    assert task["status"] == TaskStatus.COMPLETED.value
    assert task["completed_at"] is not None
    assert task["result"] is not None


def test_update_task_status_failed(queue):
    """Test updating task status to failed."""
    task_id = queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    queue.update_task_status(task_id, TaskStatus.FAILED, error="Login expired")
    task = queue.get_task(task_id)
    assert task["status"] == TaskStatus.FAILED.value
    assert task["error"] == "Login expired"


def test_get_user_tasks(queue):
    """Test getting tasks for a user."""
    # Create tasks for different users
    queue.create_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test1"},
        priority=1,
    )
    queue.create_task(
        user_id="user2",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test2"},
        priority=1,
    )
    queue.create_task(
        user_id="user1",
        platform="meituan",
        merchant_key="test-shop",
        workflow_id="meituan.reply",
        inputs={"review_id": "123"},
        priority=1,
    )

    user1_tasks = queue.get_user_tasks("user1")
    assert len(user1_tasks) == 2

    user2_tasks = queue.get_user_tasks("user2")
    assert len(user2_tasks) == 1


def test_get_nonexistent_task(queue):
    """Test getting a nonexistent task returns None."""
    task = queue.get_task("nonexistent-id")
    assert task is None
```

- [ ] **Step 3: 运行测试验证失败**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_task_queue.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.hermes'"

- [ ] **Step 4: 编写任务队列实现**

```python
# dzcz_merchant_ops/hermes/task_queue.py
"""Task queue for Hermes scheduler."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


__all__ = ["TaskQueue", "TaskStatus"]


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskQueue:
    """Task queue with SQLite persistence."""

    def __init__(self, data_dir: Path):
        """Initialize task queue.

        Args:
            data_dir: Base data directory
        """
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "scheduler.sqlite"
        self._init_db()

    def _connect_db(self) -> sqlite3.Connection:
        """Connect to SQLite database."""
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self) -> None:
        """Initialize database schema."""
        db = self._connect_db()
        try:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    merchant_key TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 2,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    result_json TEXT,
                    error TEXT
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status_priority
                ON tasks(status, priority)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_user_id
                ON tasks(user_id)
            """)
            db.commit()
        finally:
            db.close()

    def create_task(
        self,
        user_id: str,
        platform: str,
        merchant_key: str,
        workflow_id: str,
        inputs: dict[str, Any],
        priority: int = 2,
    ) -> str:
        """Create a new task.

        Args:
            user_id: User identifier
            platform: Platform name
            merchant_key: Merchant key
            workflow_id: Workflow identifier
            inputs: Workflow inputs
            priority: Task priority (1=high, 2=medium, 3=low)

        Returns:
            Task ID
        """
        task_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        db = self._connect_db()
        try:
            db.execute(
                """
                INSERT INTO tasks (task_id, user_id, platform, merchant_key, workflow_id, input_json, priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, user_id, platform, merchant_key, workflow_id, json.dumps(inputs, ensure_ascii=False), priority, TaskStatus.PENDING.value, now),
            )
            db.commit()
        finally:
            db.close()

        return task_id

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task dict or None if not found
        """
        db = self._connect_db()
        try:
            cursor = db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            task = dict(row)
            if task.get("input_json"):
                task["inputs"] = json.loads(task["input_json"])
            if task.get("result_json"):
                task["result"] = json.loads(task["result_json"])
            return task
        finally:
            db.close()

    def get_pending_tasks(self) -> list[dict[str, Any]]:
        """Get pending tasks ordered by priority.

        Returns:
            List of task dicts
        """
        db = self._connect_db()
        try:
            cursor = db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY priority ASC, created_at ASC",
                (TaskStatus.PENDING.value,),
            )
            tasks = []
            for row in cursor:
                task = dict(row)
                if task.get("input_json"):
                    task["inputs"] = json.loads(task["input_json"])
                tasks.append(task)
            return tasks
        finally:
            db.close()

    def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get tasks for a user.

        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of tasks to return

        Returns:
            List of task dicts
        """
        db = self._connect_db()
        try:
            if status:
                cursor = db.execute(
                    "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, status.value, limit),
                )
            else:
                cursor = db.execute(
                    "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit),
                )

            tasks = []
            for row in cursor:
                task = dict(row)
                if task.get("input_json"):
                    task["inputs"] = json.loads(task["input_json"])
                tasks.append(task)
            return tasks
        finally:
            db.close()

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status.

        Args:
            task_id: Task identifier
            status: New status
            result: Optional result data
            error: Optional error message
        """
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        db = self._connect_db()
        try:
            if status == TaskStatus.RUNNING:
                db.execute(
                    "UPDATE tasks SET status = ?, started_at = ? WHERE task_id = ?",
                    (status.value, now, task_id),
                )
            elif status == TaskStatus.COMPLETED:
                result_json = json.dumps(result, ensure_ascii=False) if result else None
                db.execute(
                    "UPDATE tasks SET status = ?, completed_at = ?, result_json = ? WHERE task_id = ?",
                    (status.value, now, result_json, task_id),
                )
            elif status == TaskStatus.FAILED:
                db.execute(
                    "UPDATE tasks SET status = ?, completed_at = ?, error = ? WHERE task_id = ?",
                    (status.value, now, error, task_id),
                )
            else:
                db.execute(
                    "UPDATE tasks SET status = ? WHERE task_id = ?",
                    (status.value, task_id),
                )
            db.commit()
        finally:
            db.close()
```

- [ ] **Step 5: 运行测试验证通过**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_task_queue.py -v
```

Expected: 7 passed

- [ ] **Step 6: 提交**

```bash
git add dzcz_merchant_ops/hermes/__init__.py dzcz_merchant_ops/hermes/task_queue.py tests/unit/test_task_queue.py
git commit -m "feat: add task queue for Hermes scheduler"
```

---

### Task 2: 资源管理器

**Files:**
- Create: `dzcz_merchant_ops/hermes/resource_manager.py`
- Create: `tests/unit/test_resource_manager.py`

- [ ] **Step 1: 编写资源管理器测试**

```python
# tests/unit/test_resource_manager.py
"""Tests for resource manager."""
import pytest
from dzcz_merchant_ops.hermes.resource_manager import ResourceManager


@pytest.fixture
def manager():
    """Create ResourceManager instance."""
    return ResourceManager(max_instances=3)


def test_can_execute_when_idle(manager):
    """Test can execute when resources are idle."""
    can_run, reason = manager.can_execute("profile1")
    assert can_run is True
    assert reason == "可以执行"


def test_acquire_resource(manager):
    """Test acquiring a resource."""
    manager.acquire("profile1")
    assert manager.running_count == 1
    assert manager.is_running("profile1") is True


def test_release_resource(manager):
    """Test releasing a resource."""
    manager.acquire("profile1")
    manager.release("profile1")
    assert manager.running_count == 0
    assert manager.is_running("profile1") is False


def test_can_execute_when_full(manager):
    """Test cannot execute when resources are full."""
    # Acquire all instances
    manager.acquire("profile1")
    manager.acquire("profile2")
    manager.acquire("profile3")

    can_run, reason = manager.can_execute("profile4")
    assert can_run is False
    assert "浏览器实例已满" in reason


def test_can_execute_same_profile(manager):
    """Test cannot execute same profile concurrently."""
    manager.acquire("profile1")

    can_run, reason = manager.can_execute("profile1")
    assert can_run is False
    assert "该账号正在执行任务" in reason


def test_release_nonexistent(manager):
    """Test releasing a nonexistent resource does not raise."""
    manager.release("nonexistent")
    assert manager.running_count == 0


def test_get_running_profiles(manager):
    """Test getting running profiles."""
    manager.acquire("profile1")
    manager.acquire("profile2")

    running = manager.get_running_profiles()
    assert len(running) == 2
    assert "profile1" in running
    assert "profile2" in running
```

- [ ] **Step 2: 运行测试验证失败**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_resource_manager.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.hermes.resource_manager'"

- [ ] **Step 3: 编写资源管理器实现**

```python
# dzcz_merchant_ops/hermes/resource_manager.py
"""Resource manager for browser instances."""
from __future__ import annotations

from typing import Optional


__all__ = ["ResourceManager"]


class ResourceManager:
    """Manage browser instance resources."""

    def __init__(self, max_instances: int = 3):
        """Initialize resource manager.

        Args:
            max_instances: Maximum number of concurrent browser instances
        """
        self.max_instances = max_instances
        self._running: set[str] = set()

    @property
    def running_count(self) -> int:
        """Get number of running instances."""
        return len(self._running)

    def is_running(self, profile_id: str) -> bool:
        """Check if a profile is running.

        Args:
            profile_id: Profile identifier

        Returns:
            True if profile is running
        """
        return profile_id in self._running

    def can_execute(self, profile_id: str) -> tuple[bool, str]:
        """Check if a task can be executed.

        Args:
            profile_id: Profile identifier

        Returns:
            Tuple of (can_execute, reason)
        """
        if self.is_running(profile_id):
            return False, "该账号正在执行任务，请等待完成"

        if self.running_count >= self.max_instances:
            return False, f"浏览器实例已满（最大 {self.max_instances}），请等待其他任务完成"

        return True, "可以执行"

    def acquire(self, profile_id: str) -> None:
        """Acquire a resource for a profile.

        Args:
            profile_id: Profile identifier
        """
        self._running.add(profile_id)

    def release(self, profile_id: str) -> None:
        """Release a resource for a profile.

        Args:
            profile_id: Profile identifier
        """
        self._running.discard(profile_id)

    def get_running_profiles(self) -> list[str]:
        """Get list of running profiles.

        Returns:
            List of profile IDs
        """
        return list(self._running)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_resource_manager.py -v
```

Expected: 7 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/hermes/resource_manager.py tests/unit/test_resource_manager.py
git commit -m "feat: add resource manager for browser instances"
```

---

### Task 3: 调度器

**Files:**
- Create: `dzcz_merchant_ops/hermes/scheduler.py`
- Create: `tests/unit/test_scheduler.py`

- [ ] **Step 1: 编写调度器测试**

```python
# tests/unit/test_scheduler.py
"""Tests for scheduler."""
import pytest
from pathlib import Path
from dzcz_merchant_ops.hermes.task_queue import TaskQueue, TaskStatus
from dzcz_merchant_ops.hermes.resource_manager import ResourceManager
from dzcz_merchant_ops.hermes.scheduler import Scheduler


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary data directory."""
    return tmp_path


@pytest.fixture
def scheduler(tmp_data_dir):
    """Create Scheduler instance."""
    queue = TaskQueue(tmp_data_dir)
    resource_manager = ResourceManager(max_instances=2)
    return Scheduler(queue, resource_manager)


def test_submit_task(scheduler):
    """Test submitting a task."""
    task_id = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )
    assert task_id is not None

    task = scheduler.get_task(task_id)
    assert task["status"] == TaskStatus.PENDING.value


def test_get_next_task(scheduler):
    """Test getting next task."""
    # Submit tasks with different priorities
    scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test1"},
        priority=2,
    )
    task_id2 = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test2"},
        priority=1,
    )

    next_task = scheduler.get_next_task()
    assert next_task is not None
    assert next_task["task_id"] == task_id2
    assert next_task["priority"] == 1


def test_get_next_task_when_empty(scheduler):
    """Test getting next task when queue is empty."""
    next_task = scheduler.get_next_task()
    assert next_task is None


def test_start_task(scheduler):
    """Test starting a task."""
    task_id = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    success = scheduler.start_task(task_id)
    assert success is True

    task = scheduler.get_task(task_id)
    assert task["status"] == TaskStatus.RUNNING.value


def test_start_task_when_resources_full(scheduler):
    """Test starting a task when resources are full."""
    # Submit and start tasks to fill resources
    task_id1 = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account1",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test1"},
        priority=1,
    )
    task_id2 = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account2",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test2"},
        priority=1,
    )
    task_id3 = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account3",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test3"},
        priority=1,
    )

    scheduler.start_task(task_id1)
    scheduler.start_task(task_id2)

    # Third task should fail to start
    success = scheduler.start_task(task_id3)
    assert success is False

    task = scheduler.get_task(task_id3)
    assert task["status"] == TaskStatus.PENDING.value


def test_complete_task(scheduler):
    """Test completing a task."""
    task_id = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    scheduler.start_task(task_id)
    scheduler.complete_task(task_id, result={"ok": True})

    task = scheduler.get_task(task_id)
    assert task["status"] == TaskStatus.COMPLETED.value
    assert task["result"] is not None


def test_fail_task(scheduler):
    """Test failing a task."""
    task_id = scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test"},
        priority=1,
    )

    scheduler.start_task(task_id)
    scheduler.fail_task(task_id, error="Login expired")

    task = scheduler.get_task(task_id)
    assert task["status"] == TaskStatus.FAILED.value
    assert task["error"] == "Login expired"

    # Resource should be released
    assert scheduler.resource_manager.running_count == 0


def test_get_user_tasks(scheduler):
    """Test getting user tasks."""
    scheduler.submit_task(
        user_id="user1",
        platform="bilibili",
        merchant_key="test-account",
        workflow_id="bilibili.video.like",
        inputs={"video_url": "https://bilibili.com/video/test1"},
        priority=1,
    )
    scheduler.submit_task(
        user_id="user1",
        platform="meituan",
        merchant_key="test-shop",
        workflow_id="meituan.reply",
        inputs={"review_id": "123"},
        priority=1,
    )

    tasks = scheduler.get_user_tasks("user1")
    assert len(tasks) == 2
```

- [ ] **Step 2: 运行测试验证失败**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_scheduler.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.hermes.scheduler'"

- [ ] **Step 3: 编写调度器实现**

```python
# dzcz_merchant_ops/hermes/scheduler.py
"""Task scheduler for Hermes."""
from __future__ import annotations

from typing import Any, Optional

from dzcz_merchant_ops.hermes.task_queue import TaskQueue, TaskStatus
from dzcz_merchant_ops.hermes.resource_manager import ResourceManager


__all__ = ["Scheduler"]


class Scheduler:
    """Task scheduler with resource management."""

    def __init__(self, queue: TaskQueue, resource_manager: ResourceManager):
        """Initialize scheduler.

        Args:
            queue: Task queue
            resource_manager: Resource manager
        """
        self.queue = queue
        self.resource_manager = resource_manager

    def submit_task(
        self,
        user_id: str,
        platform: str,
        merchant_key: str,
        workflow_id: str,
        inputs: dict[str, Any],
        priority: int = 2,
    ) -> str:
        """Submit a new task.

        Args:
            user_id: User identifier
            platform: Platform name
            merchant_key: Merchant key
            workflow_id: Workflow identifier
            inputs: Workflow inputs
            priority: Task priority (1=high, 2=medium, 3=low)

        Returns:
            Task ID
        """
        return self.queue.create_task(
            user_id=user_id,
            platform=platform,
            merchant_key=merchant_key,
            workflow_id=workflow_id,
            inputs=inputs,
            priority=priority,
        )

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task dict or None
        """
        return self.queue.get_task(task_id)

    def get_next_task(self) -> Optional[dict[str, Any]]:
        """Get the next pending task that can be executed.

        Returns:
            Task dict or None
        """
        pending_tasks = self.queue.get_pending_tasks()
        for task in pending_tasks:
            profile_id = f"{task['platform']}__{task['merchant_key']}"
            can_run, _ = self.resource_manager.can_execute(profile_id)
            if can_run:
                return task
        return None

    def start_task(self, task_id: str) -> bool:
        """Start a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was started, False if resources unavailable
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return False

        profile_id = f"{task['platform']}__{task['merchant_key']}"
        can_run, _ = self.resource_manager.can_execute(profile_id)
        if not can_run:
            return False

        self.resource_manager.acquire(profile_id)
        self.queue.update_task_status(task_id, TaskStatus.RUNNING)
        return True

    def complete_task(self, task_id: str, result: dict[str, Any]) -> None:
        """Complete a task.

        Args:
            task_id: Task identifier
            result: Task result data
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return

        profile_id = f"{task['platform']}__{task['merchant_key']}"
        self.resource_manager.release(profile_id)
        self.queue.update_task_status(task_id, TaskStatus.COMPLETED, result=result)

    def fail_task(self, task_id: str, error: str) -> None:
        """Fail a task.

        Args:
            task_id: Task identifier
            error: Error message
        """
        task = self.queue.get_task(task_id)
        if task is None:
            return

        profile_id = f"{task['platform']}__{task['merchant_key']}"
        self.resource_manager.release(profile_id)
        self.queue.update_task_status(task_id, TaskStatus.FAILED, error=error)

    def get_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get tasks for a user.

        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of tasks

        Returns:
            List of task dicts
        """
        return self.queue.get_user_tasks(user_id, status=status, limit=limit)
```

- [ ] **Step 4: 运行测试验证通过**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/unit/test_scheduler.py -v
```

Expected: 9 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/hermes/scheduler.py tests/unit/test_scheduler.py
git commit -m "feat: add task scheduler with resource management"
```

---

### Task 4: CLI 集成

**Files:**
- Modify: `dzcz_merchant_ops/cli.py`

- [ ] **Step 1: 添加调度器命令**

在 `cli.py` 的 `build_parser` 函数中添加新命令：

```python
# scheduler submit
scheduler_submit_parser = scheduler_sub.add_parser(
    "submit",
    help="Submit a task to the scheduler",
)
scheduler_submit_parser.add_argument("--user-id", required=True, help="User ID")
scheduler_submit_parser.add_argument("--platform", required=True, help="Platform name")
scheduler_submit_parser.add_argument("--merchant-key", required=True, help="Merchant key")
scheduler_submit_parser.add_argument("--workflow", required=True, help="Workflow ID")
scheduler_submit_parser.add_argument("--input", action="append", help="Input key=value")
scheduler_submit_parser.add_argument("--priority", type=int, default=2, help="Priority (1=high, 2=medium, 3=low)")

# scheduler status
scheduler_status_parser = scheduler_sub.add_parser(
    "status",
    help="Show scheduler status",
)

# scheduler tasks
scheduler_tasks_parser = scheduler_sub.add_parser(
    "tasks",
    help="List user tasks",
)
scheduler_tasks_parser.add_argument("--user-id", required=True, help="User ID")
scheduler_tasks_parser.add_argument("--status", help="Filter by status")
scheduler_tasks_parser.add_argument("--limit", type=int, default=10, help="Max tasks to show")
```

- [ ] **Step 2: 实现命令处理函数**

```python
def command_scheduler_submit(args: argparse.Namespace) -> dict[str, Any]:
    """Submit a task to the scheduler."""
    from dzcz_merchant_ops.hermes.task_queue import TaskQueue
    from dzcz_merchant_ops.hermes.resource_manager import ResourceManager
    from dzcz_merchant_ops.hermes.scheduler import Scheduler

    data_dir = Path(args.data_dir).expanduser()
    queue = TaskQueue(data_dir)
    resource_manager = ResourceManager(max_instances=3)
    scheduler = Scheduler(queue, resource_manager)

    inputs = parse_inputs(args.input, None)

    task_id = scheduler.submit_task(
        user_id=args.user_id,
        platform=args.platform,
        merchant_key=args.merchant_key,
        workflow_id=args.workflow,
        inputs=inputs,
        priority=args.priority,
    )

    return {
        "status": "ok",
        "task_id": task_id,
        "message": f"Task submitted: {task_id}",
    }


def command_scheduler_status(args: argparse.Namespace) -> dict[str, Any]:
    """Show scheduler status."""
    from dzcz_merchant_ops.hermes.task_queue import TaskQueue
    from dzcz_merchant_ops.hermes.resource_manager import ResourceManager

    data_dir = Path(args.data_dir).expanduser()
    queue = TaskQueue(data_dir)
    resource_manager = ResourceManager(max_instances=3)

    pending_tasks = queue.get_pending_tasks()

    return {
        "status": "ok",
        "pending_tasks": len(pending_tasks),
        "running_tasks": resource_manager.running_count,
        "max_instances": resource_manager.max_instances,
    }


def command_scheduler_tasks(args: argparse.Namespace) -> dict[str, Any]:
    """List user tasks."""
    from dzcz_merchant_ops.hermes.task_queue import TaskQueue, TaskStatus
    from dzcz_merchant_ops.hermes.resource_manager import ResourceManager
    from dzcz_merchant_ops.hermes.scheduler import Scheduler

    data_dir = Path(args.data_dir).expanduser()
    queue = TaskQueue(data_dir)
    resource_manager = ResourceManager(max_instances=3)
    scheduler = Scheduler(queue, resource_manager)

    status = TaskStatus(args.status) if args.status else None
    tasks = scheduler.get_user_tasks(args.user_id, status=status, limit=args.limit)

    return {
        "status": "ok",
        "tasks": tasks,
        "count": len(tasks),
    }
```

- [ ] **Step 3: 运行测试验证**

```bash
& "E:\anaconda\envs\Hermes\python.exe" -m pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 4: 提交**

```bash
git add dzcz_merchant_ops/cli.py
git commit -m "feat: integrate scheduler into CLI"
```

---

## 验证清单

- [ ] 所有单元测试通过
- [ ] 任务队列 CRUD 功能正常
- [ ] 资源管理器并发控制正常
- [ ] 调度器任务调度正常
- [ ] CLI 命令可用
- [ ] 文档已更新

---

## 执行选项

**计划已保存到 `docs/superpowers/plans/2026-06-14-hermes-scheduler.md`**

两种执行方式：

1. **Subagent-Driven（推荐）** - 每个任务分派独立子代理，任务间审查，快速迭代

2. **Inline Execution** - 在当前会话中执行任务，批量执行带检查点

**选择哪种方式？**
