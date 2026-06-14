"""Tests for resource manager."""
import pytest
from dzcz_merchant_ops.hermes.resource_manager import ResourceManager


@pytest.fixture
def manager():
    """Create ResourceManager instance."""
    return ResourceManager(max_instances=3)


def test_can_execute_when_idle(manager):
    """Test can execute when resources are idle."""
    can_run, reason = manager.can_execute("profile1")
    assert can_run is True
    assert reason == "可以执行"


def test_acquire_resource(manager):
    """Test acquiring a resource."""
    manager.acquire("profile1")
    assert manager.running_count == 1
    assert manager.is_running("profile1") is True


def test_release_resource(manager):
    """Test releasing a resource."""
    manager.acquire("profile1")
    manager.release("profile1")
    assert manager.running_count == 0
    assert manager.is_running("profile1") is False


def test_can_execute_when_full(manager):
    """Test cannot execute when resources are full."""
    # Acquire all instances
    manager.acquire("profile1")
    manager.acquire("profile2")
    manager.acquire("profile3")

    can_run, reason = manager.can_execute("profile4")
    assert can_run is False
    assert "浏览器实例已满" in reason


def test_can_execute_same_profile(manager):
    """Test cannot execute same profile concurrently."""
    manager.acquire("profile1")

    can_run, reason = manager.can_execute("profile1")
    assert can_run is False
    assert "该账号正在执行任务" in reason


def test_release_nonexistent(manager):
    """Test releasing a nonexistent resource does not raise."""
    manager.release("nonexistent")
    assert manager.running_count == 0


def test_get_running_profiles(manager):
    """Test getting running profiles."""
    manager.acquire("profile1")
    manager.acquire("profile2")

    running = manager.get_running_profiles()
    assert len(running) == 2
    assert "profile1" in running
    assert "profile2" in running
