from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_project_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["project", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No projects yet." in result.stdout


def test_project_add_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    add = runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    assert add.exit_code == 0
    assert "Added project #1: Film (FILM)" in add.stdout

    listed = runner.invoke(cli.app, ["project", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "ID" in listed.stdout
    assert "1" in listed.stdout
    assert "Film" in listed.stdout
    assert "FILM" in listed.stdout


def test_project_update_and_delete(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    add = runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    assert add.exit_code == 0

    update = runner.invoke(
        cli.app,
        ["project", "update", "--db", str(db_path), "--project-id", "1", "--name", "Show"],
    )
    assert update.exit_code == 0

    delete = runner.invoke(
        cli.app,
        ["project", "delete", "--db", str(db_path), "--project-id", "1"],
    )
    assert delete.exit_code == 0
