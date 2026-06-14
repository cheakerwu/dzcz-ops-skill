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
