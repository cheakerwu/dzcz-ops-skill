"""Tests for structured logger."""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from dzcz_merchant_ops.monitor.logger import StructuredLogger, TaskLog, StepLog


def test_task_log_creation():
    """Test TaskLog creation."""
    task_log = TaskLog(
        task_id="task-123",
        profile_id="profile-456",
        workflow="test-workflow",
        start_time=datetime.now(timezone.utc),
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
        start_time=datetime.now(timezone.utc),
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
    assert "timestamp" in log_entry


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
    assert "timestamp" in log_entry


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
    assert "timestamp" in log_entry


def test_structured_logger_log_task_start(tmp_path):
    """Test logging task start."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_task_start("test-workflow")

    # Read and verify log entry
    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    assert log_entry["event"] == "task_start"
    assert log_entry["workflow"] == "test-workflow"
    assert log_entry["task_id"] == "task-123"
    assert log_entry["profile_id"] == "profile-456"
    assert "timestamp" in log_entry

    # Verify internal TaskLog state
    task_log = logger.task_log
    assert task_log is not None
    assert task_log.task_id == "task-123"
    assert task_log.workflow == "test-workflow"
    assert task_log.status == "running"
    assert task_log.end_time is None


def test_structured_logger_log_task_end(tmp_path):
    """Test logging task end."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_task_start("test-workflow")
    logger.log_task_end("success")

    # Read both log entries
    with open(log_file, 'r') as f:
        start_entry = json.loads(f.readline())
        end_entry = json.loads(f.readline())

    assert start_entry["event"] == "task_start"
    assert end_entry["event"] == "task_end"
    assert end_entry["status"] == "success"
    assert end_entry["error"] is None
    assert "timestamp" in end_entry

    # Verify internal TaskLog state
    task_log = logger.task_log
    assert task_log is not None
    assert task_log.status == "success"
    assert task_log.end_time is not None


def test_structured_logger_log_task_end_with_error(tmp_path):
    """Test logging task end with error."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_task_start("test-workflow")
    logger.log_task_end("failed", "Something went wrong")

    # Read both log entries
    with open(log_file, 'r') as f:
        f.readline()  # skip start entry
        end_entry = json.loads(f.readline())

    assert end_entry["event"] == "task_end"
    assert end_entry["status"] == "failed"
    assert end_entry["error"] == "Something went wrong"

    # Verify internal TaskLog state
    task_log = logger.task_log
    assert task_log is not None
    assert task_log.status == "failed"
    assert task_log.error == "Something went wrong"


def test_structured_logger_task_log_collects_steps(tmp_path):
    """Test that TaskLog collects step logs on task end."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_task_start("test-workflow")
    logger.log_step_start("step-1")
    logger.log_step_end("step-1", "success")
    logger.log_task_end("success")

    task_log = logger.task_log
    assert task_log is not None
    assert len(task_log.steps) == 1
    assert task_log.steps[0].step_name == "step-1"
    assert task_log.steps[0].status == "success"


def test_write_log_does_not_mutate_input(tmp_path):
    """Test that _write_log does not mutate the caller's dict."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    original = {"event": "test", "data": "value"}
    copy_before = dict(original)
    logger._write_log(original)

    # Original dict must not have been mutated
    assert original == copy_before
    assert "timestamp" not in original
    assert "task_id" not in original
    assert "profile_id" not in original


def test_write_log_io_error_falls_back_to_stderr(tmp_path, monkeypatch):
    """Test that _write_log falls back to stderr on I/O error."""
    log_file = tmp_path / "nonexistent_dir" / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    # Should not raise; error is swallowed and printed to stderr
    logger._write_log({"event": "test"})


def test_timestamp_is_iso_format_utc(tmp_path):
    """Test that timestamp field is ISO format with UTC timezone."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_task_start("test-workflow")

    with open(log_file, 'r') as f:
        log_entry = json.loads(f.readline())

    timestamp = log_entry["timestamp"]
    # Should be parseable as ISO format
    parsed = datetime.fromisoformat(timestamp)
    # Should have UTC timezone info
    assert parsed.tzinfo is not None
    assert parsed.tzinfo == timezone.utc


def test_step_logs_property_returns_copy(tmp_path):
    """Test that step_logs property returns a copy, not the internal dict."""
    log_file = tmp_path / "test.log"
    logger = StructuredLogger(
        task_id="task-123",
        profile_id="profile-456",
        log_file=str(log_file)
    )

    logger.log_step_start("step-1")
    logs = logger.step_logs
    assert "step-1" in logs

    # Mutating the returned dict should not affect internal state
    logs["step-2"] = None
    assert "step-2" not in logger.step_logs


def test_all_exports():
    """Test that __all__ contains the expected exports."""
    import dzcz_merchant_ops.monitor.logger as mod
    assert set(mod.__all__) == {"StepLog", "TaskLog", "StructuredLogger"}
