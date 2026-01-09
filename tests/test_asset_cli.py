from __future__ import annotations

import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def _schema_version(db_path: Path) -> int:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
        row = cursor.fetchone()
        return int(row[0] or 0)


def test_asset_list_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["asset", "list", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No assets yet." in result.stdout
    assert _schema_version(db_path) == 7


def test_asset_add_and_list(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    runner.invoke(
        cli.app,
        ["project", "add", "--db", str(db_path), "--name", "Film", "--code", "FILM"],
    )
    runner.invoke(
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
    add = runner.invoke(
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
    assert add.exit_code == 0
    assert "Added asset #1" in add.stdout

    listed = runner.invoke(cli.app, ["asset", "list", "--db", str(db_path)])
    assert listed.exit_code == 0
    assert "#1 Hero (character, todo) [project 1, shot 1]" in listed.stdout
