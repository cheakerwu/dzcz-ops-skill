"""Tests for platform adapters."""
import pytest
import os
from pathlib import Path
from dzcz_merchant_ops.config.platform import (
    PlatformAdapter,
    WindowsAdapter,
    MacOSAdapter,
    get_platform_adapter
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
