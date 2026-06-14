"""Retry policy for workflow steps."""
from dataclasses import dataclass
import random

__all__ = ["RetryPolicy"]


@dataclass
class RetryPolicy:
    """Retry policy configuration.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delay
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        """Validate constructor parameters."""
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")
        if self.base_delay < 0:
            raise ValueError(f"base_delay must be non-negative, got {self.base_delay}")
        if self.max_delay <= 0:
            raise ValueError(f"max_delay must be positive, got {self.max_delay}")
        if self.exponential_base <= 0:
            raise ValueError(f"exponential_base must be positive, got {self.exponential_base}")

    def should_retry(self, attempt: int) -> bool:
        """Check whether a retry should be attempted.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            True if the attempt number is within the retry limit
        """
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds

        Raises:
            ValueError: If attempt is negative
        """
        if attempt < 0:
            raise ValueError(f"attempt must be non-negative, got {attempt}")
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay
