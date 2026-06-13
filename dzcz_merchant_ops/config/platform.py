"""Platform adapters for cross-platform support."""
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path


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


class WindowsAdapter(PlatformAdapter):
    """Windows platform adapter."""

    def get_browser_path(self) -> str:
        """Get Chrome browser path on Windows."""
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    def get_profile_dir(self, profile_id: str) -> Path:
        """Get profile directory on Windows."""
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "dzcz-merchant-ops" / "profiles" / profile_id

    def get_state_dir(self) -> Path:
        """Get state directory on Windows."""
        appdata = os.environ.get("APPDATA", "")
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
