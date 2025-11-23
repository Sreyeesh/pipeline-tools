from pathlib import Path

from pipeline_tools.core import paths
from pipeline_tools.core.fs_utils import create_folders
from pipeline_tools.tools.project_creator import main as pc_main
from pipeline_tools.tools.project_creator import templates


def test_make_show_root_uses_creative_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths, "CREATIVE_ROOT", tmp_path)

    result = paths.make_show_root("pks", "Poku Short 30s")

    assert result == tmp_path / "AN_PKS_PokuShort30s"


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

    argv = ["project_creator", "-c", "PKS", "-n", "Poku Short 30s"]
    monkeypatch.setattr(pc_main.sys, "argv", argv)

    pc_main.main()
    out = capsys.readouterr().out
    show_root = tmp_path / "AN_PKS_PokuShort30s"

    assert "Creating project at" in out
    assert show_root.exists()
    for rel in templates.ANIMATION_SHORT_TEMPLATE:
        assert (show_root / rel).is_dir()
