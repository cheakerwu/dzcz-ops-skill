"""Tests for retry policy."""
import pytest
from dzcz_merchant_ops.core.retry import RetryPolicy


def test_get_delay_negative_attempt_raises():
    """Test that get_delay raises ValueError for negative attempt."""
    policy = RetryPolicy()
    with pytest.raises(ValueError, match="attempt must be non-negative"):
        policy.get_delay(-1)


def test_should_retry_within_limit():
    """Test should_retry returns True when attempt is within limit."""
    policy = RetryPolicy(max_retries=3)
    assert policy.should_retry(0) is True
    assert policy.should_retry(1) is True
    assert policy.should_retry(2) is True


def test_should_retry_at_limit():
    """Test should_retry returns False when attempt reaches max_retries."""
    policy = RetryPolicy(max_retries=3)
    assert policy.should_retry(3) is False


def test_should_retry_beyond_limit():
    """Test should_retry returns False when attempt exceeds max_retries."""
    policy = RetryPolicy(max_retries=3)
    assert policy.should_retry(4) is False


def test_retry_policy_defaults():
    """Test RetryPolicy default values."""
    policy = RetryPolicy()
    assert policy.max_retries == 3
    assert policy.base_delay == 1.0
    assert policy.max_delay == 30.0
    assert policy.exponential_base == 2.0
    assert policy.jitter is True


def test_retry_policy_custom_values():
    """Test RetryPolicy with custom values."""
    policy = RetryPolicy(
        max_retries=5,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=3.0,
        jitter=False
    )
    assert policy.max_retries == 5
    assert policy.base_delay == 2.0
    assert policy.max_delay == 60.0
    assert policy.exponential_base == 3.0
    assert policy.jitter is False


def test_retry_delay_calculation_without_jitter():
    """Test delay calculation without jitter."""
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=False
    )

    # Attempt 0: 1.0 * (2.0 ** 0) = 1.0
    assert policy.get_delay(0) == 1.0
    # Attempt 1: 1.0 * (2.0 ** 1) = 2.0
    assert policy.get_delay(1) == 2.0
    # Attempt 2: 1.0 * (2.0 ** 2) = 4.0
    assert policy.get_delay(2) == 4.0
    # Attempt 3: 1.0 * (2.0 ** 3) = 8.0
    assert policy.get_delay(3) == 8.0


def test_retry_delay_max_limit():
    """Test delay respects max limit."""
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=False
    )

    # Attempt 0: 1.0
    assert policy.get_delay(0) == 1.0
    # Attempt 1: 2.0
    assert policy.get_delay(1) == 2.0
    # Attempt 2: 4.0
    assert policy.get_delay(2) == 4.0
    # Attempt 3: min(8.0, 5.0) = 5.0
    assert policy.get_delay(3) == 5.0
    # Attempt 4: min(16.0, 5.0) = 5.0
    assert policy.get_delay(4) == 5.0


def test_retry_delay_with_jitter():
    """Test delay with jitter is within expected range."""
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )

    # Run multiple times to test jitter randomness
    delays = [policy.get_delay(1) for _ in range(100)]

    # Base delay for attempt 1 is 2.0
    # With jitter: 2.0 * (0.5 + random())
    # Range: 2.0 * 0.5 = 1.0 to 2.0 * 1.5 = 3.0
    assert all(1.0 <= d <= 3.0 for d in delays)
    # Verify there's meaningful variation by checking range spread
    spread = max(delays) - min(delays)
    assert spread > 0.5, f"Expected jitter variation > 0.5, got {spread}"


def test_max_retries_zero():
    """Test that max_retries=0 means no retries allowed."""
    policy = RetryPolicy(max_retries=0)
    assert policy.should_retry(0) is False
    assert policy.should_retry(1) is False


def test_base_delay_zero():
    """Test that base_delay=0 yields zero delay."""
    policy = RetryPolicy(base_delay=0.0, jitter=False)
    assert policy.get_delay(0) == 0.0
    assert policy.get_delay(1) == 0.0
    assert policy.get_delay(5) == 0.0


def test_negative_max_retries_raises():
    """Test that negative max_retries raises ValueError."""
    with pytest.raises(ValueError, match="max_retries must be non-negative"):
        RetryPolicy(max_retries=-1)


def test_negative_base_delay_raises():
    """Test that negative base_delay raises ValueError."""
    with pytest.raises(ValueError, match="base_delay must be non-negative"):
        RetryPolicy(base_delay=-1.0)


def test_zero_max_delay_raises():
    """Test that zero max_delay raises ValueError."""
    with pytest.raises(ValueError, match="max_delay must be positive"):
        RetryPolicy(max_delay=0.0)


def test_negative_max_delay_raises():
    """Test that negative max_delay raises ValueError."""
    with pytest.raises(ValueError, match="max_delay must be positive"):
        RetryPolicy(max_delay=-5.0)


def test_zero_exponential_base_raises():
    """Test that zero exponential_base raises ValueError."""
    with pytest.raises(ValueError, match="exponential_base must be positive"):
        RetryPolicy(exponential_base=0.0)


def test_negative_exponential_base_raises():
    """Test that negative exponential_base raises ValueError."""
    with pytest.raises(ValueError, match="exponential_base must be positive"):
        RetryPolicy(exponential_base=-1.0)
