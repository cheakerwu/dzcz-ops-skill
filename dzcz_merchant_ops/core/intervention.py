"""Manual intervention handling for complex scenarios."""
import asyncio
from typing import Optional, Any


class InterventionRequest:
    """Request for manual intervention."""

    def __init__(self, step_name: str, message: str,
                 timeout_seconds: int = 300):
        self.step_name = step_name
        self.message = message
        self.timeout_seconds = timeout_seconds
        self.response: Optional[Any] = None
        self.event = asyncio.Event()

    async def wait_for_response(self) -> Any:
        """Wait for manual intervention response."""
        try:
            await asyncio.wait_for(
                self.event.wait(),
                timeout=self.timeout_seconds
            )
            return self.response
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Intervention timeout after {self.timeout_seconds}s"
            )

    def provide_response(self, response: Any) -> None:
        """Provide response to intervention request."""
        self.response = response
        self.event.set()


class InterventionManager:
    """Manage manual intervention requests."""

    def __init__(self):
        self.pending_requests: dict[str, InterventionRequest] = {}

    def request_intervention(self, step_name: str, message: str,
                           timeout_seconds: int = 300) -> InterventionRequest:
        """Create intervention request."""
        request = InterventionRequest(step_name, message, timeout_seconds)
        self.pending_requests[step_name] = request
        return request

    def provide_response(self, step_name: str, response: Any) -> None:
        """Provide response to pending request."""
        if step_name in self.pending_requests:
            self.pending_requests[step_name].provide_response(response)
            del self.pending_requests[step_name]

    def get_pending_requests(self) -> list[InterventionRequest]:
        """Get list of pending intervention requests."""
        return list(self.pending_requests.values())
