from __future__ import annotations

from pathlib import Path

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
