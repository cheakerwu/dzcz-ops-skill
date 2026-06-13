"""Execution context for workflow steps."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from copy import deepcopy


@dataclass
class Context:
    """Execution context for workflow steps.

    This context is passed through the pipeline and contains
    all the state needed for step execution.
    """
    profile_id: str
    workflow: str
    inputs: Dict[str, Any]
    state: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure inputs are deep copied for immutability."""
        self.inputs = deepcopy(self.inputs)

    def update_state(self, key: str, value: Any) -> None:
        """Update state with key-value pair."""
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from state with optional default."""
        return self.state.get(key, default)

    def add_artifact(self, artifact_path: str) -> None:
        """Add artifact path to the list."""
        self.artifacts.append(artifact_path)

    def copy(self) -> 'Context':
        """Create a deep copy of the context."""
        return Context(
            profile_id=self.profile_id,
            workflow=self.workflow,
            inputs=deepcopy(self.inputs),
            state=deepcopy(self.state),
            artifacts=self.artifacts.copy()
        )
