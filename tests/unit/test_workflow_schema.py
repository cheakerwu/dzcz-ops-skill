"""Tests for workflow schema definitions."""
import pytest
from dzcz_merchant_ops.workflow_schema import (
    WorkflowStatus,
    WorkflowSchema,
    validate_workflow_schema,
)


def test_workflow_status_enum():
    """Test WorkflowStatus enum values."""
    assert WorkflowStatus.AD_HOC.value == "ad_hoc"
    assert WorkflowStatus.CANDIDATE.value == "candidate"
    assert WorkflowStatus.STABLE.value == "stable"
    assert WorkflowStatus.DEPRECATED.value == "deprecated"


def test_workflow_schema_creation():
    """Test WorkflowSchema creation with required fields."""
    schema = WorkflowSchema(
        workflow_id="test.workflow",
        platform="bilibili",
        operation="test",
        status=WorkflowStatus.CANDIDATE,
        required_inputs=["keyword"],
        open_url="https://example.com/{keyword}",
        precheck=["logged_in"],
        actions=["click_first"],
        success_condition="operation_result.confirmed == true",
        failure_hints=["Check login"],
    )
    assert schema.workflow_id == "test.workflow"
    assert schema.platform == "bilibili"
    assert schema.status == WorkflowStatus.CANDIDATE
    assert "keyword" in schema.required_inputs


def test_workflow_schema_defaults():
    """Test WorkflowSchema default values."""
    schema = WorkflowSchema(
        workflow_id="test.workflow",
        platform="bilibili",
        operation="test",
        status=WorkflowStatus.CANDIDATE,
        required_inputs=["keyword"],
        open_url="https://example.com/{keyword}",
        precheck=["logged_in"],
        actions=["click_first"],
        success_condition="operation_result.confirmed == true",
        failure_hints=["Check login"],
    )
    assert schema.requires_ai is False
    assert schema.session_policy == "reuse_ops_session"
    assert schema.description == ""


def test_validate_workflow_schema_valid():
    """Test schema validation with valid data."""
    data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "candidate",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }
    schema = validate_workflow_schema(data)
    assert schema.workflow_id == "test.workflow"


def test_validate_workflow_schema_missing_required():
    """Test schema validation with missing required fields."""
    data = {
        "workflow_id": "test.workflow",
        # Missing platform, operation, status, etc.
    }
    with pytest.raises(ValueError, match="Missing required field"):
        validate_workflow_schema(data)


def test_validate_workflow_schema_invalid_status():
    """Test schema validation with invalid status."""
    data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "invalid_status",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }
    with pytest.raises(ValueError, match="Invalid status"):
        validate_workflow_schema(data)


def test_workflow_schema_to_dict():
    """Test WorkflowSchema serialization to dict."""
    schema = WorkflowSchema(
        workflow_id="test.workflow",
        platform="bilibili",
        operation="test",
        status=WorkflowStatus.CANDIDATE,
        required_inputs=["keyword"],
        open_url="https://example.com/{keyword}",
        precheck=["logged_in"],
        actions=["click_first"],
        success_condition="operation_result.confirmed == true",
        failure_hints=["Check login"],
    )
    data = schema.to_dict()
    assert data["workflow_id"] == "test.workflow"
    assert data["status"] == "candidate"
    assert "keyword" in data["required_inputs"]


def test_workflow_schema_from_dict():
    """Test WorkflowSchema deserialization from dict."""
    data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "candidate",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }
    schema = WorkflowSchema.from_dict(data)
    assert schema.workflow_id == "test.workflow"
    assert schema.status == WorkflowStatus.CANDIDATE
