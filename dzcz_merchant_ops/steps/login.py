"""Login detection and handling steps."""
from enum import Enum
from typing import Dict, Any
from dzcz_merchant_ops.core.step import Step
from dzcz_merchant_ops.core.context import Context
from dzcz_merchant_ops.core.errors import LoginExpiredError


class LoginMethod(Enum):
    """Supported login methods."""
    PASSWORD = "password"
    SMS = "sms"
    QR_CODE = "qr_code"
    TWO_FACTOR = "two_factor"


class LoginDetectionStep(Step):
    """Detect login status and handle login flows."""

    def __init__(self, platform: str, selectors: Dict[str, str]):
        """
        Args:
            platform: Platform name (bilibili, meituan, douyin)
            selectors: CSS selectors for login detection
        """
        super().__init__()
        self.platform = platform
        self.selectors = selectors

    @property
    def name(self) -> str:
        return f"login_detection_{self.platform}"

    async def execute(self, context: Context) -> Context:
        """Execute login detection."""
        # 1. Check if already logged in
        is_logged_in = await self._check_login_status(context)
        if is_logged_in:
            return context.with_state("login_status", "logged_in")

        # 2. Detect login method required
        login_method = await self._detect_login_method(context)

        # 3. Handle based on method
        if login_method == LoginMethod.PASSWORD:
            return await self._handle_password_login(context)
        elif login_method == LoginMethod.SMS:
            return await self._handle_sms_login(context)
        elif login_method == LoginMethod.QR_CODE:
            return await self._handle_qr_login(context)
        else:
            raise LoginExpiredError(
                f"Unsupported login method: {login_method}",
                platform=self.platform,
                requires_intervention=True
            )

    async def _check_login_status(self, context: Context) -> bool:
        """Check if user is already logged in.

        Override this method for platform-specific login detection.
        Default implementation returns False (not logged in).
        """
        return False

    async def _detect_login_method(self, context: Context) -> LoginMethod:
        """Detect which login method is required.

        Override this method for platform-specific login method detection.
        Default implementation returns PASSWORD.
        """
        return LoginMethod.PASSWORD

    async def _handle_password_login(self, context: Context) -> Context:
        """Handle password-based login."""
        # Password login requires manual intervention
        raise LoginExpiredError(
            "Password login required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )

    async def _handle_sms_login(self, context: Context) -> Context:
        """Handle SMS verification login."""
        # SMS login requires manual intervention
        raise LoginExpiredError(
            "SMS verification required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )

    async def _handle_qr_login(self, context: Context) -> Context:
        """Handle QR code login."""
        # QR code requires manual scan
        raise LoginExpiredError(
            "QR code scan required - manual intervention needed",
            platform=self.platform,
            requires_intervention=True
        )
