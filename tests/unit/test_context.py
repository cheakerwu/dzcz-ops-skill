"""Tests for execution context."""
import pytest
from dzcz_merchant_ops.core.context import Context


def test_context_creation():
    """Test Context creation with required fields."""
    context = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={"key": "value"}
    )
    assert context.profile_id == "test-profile"
    assert context.workflow == "test-workflow"
    assert context.inputs == {"key": "value"}
    assert context.state == {}
    assert context.artifacts == []
    assert context.logger is None


def test_context_state_update():
    """Test Context state update."""
    context = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={}
    )
    context.update_state("key", "value")
    assert context.get_state("key") == "value"


def test_context_state_default():
    """Test Context state default value."""
    context = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={}
    )
    assert context.get_state("nonexistent") is None
    assert context.get_state("nonexistent", "default") == "default"


def test_context_add_artifact():
    """Test adding artifact to context."""
    context = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={}
    )
    context.add_artifact("/path/to/screenshot.png")
    assert "/path/to/screenshot.png" in context.artifacts


def test_context_is_immutable_inputs():
    """Test that inputs are not shared between contexts."""
    inputs = {"key": "value"}
    context1 = Context(
        profile_id="test1",
        workflow="test",
        inputs=inputs
    )
    context2 = Context(
        profile_id="test2",
        workflow="test",
        inputs=inputs
    )
    context1.inputs["key"] = "modified"
    assert context2.inputs["key"] == "value"


def test_context_copy():
    """Test Context copy creates independent deep copy."""
    import logging

    logger = logging.getLogger("test")
    original = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={"key": "value"},
        state={"state_key": "state_value"},
        artifacts=["/path/to/artifact.png"],
        logger=logger
    )

    copied = original.copy()

    # Verify all fields are copied correctly
    assert copied.profile_id == original.profile_id
    assert copied.workflow == original.workflow
    assert copied.inputs == original.inputs
    assert copied.state == original.state
    assert copied.artifacts == original.artifacts
    assert copied.logger is original.logger

    # Verify deep copy - modifications don't affect original
    copied.inputs["new_key"] = "new_value"
    assert "new_key" not in original.inputs

    copied.state["new_state"] = "new_value"
    assert "new_state" not in original.state

    copied.artifacts.append("/new/artifact.png")
    assert len(original.artifacts) == 1


def test_with_state_returns_new_context():
    """Test with_state returns a new Context without mutating the original."""
    original = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={"key": "value"},
        state={"existing": "data"},
    )

    updated = original.with_state("new_key", "new_value")

    # Original is unchanged
    assert original.state == {"existing": "data"}
    assert "new_key" not in original.state

    # New context has both keys
    assert updated.state == {"existing": "data", "new_key": "new_value"}
    assert updated.profile_id == original.profile_id
    assert updated.workflow == original.workflow
    assert updated.inputs == original.inputs
    assert updated.artifacts == original.artifacts


def test_with_artifact_returns_new_context():
    """Test with_artifact returns a new Context without mutating the original."""
    original = Context(
        profile_id="test-profile",
        workflow="test-workflow",
        inputs={},
        artifacts=["/existing/artifact.png"],
    )

    updated = original.with_artifact("/new/artifact.png")

    # Original is unchanged
    assert original.artifacts == ["/existing/artifact.png"]

    # New context has both artifacts
    assert updated.artifacts == ["/existing/artifact.png", "/new/artifact.png"]
    assert updated.profile_id == original.profile_id
    assert updated.workflow == original.workflow
    assert updated.inputs == original.inputs
