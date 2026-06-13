"""Tests for structured logger."""
import pytest
import json
from pathlib import Path
from datetime import datetime
from dzcz_merchant_ops.monitor.logger import StructuredLogger, TaskLog, StepLog


def test_task_log_creation():
    """Test TaskLog creation."""
    task_log = TaskLog(
        task_id="task-123",
        profile_id="profile-456",
        workflow="test-workflow",
        start_time=datetime.now(),
        end_time=None,
        status="running",
        steps=[],
        artifacts=[],
        error=None
    )

    assert task_log.task_id == "task-123"
    assert task_log.profile_id == "profile-456"
    assert task_log.status == "running"
    assert task_log.end_time is None


def test_step_log_creation():
    """Test StepLog creation."""
    step_log = StepLog(
        step_name="test-step",
        start_time=datetime.now(),
        end_time=None,
        status="running",
        attempt=1,
        error=None,
        metrics={"key": "value"}
    )

    assert step_log.step_name == "test-step"
    assert step_log.attempt == 1
    assert step_log.metrics == {"key": "value"}


def test_structured_logger_initialization(tmp_path):
    """Test StructuredLogger initialization."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    assert logger.task_id == "task-123"
    assert logger.profile_id == "profile-456"
    assert logger.log_file == str(log_file)


def test_structured_logger_log_step_start(tmp_path):
    """Test logging step start."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_step_start("test-step")

    # Read and verify log entry
    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    assert log_entry["task_id"] == "task-123"
    assert log_entry["profile_id"] == "profile-456"
    assert log_entry["step"] == "test-step"
    assert log_entry["event"] == "step_start"


def test_structured_logger_log_step_end(tmp_path):
    """Test logging step end."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_step_end("test-step", "success")

    # Read and verify log entry
    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    assert log_entry["task_id"] == "task-123"
    assert log_entry["step"] == "test-step"
    assert log_entry["event"] == "step_end"
    assert log_entry["status"] == "success"
    assert log_entry["error"] is None


def test_structured_logger_log_step_end_with_error(tmp_path):
    """Test logging step end with error."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_step_end("test-step", "failed", "Test error message")

    # Read and verify log entry
    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    assert log_entry["status"] == "failed"
    assert log_entry["error"] == "Test error message"


def test_structured_logger_log_metrics(tmp_path):
    """Test logging metrics."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    metrics = {"duration": 1.5, "success": True}
    logger.log_metrics(metrics)

    # Read and verify log entry
    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    assert log_entry["event"] == "metrics"
    assert log_entry["metrics"] == metrics
