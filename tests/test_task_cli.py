from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_task_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["task", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No tasks yet." in result.stdout


def test_task_add_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["asset", "add", "--db", str(db_path), "--name", "Hero", "--type", "character"],
    )
    add = runner.invoke(
        cli.app,
        [
            "task",
            "add",
            "--db",
            str(db_path),
            "--asset-id",
            "1",
            "--name",
            "Model",
            "--assignee",
            "Sam",
            "--due",
            "2025-02-01",
        ],
    )
    assert add.exit_code == 0
    assert "Added task #1 for asset #1" in add.stdout

    listed = runner.invoke(cli.app, ["task", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "#1 asset #1 Model (todo, Sam, due 2025-02-01)" in listed.stdout
