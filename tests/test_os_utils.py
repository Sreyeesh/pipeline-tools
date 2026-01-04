from __future__ import annotations

import pytest
import pipeline_tools.os_utils as os_utils


@pytest.fixture(autouse=True)
def reset_os_cache() -> None:
    os_utils.reset_os_cache()
    yield
    os_utils.reset_os_cache()


def _set_os(monkeypatch, name: str) -> None:
    monkeypatch.setattr(os_utils.platform, "system", lambda: name)


def test_default_root_prefers_env(monkeypatch, tmp_path) -> None:
    env_path = tmp_path / "Projects"
    env_path.mkdir()
    monkeypatch.setenv(os_utils.DEFAULT_ROOT_ENV, str(env_path))
    os_utils.reset_os_cache()
    assert os_utils.default_projects_root() == env_path
    monkeypatch.delenv(os_utils.DEFAULT_ROOT_ENV)


def test_windows_reserved_names_are_adjusted(monkeypatch) -> None:
    _set_os(monkeypatch, "Windows")
    assert os_utils.sanitize_folder_name("CON") == "CON_"
    assert os_utils.sanitize_folder_name("Folder ") == "Folder"


def test_linux_defaults_to_home_projects(monkeypatch, tmp_path) -> None:
    _set_os(monkeypatch, "Linux")
    home_projects = tmp_path / "Projects"
    home_projects.mkdir()

    # Patch Path.home to point at tmp_path
    monkeypatch.setattr(os_utils.Path, "home", lambda: tmp_path)

    result = os_utils.default_projects_root()
    assert result == home_projects


def test_resolve_root_uses_argument(monkeypatch, tmp_path) -> None:
    target = tmp_path / "custom"
    resolved = os_utils.resolve_root(target)
    assert resolved == target
