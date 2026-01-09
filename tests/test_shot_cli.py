from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_shot_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["shot", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No shots yet." in result.stdout


def test_shot_add_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    add = runner.invoke(
        cli.app,
        [
            "shot",
            "add",
            "--db",
            str(db_path),
            "--project-id",
            "1",
            "--code",
            "S010",
            "--name",
            "Opening",
        ],
    )
    assert add.exit_code == 0
    assert "Added shot #1 to project #1" in add.stdout

    listed = runner.invoke(cli.app, ["shot", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "ID" in listed.stdout
    assert "1" in listed.stdout
    assert "S010" in listed.stdout
    assert "Opening" in listed.stdout


def test_shot_add_requires_project(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(
        cli.app,
        ["shot", "add", "--db", str(db_path), "--project-id", "99", "--code", "S010", "--name", "Opening"],
    )
    assert result.exit_code != 0
    assert "Project ID not found" in result.stdout
