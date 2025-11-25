import os
from pathlib import Path
from typing import Optional

"""
Creative root handling:
- Env override: PIPELINE_TOOLS_ROOT
- Config override (DB key: creative_root)
- Platform defaults:
  * WSL: /mnt/c/Projects
  * Windows: C:/Projects
  * macOS/Linux: ~/Projects
"""


def _is_wsl() -> bool:
    try:
        with open("/proc/version", "r", encoding="utf-8") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def _default_creative_root() -> Path:
    if _is_wsl():
        return Path("/mnt/c/Projects")
    if os.name == "nt":
        return Path("C:/Projects")
    return Path.home() / "Projects"


_CREATIVE_ROOT_DEFAULT = _default_creative_root()

# Backward-compatible global; value is still used as a fallback.
CREATIVE_ROOT = _CREATIVE_ROOT_DEFAULT
_PREFIX_BY_TEMPLATE = {
    "animation_short": "AN",
    "game_dev_small": "GD",
    "drawing_single": "DR",
}


def get_creative_root() -> Path:
    env_root = os.environ.get("PIPELINE_TOOLS_ROOT")
    if env_root:
        return Path(env_root)
    try:
        # Lazy import to avoid cycles for core utilities.
        from pipeline_tools.core import db

        conn = db.get_conn()
        cfg_root: Optional[str] = db.get_config(conn, "creative_root")
        if cfg_root:
            return Path(cfg_root)
    except Exception:
        # If config cannot be read, keep going with defaults.
        pass
    if CREATIVE_ROOT:
        return Path(CREATIVE_ROOT)
    return _CREATIVE_ROOT_DEFAULT


def make_show_root(
    show_code: str,
    project_name: str,
    template_key: Optional[str] = None,
    creative_root: Path | None = None,
) -> Path:
    """
    Build a show root folder name like:
    AN_DMO_DemoShort30s  under the resolved creative root.

    - show_code: short code like "DMO"
    - project_name: e.g. "Demo Short 30s"
    - template_key: optional template key to derive a prefix (defaults to animation prefix)
    - creative_root: optional override Path
    """
    safe_name = project_name.replace(" ", "")
    prefix = _PREFIX_BY_TEMPLATE.get(template_key or "animation_short", "AN")
    folder_name = f"{prefix}_{show_code.upper()}_{safe_name}"
    root = Path(creative_root) if creative_root else get_creative_root()
    return root / folder_name
