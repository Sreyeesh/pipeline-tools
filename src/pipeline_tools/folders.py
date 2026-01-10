from __future__ import annotations

from pathlib import Path

from pipeline_tools.os_utils import sanitize_folder_name

SHOT_SUBFOLDERS: dict[str, tuple[str, ...]] = {
    "animation": ("plates", "layout", "anim", "fx", "lighting", "comp", "renders"),
    "game": ("blockout", "lighting", "setdress", "gameplay", "fx", "build"),
}

ASSET_SUBFOLDERS: dict[str, tuple[str, ...]] = {
    "animation": ("model", "rig", "surfacing", "textures", "lookdev", "publish"),
    "game": ("model", "rig", "textures", "materials", "prefab", "export"),
    "art": ("refs", "wip", "final"),
}


def _safe_folder(name: str, fallback: str) -> str:
    return sanitize_folder_name(name, fallback=fallback)


def ensure_shot_folders(project_path: Path, project_type: str, shot_code: str) -> Path | None:
    if project_type not in SHOT_SUBFOLDERS:
        return None
    shot_root = project_path / "04_SHOTS" / _safe_folder(shot_code, fallback="SHOT")
    shot_root.mkdir(parents=True, exist_ok=True)
    for folder in SHOT_SUBFOLDERS[project_type]:
        (shot_root / folder).mkdir(parents=True, exist_ok=True)
    return shot_root


def ensure_asset_folders(
    project_path: Path,
    project_type: str,
    asset_type: str,
    asset_name: str,
) -> Path | None:
    subfolders = ASSET_SUBFOLDERS.get(project_type)
    if not subfolders:
        return None
    asset_root: Path
    if project_type == "art":
        asset_root = project_path / "02_WIP" / _safe_folder(asset_name, fallback="asset")
    else:
        asset_root = (
            project_path
            / "03_ASSETS"
            / _safe_folder(asset_type, fallback="asset")
            / _safe_folder(asset_name, fallback="asset")
        )
    asset_root.mkdir(parents=True, exist_ok=True)
    for folder in subfolders:
        (asset_root / folder).mkdir(parents=True, exist_ok=True)
    return asset_root
