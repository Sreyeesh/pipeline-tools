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
    (
        3,
        """
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(asset_id) REFERENCES assets(id)
        );
        INSERT INTO schema_migrations (version) VALUES (3);
        """,
    ),
    (
        4,
        """
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(asset_id) REFERENCES assets(id)
        );
        INSERT INTO schema_migrations (version) VALUES (4);
        """,
    ),
    (
        5,
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        INSERT INTO schema_migrations (version) VALUES (5);
        """,
    ),
    (
        6,
        """
        CREATE TABLE IF NOT EXISTS shots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        INSERT INTO schema_migrations (version) VALUES (6);
        """,
    ),
    (
        7,
        """
        ALTER TABLE assets ADD COLUMN project_id INTEGER REFERENCES projects(id);
        ALTER TABLE assets ADD COLUMN shot_id INTEGER REFERENCES shots(id);
        INSERT INTO schema_migrations (version) VALUES (7);
        """,
    ),
    (
        8,
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            assignee TEXT,
            due_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(asset_id) REFERENCES assets(id)
        );
        INSERT INTO schema_migrations (version) VALUES (8);
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
        try:
            conn.executescript(script)
        except sqlite3.OperationalError:
            # Allow idempotent column additions on older SQLite files.
            if "ALTER TABLE assets ADD COLUMN" in script:
                pass
            else:
                raise
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
    project_id: int | None,
    shot_id: int | None,
) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO assets (name, asset_type, status, created_at, project_id, shot_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, asset_type, status, datetime.utcnow().isoformat(), project_id, shot_id),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_assets(
    db_path: Path,
    project_id: int | None = None,
    shot_id: int | None = None,
) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        query = """
            SELECT id, name, asset_type, status, created_at, project_id, shot_id
            FROM assets
        """
        params: list[int] = []
        conditions: list[str] = []
        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)
        if shot_id is not None:
            conditions.append("shot_id = ?")
            params.append(shot_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_approval(
    db_path: Path,
    asset_id: int,
    status: str,
    note: str | None,
) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO approvals (asset_id, status, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, status, note, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_approvals(db_path: Path, asset_id: int | None = None) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        if asset_id is None:
            cursor = conn.execute(
                """
                SELECT id, asset_id, status, note, created_at
                FROM approvals
                ORDER BY id
                """
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, asset_id, status, note, created_at
                FROM approvals
                WHERE asset_id = ?
                ORDER BY id
                """,
                (asset_id,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_schedule(
    db_path: Path,
    asset_id: int,
    task: str,
    due_date: str,
    status: str,
) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO schedules (asset_id, task, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset_id, task, due_date, status, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_schedules(db_path: Path, asset_id: int | None = None) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        if asset_id is None:
            cursor = conn.execute(
                """
                SELECT id, asset_id, task, due_date, status, created_at
                FROM schedules
                ORDER BY due_date, id
                """
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, asset_id, task, due_date, status, created_at
                FROM schedules
                WHERE asset_id = ?
                ORDER BY due_date, id
                """,
                (asset_id,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_project(db_path: Path, name: str, code: str) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO projects (name, code, created_at)
            VALUES (?, ?, ?)
            """,
            (name, code, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_projects(db_path: Path) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, name, code, created_at
            FROM projects
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_shot(db_path: Path, project_id: int, code: str, name: str) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO shots (project_id, code, name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, code, name, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_shots(db_path: Path, project_id: int | None = None) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        if project_id is None:
            cursor = conn.execute(
                """
                SELECT id, project_id, code, name, created_at
                FROM shots
                ORDER BY id
                """
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, project_id, code, name, created_at
                FROM shots
                WHERE project_id = ?
                ORDER BY id
                """,
                (project_id,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def create_task(
    db_path: Path,
    asset_id: int,
    name: str,
    status: str,
    assignee: str | None,
    due_date: str | None,
) -> int:
    conn = connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO tasks (asset_id, name, status, assignee, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asset_id, name, status, assignee, due_date, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_tasks(db_path: Path, asset_id: int | None = None) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        if asset_id is None:
            cursor = conn.execute(
                """
                SELECT id, asset_id, name, status, assignee, due_date, created_at
                FROM tasks
                ORDER BY id
                """
            )
        else:
            cursor = conn.execute(
                """
                SELECT id, asset_id, name, status, assignee, due_date, created_at
                FROM tasks
                WHERE asset_id = ?
                ORDER BY id
                """,
                (asset_id,),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def _count_by_status(conn: sqlite3.Connection, table: str) -> dict[str, int]:
    cursor = conn.execute(f"SELECT status, COUNT(*) AS count FROM {table} GROUP BY status")
    return {row["status"]: int(row["count"]) for row in cursor.fetchall()}


def report_summary(db_path: Path) -> dict[str, object]:
    conn = connect(db_path)
    try:
        counts = {
            "projects": conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
            "shots": conn.execute("SELECT COUNT(*) FROM shots").fetchone()[0],
            "assets": conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0],
            "tasks": conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "approvals": conn.execute("SELECT COUNT(*) FROM approvals").fetchone()[0],
            "schedules": conn.execute("SELECT COUNT(*) FROM schedules").fetchone()[0],
        }
        return {
            "counts": {k: int(v) for k, v in counts.items()},
            "asset_status": _count_by_status(conn, "assets"),
            "task_status": _count_by_status(conn, "tasks"),
        }
    finally:
        conn.close()


def _id_exists(conn: sqlite3.Connection, table: str, entity_id: int) -> bool:
    cursor = conn.execute(f"SELECT 1 FROM {table} WHERE id = ? LIMIT 1", (entity_id,))
    return cursor.fetchone() is not None


def project_exists(db_path: Path, project_id: int) -> bool:
    conn = connect(db_path)
    try:
        return _id_exists(conn, "projects", project_id)
    finally:
        conn.close()


def shot_exists(db_path: Path, shot_id: int) -> bool:
    conn = connect(db_path)
    try:
        return _id_exists(conn, "shots", shot_id)
    finally:
        conn.close()


def asset_exists(db_path: Path, asset_id: int) -> bool:
    conn = connect(db_path)
    try:
        return _id_exists(conn, "assets", asset_id)
    finally:
        conn.close()
