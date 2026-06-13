"""Lock mechanism for profile and global locks."""
import asyncio
from typing import Dict, Optional

from dzcz_merchant_ops.core.errors import DeadlockError, LockError


class LockManager:
    """Manager for profile and global locks.

    This class manages locks for profiles to prevent concurrent
    access to the same browser profile.
    """

    def __init__(self):
        """Initialize lock manager."""
        self.global_lock = asyncio.Lock()
        self.profile_locks: Dict[str, asyncio.Lock] = {}
        self.lock_owners: Dict[str, str] = {}

    async def acquire_profile_lock(self, profile_id: str, task_id: str) -> bool:
        """Acquire lock for a profile.

        Args:
            profile_id: Profile identifier
            task_id: Task identifier requesting the lock

        Returns:
            True if lock was acquired, False if already locked

        Raises:
            DeadlockError: If same task tries to acquire same lock
        """
        if profile_id not in self.profile_locks:
            self.profile_locks[profile_id] = asyncio.Lock()

        lock = self.profile_locks[profile_id]

        if lock.locked():
            # Check for deadlock (same task trying to acquire same lock)
            if self.lock_owners.get(profile_id) == task_id:
                raise DeadlockError(
                    f"Task {task_id} already holds lock for {profile_id}"
                )
            return False

        await lock.acquire()
        self.lock_owners[profile_id] = task_id
        return True

    def release_profile_lock(self, profile_id: str, task_id: str) -> None:
        """Release lock for a profile.

        Args:
            profile_id: Profile identifier
            task_id: Task identifier releasing the lock

        Raises:
            LockError: If task doesn't own the lock
        """
        if self.lock_owners.get(profile_id) != task_id:
            raise LockError(
                f"Task {task_id} does not hold lock for {profile_id}"
            )

        self.profile_locks[profile_id].release()
        del self.lock_owners[profile_id]

    def is_locked(self, profile_id: str) -> bool:
        """Check if a profile is locked.

        Args:
            profile_id: Profile identifier

        Returns:
            True if profile is locked
        """
        if profile_id not in self.profile_locks:
            return False
        return self.profile_locks[profile_id].locked()

    def get_lock_owner(self, profile_id: str) -> Optional[str]:
        """Get the task ID that owns the lock.

        Args:
            profile_id: Profile identifier

        Returns:
            Task ID that owns the lock, or None if not locked
        """
        return self.lock_owners.get(profile_id)
