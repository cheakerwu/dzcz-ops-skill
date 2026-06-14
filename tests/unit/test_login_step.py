"""Tests for login detection step."""
import pytest
from dzcz_merchant_ops.steps.login import LoginDetectionStep, LoginMethod
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import LoginExpiredError


@pytest.fixture
def context():
    return Context(
        profile_id="test_user",
        workflow="test",
        inputs={}
    )


def test_login_method_enum():
    """Test LoginMethod enum values."""
    assert LoginMethod.PASSWORD.value == "password"
    assert LoginMethod.SMS.value == "sms"
    assert LoginMethod.QR_CODE.value == "qr_code"
    assert LoginMethod.TWO_FACTOR.value == "two_factor"


def test_login_detection_step_name():
    """Test step name generation."""
    step = LoginDetectionStep(platform="bilibili", selectors={})
    assert step.name == "login_detection_bilibili"


def test_login_detection_step_name_meituan():
    """Test step name generation for meituan."""
    step = LoginDetectionStep(platform="meituan", selectors={})
    assert step.name == "login_detection_meituan"


@pytest.mark.asyncio
async def test_login_detection_requires_intervention(context):
    """Test that login detection raises error for manual intervention."""
    step = LoginDetectionStep(platform="bilibili", selectors={})
    with pytest.raises(LoginExpiredError) as exc_info:
        await step.execute(context)
    assert exc_info.value.requires_intervention is True
    assert exc_info.value.platform == "bilibili"


@pytest.mark.asyncio
async def test_login_detection_sms_method(context):
    """Test SMS login method detection."""
    class SmsLoginStep(LoginDetectionStep):
        async def _detect_login_method(self, context):
            return LoginMethod.SMS

    step = SmsLoginStep(platform="test", selectors={})
    with pytest.raises(LoginExpiredError) as exc_info:
        await step.execute(context)
    assert "SMS verification required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_login_detection_qr_method(context):
    """Test QR code login method detection."""
    class QrLoginStep(LoginDetectionStep):
        async def _detect_login_method(self, context):
            return LoginMethod.QR_CODE

    step = QrLoginStep(platform="test", selectors={})
    with pytest.raises(LoginExpiredError) as exc_info:
        await step.execute(context)
    assert "QR code scan required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_login_detection_already_logged_in(context):
    """Test that logged in status returns context without error."""
    class LoggedInStep(LoginDetectionStep):
        async def _check_login_status(self, context):
            return True

    step = LoggedInStep(platform="test", selectors={})
    result = await step.execute(context)
    assert result.state.get("login_status") == "logged_in"
