"""Workflow manager for draft/promote lifecycle."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from dzcz_merchant_ops.workflow_schema import (
    WorkflowSchema,
    WorkflowStatus,
    validate_workflow_schema,
)


__all__ = ["WorkflowManager"]


# Status transition map
STATUS_TRANSITIONS = {
    WorkflowStatus.AD_HOC: WorkflowStatus.CANDIDATE,
    WorkflowStatus.CANDIDATE: WorkflowStatus.STABLE,
    WorkflowStatus.STABLE: WorkflowStatus.DEPRECATED,
    WorkflowStatus.DEPRECATED: None,  # Cannot promote further
}


class WorkflowManager:
    """Manage workflow lifecycle: draft, promote, load, list."""

    def __init__(self, data_dir: Path):
        """Initialize workflow manager.

        Args:
            data_dir: Base data directory (e.g., ~/.dzcz-merchant-ops/)
        """
        self.data_dir = Path(data_dir)
        self.workflows_dir = self.data_dir / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def _get_workflow_path(self, workflow_id: str) -> Path:
        """Get path to workflow file."""
        return self.workflows_dir / f"{workflow_id}.json"

    def save_draft(self, workflow_data: dict[str, Any]) -> WorkflowSchema:
        """Save a workflow as draft.

        Args:
            workflow_data: Workflow definition dictionary

        Returns:
            Saved WorkflowSchema
        """
        # Validate schema
        schema = validate_workflow_schema(workflow_data)

        # Save to file
        workflow_path = self._get_workflow_path(schema.workflow_id)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(schema.to_dict(), f, indent=2, ensure_ascii=False)

        return schema

    def load_workflow(self, workflow_id: str) -> WorkflowSchema:
        """Load a workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowSchema

        Raises:
            FileNotFoundError: If workflow not found
        """
        workflow_path = self._get_workflow_path(workflow_id)
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_id}")

        with open(workflow_path, encoding="utf-8") as f:
            data = json.load(f)

        return WorkflowSchema.from_dict(data)

    def promote_workflow(self, workflow_id: str) -> WorkflowSchema:
        """Promote a workflow to next status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Updated WorkflowSchema

        Raises:
            ValueError: If workflow cannot be promoted
        """
        schema = self.load_workflow(workflow_id)

        # Check if promotion is possible
        next_status = STATUS_TRANSITIONS.get(schema.status)
        if next_status is None:
            raise ValueError(
                f"Cannot promote workflow with status: {schema.status.value}"
            )

        # Update status
        schema.status = next_status

        # Save updated workflow
        workflow_path = self._get_workflow_path(workflow_id)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(schema.to_dict(), f, indent=2, ensure_ascii=False)

        return schema

    def deprecate_workflow(self, workflow_id: str) -> WorkflowSchema:
        """Deprecate a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Updated WorkflowSchema
        """
        schema = self.load_workflow(workflow_id)
        schema.status = WorkflowStatus.DEPRECATED

        # Save updated workflow
        workflow_path = self._get_workflow_path(workflow_id)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(schema.to_dict(), f, indent=2, ensure_ascii=False)

        return schema

    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None
    ) -> list[WorkflowSchema]:
        """List all workflows, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of WorkflowSchema
        """
        workflows = []
        for workflow_file in self.workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, encoding="utf-8") as f:
                    data = json.load(f)
                schema = WorkflowSchema.from_dict(data)

                # Apply status filter
                if status is None or schema.status == status:
                    workflows.append(schema)
            except (json.JSONDecodeError, ValueError):
                # Skip invalid workflow files
                continue

        return workflows

    def workflow_exists(self, workflow_id: str) -> bool:
        """Check if a workflow exists.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if workflow exists
        """
        return self._get_workflow_path(workflow_id).exists()
