"""Platform adapters for cross-platform support."""
import os
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path

__all__ = ["PlatformAdapter", "WindowsAdapter", "MacOSAdapter", "get_platform_adapter"]


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters."""

    @abstractmethod
    def get_browser_path(self) -> str:
        """Get browser executable path."""
        pass

    @abstractmethod
    def get_profile_dir(self, profile_id: str) -> Path:
        """Get profile directory path."""
        pass

    @abstractmethod
    def get_state_dir(self) -> Path:
        """Get state directory path."""
        pass

    @abstractmethod
    def get_temp_dir(self) -> Path:
        """Get temp directory path."""
        pass


def _validate_profile_id(profile_id: str) -> None:
    """Validate profile_id contains only safe characters.

    Allowed: alphanumeric, hyphens, underscores, dots.
    Rejects path traversal attempts and special characters.

    Raises:
        ValueError: If profile_id is empty or contains unsafe characters.
    """
    if not profile_id:
        raise ValueError("profile_id must not be empty")
    if profile_id in {".", ".."} or ".." in profile_id:
        raise ValueError(
            f"profile_id contains unsafe characters/path segment: {profile_id!r}"
        )
    if not re.fullmatch(r"[A-Za-z0-9._-]+", profile_id):
        raise ValueError(
            f"profile_id contains unsafe characters: {profile_id!r}. "
            "Only alphanumeric, hyphens, underscores, and dots are allowed."
        )


def _get_appdata() -> str:
    """Get the APPDATA environment variable, raising if unset or empty.

    Raises:
        EnvironmentError: If APPDATA is not set or is empty.
    """
    value = os.environ.get("APPDATA", "")
    if not value:
        raise EnvironmentError(
            "APPDATA environment variable is not set or is empty. "
            "This is required on Windows to locate profile and state directories."
        )
    return value


class WindowsAdapter(PlatformAdapter):
    """Windows platform adapter."""

    def get_browser_path(self) -> str:
        """Get Chrome browser path on Windows."""
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    def get_profile_dir(self, profile_id: str) -> Path:
        """Get profile directory on Windows."""
        _validate_profile_id(profile_id)
        appdata = _get_appdata()
        return Path(appdata) / "dzcz-merchant-ops" / "profiles" / profile_id

    def get_state_dir(self) -> Path:
        """Get state directory on Windows."""
        appdata = _get_appdata()
        return Path(appdata) / "dzcz-merchant-ops"

    def get_temp_dir(self) -> Path:
        """Get temp directory on Windows."""
        return Path(os.environ.get("TEMP", "/tmp"))


class MacOSAdapter(PlatformAdapter):
    """macOS platform adapter."""

    def get_browser_path(self) -> str:
        """Get Chrome browser path on macOS."""
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    def get_profile_dir(self, profile_id: str) -> Path:
        """Get profile directory on macOS."""
        _validate_profile_id(profile_id)
        return Path.home() / ".dzcz-merchant-ops" / "profiles" / profile_id

    def get_state_dir(self) -> Path:
        """Get state directory on macOS."""
        return Path.home() / ".dzcz-merchant-ops"

    def get_temp_dir(self) -> Path:
        """Get temp directory on macOS."""
        return Path("/tmp")


def get_platform_adapter() -> PlatformAdapter:
    """Get platform adapter for current platform.

    Returns:
        PlatformAdapter for current platform

    Raises:
        ValueError: If platform is not supported
    """
    if os.name == 'nt':
        return WindowsAdapter()
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            return MacOSAdapter()
        else:
            raise ValueError(f"Unsupported platform: {sys.platform}")
    else:
        raise ValueError(f"Unsupported OS: {os.name}")
