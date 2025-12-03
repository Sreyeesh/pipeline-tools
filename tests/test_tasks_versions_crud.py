from __future__ import annotations

import os
from datetime import datetime

from pipeline_tools.core import db
from pipeline_tools.tools import tasks, versions


def _with_temp_db(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    os.environ["PIPELINE_TOOLS_DB"] = str(db_path)
    return db_path


def test_tasks_delete_removes_task(monkeypatch, tmp_path):
    _with_temp_db(tmp_path)
    now = datetime.utcnow().isoformat()
    data = {
        "shows": {},
        "assets": {"DMO_CH_Hero": {"id": "DMO_CH_Hero"}},
        "shots": {},
        "tasks": {"DMO_CH_Hero": [{"name": "Layout", "status": "not_started", "updated_at": now}]},
        "versions": {},
        "config": {"current_show": "DMO"},
        "current_show": "DMO",
    }
    db.save_db(data)

    args = tasks.parse_args(["delete", "DMO_CH_Hero", "Layout"])
    tasks.cmd_delete(args)

    saved = db.load_db()
    assert "DMO_CH_Hero" not in saved.get("tasks", {})


def test_versions_delete_removes_entry(tmp_path):
    _with_temp_db(tmp_path)
    now = datetime.utcnow().isoformat()
    data = {
        "shows": {},
        "assets": {},
        "shots": {"DMO_SH010": {"id": "DMO_SH010", "show_code": "DMO"}},
        "tasks": {},
        "versions": {
            "DMO_SH010_anim_v001": {
                "version_id": "DMO_SH010_anim_v001",
                "target_id": "DMO_SH010",
                "kind": "anim",
                "show_code": "DMO",
                "tags": [],
                "created_at": now,
                "updated_at": now,
            }
        },
        "config": {"current_show": "DMO"},
        "current_show": "DMO",
    }
    db.save_db(data)

    args = versions.parse_args(["delete", "DMO_SH010_anim_v001"])
    versions.cmd_delete(args)

    saved = db.load_db()
    assert "DMO_SH010_anim_v001" not in saved.get("versions", {})
