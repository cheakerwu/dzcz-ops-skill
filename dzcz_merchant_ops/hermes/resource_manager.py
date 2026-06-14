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
