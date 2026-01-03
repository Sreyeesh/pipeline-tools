from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipeline_tools import cli

runner = CliRunner()


def test_loop_create_version_and_deliver(tmp_path: Path) -> None:
    root = tmp_path / "projects"

    result = runner.invoke(
        cli.app,
        [
            "loop",
            "create",
            "--project",
            "DemoReel",
            "--target",
            "Hero",
            "--task",
            "sculpt",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0

    task_root = root / "DemoReel" / "Hero" / "sculpt"
    work_file = task_root / "work" / "current.obj"
    work_file.write_text("mesh", encoding="utf-8")

    version_result = runner.invoke(
        cli.app,
        [
            "loop",
            "version",
            "--task",
            "DemoReel/Hero/sculpt",
            "--root",
            str(root),
            "--description",
            "first pass",
            "--source",
            str(work_file),
        ],
    )
    assert version_result.exit_code == 0
    versions = list((task_root / "versions").glob("*.obj"))
    assert versions

    deliver_result = runner.invoke(
        cli.app,
        [
            "loop",
            "deliver",
            "--task",
            "DemoReel/Hero/sculpt",
            "--root",
            str(root),
            "--target",
            "dailies",
        ],
        input="1\n",
    )
    assert deliver_result.exit_code == 0
    deliveries = list((task_root / "deliveries").glob("delivery_*"))
    assert deliveries
