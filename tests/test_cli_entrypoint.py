from __future__ import annotations

from typing import List

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_top_level_defaults_to_interactive() -> None:
    result = runner.invoke(cli.app, [], input="\n")  # Simulate pressing Enter to exit

    assert result.exit_code == 0
    assert "Pipeline Tools" in result.stdout or "pipeline-tools>" in result.stdout


def test_list_shows_commands() -> None:
    result = runner.invoke(cli.app, ["--list"])

    assert result.exit_code == 0
    assert "create" in result.stdout
    assert "doctor" in result.stdout


def test_create_passes_args_to_project_creator(monkeypatch) -> None:
    captured: List[str] = []

    def fake_main(argv: List[str]) -> None:
        captured.extend(argv)

    monkeypatch.setattr(cli.project_creator_main, "main", fake_main)

    result = runner.invoke(
        cli.app,
        ["create", "-c", "DMO", "-n", "Test Project", "--dry-run", "-y"],
    )

    assert result.exit_code == 0
    assert captured == ["-c", "DMO", "-n", "Test Project", "--dry-run", "--yes"]


def test_doctor_includes_admin_prefix(monkeypatch) -> None:
    captured: List[str] = []

    def fake_admin(argv: List[str]) -> None:
        captured.extend(argv)

    monkeypatch.setattr(cli.admin_main, "main", fake_admin)

    result = runner.invoke(cli.app, ["doctor", "--extra"])

    assert result.exit_code == 0
    assert captured == ["doctor", "--extra"]


def test_passthrough_commands_allow_extra_args(monkeypatch) -> None:
    captured: List[str] = []

    def fake_shows(argv: List[str]) -> None:
        captured.extend(argv)

    monkeypatch.setattr(cli.shows_main, "main", fake_shows)

    result = runner.invoke(cli.app, ["shows", "list", "--verbose"])

    assert result.exit_code == 0
    assert captured == ["list", "--verbose"]


def test_hyphenated_command_for_character_thumbnails(monkeypatch) -> None:
    captured: List[str] = []

    def fake_ct(argv: List[str]) -> None:
        captured.extend(argv)

    monkeypatch.setattr(cli.character_thumbnails_main, "main", fake_ct)

    result = runner.invoke(cli.app, ["character-thumbnails", "--foo"])

    assert result.exit_code == 0
    assert captured == ["--foo"]


def test_version_flag() -> None:
    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert "pipeline-tools" in result.stdout
