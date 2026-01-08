from __future__ import annotations

from pathlib import Path
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
]


def default_db_path() -> Path:
    env_override = os.environ.get(DEFAULT_DB_ENV)
    if env_override:
        return Path(env_override).expanduser()
    return DEFAULT_DB_DIR / DEFAULT_DB_NAME


def resolve_db_path(db_path: Path | None) -> Path:
    return Path(db_path).expanduser() if db_path else default_db_path()


def connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


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
