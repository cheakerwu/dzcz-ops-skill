"""Tests for lock mechanism."""
import pytest
import asyncio
from dzcz_merchant_ops.scheduler.lock import LockManager
from dzcz_merchant_ops.core.errors import DeadlockError, LockError


@pytest.mark.asyncio
async def test_lock_manager_acquire_release():
    """Test basic lock acquire and release."""
    lock_manager = LockManager()

    acquired = await lock_manager.acquire_profile_lock("profile1", "task1")
    assert acquired is True

    lock_manager.release_profile_lock("profile1", "task1")


@pytest.mark.asyncio
async def test_lock_manager_acquire_conflict():
    """Test lock acquisition conflict."""
    lock_manager = LockManager()

    # First task acquires lock
    acquired1 = await lock_manager.acquire_profile_lock("profile1", "task1")
    assert acquired1 is True

    # Second task fails to acquire same lock
    acquired2 = await lock_manager.acquire_profile_lock("profile1", "task2")
    assert acquired2 is False

    # Release first task's lock
    lock_manager.release_profile_lock("profile1", "task1")

    # Now second task can acquire
    acquired3 = await lock_manager.acquire_profile_lock("profile1", "task2")
    assert acquired3 is True

    lock_manager.release_profile_lock("profile1", "task2")


@pytest.mark.asyncio
async def test_lock_manager_deadlock_detection():
    """Test deadlock detection."""
    lock_manager = LockManager()

    # Task acquires lock
    await lock_manager.acquire_profile_lock("profile1", "task1")

    # Same task tries to acquire same lock again - should raise DeadlockError
    with pytest.raises(DeadlockError):
        await lock_manager.acquire_profile_lock("profile1", "task1")

    # Cleanup
    lock_manager.release_profile_lock("profile1", "task1")


@pytest.mark.asyncio
async def test_lock_manager_release_wrong_owner():
    """Test releasing lock with wrong owner."""
    lock_manager = LockManager()

    # Task acquires lock
    await lock_manager.acquire_profile_lock("profile1", "task1")

    # Different task tries to release - should raise LockError
    with pytest.raises(LockError):
        lock_manager.release_profile_lock("profile1", "task2")

    # Cleanup
    lock_manager.release_profile_lock("profile1", "task1")


@pytest.mark.asyncio
async def test_lock_manager_multiple_profiles():
    """Test locking multiple profiles."""
    lock_manager = LockManager()

    # Acquire locks for different profiles
    acquired1 = await lock_manager.acquire_profile_lock("profile1", "task1")
    acquired2 = await lock_manager.acquire_profile_lock("profile2", "task1")

    assert acquired1 is True
    assert acquired2 is True

    # Release both
    lock_manager.release_profile_lock("profile1", "task1")
    lock_manager.release_profile_lock("profile2", "task1")


@pytest.mark.asyncio
async def test_lock_manager_concurrent_access():
    """Test concurrent lock access."""
    lock_manager = LockManager()
    results = []

    async def task(task_id: str, profile_id: str):
        acquired = await lock_manager.acquire_profile_lock(profile_id, task_id)
        if acquired:
            await asyncio.sleep(0.01)  # Simulate work
            lock_manager.release_profile_lock(profile_id, task_id)
            results.append(f"{task_id}_success")
        else:
            results.append(f"{task_id}_failed")

    # Run concurrent tasks on same profile
    await asyncio.gather(
        task("task1", "profile1"),
        task("task2", "profile1"),
    )

    # Exactly one should succeed and one should fail (order is not deterministic)
    successes = [r for r in results if r.endswith("_success")]
    failures = [r for r in results if r.endswith("_failed")]
    assert len(successes) == 1
    assert len(failures) == 1


@pytest.mark.asyncio
async def test_lock_manager_is_locked():
    """Test is_locked check."""
    lock_manager = LockManager()

    # Profile not locked initially
    assert lock_manager.is_locked("profile1") is False

    # Acquire lock
    await lock_manager.acquire_profile_lock("profile1", "task1")
    assert lock_manager.is_locked("profile1") is True

    # Release lock
    lock_manager.release_profile_lock("profile1", "task1")
    assert lock_manager.is_locked("profile1") is False


@pytest.mark.asyncio
async def test_lock_manager_get_lock_owner():
    """Test get_lock_owner."""
    lock_manager = LockManager()

    # No owner initially
    assert lock_manager.get_lock_owner("profile1") is None

    # Acquire lock
    await lock_manager.acquire_profile_lock("profile1", "task1")
    assert lock_manager.get_lock_owner("profile1") == "task1"

    # Release lock
    lock_manager.release_profile_lock("profile1", "task1")
    assert lock_manager.get_lock_owner("profile1") is None


@pytest.mark.asyncio
async def test_lock_manager_release_nonexistent_profile():
    """Test releasing lock for a profile that was never locked."""
    lock_manager = LockManager()

    with pytest.raises(LockError, match="No lock exists for profile"):
        lock_manager.release_profile_lock("profile1", "task1")


@pytest.mark.asyncio
async def test_lock_manager_release_cleans_up_profile_locks():
    """Test that releasing a lock removes the entry from profile_locks."""
    lock_manager = LockManager()

    await lock_manager.acquire_profile_lock("profile1", "task1")
    assert "profile1" in lock_manager.profile_locks

    lock_manager.release_profile_lock("profile1", "task1")
    assert "profile1" not in lock_manager.profile_locks
    assert lock_manager.is_locked("profile1") is False
