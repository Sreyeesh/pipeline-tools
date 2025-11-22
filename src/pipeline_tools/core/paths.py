from pathlib import Path

# Root where your creative projects live on Windows.
# In WSL, C:\Projects is mounted at /mnt/c/Projects
CREATIVE_ROOT = Path("/mnt/c/Projects")


def make_show_root(show_code: str, project_name: str) -> Path:
    """
    Build a show root folder name like:
    AN_PKS_PokuShort30s  under CREATIVE_ROOT.

    - show_code: short code like "PKS"
    - project_name: e.g. "Poku Short 30s"
    """
    safe_name = project_name.replace(" ", "")
    folder_name = f"AN_{show_code.upper()}_{safe_name}"
    return CREATIVE_ROOT / folder_name
