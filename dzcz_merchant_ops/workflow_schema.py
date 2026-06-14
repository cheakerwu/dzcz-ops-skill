"""Workflow schema definitions for configuration-based workflows."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


__all__ = [
    "WorkflowStatus",
    "WorkflowSchema",
    "validate_workflow_schema",
]


class WorkflowStatus(Enum):
    """Workflow lifecycle status."""
    AD_HOC = "ad_hoc"          # 临时执行，未封装
    CANDIDATE = "candidate"    # 已封装但未充分验证
    STABLE = "stable"          # 多次验证通过，可默认使用
    DEPRECATED = "deprecated"  # 页面结构变化或不再使用


@dataclass
class WorkflowSchema:
    """Workflow configuration schema.

    This defines the structure for workflow definition files,
    replacing hardcoded workflow definitions.
    """
    workflow_id: str
    platform: str
    operation: str
    status: WorkflowStatus
    required_inputs: list[str]
    open_url: str
    precheck: list[str]
    actions: list[str]
    success_condition: str
    failure_hints: list[str]
    requires_ai: bool = False
    session_policy: str = "reuse_ops_session"
    description: str = ""
    executor: str = "agent_browser.deterministic"
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "platform": self.platform,
            "operation": self.operation,
            "status": self.status.value,
            "required_inputs": self.required_inputs,
            "open_url": self.open_url,
            "precheck": self.precheck,
            "actions": self.actions,
            "success_condition": self.success_condition,
            "failure_hints": self.failure_hints,
            "requires_ai": self.requires_ai,
            "session_policy": self.session_policy,
            "description": self.description,
            "executor": self.executor,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowSchema:
        """Deserialize from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            platform=data["platform"],
            operation=data["operation"],
            status=WorkflowStatus(data["status"]),
            required_inputs=data["required_inputs"],
            open_url=data["open_url"],
            precheck=data["precheck"],
            actions=data["actions"],
            success_condition=data["success_condition"],
            failure_hints=data["failure_hints"],
            requires_ai=data.get("requires_ai", False),
            session_policy=data.get("session_policy", "reuse_ops_session"),
            description=data.get("description", ""),
            executor=data.get("executor", "agent_browser.deterministic"),
            version=data.get("version", "1.0.0"),
        )


def validate_workflow_schema(data: dict[str, Any]) -> WorkflowSchema:
    """Validate and create WorkflowSchema from dictionary.

    Args:
        data: Dictionary with workflow definition

    Returns:
        Validated WorkflowSchema

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = [
        "workflow_id", "platform", "operation", "status",
        "required_inputs", "open_url", "precheck", "actions",
        "success_condition", "failure_hints",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate status
    try:
        WorkflowStatus(data["status"])
    except ValueError:
        valid_statuses = [s.value for s in WorkflowStatus]
        raise ValueError(
            f"Invalid status: {data['status']}. "
            f"Must be one of: {valid_statuses}"
        )

    # Validate workflow_id format
    workflow_id = data["workflow_id"]
    if not workflow_id or ".." in workflow_id:
        raise ValueError(f"Invalid workflow_id: {workflow_id}")

    return WorkflowSchema.from_dict(data)
