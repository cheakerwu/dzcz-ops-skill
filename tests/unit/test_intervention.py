"""Tests for intervention manager."""
import pytest
import asyncio
from dzcz_merchant_ops.core.intervention import InterventionManager


@pytest.mark.asyncio
async def test_intervention_request_response():
    """Test intervention request and response flow."""
    manager = InterventionManager()
    request = manager.request_intervention(
        "login_step",
        "Please scan QR code",
        timeout_seconds=5
    )

    # Simulate response after delay
    async def provide_response():
        await asyncio.sleep(0.1)
        manager.provide_response("login_step", "scanned")

    asyncio.create_task(provide_response())
    response = await request.wait_for_response()
    assert response == "scanned"


@pytest.mark.asyncio
async def test_intervention_timeout():
    """Test intervention timeout."""
    manager = InterventionManager()
    request = manager.request_intervention(
        "login_step",
        "Please scan QR code",
        timeout_seconds=1
    )

    with pytest.raises(TimeoutError):
        await request.wait_for_response()


def test_get_pending_requests():
    """Test getting pending requests."""
    manager = InterventionManager()
    assert len(manager.get_pending_requests()) == 0

    manager.request_intervention("step1", "msg1")
    manager.request_intervention("step2", "msg2")

    pending = manager.get_pending_requests()
    assert len(pending) == 2
    assert pending[0].step_name == "step1"
    assert pending[1].step_name == "step2"


def test_provide_response_removes_request():
    """Test that providing response removes request from pending."""
    manager = InterventionManager()
    manager.request_intervention("step1", "msg1")
    assert len(manager.get_pending_requests()) == 1

    manager.provide_response("step1", "done")
    assert len(manager.get_pending_requests()) == 0
