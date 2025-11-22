from pathlib import Path
from typing import Iterable


def create_folders(base: Path, rel_paths: Iterable[str]) -> None:
    """
    Given a base path and a list of relative folder paths, create them all.

    Example:
        base = Path("/mnt/c/Projects/AN_PKS_PokuShort30s")
        rel_paths = ["01_ADMIN", "02_PREPRO/script", ...]
    """
    for rel in rel_paths:
        target = base / rel
        target.mkdir(parents=True, exist_ok=True)
