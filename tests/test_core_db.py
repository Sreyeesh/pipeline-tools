from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from pipeline_tools.core import db


def test_encode_decode_tags_round_trip():
    tags = ["hero", "main", "v1"]
    encoded = db.encode_tags(tags)
    assert isinstance(encoded, str)
    decoded = db.decode_tags(encoded)
    assert decoded == tags


def test_decode_tags_handles_bad_json():
    assert db.decode_tags("not-json") == []
    assert db.decode_tags(None) == []


def test_get_conn_creates_tables(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}

    expected = {"config", "shows", "assets", "shots", "tasks", "versions"}
    assert expected.issubset(tables)


def test_load_save_round_trip(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))

    # Save data
    data = {
        "config": {"current_show": "DMO"},
        "current_show": "DMO",
        "shows": {
            "DMO": {
                "code": "DMO",
                "name": "Demo",
                "template": "animation_short",
                "root": "/tmp/AN_DMO_Demo",
                "created_at": "t1",
                "updated_at": "t1",
            }
        },
        "assets": {},
        "shots": {},
        "tasks": {},
        "versions": {},
    }
    db.save_db(data, db_path)

    loaded = db.load_db(db_path)
    assert loaded["shows"]["DMO"]["name"] == "Demo"
    assert loaded["current_show"] == "DMO"
