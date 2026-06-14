"""Execution context for workflow steps."""
import logging
from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy

__all__ = ["Context"]


@dataclass
class Context:
    """Execution context for workflow steps.

    This context is passed through the pipeline and contains
    all the state needed for step execution.
    """
    profile_id: str
    workflow: str
    inputs: dict[str, Any]
    state: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        """Ensure inputs are deep copied for immutability."""
        self.inputs = deepcopy(self.inputs)

    def update_state(self, key: str, value: Any) -> None:
        """Update state with key-value pair.

        Note: This mutates in place. Prefer ``with_state`` for
        immutable pipelines.
        """
        self.state[key] = value

    def with_state(self, key: str, value: Any) -> 'Context':
        """Return a new Context with the given state key set.

        The original Context is not modified.
        """
        new_state = deepcopy(self.state)
        new_state[key] = value
        return Context(
            profile_id=self.profile_id,
            workflow=self.workflow,
            inputs=deepcopy(self.inputs),
            state=new_state,
            artifacts=self.artifacts.copy(),
            logger=self.logger,
        )

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from state with optional default."""
        return self.state.get(key, default)

    def add_artifact(self, artifact_path: str) -> None:
        """Add artifact path to the list.

        Note: This mutates in place. Prefer ``with_artifact`` for
        immutable pipelines.
        """
        self.artifacts.append(artifact_path)

    def with_artifact(self, artifact_path: str) -> 'Context':
        """Return a new Context with the artifact appended.

        The original Context is not modified.
        """
        new_artifacts = self.artifacts.copy()
        new_artifacts.append(artifact_path)
        return Context(
            profile_id=self.profile_id,
            workflow=self.workflow,
            inputs=deepcopy(self.inputs),
            state=deepcopy(self.state),
            artifacts=new_artifacts,
            logger=self.logger,
        )

    def copy(self) -> 'Context':
        """Create a deep copy of the context."""
        return Context(
            profile_id=self.profile_id,
            workflow=self.workflow,
            inputs=deepcopy(self.inputs),
            state=deepcopy(self.state),
            artifacts=self.artifacts.copy(),
            logger=self.logger,
        )
