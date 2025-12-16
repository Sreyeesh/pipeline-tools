import os
from pathlib import Path

from pipeline_tools.core import db
from pipeline_tools.core import paths
from pipeline_tools.core.fs_utils import create_folders
from pipeline_tools.tools.project_creator import main as pc_main
from pipeline_tools.tools.project_creator import templates
from pipeline_tools.tools.character_thumbnails import main as ct_main
from pipeline_tools.tools.shows import main as show_main
from pipeline_tools.tools.assets import main as asset_main
from pipeline_tools.tools.shots import main as shot_main
from pipeline_tools.tools.tasks import main as task_main
from pipeline_tools.tools.versions import main as version_main


def test_make_show_root_uses_creative_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    result = paths.make_show_root("dmo", "Demo Short 30s")

    assert result == tmp_path / "AN_DMO_DemoShort30s"


def test_make_show_root_uses_template_prefix(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    result = paths.make_show_root("dmo", "Game Name", template_key="game_dev_small")

    assert result == tmp_path / "GD_DMO_GameName"


def test_create_folders_makes_structure(tmp_path: Path) -> None:
    rel_paths = ["a", "b/c", "d/e/f"]

    create_folders(tmp_path, rel_paths)

    for rel in rel_paths:
        assert (tmp_path / rel).is_dir()


def test_cli_happy_path_creates_template(monkeypatch, tmp_path: Path, capsys) -> None:
    # Point CLI to a temp creative root to avoid touching real paths.
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)
    monkeypatch.setattr(
        pc_main, "make_show_root", paths.make_show_root
    )  # ensure it picks up patched CREATIVE_ROOT
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))

    argv = ["project_creator", "-c", "DMO", "-n", "Demo Short 30s"]
    monkeypatch.setattr(pc_main.sys, "argv", argv)

    pc_main.main()
    out = capsys.readouterr().out
    show_root = tmp_path / "AN_DMO_DemoShort30s"

    assert "Creating project at" in out
    assert show_root.exists()
    for rel in templates.ANIMATION_SHORT_TEMPLATE:
        assert (show_root / rel).is_dir()


def test_character_thumbnails_default_assets(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)
    monkeypatch.setattr(ct_main.paths, "CREATIVE_ROOT", tmp_path)

    argv = [
        "character_thumbnails",
        "-c",
        "DMO",
        "-n",
        "Demo Short 30s",
        "--character",
        "courierA",
    ]
    monkeypatch.setattr(ct_main.sys, "argv", argv)

    ct_main.main()
    out = capsys.readouterr().out

    target = tmp_path / "AN_DMO_DemoShort30s/03_ASSETS/characters/courierA/thumbnails"

    assert "Creating character thumbnails folder" in out
    assert target.is_dir()


def test_character_thumbnails_prepro(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)
    monkeypatch.setattr(ct_main.paths, "CREATIVE_ROOT", tmp_path)

    argv = [
        "character_thumbnails",
        "-c",
        "DMO",
        "-n",
        "Demo Short 30s",
        "--character",
        "courierB",
        "-l",
        "prepro",
    ]
    monkeypatch.setattr(ct_main.sys, "argv", argv)

    ct_main.main()

    target = tmp_path / "AN_DMO_DemoShort30s/02_PREPRO/designs/characters/courierB/thumbnails"
    assert target.is_dir()


def test_show_create_registers_in_db(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    argv = ["shows", "create", "-c", "DMO", "-n", "Demo Short 30s"]
    monkeypatch.setattr(show_main.sys, "argv", argv)

    show_main.main()

    data = db.load_db(db_path)
    assert data["shows"]["DMO"]["name"] == "Demo Short 30s"
    assert data["current_show"] == "DMO"
    assert (tmp_path / "AN_DMO_DemoShort30s").exists()


def test_asset_add_creates_folder_and_db(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    # Create show first
    monkeypatch.setattr(show_main.sys, "argv", ["shows", "create", "-c", "DMO", "-n", "Demo Short 30s"])
    show_main.main()

    # Add asset
    monkeypatch.setattr(asset_main.sys, "argv", ["assets", "add", "-t", "CH", "-n", "Hero"])
    asset_main.main()

    data = db.load_db(db_path)
    asset = data["assets"]["DMO_CH_Hero"]
    assert asset["status"] == "design"

    target = tmp_path / "AN_DMO_DemoShort30s/03_ASSETS/characters/Hero"
    assert target.is_dir()
    assert (target / "workfiles").is_dir()
    assert (target / "renders").is_dir()

    # Update status
    monkeypatch.setattr(asset_main.sys, "argv", ["assets", "status", "DMO_CH_Hero", "done"])
    asset_main.main()
    data = db.load_db(db_path)
    assert data["assets"]["DMO_CH_Hero"]["status"] == "done"


def test_asset_tag_and_find(monkeypatch, tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)
    # Create show and asset
    monkeypatch.setattr(show_main.sys, "argv", ["shows", "create", "-c", "DMO", "-n", "Demo Short 30s"])
    show_main.main()
    monkeypatch.setattr(asset_main.sys, "argv", ["assets", "add", "-t", "CH", "-n", "Hero"])
    asset_main.main()

    monkeypatch.setattr(asset_main.sys, "argv", ["assets", "tag", "DMO_CH_Hero", "hero"])
    asset_main.main()

    monkeypatch.setattr(asset_main.sys, "argv", ["assets", "find", "--tag", "hero"])
    asset_main.main()
    out = capsys.readouterr().out
    assert "DMO_CH_Hero" in out


def test_shot_and_version_and_task(monkeypatch, tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "db.sqlite3"
    monkeypatch.setenv("PIPELINE_TOOLS_DB", str(db_path))
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    monkeypatch.setattr(show_main.sys, "argv", ["shows", "create", "-c", "DMO", "-n", "Demo Short 30s"])
    show_main.main()

    monkeypatch.setattr(shot_main.sys, "argv", ["shots", "add", "SH010", "Test shot"])
    shot_main.main()

    monkeypatch.setattr(task_main.sys, "argv", ["tasks", "add", "DMO_SH010", "Layout"])
    task_main.main()
    monkeypatch.setattr(task_main.sys, "argv", ["tasks", "status", "DMO_SH010", "Layout", "in_progress"])
    task_main.main()
    out = capsys.readouterr().out
    assert "in_progress" in out

    monkeypatch.setattr(version_main.sys, "argv", ["versions", "new", "DMO_SH010", "anim"])
    version_main.main()
    monkeypatch.setattr(version_main.sys, "argv", ["versions", "latest", "--shot", "DMO_SH010", "--kind", "anim"])
    version_main.main()
    out = capsys.readouterr().out
    assert "DMO_SH010_anim_v001" in out
