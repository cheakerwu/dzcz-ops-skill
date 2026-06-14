"""Tests for workflow manager."""
import pytest
import json
from pathlib import Path
from dzcz_merchant_ops.workflow_schema import WorkflowStatus
from dzcz_merchant_ops.workflow_manager import WorkflowManager


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary data directory."""
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()
    return tmp_path


@pytest.fixture
def manager(tmp_data_dir):
    """Create WorkflowManager instance."""
    return WorkflowManager(tmp_data_dir)


def test_save_draft_workflow(manager, tmp_data_dir):
    """Test saving a draft workflow."""
    workflow_data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "ad_hoc",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
        "description": "Test workflow",
    }

    manager.save_draft(workflow_data)

    # Verify file exists
    workflow_file = tmp_data_dir / "workflows" / "test.workflow.json"
    assert workflow_file.exists()

    # Verify content
    with open(workflow_file) as f:
        saved = json.load(f)
    assert saved["workflow_id"] == "test.workflow"
    assert saved["status"] == "ad_hoc"


def test_load_workflow(manager, tmp_data_dir):
    """Test loading a workflow."""
    workflow_data = {
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

    # Save workflow
    workflow_file = tmp_data_dir / "workflows" / "test.workflow.json"
    with open(workflow_file, "w") as f:
        json.dump(workflow_data, f)

    # Load workflow
    loaded = manager.load_workflow("test.workflow")
    assert loaded.workflow_id == "test.workflow"
    assert loaded.status == WorkflowStatus.CANDIDATE


def test_load_nonexistent_workflow(manager):
    """Test loading a nonexistent workflow raises error."""
    with pytest.raises(FileNotFoundError):
        manager.load_workflow("nonexistent.workflow")


def test_promote_workflow(manager, tmp_data_dir):
    """Test promoting a workflow to next status."""
    workflow_data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "ad_hoc",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }

    manager.save_draft(workflow_data)

    # Promote to candidate
    manager.promote_workflow("test.workflow")

    # Verify status changed
    loaded = manager.load_workflow("test.workflow")
    assert loaded.status == WorkflowStatus.CANDIDATE


def test_promote_workflow_stable(manager, tmp_data_dir):
    """Test promoting a workflow to stable."""
    workflow_data = {
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

    manager.save_draft(workflow_data)

    # Promote to stable
    manager.promote_workflow("test.workflow")

    # Verify status changed
    loaded = manager.load_workflow("test.workflow")
    assert loaded.status == WorkflowStatus.STABLE


def test_promote_workflow_deprecated_fails(manager, tmp_data_dir):
    """Test promoting a deprecated workflow fails."""
    workflow_data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "deprecated",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }

    manager.save_draft(workflow_data)

    with pytest.raises(ValueError, match="Cannot promote"):
        manager.promote_workflow("test.workflow")


def test_list_workflows(manager, tmp_data_dir):
    """Test listing all workflows."""
    # Create multiple workflows
    for i in range(3):
        workflow_data = {
            "workflow_id": f"test.workflow{i}",
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
        manager.save_draft(workflow_data)

    workflows = manager.list_workflows()
    assert len(workflows) == 3
    assert "test.workflow0" in [w.workflow_id for w in workflows]


def test_list_workflows_by_status(manager, tmp_data_dir):
    """Test listing workflows filtered by status."""
    # Create workflows with different statuses
    statuses = ["ad_hoc", "candidate", "stable"]
    for status in statuses:
        workflow_data = {
            "workflow_id": f"test.{status}",
            "platform": "bilibili",
            "operation": "test",
            "status": status,
            "required_inputs": ["keyword"],
            "open_url": "https://example.com/{keyword}",
            "precheck": ["logged_in"],
            "actions": ["click_first"],
            "success_condition": "operation_result.confirmed == true",
            "failure_hints": ["Check login"],
        }
        manager.save_draft(workflow_data)

    # Filter by candidate
    candidates = manager.list_workflows(status=WorkflowStatus.CANDIDATE)
    assert len(candidates) == 1
    assert candidates[0].status == WorkflowStatus.CANDIDATE


def test_deprecate_workflow(manager, tmp_data_dir):
    """Test deprecating a workflow."""
    workflow_data = {
        "workflow_id": "test.workflow",
        "platform": "bilibili",
        "operation": "test",
        "status": "stable",
        "required_inputs": ["keyword"],
        "open_url": "https://example.com/{keyword}",
        "precheck": ["logged_in"],
        "actions": ["click_first"],
        "success_condition": "operation_result.confirmed == true",
        "failure_hints": ["Check login"],
    }

    manager.save_draft(workflow_data)

    # Deprecate workflow
    manager.deprecate_workflow("test.workflow")

    # Verify status changed
    loaded = manager.load_workflow("test.workflow")
    assert loaded.status == WorkflowStatus.DEPRECATED
