"""Standardized failure reporting for workflows."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


__all__ = [
    "FailureStage",
    "FailureReport",
    "create_failure_report",
]


class FailureStage(Enum):
    """Stage where failure occurred."""
    PRECHECK = "precheck"    # Pre-execution checks (login, page load)
    ACTION = "action"        # During action execution
    CONFIRM = "confirm"      # Post-action confirmation
    LOGIN = "login"          # Login-related failures
    BROWSER = "browser"      # Browser/infrastructure failures


@dataclass
class FailureReport:
    """Standardized failure report.

    Provides structured failure information for Hermes
    to give actionable guidance to operators.
    """
    run_id: str
    workflow_id: str
    stage: FailureStage
    reason: str
    next_action: str
    artifact_dir: str
    screenshot: Optional[str] = None
    operation_result: Optional[dict[str, Any]] = None
    error_details: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "stage": self.stage.value,
            "reason": self.reason,
            "next_action": self.next_action,
            "artifact_dir": self.artifact_dir,
        }

        if self.screenshot:
            data["screenshot"] = self.screenshot

        if self.operation_result:
            data["operation_result"] = self.operation_result

        if self.error_details:
            data["error_details"] = self.error_details

        return data

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


def create_failure_report(
    run_id: str,
    workflow_id: str,
    stage: FailureStage,
    reason: str,
    next_action: str,
    artifact_dir: str,
    screenshot: Optional[str] = None,
    operation_result: Optional[dict[str, Any]] = None,
    error_details: Optional[str] = None,
) -> FailureReport:
    """Create a failure report.

    Args:
        run_id: Task run identifier
        workflow_id: Workflow identifier
        stage: Where the failure occurred
        reason: Human-readable failure reason
        next_action: Suggested next action for operator
        artifact_dir: Path to artifact directory
        screenshot: Optional path to screenshot
        operation_result: Optional operation result data
        error_details: Optional detailed error information

    Returns:
        FailureReport instance
    """
    return FailureReport(
        run_id=run_id,
        workflow_id=workflow_id,
        stage=stage,
        reason=reason,
        next_action=next_action,
        artifact_dir=artifact_dir,
        screenshot=screenshot,
        operation_result=operation_result,
        error_details=error_details,
    )
