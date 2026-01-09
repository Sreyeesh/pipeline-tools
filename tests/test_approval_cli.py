from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_approval_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["approve", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No approvals yet." in result.stdout


def test_approval_set_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["asset", "add", "--db", str(db_path), "--name", "Hero", "--type", "character"],
    )
    set_result = runner.invoke(
        cli.app,
        [
            "approve",
            "set",
            "--db",
            str(db_path),
            "--asset-id",
            "1",
            "--status",
            "approved",
            "--note",
            "Looks good",
        ],
    )
    assert set_result.exit_code == 0
    assert "Recorded approval #1 for asset #1" in set_result.stdout

    listed = runner.invoke(cli.app, ["approve", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "ID" in listed.stdout
    assert "approved" in listed.stdout
    assert "Looks good" in listed.stdout


def test_approval_requires_asset(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(
        cli.app,
        ["approve", "set", "--db", str(db_path), "--asset-id", "42", "--status", "approved"],
    )
    assert result.exit_code != 0
    assert "Asset ID not found" in result.stderr
