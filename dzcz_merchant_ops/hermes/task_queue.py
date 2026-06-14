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
