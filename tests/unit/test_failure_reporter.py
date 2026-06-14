"""Tests for failure reporter."""
import pytest
from dzcz_merchant_ops.failure_reporter import (
    FailureStage,
    FailureReport,
    create_failure_report,
)


def test_failure_stage_enum():
    """Test FailureStage enum values."""
    assert FailureStage.PRECHECK.value == "precheck"
    assert FailureStage.ACTION.value == "action"
    assert FailureStage.CONFIRM.value == "confirm"
    assert FailureStage.LOGIN.value == "login"
    assert FailureStage.BROWSER.value == "browser"


def test_failure_report_creation():
    """Test FailureReport creation."""
    report = FailureReport(
        run_id="test-123",
        workflow_id="test.workflow",
        stage=FailureStage.ACTION,
        reason="Like button not found",
        next_action="Check if page loaded correctly",
        artifact_dir="/path/to/artifacts",
        screenshot="/path/to/screenshot.png",
    )
    assert report.run_id == "test-123"
    assert report.stage == FailureStage.ACTION
    assert report.reason == "Like button not found"


def test_failure_report_to_dict():
    """Test FailureReport serialization."""
    report = FailureReport(
        run_id="test-123",
        workflow_id="test.workflow",
        stage=FailureStage.ACTION,
        reason="Like button not found",
        next_action="Check if page loaded correctly",
        artifact_dir="/path/to/artifacts",
        screenshot="/path/to/screenshot.png",
    )
    data = report.to_dict()
    assert data["run_id"] == "test-123"
    assert data["stage"] == "action"
    assert data["reason"] == "Like button not found"


def test_failure_report_to_json():
    """Test FailureReport JSON serialization."""
    report = FailureReport(
        run_id="test-123",
        workflow_id="test.workflow",
        stage=FailureStage.ACTION,
        reason="Like button not found",
        next_action="Check if page loaded correctly",
        artifact_dir="/path/to/artifacts",
        screenshot="/path/to/screenshot.png",
    )
    json_str = report.to_json()
    assert '"run_id": "test-123"' in json_str
    assert '"stage": "action"' in json_str


def test_create_failure_report():
    """Test create_failure_report helper function."""
    report = create_failure_report(
        run_id="test-123",
        workflow_id="test.workflow",
        stage=FailureStage.PRECHECK,
        reason="Not logged in",
        next_action="Open profile and log in manually",
        artifact_dir="/path/to/artifacts",
    )
    assert report.stage == FailureStage.PRECHECK
    assert report.screenshot is None


def test_failure_report_with_operation_result():
    """Test FailureReport with operation result."""
    report = FailureReport(
        run_id="test-123",
        workflow_id="test.workflow",
        stage=FailureStage.CONFIRM,
        reason="Like not confirmed",
        next_action="Check operation_result for details",
        artifact_dir="/path/to/artifacts",
        operation_result={"confirmed": False, "liked": False},
    )
    data = report.to_dict()
    assert data["operation_result"]["confirmed"] is False