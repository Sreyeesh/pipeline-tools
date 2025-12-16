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


def test_shows_create_shorthand_stays_together(monkeypatch, tmp_path):
    captured: list[tuple[list[str], bool]] = []

    class FakeApp:
        def __call__(self, args, standalone_mode=False):
            captured.append((list(args), standalone_mode))

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ['shows create DMO "Demo" animation_short']

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "app", FakeApp())

    interactive.run_interactive()

    assert captured == [
        (["shows", "create", "-c", "DMO", "-n", "Demo", "-t", "animation_short"], False)
    ]


def test_workspace_show_calls_summary(monkeypatch, tmp_path):
    calls: list[list] = []

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["workspace show"]

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    def fake_summary(show_code=None):
        calls.append([show_code])

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(interactive, "_workspace_summary", fake_summary)
    monkeypatch.setattr(cli, "app", lambda *args, **kwargs: None)

    interactive.run_interactive()

    assert calls == [[None]]


def test_workspace_on_runs_after_commands(monkeypatch, tmp_path):
    summary_calls: list[list] = []
    app_calls: list[list[str]] = []

    class FakeApp:
        def __call__(self, args, standalone_mode=False):
            app_calls.append(list(args))

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["workspace on", "tasks list DMO_SH010"]

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    def fake_summary(show_code=None):
        summary_calls.append([show_code])

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(interactive, "_workspace_summary", fake_summary)
    monkeypatch.setattr(cli, "app", FakeApp())

    interactive.run_interactive()

    assert app_calls == [["tasks", "list", "DMO_SH010"]]
    # Called once when enabling, once after the passthrough command
    assert summary_calls == [[None], [None]]


def test_projects_list_updates_after_delete(monkeypatch, tmp_path):
    project_dir = tmp_path / "AN_DMO_DemoShort30s"
    project_dir.mkdir()
    import shutil

    class FakeApp:
        def __init__(self):
            self.calls: list[list[str]] = []

        def __call__(self, args, standalone_mode=False):
            self.calls.append(list(args))
            if args[:3] == ["shows", "delete", "-c"]:
                if project_dir.exists():
                    shutil.rmtree(project_dir)

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["projects", "delete AN_DMO_DemoShort30s", "projects", "exit"]

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            return self._commands.pop(0)

    class RecordingCompleter:
        def __init__(self):
            self.history: list[list[str]] = []

        def update_context(self, projects=None, dccs=None, show_dcc_menu=False):
            if projects is None:
                names = []
            else:
                names = [p.name for p in projects]
            self.history.append(names)

        def get_completions(self, *_, **__):
            return iter(())

    fake_completer = RecordingCompleter()

    def fake_interpret(text, *_args, **_kwargs):
        if text.lower().startswith("delete"):
            return (["shows", "delete", "-c", "DMO", "--delete-folders"], "note")
        return None

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(interactive, "PipelineCompleter", lambda: fake_completer)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "app", FakeApp())
    monkeypatch.setattr(interactive, "_interpret_natural_command", fake_interpret)

    interactive.run_interactive()

    # After deletion, the completer should have been updated with no remaining projects
    assert [] in fake_completer.history


def test_projects_list_reflects_removed_folder(monkeypatch, tmp_path):
    project_dir = tmp_path / "AN_DMO_DemoShort30s"
    project_dir.mkdir()

    class FakeSession:
        def __init__(self, *_, **__):
            self._commands = ["projects", "projects", "exit"]
            self._count = 0

        def prompt(self, *_, **__):
            if not self._commands:
                raise EOFError
            cmd = self._commands.pop(0)
            self._count += 1
            if self._count == 2 and project_dir.exists():
                project_dir.rmdir()
            return cmd

    class RecordingCompleter:
        def __init__(self):
            self.history: list[list[str]] = []

        def update_context(self, projects=None, dccs=None, show_dcc_menu=False):
            names = [p.name for p in projects] if projects else []
            self.history.append(names)

        def get_completions(self, *_, **__):
            return iter(())

    fake_completer = RecordingCompleter()

    monkeypatch.setattr(interactive, "PromptSession", FakeSession)
    monkeypatch.setattr(interactive, "PipelineCompleter", lambda: fake_completer)
    monkeypatch.setattr(core_paths, "get_creative_root", lambda: tmp_path)

    interactive.run_interactive()

    assert [] in fake_completer.history
