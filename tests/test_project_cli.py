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


def test_project_purge(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Show", "--code", "SHOW"],
    )

    purge = runner.invoke(
        cli.app,
        ["project", "purge", "--db", str(db_path)],
        input="y\n",
    )
    assert purge.exit_code == 0
    assert "Deleted 2 project" in purge.stdout


def test_project_purge_cancelled(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    purge = runner.invoke(
        cli.app,
        ["project", "purge", "--db", str(db_path)],
        input="n\n",
    )
    assert purge.exit_code == 0
    assert "Purge cancelled" in purge.stdout

    listed = runner.invoke(cli.app, ["project", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "Film" in listed.stdout


def test_project_purge_all_cascades(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    runner.invoke(
        cli.app,
        ["shot", "add", "--db", str(db_path), "--project-id", "1", "--code", "S010", "--name", "Opening"],
    )
    runner.invoke(
        cli.app,
        [
            "asset",
            "add",
            "--db",
            str(db_path),
            "--name",
            "Hero",
            "--type",
            "character",
            "--project-id",
            "1",
            "--shot-id",
            "1",
        ],
    )
    runner.invoke(
        cli.app,
        ["task", "add", "--db", str(db_path), "--asset-id", "1", "--name", "Model"],
    )
    runner.invoke(
        cli.app,
        ["approve", "set", "--db", str(db_path), "--asset-id", "1", "--status", "approved"],
    )
    runner.invoke(
        cli.app,
        ["schedule", "add", "--db", str(db_path), "--asset-id", "1", "--task", "Model", "--due", "2025-01-10"],
    )

    purge = runner.invoke(
        cli.app,
        ["project", "purge", "--db", str(db_path), "--all"],
        input="y\n",
    )
    assert purge.exit_code == 0
    assert "Deleted 1 project" in purge.stdout

    for command in (
        ["project", "list"],
        ["shot", "list"],
        ["asset", "list"],
        ["task", "list"],
        ["approve", "list"],
        ["schedule", "list"],
    ):
        result = runner.invoke(cli.app, [*command, "--db", str(db_path)])
        assert result.exit_code == 0
