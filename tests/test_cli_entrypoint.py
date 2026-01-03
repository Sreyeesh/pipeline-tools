from __future__ import annotations

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_root_command_points_users_to_loop() -> None:
    result = runner.invoke(cli.app, [])

    assert result.exit_code == 0
    assert "loop create" in result.stdout


def test_version_flag() -> None:
    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert "pipely" in result.stdout


def test_loop_help_is_available() -> None:
    result = runner.invoke(cli.app, ["loop", "--help"])

    assert result.exit_code == 0
    assert not result.stdout or "Usage" in result.stdout
