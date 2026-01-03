from __future__ import annotations

import os
import platform
import re
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path


class OperatingSystem(Enum):
    WINDOWS = auto()
    MAC = auto()
    LINUX = auto()


WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

DEFAULT_ROOT_ENV = "PIPELY_ROOT"


def _detect_os(system_name: str) -> OperatingSystem:
    name = system_name.lower()
    if "windows" in name:
        return OperatingSystem.WINDOWS
    if "darwin" in name or "mac" in name:
        return OperatingSystem.MAC
    return OperatingSystem.LINUX


@lru_cache(maxsize=1)
def current_os() -> OperatingSystem:
    """Return the current operating system (cached)."""
    return _detect_os(platform.system())


def reset_os_cache() -> None:
    """Testing helper to reset cached OS detection."""
    current_os.cache_clear()


def default_projects_root() -> Path:
    """Pick a sensible default projects root per OS."""
    env_override = os.environ.get(DEFAULT_ROOT_ENV)
    if env_override:
        return Path(env_override).expanduser()

    os_type = current_os()
    if os_type == OperatingSystem.WINDOWS:
        # Prefer WSL-style mount if present, fallback to Documents/Projects then home Projects.
        for candidate in (
            Path("/mnt/c/Projects"),
            Path.home() / "Documents" / "Projects",
            Path.home() / "Projects",
        ):
            if candidate.exists():
                return candidate
        return Path.home() / "Projects"

    # macOS/Linux default to ~/Projects if it exists, else cwd.
    home_projects = Path.home() / "Projects"
    if home_projects.exists():
        return home_projects
    return Path.cwd()


def sanitize_folder_name(value: str, fallback: str = "project") -> str:
    """Normalize folder names and avoid reserved names on Windows."""
    value = (value or "").strip()
    value = value.replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9._-]", "", value)
    value = value or fallback

    if current_os() == OperatingSystem.WINDOWS:
        trimmed = value.rstrip(" .")
        value = trimmed or fallback
        upper = value.upper()
        if upper in WINDOWS_RESERVED_NAMES:
            value = f"{value}_"
    return value


def resolve_root(root: Path | None) -> Path:
    """Resolve a user-provided root or fall back to the default per OS."""
    if root:
        return Path(root).expanduser()
    return default_projects_root()
