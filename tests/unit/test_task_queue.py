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
