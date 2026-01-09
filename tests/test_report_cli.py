from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_report_summary_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["report", "summary", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Totals: 0 projects, 0 shots, 0 assets, 0 tasks, 0 approvals, 0 schedules" in result.stdout


def test_report_summary_with_data(tmp_path: Path) -> None:
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
        ["task", "add", "--db", str(db_path), "--asset-id", "1", "--name", "Model", "--status", "todo"],
    )
    runner.invoke(
        cli.app,
        ["approve", "set", "--db", str(db_path), "--asset-id", "1", "--status", "approved"],
    )
    runner.invoke(
        cli.app,
        ["schedule", "add", "--db", str(db_path), "--asset-id", "1", "--task", "Model", "--due", "2025-01-10"],
    )
    result = runner.invoke(cli.app, ["report", "summary", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Totals: 1 projects, 1 shots, 1 assets, 1 tasks, 1 approvals, 1 schedules" in result.stdout
    assert "Assets by status:" in result.stdout
    assert "todo: 1" in result.stdout
    assert "Tasks by status:" in result.stdout
    assert "todo: 1" in result.stdout
