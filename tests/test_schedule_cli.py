from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_schedule_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["schedule", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No schedule items yet." in result.stdout


def test_schedule_add_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["asset", "add", "--db", str(db_path), "--name", "Prop", "--type", "prop"],
    )
    add = runner.invoke(
        cli.app,
        [
            "schedule",
            "add",
            "--db",
            str(db_path),
            "--asset-id",
            "1",
            "--task",
            "Model",
            "--due",
            "2025-01-10",
        ],
    )
    assert add.exit_code == 0
    assert "Added schedule #1 for asset #1" in add.stdout

    listed = runner.invoke(cli.app, ["schedule", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "ID" in listed.stdout
    assert "Model" in listed.stdout
    assert "2025-01-10" in listed.stdout
    assert "scheduled" in listed.stdout


def test_schedule_requires_asset(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(
        cli.app,
        ["schedule", "add", "--db", str(db_path), "--asset-id", "3", "--task", "Model", "--due", "2025-01-10"],
    )
    assert result.exit_code != 0
    assert "Asset ID not found" in result.stderr
