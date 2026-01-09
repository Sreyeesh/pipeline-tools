from __future__ import annotations

from pathlib import Path

from pipeline_tools import cli


def test_cli_imports_from_local_src() -> None:
    cli_path = Path(cli.__file__).resolve()
    assert "pipeline-tools" in cli_path.parts
    assert "src" in cli_path.parts
