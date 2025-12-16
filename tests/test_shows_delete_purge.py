from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from pipeline_tools.core import db
from pipeline_tools.tools.shows import main as shows_main


def _with_temp_db(tmp_path: Path) -> None:
    os.environ["PIPELINE_TOOLS_DB"] = str(tmp_path / "db.sqlite3")


def test_delete_show_removes_db_and_folder(tmp_path):
    _with_temp_db(tmp_path)
    now = datetime.utcnow().isoformat()
    show_root = tmp_path / "AN_PKU_TestShow"
    show_root.mkdir(parents=True, exist_ok=True)

    data = {
        "shows": {
            "PKU": {
                "code": "PKU",
                "name": "TestShow",
                "template": "animation_short",
                "root": str(show_root),
                "created_at": now,
                "updated_at": now,
            }
        },
        "assets": {"PKU_CH_Test": {"id": "PKU_CH_Test", "show_code": "PKU"}},
        "shots": {"PKU_SH010": {"id": "PKU_SH010", "show_code": "PKU"}},
        "tasks": {"PKU_SH010": [{"name": "Layout", "status": "not_started", "updated_at": now}]},
        "versions": {
            "PKU_SH010_anim_v001": {
                "version_id": "PKU_SH010_anim_v001",
                "target_id": "PKU_SH010",
                "kind": "anim",
                "show_code": "PKU",
                "tags": [],
                "created_at": now,
                "updated_at": now,
            }
        },
        "config": {"current_show": "PKU"},
        "current_show": "PKU",
    }
    db.save_db(data)

    args = shows_main.parse_args(["delete", "-c", "PKU", "--delete-folders"])
    shows_main.cmd_delete(args)

    saved = db.load_db()
    assert "PKU" not in saved["shows"]
    assert saved.get("current_show") is None
    assert not show_root.exists()
    assert all(k.startswith("PKU_") is False for k in saved.get("assets", {}))
    assert all(k.startswith("PKU_") is False for k in saved.get("shots", {}))
    assert "PKU_SH010" not in saved.get("tasks", {})
    assert all(v.get("show_code") != "PKU" for v in saved.get("versions", {}).values())


def test_delete_show_removes_secondary_creative_root(tmp_path, monkeypatch):
    _with_temp_db(tmp_path)
    now = datetime.utcnow().isoformat()
    db_root = tmp_path / "temp_storage" / "AN_PKU_TestShow"
    db_root.mkdir(parents=True, exist_ok=True)

    creative_root = tmp_path / "artist_root"
    creative_root.mkdir()
    duplicate_folder = creative_root / "AN_PKU_TestShow"
    duplicate_folder.mkdir()

    data = {
        "shows": {
            "PKU": {
                "code": "PKU",
                "name": "TestShow",
                "template": "animation_short",
                "root": str(db_root),
                "created_at": now,
                "updated_at": now,
            }
        },
        "assets": {},
        "shots": {},
        "tasks": {},
        "versions": {},
        "current_show": "PKU",
    }
    db.save_db(data)

    monkeypatch.setenv("PIPELINE_TOOLS_ROOT", str(creative_root))

    args = shows_main.parse_args(["delete", "-c", "PKU", "--delete-folders"])
    shows_main.cmd_delete(args)

    assert not db_root.exists()
    assert not duplicate_folder.exists()
