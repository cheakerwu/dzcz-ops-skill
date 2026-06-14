# Workflow Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现工作流自沉淀机制、配置化定义、强化成功条件验证、增强失败报告和远程维护能力

**Architecture:** 扩展现有 cli.py 体系，新增工作流配置文件格式、draft/promote 机制、标准化失败输出、远程诊断包导出

**Tech Stack:** Python 3.10+, JSON, SQLite, argparse

---

## 文件结构映射

### 新增文件
- `dzcz_merchant_ops/workflow_schema.py` - 工作流配置文件 schema 定义
- `dzcz_merchant_ops/workflow_manager.py` - 工作流管理器（draft/promote/load）
- `dzcz_merchant_ops/failure_reporter.py` - 标准化失败报告
- `dzcz_merchant_ops/diagnostics.py` - 远程诊断包导出
- `tests/unit/test_workflow_schema.py` - 工作流 schema 测试
- `tests/unit/test_workflow_manager.py` - 工作流管理器测试
- `tests/unit/test_failure_reporter.py` - 失败报告测试
- `tests/unit/test_diagnostics.py` - 诊断包测试

### 修改文件
- `dzcz_merchant_ops/cli.py` - 集成新模块，新增命令
- `skills/hermes/dzcz-merchant-ops/SKILL.md` - 更新 Hermes 行为规则

---

## 实施任务

### Task 1: 工作流配置文件 Schema

**Files:**
- Create: `dzcz_merchant_ops/workflow_schema.py`
- Create: `tests/unit/test_workflow_schema.py`

- [ ] **Step 1: 编写工作流 schema 测试**

```python
# tests/unit/test_workflow_schema.py
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_workflow_schema.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.workflow_schema'"

- [ ] **Step 3: 编写工作流 schema 实现**

```python
# dzcz_merchant_ops/workflow_schema.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_workflow_schema.py -v
```

Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/workflow_schema.py tests/unit/test_workflow_schema.py
git commit -m "feat: add workflow schema definitions"
```

---

### Task 2: 工作流管理器（draft/promote）

**Files:**
- Create: `dzcz_merchant_ops/workflow_manager.py`
- Create: `tests/unit/test_workflow_manager.py`

- [ ] **Step 1: 编写工作流管理器测试**

```python
# tests/unit/test_workflow_manager.py
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
    return tmp_data_dir


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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_workflow_manager.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.workflow_manager'"

- [ ] **Step 3: 编写工作流管理器实现**

```python
# dzcz_merchant_ops/workflow_manager.py
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
        """Save a workflow as draft (ad_hoc status).

        Args:
            workflow_data: Workflow definition dictionary

        Returns:
            Saved WorkflowSchema
        """
        # Validate schema
        schema = validate_workflow_schema(workflow_data)

        # Force ad_hoc status for drafts
        schema.status = WorkflowStatus.AD_HOC

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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_workflow_manager.py -v
```

Expected: 10 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/workflow_manager.py tests/unit/test_workflow_manager.py
git commit -m "feat: add workflow manager with draft/promote lifecycle"
```

---

### Task 3: 标准化失败报告

**Files:**
- Create: `dzcz_merchant_ops/failure_reporter.py`
- Create: `tests/unit/test_failure_reporter.py`

- [ ] **Step 1: 编写失败报告测试**

```python
# tests/unit/test_failure_reporter.py
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
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_failure_reporter.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.failure_reporter'"

- [ ] **Step 3: 编写失败报告实现**

```python
# dzcz_merchant_ops/failure_reporter.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_failure_reporter.py -v
```

Expected: 7 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/failure_reporter.py tests/unit/test_failure_reporter.py
git commit -m "feat: add standardized failure reporting"
```

---

### Task 4: 远程诊断包导出

**Files:**
- Create: `dzcz_merchant_ops/diagnostics.py`
- Create: `tests/unit/test_diagnostics.py`

- [ ] **Step 1: 编写诊断包测试**

```python
# tests/unit/test_diagnostics.py
"""Tests for diagnostics export."""
import pytest
import json
from pathlib import Path
from dzcz_merchant_ops.diagnostics import DiagnosticsExporter


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary data directory with test data."""
    # Create artifact directory
    artifacts_dir = tmp_path / "artifacts" / "test-run-123"
    artifacts_dir.mkdir(parents=True)

    # Create test files
    (artifacts_dir / "final.png").write_bytes(b"fake-png")
    (artifacts_dir / "result.json").write_text(json.dumps({
        "ok": True,
        "confirmed": True,
    }))
    (artifacts_dir / "error.txt").write_text("Test error")

    # Create run record
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "test-run-123.json").write_text(json.dumps({
        "run_id": "test-run-123",
        "workflow_id": "test.workflow",
        "status": "failed",
    }))

    return tmp_data_dir


@pytest.fixture
def exporter(tmp_data_dir):
    """Create DiagnosticsExporter instance."""
    return DiagnosticsExporter(tmp_data_dir)


def test_export_diagnostics(exporter, tmp_data_dir):
    """Test exporting diagnostics package."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    exporter.export("test-run-123", export_path)

    # Verify export files exist
    assert (export_path / "run_info.json").exists()
    assert (export_path / "artifacts").exists()
    assert (export_path / "artifacts" / "final.png").exists()
    assert (export_path / "artifacts" / "result.json").exists()


def test_export_diagnostics_with_summary(exporter, tmp_data_dir):
    """Test export includes summary."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    exporter.export("test-run-123", export_path)

    # Verify summary
    summary_path = export_path / "summary.json"
    assert summary_path.exists()

    with open(summary_path) as f:
        summary = json.load(f)

    assert summary["run_id"] == "test-run-123"
    assert "exported_files" in summary


def test_export_nonexistent_run(exporter, tmp_data_dir):
    """Test exporting nonexistent run raises error."""
    export_path = tmp_data_dir / "export"
    export_path.mkdir()

    with pytest.raises(FileNotFoundError):
        exporter.export("nonexistent-run", export_path)


def test_list_runs(exporter, tmp_data_dir):
    """Test listing available runs."""
    runs = exporter.list_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "test-run-123"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_diagnostics.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'dzcz_merchant_ops.diagnostics'"

- [ ] **Step 3: 编写诊断包实现**

```python
# dzcz_merchant_ops/diagnostics.py
"""Remote diagnostics export for troubleshooting."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


__all__ = ["DiagnosticsExporter"]


class DiagnosticsExporter:
    """Export diagnostic packages for remote troubleshooting."""

    def __init__(self, data_dir: Path):
        """Initialize diagnostics exporter.

        Args:
            data_dir: Base data directory
        """
        self.data_dir = Path(data_dir)
        self.artifacts_dir = self.data_dir / "artifacts"
        self.runs_dir = self.data_dir / "runs"

    def list_runs(self) -> list[dict[str, Any]]:
        """List all available runs.

        Returns:
            List of run summaries
        """
        runs = []
        for run_file in self.runs_dir.glob("*.json"):
            try:
                with open(run_file, encoding="utf-8") as f:
                    data = json.load(f)
                runs.append({
                    "run_id": data.get("run_id", run_file.stem),
                    "workflow_id": data.get("workflow_id"),
                    "status": data.get("status"),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return runs

    def export(self, run_id: str, export_path: Path) -> Path:
        """Export diagnostics for a run.

        Args:
            run_id: Run identifier
            export_path: Directory to export to

        Returns:
            Path to export directory

        Raises:
            FileNotFoundError: If run not found
        """
        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)

        # Load run info
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")

        with open(run_file, encoding="utf-8") as f:
            run_info = json.load(f)

        # Copy run info
        with open(export_path / "run_info.json", "w", encoding="utf-8") as f:
            json.dump(run_info, f, indent=2, ensure_ascii=False)

        # Copy artifacts
        run_artifacts = self.artifacts_dir / run_id
        if run_artifacts.exists():
            dest_artifacts = export_path / "artifacts"
            shutil.copytree(run_artifacts, dest_artifacts, dirs_exist_ok=True)

        # Create summary
        exported_files = list(export_path.rglob("*"))
        summary = {
            "run_id": run_id,
            "workflow_id": run_info.get("workflow_id"),
            "status": run_info.get("status"),
            "exported_files": [str(f.relative_to(export_path)) for f in exported_files if f.is_file()],
        }

        with open(export_path / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return export_path
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_diagnostics.py -v
```

Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add dzcz_merchant_ops/diagnostics.py tests/unit/test_diagnostics.py
git commit -m "feat: add remote diagnostics export"
```

---

### Task 5: 集成到 CLI

**Files:**
- Modify: `dzcz_merchant_ops/cli.py`

- [ ] **Step 1: 添加新命令到 CLI**

在 `cli.py` 的 `build_parser` 函数中添加新命令：

```python
# workflow save 命令
workflow_save_parser = workflow_sub.add_parser(
    "save",
    help="Save a workflow definition from JSON file",
)
workflow_save_parser.add_argument(
    "workflow_file",
    help="Path to workflow JSON file",
)

# workflow promote 命令
workflow_promote_parser = workflow_sub.add_parser(
    "promote",
    help="Promote a workflow to next status",
)
workflow_promote_parser.add_argument(
    "workflow_id",
    help="Workflow ID to promote",
)

# workflow deprecate 命令
workflow_deprecate_parser = workflow_sub.add_parser(
    "deprecate",
    help="Deprecate a workflow",
)
workflow_deprecate_parser.add_argument(
    "workflow_id",
    help="Workflow ID to deprecate",
)

# task export 命令
task_export_parser = task_sub.add_parser(
    "export",
    help="Export diagnostics for a run",
)
task_export_parser.add_argument(
    "--run-id",
    required=True,
    help="Run ID to export",
)
task_export_parser.add_argument(
    "--output",
    required=True,
    help="Output directory",
)
```

- [ ] **Step 2: 实现命令处理函数**

```python
def command_workflow_save(args: argparse.Namespace) -> dict[str, Any]:
    """Save a workflow from JSON file."""
    from dzcz_merchant_ops.workflow_manager import WorkflowManager

    data_dir = Path(args.data_dir).expanduser()
    manager = WorkflowManager(data_dir)

    workflow_file = Path(args.workflow_file)
    if not workflow_file.exists():
        raise UserFacingError(f"Workflow file not found: {workflow_file}")

    with open(workflow_file, encoding="utf-8") as f:
        workflow_data = json.load(f)

    schema = manager.save_draft(workflow_data)

    return {
        "status": "ok",
        "workflow_id": schema.workflow_id,
        "status": schema.status.value,
        "message": f"Workflow saved as draft: {schema.workflow_id}",
    }


def command_workflow_promote(args: argparse.Namespace) -> dict[str, Any]:
    """Promote a workflow to next status."""
    from dzcz_merchant_ops.workflow_manager import WorkflowManager

    data_dir = Path(args.data_dir).expanduser()
    manager = WorkflowManager(data_dir)

    try:
        schema = manager.promote_workflow(args.workflow_id)
    except FileNotFoundError:
        raise UserFacingError(f"Workflow not found: {args.workflow_id}")
    except ValueError as e:
        raise UserFacingError(str(e))

    return {
        "status": "ok",
        "workflow_id": schema.workflow_id,
        "new_status": schema.status.value,
        "message": f"Workflow promoted to: {schema.status.value}",
    }


def command_workflow_deprecate(args: argparse.Namespace) -> dict[str, Any]:
    """Deprecate a workflow."""
    from dzcz_merchant_ops.workflow_manager import WorkflowManager

    data_dir = Path(args.data_dir).expanduser()
    manager = WorkflowManager(data_dir)

    try:
        schema = manager.deprecate_workflow(args.workflow_id)
    except FileNotFoundError:
        raise UserFacingError(f"Workflow not found: {args.workflow_id}")

    return {
        "status": "ok",
        "workflow_id": schema.workflow_id,
        "message": f"Workflow deprecated: {args.workflow_id}",
    }


def command_task_export(args: argparse.Namespace) -> dict[str, Any]:
    """Export diagnostics for a run."""
    from dzcz_merchant_ops.diagnostics import DiagnosticsExporter

    data_dir = Path(args.data_dir).expanduser()
    exporter = DiagnosticsExporter(data_dir)

    export_path = Path(args.output)

    try:
        exporter.export(args.run_id, export_path)
    except FileNotFoundError:
        raise UserFacingError(f"Run not found: {args.run_id}")

    return {
        "status": "ok",
        "run_id": args.run_id,
        "export_path": str(export_path),
        "message": f"Diagnostics exported to: {export_path}",
    }
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 4: 提交**

```bash
git add dzcz_merchant_ops/cli.py
git commit -m "feat: integrate workflow management and diagnostics into CLI"
```

---

### Task 6: 更新 Hermes Skill 文档

**Files:**
- Modify: `skills/hermes/dzcz-merchant-ops/SKILL.md`

- [ ] **Step 1: 更新 Hermes 行为规则**

在 SKILL.md 中添加新的行为规则：

```markdown
## Hermes Behavior Rules

### Workflow Discovery

1. **优先查 workflow show** - 如果用户请求的操作有现成工作流，直接使用
2. **没有 workflow 才探索** - 如果没有现成工作流，使用探索执行
3. **探索成功后询问是否封装** - 执行成功后，询问用户是否保存为 draft workflow
4. **stable workflow 默认可执行** - stable 状态的工作流可以直接执行
5. **candidate workflow 执行前说明风险** - candidate 状态的工作流需要告知用户风险

### Workflow Lifecycle

- **ad_hoc**: 临时执行，未封装
- **candidate**: 已封装但未充分验证
- **stable**: 多次验证通过，可默认使用
- **deprecated**: 页面结构变化或不再使用

### Failure Handling

当工作流失败时，Hermes 应该：
1. 获取 failure_report（包含 stage、reason、next_action）
2. 根据 stage 给出具体建议：
   - **precheck**: 检查登录状态、页面加载
   - **action**: 检查元素选择器、页面结构
   - **confirm**: 检查操作是否真正生效
   - **login**: 引导用户重新登录
   - **browser**: 检查浏览器状态
3. 提供 artifact_dir 路径，让用户查看截图和日志
```

- [ ] **Step 2: 提交**

```bash
git add skills/hermes/dzcz-merchant-ops/SKILL.md
git commit -m "docs: update Hermes behavior rules for workflow lifecycle"
```

---

## 验证清单

- [ ] 所有单元测试通过
- [ ] 工作流 schema 验证正常
- [ ] 工作流管理器 draft/promote 功能正常
- [ ] 失败报告格式正确
- [ ] 诊断包导出功能正常
- [ ] CLI 新命令可用
- [ ] 文档已更新

---

## 执行选项

**计划已保存到 `docs/superpowers/plans/2026-06-14-workflow-optimization.md`**

两种执行方式：

1. **Subagent-Driven（推荐）** - 每个任务分派独立子代理，任务间审查，快速迭代

2. **Inline Execution** - 在当前会话中执行任务，批量执行带检查点

选择哪种方式？
