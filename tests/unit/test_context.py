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
