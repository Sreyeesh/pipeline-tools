import json
import os
import sqlite3
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    """Return the location for the SQLite DB."""
    env_path = os.environ.get("PIPELINE_TOOLS_DB")
    if env_path:
        return Path(env_path)
    return Path.home() / ".pipeline_tools" / "db.sqlite3"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Return a SQLite connection with tables ensured.
    """
    path = Path(db_path) if db_path else get_db_path()
    _ensure_parent(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS shows (
            code TEXT PRIMARY KEY,
            name TEXT,
            template TEXT,
            root TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            show_code TEXT,
            type TEXT,
            name TEXT,
            status TEXT,
            path TEXT,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS shots (
            id TEXT PRIMARY KEY,
            code TEXT,
            show_code TEXT,
            description TEXT,
            status TEXT,
            path TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id TEXT,
            name TEXT,
            status TEXT,
            updated_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS versions (
            version_id TEXT PRIMARY KEY,
            target_id TEXT,
            kind TEXT,
            show_code TEXT,
            tags TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()


def get_config(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_config(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO config(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def decode_tags(value: Optional[str]) -> list[str]:
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []


def encode_tags(tags: list[str]) -> str:
    return json.dumps(tags)


def load_db(db_path: Optional[Path] = None) -> dict:
    """
    Load the DB content into a dict (compat layer).
    """
    conn = get_conn(db_path)
    data: dict = {
        "shows": {},
        "assets": {},
        "shots": {},
        "tasks": {},
        "versions": {},
        "asset_tasks": {},
        "playlists": {},
        "notes": [],
        "config": {},
        "current_show": None,
    }

    for row in conn.execute("SELECT key, value FROM config"):
        data["config"][row["key"]] = row["value"]
    data["current_show"] = data["config"].get("current_show")

    for row in conn.execute("SELECT * FROM shows"):
        data["shows"][row["code"]] = dict(row)

    for row in conn.execute("SELECT * FROM assets"):
        entry = dict(row)
        entry["tags"] = decode_tags(row["tags"])
        data["assets"][row["id"]] = entry

    for row in conn.execute("SELECT * FROM shots"):
        data["shots"][row["id"]] = dict(row)

    tasks: dict[str, list] = {}
    for row in conn.execute("SELECT * FROM tasks"):
        tasks.setdefault(row["target_id"], []).append(
            {"name": row["name"], "status": row["status"], "updated_at": row["updated_at"]}
        )
    data["tasks"] = tasks

    for row in conn.execute("SELECT * FROM versions"):
        entry = dict(row)
        entry["tags"] = decode_tags(row["tags"])
        data["versions"][row["version_id"]] = entry

    return data


def save_db(data: dict, db_path: Optional[Path] = None) -> None:
    """
    Persist the dict content into SQLite (compat layer).
    """
    conn = get_conn(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM versions")
    cur.execute("DELETE FROM tasks")
    cur.execute("DELETE FROM shots")
    cur.execute("DELETE FROM assets")
    cur.execute("DELETE FROM shows")
    cur.execute("DELETE FROM config")

    # Config and current show
    cfg = data.get("config", {})
    for key, value in cfg.items():
        cur.execute("INSERT INTO config(key, value) VALUES(?, ?)", (key, str(value)))
    if data.get("current_show"):
        cur.execute(
            "INSERT INTO config(key, value) VALUES('current_show', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (data["current_show"],),
        )

    # Shows
    for show in data.get("shows", {}).values():
        cur.execute(
            "INSERT INTO shows(code, name, template, root, created_at, updated_at) VALUES(?,?,?,?,?,?)",
            (
                show.get("code"),
                show.get("name"),
                show.get("template"),
                show.get("root"),
                show.get("created_at"),
                show.get("updated_at"),
            ),
        )

    # Assets
    for asset in data.get("assets", {}).values():
        cur.execute(
            "INSERT INTO assets(id, show_code, type, name, status, path, tags, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                asset.get("id"),
                asset.get("show_code"),
                asset.get("type"),
                asset.get("name"),
                asset.get("status"),
                asset.get("path"),
                encode_tags(asset.get("tags", [])),
                asset.get("created_at"),
                asset.get("updated_at"),
            ),
        )

    # Shots
    for shot in data.get("shots", {}).values():
        cur.execute(
            "INSERT INTO shots(id, code, show_code, description, status, path, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                shot.get("id"),
                shot.get("code"),
                shot.get("show_code"),
                shot.get("description"),
                shot.get("status"),
                shot.get("path"),
                shot.get("created_at"),
                shot.get("updated_at"),
            ),
        )

    # Tasks
    for target_id, tasks in data.get("tasks", {}).items():
        for task in tasks:
            cur.execute(
                "INSERT INTO tasks(target_id, name, status, updated_at) VALUES(?,?,?,?)",
                (
                    target_id,
                    task.get("name"),
                    task.get("status"),
                    task.get("updated_at"),
                ),
            )

    # Versions
    for ver in data.get("versions", {}).values():
        cur.execute(
            "INSERT INTO versions(version_id, target_id, kind, show_code, tags, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
            (
                ver.get("version_id"),
                ver.get("target_id"),
                ver.get("kind"),
                ver.get("show_code"),
                encode_tags(ver.get("tags", [])),
                ver.get("created_at"),
                ver.get("updated_at"),
            ),
        )

    conn.commit()
