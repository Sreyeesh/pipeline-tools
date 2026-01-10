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


def test_db_init_creates_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["db", "init", "--db", str(db_path)])
    assert result.exit_code == 0
    assert db_path.exists()
    assert _schema_version(db_path) == 9


def test_db_init_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    first = runner.invoke(cli.app, ["db", "init", "--db", str(db_path)])
    assert first.exit_code == 0
    second = runner.invoke(cli.app, ["db", "init", "--db", str(db_path)])
    assert second.exit_code == 0
    assert "Database ready" in second.stdout


def test_db_path_outputs_requested_location(tmp_path: Path) -> None:
    db_path = tmp_path / "pipely.db"
    result = runner.invoke(cli.app, ["db", "path", "--db", str(db_path)])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(db_path)
