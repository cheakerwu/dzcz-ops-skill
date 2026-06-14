"""Structured logging for task execution."""
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


__all__ = ["StepLog", "TaskLog", "StructuredLogger"]


@dataclass
class StepLog:
    """Log entry for a single step execution."""
    step_name: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    attempt: int
    error: Optional[str]
    metrics: Dict[str, Any]


@dataclass
class TaskLog:
    """Log entry for a complete task execution."""
    task_id: str
    profile_id: str
    workflow: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    steps: List[StepLog]
    artifacts: List[str]
    error: Optional[str]


class StructuredLogger:
    """Structured logger for task execution.

    Logs are written as JSON lines for easy parsing and analysis.
    """

    def __init__(self, task_id: str, profile_id: str, log_file: str):
        """Initialize logger.

        Args:
            task_id: Task identifier
            profile_id: Profile identifier
            log_file: Path to log file
        """
        self.task_id = task_id
        self.profile_id = profile_id
        self.log_file = log_file
        self._task_log: Optional[TaskLog] = None
        self._step_logs: Dict[str, StepLog] = {}

    def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the log file.

        Args:
            log_entry: Log entry to write (not mutated)
        """
        entry = {
            **log_entry,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": self.task_id,
            "profile_id": self.profile_id,
        }

        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except OSError:
            print(
                f"[StructuredLogger] Failed to write to {self.log_file}",
                file=sys.stderr,
            )

    def log_step_start(self, step_name: str) -> None:
        """Log step start.

        Args:
            step_name: Name of the step
        """
        now = datetime.now(timezone.utc)
        self._step_logs[step_name] = StepLog(
            step_name=step_name,
            start_time=now,
            end_time=None,
            status="running",
            attempt=1,
            error=None,
            metrics={},
        )

        log_entry = {
            "step": step_name,
            "event": "step_start"
        }
        self._write_log(log_entry)

    def log_step_end(self, step_name: str, status: str,
                     error: Optional[str] = None) -> None:
        """Log step end.

        Args:
            step_name: Name of the step
            status: Step status (success, failed)
            error: Error message if failed
        """
        now = datetime.now(timezone.utc)
        step_log = self._step_logs.get(step_name)
        if step_log is not None:
            step_log.end_time = now
            step_log.status = status
            step_log.error = error

        log_entry = {
            "step": step_name,
            "event": "step_end",
            "status": status,
            "error": error
        }
        self._write_log(log_entry)

    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics.

        Args:
            metrics: Metrics to log
        """
        log_entry = {
            "event": "metrics",
            "metrics": metrics
        }
        self._write_log(log_entry)

    def log_task_start(self, workflow: str) -> None:
        """Log task start.

        Args:
            workflow: Workflow name
        """
        now = datetime.now(timezone.utc)
        self._task_log = TaskLog(
            task_id=self.task_id,
            profile_id=self.profile_id,
            workflow=workflow,
            start_time=now,
            end_time=None,
            status="running",
            steps=[],
            artifacts=[],
            error=None,
        )

        log_entry = {
            "event": "task_start",
            "workflow": workflow
        }
        self._write_log(log_entry)

    def log_task_end(self, status: str, error: Optional[str] = None) -> None:
        """Log task end.

        Args:
            status: Task status (success, failed)
            error: Error message if failed
        """
        now = datetime.now(timezone.utc)
        if self._task_log is not None:
            self._task_log.end_time = now
            self._task_log.status = status
            self._task_log.error = error
            self._task_log.steps = list(self._step_logs.values())

        log_entry = {
            "event": "task_end",
            "status": status,
            "error": error
        }
        self._write_log(log_entry)

    @property
    def task_log(self) -> Optional[TaskLog]:
        """Return the current TaskLog, or None if task has not started."""
        return self._task_log

    @property
    def step_logs(self) -> Dict[str, StepLog]:
        """Return a copy of the current step logs."""
        return dict(self._step_logs)
