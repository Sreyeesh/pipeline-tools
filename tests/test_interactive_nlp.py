import os
from pathlib import Path

import pytest

from pipeline_tools.core import db
from pipeline_tools.interactive import (
    PASSTHROUGH_CMDS,
    _ensure_task_for_asset,
    _find_asset,
    _interpret_natural_command,
    _split_user_commands,
)


@pytest.fixture()
def temp_db(monkeypatch, tmp_path):
    """Create an isolated DB with a sample show/asset."""
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))

    data = {
        "shows": {
            "PKU": {
                "code": "PKU",
                "name": "Test Show",
                "template": "animation_short",
                "root": "/tmp/AN_PKU_TestShow",
                "created_at": "now",
                "updated_at": "now",
            }
        },
        "assets": {
            "PKU_ENV_BG_Forest": {
                "id": "PKU_ENV_BG_Forest",
                "show_code": "PKU",
                "type": "ENV",
                "name": "BG_Forest",
                "status": "design",
                "path": "/tmp/AN_PKU_TestShow/03_ASSETS/environments/BG_Forest",
                "tags": [],
                "created_at": "now",
                "updated_at": "now",
            }
        },
        "shots": {},
        "tasks": {},
        "versions": {},
        "asset_tasks": {},
        "playlists": {},
        "notes": [],
        "config": {"current_show": "PKU"},
    }
    db.save_db(data, db_path=db_path)
    yield db_path


def test_split_keeps_open_project_phrase():
    cmds = _split_user_commands("open project 1 with krita", PASSTHROUGH_CMDS)
    assert cmds == ["open project 1 with krita"]


def test_split_keeps_list_phrase():
    cmds = _split_user_commands("list assets for show PKU", PASSTHROUGH_CMDS)
    assert cmds == ["list assets for show PKU"]


def test_interpret_add_asset():
    args, _ = _interpret_natural_command("add environment asset called BG_Forest for show PKU")
    assert args == ["assets", "add", "-t", "ENV", "-n", "BG_Forest", "-c", "PKU"]


def test_interpret_task_intents():
    args, _ = _interpret_natural_command("add task Paint for PKU_ENV_BG_Forest")
    assert args == ["tasks", "add", "PKU_ENV_BG_Forest", "Paint"]

    args, _ = _interpret_natural_command("list tasks for PKU_ENV_BG_Forest")
    assert args == ["tasks", "list", "PKU_ENV_BG_Forest"]

    args, _ = _interpret_natural_command("mark task Paint for PKU_ENV_BG_Forest done")
    assert args == ["tasks", "status", "PKU_ENV_BG_Forest", "Paint", "done"]


def test_find_asset_and_ensure_task(temp_db):
    # Finds by partial match
    result = _find_asset("BG_Forest")
    assert result and result[0] == "PKU_ENV_BG_Forest"

    # Adds/updates task in isolated DB
    _ensure_task_for_asset("PKU_ENV_BG_Forest", "Paint", status="in_progress")
    data = db.load_db(db_path=temp_db)
    tasks = data.get("tasks", {}).get("PKU_ENV_BG_Forest", [])
    assert tasks and tasks[0]["name"] == "Paint" and tasks[0]["status"] == "in_progress"
