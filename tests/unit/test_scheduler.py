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
