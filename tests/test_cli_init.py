from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_init_animation_creates_template(tmp_path: Path) -> None:
    result = runner.invoke(
        cli.app,
        [
            "init",
            "--name",
            "Demo Reel",
            "--type",
            "animation",
            "--root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0

    project_dir = tmp_path / "Demo_Reel"
    assert project_dir.exists()
    expected = ["01_ADMIN", "02_PREPRO", "03_ASSETS", "04_SHOTS", "05_WORK", "06_DELIVERY", "z_TEMP"]
    for rel in expected:
        assert (project_dir / rel).is_dir()


def test_init_prompts_for_missing_values(tmp_path: Path) -> None:
    result = runner.invoke(
        cli.app,
        [
            "init",
            "--root",
            str(tmp_path),
        ],
        input="Gallery Piece\nart\n",
    )
    assert result.exit_code == 0

    project_dir = tmp_path / "Gallery_Piece"
    assert project_dir.exists()
    art_dirs = ["01_REFERENCE", "02_WIP", "03_EXPORTS", "04_DELIVERY", "z_TEMP"]
    for rel in art_dirs:
        assert (project_dir / rel).is_dir()
