from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sqlite3


DEFAULT_DB_ENV = "PIPELY_DB"
DEFAULT_DB_DIR = Path.home() / ".pipely"
DEFAULT_DB_NAME = "pipely.db"


MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY
        );
        INSERT INTO schema_migrations (version) VALUES (1);
        """,
    ),
    (
        2,
        """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        INSERT INTO schema_migrations (version) VALUES (2);
        """,
    ),
]


def default_db_path() -> Path:
    env_override = os.environ.get(DEFAULT_DB_ENV)
    if env_override:
        return Path(env_override).expanduser()
    return DEFAULT_DB_DIR / DEFAULT_DB_NAME


def resolve_db_path(db_path: Path | None) -> Path:
    return Path(db_path).expanduser() if db_path else default_db_path()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _has_schema_table(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    )
    return cursor.fetchone() is not None


def _current_version(conn: sqlite3.Connection) -> int:
    if not _has_schema_table(conn):
        return 0
    cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
    row = cursor.fetchone()
    return int(row[0] or 0)


def _apply_migrations(conn: sqlite3.Connection) -> int:
    current = _current_version(conn)
    applied = 0
    for version, script in MIGRATIONS:
        if version <= current:
            continue
        conn.executescript(script)
        applied += 1
    conn.commit()
    return applied


def init_db(db_path: Path | None = None) -> tuple[Path, int]:
    path = resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        applied = _apply_migrations(conn)
    finally:
        conn.close()
    return path, applied


def create_asset(
    db_path: Path,
    name: str,
    asset_type: str,
    status: str,
) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO assets (name, asset_type, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, asset_type, status, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_assets(db_path: Path) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, name, asset_type, status, created_at
            FROM assets
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
