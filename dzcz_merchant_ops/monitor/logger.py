"""Structured logging for task execution."""
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional


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

    def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """Write a log entry to the log file.

        Args:
            log_entry: Log entry to write
        """
        # Add common fields
        log_entry["timestamp"] = datetime.utcnow().isoformat()
        log_entry["task_id"] = self.task_id
        log_entry["profile_id"] = self.profile_id

        # Write as JSON line
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def log_step_start(self, step_name: str) -> None:
        """Log step start.

        Args:
            step_name: Name of the step
        """
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
        log_entry = {
            "event": "task_end",
            "status": status,
            "error": error
        }
        self._write_log(log_entry)
