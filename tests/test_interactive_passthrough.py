from __future__ import annotations

from pipeline_tools import interactive
from pipeline_tools import cli
from pipeline_tools.core import paths as core_paths


def test_interactive_forwards_tasks(monkeypatch, tmp_path):
    captured: list[tuple[list[str], bool]] = []

    class FakeApp:
        def __call__(self, args, standalone_mode=False):
            captured.append((list(args), standalone_mode))

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["tasks list DMO_SH010"]

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "app", FakeApp())

    interactive.run_interactive()

    assert captured == [(["tasks", "list", "DMO_SH010"], False)]


def test_interactive_auto_adds_project_to_open(monkeypatch, tmp_path):
    captured: list[tuple[list[str], bool]] = []

    class FakeApp:
        def __call__(self, args, standalone_mode=False):
            captured.append((list(args), standalone_mode))

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["1", "open blender"]

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    project_dir = tmp_path / "AN_TEST_Project"
    project_dir.mkdir()

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "app", FakeApp())

    interactive.run_interactive()

    assert captured[-1] == (["open", "blender", "--project", "AN_TEST_Project"], False)
