"""DCC Launcher - Launch applications with project context."""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, List

# DCC executable paths by platform
DCC_PATHS = {
    "krita": {
        "Linux": [
            "/usr/bin/krita",
            "/usr/local/bin/krita",
            "krita",  # Try PATH
        ],
        "Windows": [
            r"C:/Program Files/Krita (x64)/bin/krita.exe",
            r"C:/Program Files/Krita/bin/krita.exe",
            r"C:\Program Files\Krita (x64)\bin\krita.exe",
            r"C:\Program Files\Krita\bin\krita.exe",
            "krita.exe",  # Try PATH
        ],
        "Darwin": [  # macOS
            "/Applications/krita.app/Contents/MacOS/krita",
            "krita",
        ],
    },
    "blender": {
        "Linux": [
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "blender",
        ],
        "Windows": [
            r"C:/Program Files/Blender Foundation/Blender 5.0/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 4.3/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 4.2/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender 3.6/blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            "blender.exe",
        ],
        "Darwin": [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "blender",
        ],
    },
    "photoshop": {
        "Windows": [
            r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
            r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
        ],
        "Darwin": [
            "/Applications/Adobe Photoshop 2024/Adobe Photoshop 2024.app/Contents/MacOS/Adobe Photoshop 2024",
        ],
    },
    "aftereffects": {
        "Windows": [
            r"C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\AfterFX.exe",
            r"C:\Program Files\Adobe\Adobe After Effects 2023\Support Files\AfterFX.exe",
        ],
        "Darwin": [
            "/Applications/Adobe After Effects 2024/Adobe After Effects 2024.app/Contents/MacOS/After Effects",
        ],
    },
}


def get_dcc_executable(dcc_name: str) -> Optional[str]:
    """
    Find the DCC executable path for the current platform.

    Args:
        dcc_name: Name of the DCC (krita, blender, photoshop, etc.)

    Returns:
        Path to executable if found, None otherwise
    """
    system = platform.system()
    dcc_name_lower = dcc_name.lower()

    if dcc_name_lower not in DCC_PATHS:
        return None

    paths = DCC_PATHS[dcc_name_lower].get(system, [])

    # On WSL, also check Windows paths
    if system == "Linux" and os.path.exists("/mnt/c"):
        # We're on WSL, add Windows paths too
        windows_paths = DCC_PATHS[dcc_name_lower].get("Windows", [])
        # Convert Windows paths to WSL paths
        wsl_paths = []
        for win_path in windows_paths:
            # Convert C:\... or C:/... to /mnt/c/...
            if win_path.startswith("C:\\") or win_path.startswith("C:/"):
                wsl_path = win_path.replace("C:\\", "/mnt/c/").replace("C:/", "/mnt/c/")
                wsl_path = wsl_path.replace("\\", "/")
                wsl_paths.append(wsl_path)
        paths = paths + wsl_paths

    # Try each path
    for path in paths:
        # Check if it's an absolute path that exists
        if os.path.isabs(path) and os.path.exists(path):
            return path

        # Try to find in PATH
        try:
            # Use 'where' on Windows, 'which' on Unix
            cmd = "where" if system == "Windows" else "which"
            result = subprocess.run(
                [cmd, path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                found_path = result.stdout.strip().split('\n')[0]
                if found_path:
                    return found_path
        except Exception:
            continue

    return None


def launch_dcc(
    dcc_name: str,
    file_path: Optional[str] = None,
    project_root: Optional[str] = None,
    background: bool = False,
    additional_args: Optional[List[str]] = None
) -> subprocess.Popen:
    """
    Launch a DCC application.

    Args:
        dcc_name: Name of the DCC (krita, blender, etc.)
        file_path: Optional file to open
        project_root: Optional project root directory to set as working directory
        background: If True, launch in background and return immediately
        additional_args: Additional command line arguments

    Returns:
        Popen object

    Raises:
        FileNotFoundError: If DCC executable not found
        ValueError: If file_path provided but doesn't exist
    """
    # Find executable
    executable = get_dcc_executable(dcc_name)
    if not executable:
        raise FileNotFoundError(
            f"Could not find {dcc_name} executable. "
            f"Please ensure {dcc_name} is installed."
        )

    # Build command
    cmd = [executable]

    # Check if we're on WSL launching a Windows app
    is_wsl_to_windows = (
        platform.system() == "Linux" and
        os.path.exists("/mnt/c") and
        executable.startswith("/mnt/c")
    )

    # Note: File path handling disabled - just open the DCC without files
    # Users can open files from within the application
    # if file_path:
    #     ... (code removed to prevent automatic file opening)

    # Add additional arguments
    if additional_args:
        cmd.extend(additional_args)

    # Set working directory
    # Note: On WSL launching Windows apps, we can't set cwd to a Windows path
    # so we skip it and rely on absolute file paths
    cwd = None
    if project_root and not is_wsl_to_windows:
        cwd = str(Path(project_root).absolute())

    # Launch
    if background:
        # Launch in background, detach from terminal
        if platform.system() == "Windows":
            # On Windows, use CREATE_NEW_PROCESS_GROUP and DETACHED_PROCESS
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # On Unix, use nohup-like behavior
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    else:
        # Launch and wait
        process = subprocess.Popen(cmd, cwd=cwd)

    return process
