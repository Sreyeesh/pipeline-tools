from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from pipeline_tools.tools.dcc_launcher import launcher


def test_get_dcc_executable_returns_existing_path(monkeypatch):
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(launcher, "DCC_PATHS", {"fake": {"Linux": ["/usr/bin/fake"]}})
    monkeypatch.setattr(launcher.os.path, "exists", lambda p: p == "/usr/bin/fake")

    assert launcher.get_dcc_executable("fake") == "/usr/bin/fake"


def test_get_dcc_executable_wsl_converts_windows_path(monkeypatch):
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(launcher, "DCC_PATHS", {"fake": {"Linux": [], "Windows": ["C:/Program Files/Fake/fake.exe"]}})
    # Simulate WSL with /mnt/c existing and converted path present
    def fake_exists(path: str) -> bool:
        return path in {"/mnt/c", "/mnt/c/Program Files/Fake/fake.exe"}

    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)

    result = launcher.get_dcc_executable("fake")
    assert result == "/mnt/c/Program Files/Fake/fake.exe"


def test_get_dcc_executable_searches_extra_windows_mounts(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    program_root = tmp_path / "Program Files"
    program_root.mkdir()
    fake_root = program_root / "Epic Games"
    exe = fake_root / "UE_5.3" / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")

    monkeypatch.setattr(
        launcher,
        "_detect_windows_roots",
        lambda system: [str(program_root)],
    )

    monkeypatch.setattr(
        launcher,
        "DCC_PATHS",
        {
            "unreal": {
                "Linux": [],
                "Windows": ["C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe"],
            }
        },
    )

    result = launcher.get_dcc_executable("unreal")
    assert result == str(exe)


def test_get_dcc_executable_skips_deep_search_when_disabled(monkeypatch):
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        launcher,
        "DCC_PATHS",
        {"fake": {"Linux": [], "Windows": ["C:/Program Files/Fake/fake.exe"]}},
    )

    # WSL root exists but executable path does not.
    def fake_exists(path: str) -> bool:
        return path == "/mnt/c"

    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)

    def fail_search(names):
        raise AssertionError("Deep search should be skipped")

    monkeypatch.setattr(launcher, "_search_windows_drive", fail_search)

    assert launcher.get_dcc_executable("fake", allow_deep_search=False) is None


def test_launch_krita_without_python_script_flag(tmp_path, monkeypatch):
    """Test that Krita launches without the --python-script flag."""
    # Create a test file
    test_file = tmp_path / "test.kra"
    test_file.write_text("test")

    # Mock the executable finder
    krita_path = "/mnt/c/Program Files/Krita (x64)/bin/krita.exe"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: krita_path)

    # Mock platform and path checks
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    def fake_exists(path):
        return path in {"/mnt/c", str(test_file)}
    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)

    # Mock subprocess.Popen
    mock_popen = Mock(return_value=Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", mock_popen)

    # Launch Krita with a file
    launcher.launch_dcc("krita", file_path=str(test_file))

    # Verify Popen was called
    assert mock_popen.called
    call_args = mock_popen.call_args
    cmd = call_args[0][0]

    # Verify --python-script is NOT in the command
    assert "--python-script" not in cmd
    # Verify the executable and file are in the command
    assert cmd[0] == krita_path
    assert any("test.kra" in str(arg) for arg in cmd)


def test_launch_krita_wsl_path_conversion(tmp_path, monkeypatch):
    """Test that file paths are converted from WSL to Windows format."""
    # Create a test file in /mnt/c (simulated WSL path)
    test_file_wsl = "/mnt/c/Projects/test.kra"

    # Mock the executable finder
    krita_path = "/mnt/c/Program Files/Krita (x64)/bin/krita.exe"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: krita_path)

    # Mock platform and path checks
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    def fake_exists(path):
        return path in {"/mnt/c", test_file_wsl}
    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)

    # Mock Path.exists() for the file check
    def mock_path_exists(self):
        return str(self) == test_file_wsl
    monkeypatch.setattr(Path, "exists", mock_path_exists)

    # Mock subprocess.Popen
    mock_popen = Mock(return_value=Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", mock_popen)

    # Launch Krita with a WSL file path
    launcher.launch_dcc("krita", file_path=test_file_wsl)

    # Verify the path was converted to Windows format
    call_args = mock_popen.call_args
    cmd = call_args[0][0]

    # Should contain Windows-style path
    assert any("C:\\Projects\\test.kra" in str(arg) for arg in cmd)


def test_launch_dcc_background_mode(tmp_path, monkeypatch):
    """Test that background launch uses correct subprocess flags."""
    test_file = tmp_path / "test.kra"
    test_file.write_text("test")

    krita_path = "/mnt/c/Program Files/Krita (x64)/bin/krita.exe"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: krita_path)
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    def fake_exists(path):
        return path in {"/mnt/c", str(test_file)}
    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)

    # Mock subprocess.Popen
    mock_popen = Mock(return_value=Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", mock_popen)

    # Launch in background
    launcher.launch_dcc("krita", file_path=str(test_file), background=True)

    # Verify background flags were used
    call_args = mock_popen.call_args
    kwargs = call_args[1]

    # Should have start_new_session=True for Unix
    assert kwargs.get("start_new_session") is True
    assert kwargs.get("stdout") == subprocess.DEVNULL
    assert kwargs.get("stderr") == subprocess.DEVNULL


def test_launch_dcc_raises_on_missing_executable(monkeypatch):
    """Test that FileNotFoundError is raised when executable is not found."""
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: None)

    with pytest.raises(FileNotFoundError, match="Could not find krita executable"):
        launcher.launch_dcc("krita")


def test_launch_dcc_raises_on_missing_file(tmp_path, monkeypatch):
    """Test that ValueError is raised when file doesn't exist."""
    krita_path = "/usr/bin/krita"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: krita_path)

    nonexistent_file = tmp_path / "nonexistent.kra"

    with pytest.raises(ValueError, match="File does not exist"):
        launcher.launch_dcc("krita", file_path=str(nonexistent_file))


def test_launch_blender_includes_python_flag(tmp_path, monkeypatch):
    """Test that Blender still gets --python flag (not affected by Krita fix)."""
    test_file = tmp_path / "test.blend"
    test_file.write_text("test")
    project_root = str(tmp_path)

    blender_path = "/mnt/c/Program Files/Blender Foundation/Blender 4.3/blender.exe"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: blender_path)
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")

    def fake_exists(path):
        return path in {"/mnt/c", str(test_file)} or "/mnt/c/Users" in str(path)
    monkeypatch.setattr(launcher.os.path, "exists", fake_exists)
    monkeypatch.setattr(launcher.os.path, "isabs", lambda p: p.startswith("/"))

    # Mock Path operations
    original_path = Path
    def mock_path_new(cls, *args, **kwargs):
        p = original_path(*args, **kwargs)
        # Mock expanduser to return existing path
        original_expanduser = p.expanduser
        def fake_expanduser():
            return original_path("/mnt/c/Users/testuser/Desktop")
        p.expanduser = fake_expanduser
        return p

    # Mock subprocess commands
    mock_run = Mock(return_value=Mock(stdout="testuser\n", returncode=0))
    monkeypatch.setattr(launcher.subprocess, "run", mock_run)

    mock_popen = Mock(return_value=Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", mock_popen)

    # Mock Path.exists for temp paths
    original_path_exists = Path.exists
    def mock_exists(self):
        path_str = str(self)
        if "Temp" in path_str or "Desktop" in path_str:
            return True
        return original_path_exists(self)
    monkeypatch.setattr(Path, "exists", mock_exists)

    # Mock open for script writing
    mock_open = MagicMock()
    monkeypatch.setattr("builtins.open", mock_open)

    # Launch Blender with project root (triggers startup script creation)
    launcher.launch_dcc("blender", file_path=str(test_file), project_root=project_root)

    # Verify Popen was called
    assert mock_popen.called
    call_args = mock_popen.call_args
    cmd = call_args[0][0]

    # Verify --python IS in the command for Blender
    assert "--python" in cmd


def test_launch_krita_no_project_root(tmp_path, monkeypatch):
    """Test that Krita launches successfully without project root."""
    test_file = tmp_path / "test.kra"
    test_file.write_text("test")

    krita_path = "/usr/bin/krita"
    monkeypatch.setattr(launcher, "get_dcc_executable", lambda x: krita_path)
    monkeypatch.setattr(launcher.platform, "system", lambda: "Linux")
    monkeypatch.setattr(launcher.os.path, "exists", lambda p: str(p) == str(test_file))

    mock_popen = Mock(return_value=Mock())
    monkeypatch.setattr(launcher.subprocess, "Popen", mock_popen)

    # Launch without project root
    launcher.launch_dcc("krita", file_path=str(test_file))

    # Verify it launched successfully
    assert mock_popen.called
    call_args = mock_popen.call_args
    cmd = call_args[0][0]

    assert cmd[0] == krita_path
    assert str(test_file) in cmd
