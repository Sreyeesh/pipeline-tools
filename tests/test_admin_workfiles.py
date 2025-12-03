from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

from pipeline_tools.core import db
from pipeline_tools.tools.admin import main as admin_main
from pipeline_tools.tools.workfiles import main as workfiles_main


def _with_temp_db(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(tmp_path / "db.sqlite3"))


def _seed_show(tmp_path: Path, code: str = "PKU") -> Path:
    show_root = tmp_path / f"AN_{code}_TestShow"
    (show_root / "01_ADMIN").mkdir(parents=True, exist_ok=True)
    data = {
        "shows": {
            code: {
                "code": code,
                "name": "TestShow",
                "template": "animation_short",
                "root": str(show_root),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        },
        "assets": {},
        "shots": {},
        "tasks": {},
        "versions": {},
        "config": {"current_show": code},
        "current_show": code,
    }
    db.save_db(data)
    return show_root


def test_admin_template_copies_animation_bible(monkeypatch, tmp_path):
    _with_temp_db(monkeypatch, tmp_path)
    show_root = _seed_show(tmp_path, "DMO")

    args = admin_main.parse_args(["template", "--template", "animation_bible"])
    admin_main.cmd_template(args)

    dest = show_root / "01_ADMIN" / "DMO_animation_bible.md"
    assert dest.exists()
    assert "Animation Bible" in dest.read_text() or dest.stat().st_size > 0


def test_workfiles_add_and_list(monkeypatch, tmp_path, capsys):
    _with_temp_db(monkeypatch, tmp_path)
    show_root = _seed_show(tmp_path, "PKU")

    args = workfiles_main.parse_args(["add", "PKU_CH_Poku_Main", "--kind", "krita"])
    workfiles_main.cmd_add(args)

    created = show_root / "05_WORK" / "assets" / "PKU_CH_Poku_Main" / "krita" / "PKU_CH_Poku_Main_krita_w001.kra"
    assert created.exists()

    args = workfiles_main.parse_args(["list", "--target-id", "PKU_CH_Poku_Main"])
    workfiles_main.cmd_list(args)
    out = capsys.readouterr().out
    assert "PKU_CH_Poku_Main_krita_w001.kra" in out


def test_workfiles_open_picks_latest(monkeypatch, tmp_path):
    _with_temp_db(monkeypatch, tmp_path)
    show_root = _seed_show(tmp_path, "PKU")
    base = show_root / "05_WORK" / "assets" / "PKU_CH_Poku_Main" / "krita"
    base.mkdir(parents=True, exist_ok=True)

    old = base / "PKU_CH_Poku_Main_krita_w001.kra"
    new = base / "PKU_CH_Poku_Main_krita_w002.kra"
    old.write_text("old")
    new.write_text("new")
    os.utime(new, None)

    opened = {}

    def fake_open(path, kind=None):
        opened["path"] = Path(path)
        opened["kind"] = kind

    monkeypatch.setattr(workfiles_main, "_open_workfile", fake_open)

    args = workfiles_main.parse_args(["open", "--target-id", "PKU_CH_Poku_Main", "--kind", "krita"])
    workfiles_main.cmd_open(args)

    assert opened["path"].name == "PKU_CH_Poku_Main_krita_w002.kra"
    assert opened["kind"] == "krita"


def test_admin_create_with_content(monkeypatch, tmp_path):
    _with_temp_db(monkeypatch, tmp_path)
    show_root = _seed_show(tmp_path, "PKU")

    args = admin_main.parse_args(["create", "--name", "PKU_animation_bible.md", "--content", "hello"])
    admin_main.cmd_create(args)

    dest = show_root / "01_ADMIN" / "PKU_animation_bible.md"
    assert dest.exists()
    assert dest.read_text().strip() == "hello"


def test_admin_files_open_fallback(monkeypatch, tmp_path, capsys):
    _with_temp_db(monkeypatch, tmp_path)
    show_root = _seed_show(tmp_path, "PKU")
    target = show_root / "01_ADMIN" / "PKU_animation_bible.md"
    target.write_text("hi")

    # Simulate xdg-open failure
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("xdg-open missing")
    monkeypatch.setattr(admin_main.subprocess, "run", fake_run)
    # Simulate webbrowser.open returning False
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda *_a, **_k: False)

    admin_main._open_file(target)
    out = capsys.readouterr().out
    assert "Open manually" in out
