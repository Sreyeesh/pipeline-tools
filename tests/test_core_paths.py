from __future__ import annotations

from pathlib import Path

from pipeline_tools.core import paths
from pipeline_tools.core import db


def test_get_creative_root_prefers_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PIPELINE_TOOLS_ROOT", str(tmp_path))
    result = paths.get_creative_root()
    assert result == tmp_path


def test_get_creative_root_reads_db(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("PIPELINE_TOOLS_ROOT", raising=False)
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))
    conn = db.get_conn(db_path)
    db.set_config(conn, "creative_root", str(tmp_path / "custom"))

    result = paths.get_creative_root()
    assert result == tmp_path / "custom"


def test_make_show_root_uses_prefix(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)
    root = paths.make_show_root("dmo", "Game Name", template_key="game_dev_small")
    assert root.name == "GD_DMO_GameName"
    assert root.parent == tmp_path
