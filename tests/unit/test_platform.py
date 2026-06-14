"""Tests for platform adapters."""
import pytest
import os
from pathlib import Path
from dzcz_merchant_ops.config.platform import (
    PlatformAdapter,
    WindowsAdapter,
    MacOSAdapter,
    get_platform_adapter,
    _validate_profile_id,
)


def test_platform_adapter_abstract():
    """Test PlatformAdapter is abstract."""
    with pytest.raises(TypeError):
        PlatformAdapter()


def test_windows_adapter_browser_path():
    """Test WindowsAdapter browser path."""
    adapter = WindowsAdapter()
    browser_path = adapter.get_browser_path()
    assert "chrome.exe" in browser_path.lower()


def test_windows_adapter_profile_dir():
    """Test WindowsAdapter profile directory."""
    adapter = WindowsAdapter()
    profile_dir = adapter.get_profile_dir("test-profile")
    assert "test-profile" in str(profile_dir)
    assert "dzcz-merchant-ops" in str(profile_dir)


def test_windows_adapter_state_dir():
    """Test WindowsAdapter state directory."""
    adapter = WindowsAdapter()
    state_dir = adapter.get_state_dir()
    assert "dzcz-merchant-ops" in str(state_dir)


def test_windows_adapter_temp_dir():
    """Test WindowsAdapter temp directory."""
    adapter = WindowsAdapter()
    temp_dir = adapter.get_temp_dir()
    assert temp_dir.exists()


def test_macos_adapter_browser_path():
    """Test MacOSAdapter browser path."""
    adapter = MacOSAdapter()
    browser_path = adapter.get_browser_path()
    assert "Google Chrome" in browser_path
    assert "MacOS" in browser_path


def test_macos_adapter_profile_dir():
    """Test MacOSAdapter profile directory."""
    adapter = MacOSAdapter()
    profile_dir = adapter.get_profile_dir("test-profile")
    assert "test-profile" in str(profile_dir)
    assert ".dzcz-merchant-ops" in str(profile_dir)


def test_macos_adapter_state_dir():
    """Test MacOSAdapter state directory."""
    adapter = MacOSAdapter()
    state_dir = adapter.get_state_dir()
    assert ".dzcz-merchant-ops" in str(state_dir)


def test_macos_adapter_temp_dir():
    """Test MacOSAdapter temp directory."""
    adapter = MacOSAdapter()
    temp_dir = adapter.get_temp_dir()
    # Path("/tmp") normalizes differently on Windows vs Unix
    assert temp_dir == Path("/tmp")


def test_get_platform_adapter_windows(monkeypatch):
    """Test get_platform_adapter for Windows."""
    monkeypatch.setattr(os, 'name', 'nt')
    adapter = get_platform_adapter()
    assert isinstance(adapter, WindowsAdapter)


def test_get_platform_adapter_macos(monkeypatch):
    """Test get_platform_adapter for macOS."""
    monkeypatch.setattr(os, 'name', 'posix')
    monkeypatch.setattr('sys.platform', 'darwin')
    adapter = get_platform_adapter()
    assert isinstance(adapter, MacOSAdapter)


def test_get_platform_adapter_unsupported(monkeypatch):
    """Test get_platform_adapter for unsupported platform."""
    monkeypatch.setattr(os, 'name', 'posix')
    monkeypatch.setattr('sys.platform', 'linux')
    with pytest.raises(ValueError):
        get_platform_adapter()


# --- APPDATA environment variable tests ---

def test_windows_profile_dir_appdata_not_set(monkeypatch):
    """Test WindowsAdapter raises EnvironmentError when APPDATA is not set."""
    monkeypatch.delenv("APPDATA", raising=False)
    adapter = WindowsAdapter()
    with pytest.raises(EnvironmentError, match="APPDATA"):
        adapter.get_profile_dir("test-profile")


def test_windows_state_dir_appdata_not_set(monkeypatch):
    """Test WindowsAdapter raises EnvironmentError when APPDATA is not set."""
    monkeypatch.delenv("APPDATA", raising=False)
    adapter = WindowsAdapter()
    with pytest.raises(EnvironmentError, match="APPDATA"):
        adapter.get_state_dir()


def test_windows_profile_dir_appdata_empty(monkeypatch):
    """Test WindowsAdapter raises EnvironmentError when APPDATA is empty string."""
    monkeypatch.setenv("APPDATA", "")
    adapter = WindowsAdapter()
    with pytest.raises(EnvironmentError, match="APPDATA"):
        adapter.get_profile_dir("test-profile")


def test_windows_state_dir_appdata_empty(monkeypatch):
    """Test WindowsAdapter raises EnvironmentError when APPDATA is empty string."""
    monkeypatch.setenv("APPDATA", "")
    adapter = WindowsAdapter()
    with pytest.raises(EnvironmentError, match="APPDATA"):
        adapter.get_state_dir()


# --- profile_id validation tests ---

@pytest.mark.parametrize("profile_id", [
    "normal-profile",
    "profile_123",
    "my.profile.v2",
    "ABC-123_def.test",
])
def test_validate_profile_id_valid(profile_id):
    """Test _validate_profile_id accepts safe characters."""
    # Should not raise
    _validate_profile_id(profile_id)


@pytest.mark.parametrize("profile_id", [
    "",
    ".",
    "..",
    "...",
    "a..b",
    "path/traversal",
    "..\\escape",
    "profile with spaces",
    "profile@special",
    "profile#hash",
    "profile$dollar",
    "../../../etc/passwd",
    "..\\..\\Windows\\System32",
    "profile\x00null",
])
def test_validate_profile_id_rejected(profile_id):
    """Test _validate_profile_id rejects unsafe characters."""
    with pytest.raises(ValueError):
        _validate_profile_id(profile_id)


def test_windows_profile_dir_path_traversal(monkeypatch):
    """Test WindowsAdapter rejects path traversal in profile_id."""
    monkeypatch.setenv("APPDATA", "C:\\Users\\test\\AppData\\Roaming")
    adapter = WindowsAdapter()
    with pytest.raises(ValueError, match="unsafe characters"):
        adapter.get_profile_dir("../../../etc/passwd")


def test_macos_profile_dir_path_traversal():
    """Test MacOSAdapter rejects path traversal in profile_id."""
    adapter = MacOSAdapter()
    with pytest.raises(ValueError, match="unsafe characters"):
        adapter.get_profile_dir("..\\..\\escape")
