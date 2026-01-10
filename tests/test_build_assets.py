from __future__ import annotations

from pathlib import Path


def test_pyinstaller_spec_exists() -> None:
    spec_path = Path("build/pyinstaller/pipely.spec")
    assert spec_path.exists()
    contents = spec_path.read_text(encoding="utf-8")
    assert "__main__.py" in contents or "cli.py" in contents
