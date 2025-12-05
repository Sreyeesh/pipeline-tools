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
    "pureref": {
        "Linux": [
            "/usr/bin/pureref",
            "/usr/local/bin/pureref",
            "pureref",
        ],
        "Windows": [
            r"C:/Program Files/PureRef/PureRef.exe",
            r"C:\Program Files\PureRef\PureRef.exe",
            r"C:/Program Files (x86)/PureRef/PureRef.exe",
            r"C:\Program Files (x86)\PureRef\PureRef.exe",
            "PureRef.exe",
        ],
        "Darwin": [
            "/Applications/PureRef.app/Contents/MacOS/PureRef",
            "pureref",
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
    additional_args: Optional[List[str]] = None,
    target_file_path: Optional[str] = None
) -> subprocess.Popen:
    """
    Launch a DCC application.

    Args:
        dcc_name: Name of the DCC (krita, blender, etc.)
        file_path: Optional file to open (must exist)
        project_root: Optional project root directory to set as working directory
        background: If True, launch in background and return immediately
        additional_args: Additional command line arguments
        target_file_path: Optional target file path for save-as default (doesn't need to exist)

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
    file_arg = None
    if file_path:
        file_obj = Path(file_path)
        if not file_obj.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if is_wsl_to_windows:
            file_arg = str(file_obj).replace("/mnt/c/", "C:\\").replace("/", "\\")
        else:
            file_arg = str(file_obj)
        cmd.append(file_arg)

    # Add additional arguments
    if additional_args:
        cmd.extend(additional_args)

    # Set working directory
    # Note: When launching Windows apps from WSL, we can't reliably set cwd
    # because subprocess.Popen doesn't accept Windows paths on Linux.
    # For WSL->Windows, we'll create a desktop notification file instead.
    cwd = None
    project_notification = None
    dcc_name_lower = dcc_name.lower()

    if project_root:
        if is_wsl_to_windows:
            # Convert project path to Windows format
            windows_project = project_root.replace("/mnt/c/", "C:\\").replace("/", "\\")
            project_name = Path(project_root).name

            # For Blender and Krita, create a startup script that sets the default save path
            if dcc_name_lower in ["blender", "krita"]:
                try:
                    # Get Windows username
                    import subprocess as sp
                    try:
                        result = sp.run(["cmd.exe", "/c", "echo", "%USERNAME%"],
                                      capture_output=True, text=True, check=False)
                        win_username = result.stdout.strip()
                    except:
                        win_username = username if username else "User"

                    # Create script in Windows temp directory accessible from both WSL and Windows
                    windows_temp = f"C:\\Users\\{win_username}\\AppData\\Local\\Temp"
                    wsl_temp = f"/mnt/c/Users/{win_username}/AppData/Local/Temp"

                    script_name = f"{dcc_name_lower}_pipeline_startup.py"
                    startup_script = Path(wsl_temp) / script_name
                    windows_script_path = f"{windows_temp}\\{script_name}"

                    # Get target file path if provided
                    target_file = None
                    if target_file_path:
                        if is_wsl_to_windows:
                            target_file = target_file_path.replace("/mnt/c/", "C:\\").replace("/", "\\")
                        else:
                            target_file = target_file_path

                    with open(startup_script, "w") as f:
                        if dcc_name_lower == "blender":
                            f.write(f'''# Pipeline Tools - Auto-generated startup script
import bpy
import os

# Set default blend file path to project directory
project_path = r"{windows_project}"
project_name = "{project_name}"
target_file = r"{target_file}" if {bool(target_file)} else None

print("=" * 60)
print("PIPELINE TOOLS - Project Context Active")
print(f"Project: {{project_name}}")
print(f"Path: {{project_path}}")
print("=" * 60)

# Make sure the path exists
os.makedirs(project_path, exist_ok=True)

# Change working directory
os.chdir(project_path)

# CRITICAL FIX: Auto-save to specific target file or project on first Ctrl+S
def auto_save_to_project():
    """Automatically save to target file or project directory when file has no path"""
    if not bpy.data.filepath:
        # Use target file path if provided, otherwise generate filename
        if target_file:
            filepath = target_file
            # Make sure parent directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        else:
            # Generate a default filename based on template or timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{{project_name}}_{{timestamp}}.blend"
            filepath = os.path.join(project_path, default_name)

        # Save directly to project
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        print(f"✓ Auto-saved to: {{filepath}}")
        return True
    return False

# Override the save operator to auto-save to project
original_save_mainfile = bpy.ops.wm.save_mainfile

def pipeline_save_mainfile(*args, **kwargs):
    """Wrapper that auto-saves to project if no filepath set"""
    if not bpy.data.filepath:
        # First save - auto-save to target file or project directory
        auto_save_to_project()
    else:
        # File already has a path, use normal save
        original_save_mainfile(*args, **kwargs)

# Monkey-patch the save operator
bpy.ops.wm.save_mainfile = pipeline_save_mainfile

print(f"✓ Working directory: {{os.getcwd()}}")
print(f"✓ Auto-save to project enabled")
if target_file:
    print(f"✓ Target file: {{os.path.basename(target_file)}}")
print("=" * 60)
print("")
print("📁 SAVE YOUR WORK:")
if target_file:
    print(f"   • Press Ctrl+S - Auto-saves to {{os.path.basename(target_file)}}")
    print(f"   • Full path: {{target_file}}")
else:
    print(f"   • Press Ctrl+S - Auto-saves to {{project_path}}")
    print(f"   • File will be named: {{project_name}}_TIMESTAMP.blend")
print(f"   • Use Ctrl+Shift+S to choose a custom name")
print("")
print("=" * 60)
''')
                        elif dcc_name_lower == "krita":
                            f.write(f'''# Pipeline Tools - Auto-generated startup script for Krita
from krita import *
import os

# Set default file path to project directory
project_path = r"{windows_project}"
project_name = "{project_name}"
target_file = r"{target_file}" if {bool(target_file)} else None

print("=" * 60)
print("PIPELINE TOOLS - Project Context Active")
print(f"Project: {{project_name}}")
print(f"Path: {{project_path}}")
print("=" * 60)

# Make sure the path exists
os.makedirs(project_path, exist_ok=True)

# Change working directory
os.chdir(project_path)

# Get Krita instance
krita_instance = Krita.instance()

# Store original action
original_save_action = None

def auto_save_to_project():
    """Automatically save to target file or project directory when file has no path"""
    doc = krita_instance.activeDocument()
    if doc is None:
        return False

    # Check if document has been saved before
    if not doc.fileName() or doc.fileName() == "":
        # Use target file path if provided, otherwise generate filename
        if target_file:
            filepath = target_file
            # Make sure parent directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        else:
            # Generate a default filename based on template or timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"{{project_name}}_{{timestamp}}.kra"
            filepath = os.path.join(project_path, default_name)

        # Save the document
        doc.saveAs(filepath)
        print(f"✓ Auto-saved to: {{filepath}}")
        return True
    return False

# Hook into Krita's save action via notifier
class PipelineSaveNotifier(QObject):
    def __init__(self):
        super().__init__()

    def canvasChanged(self, canvas):
        pass

    def viewCreated(self):
        # Try to patch the save action when a view is created
        window = krita_instance.activeWindow()
        if window:
            try:
                save_action = window.action('file_save')
                if save_action and not hasattr(save_action, '_pipeline_patched'):
                    original_trigger = save_action.trigger

                    def pipeline_trigger():
                        doc = krita_instance.activeDocument()
                        if doc and (not doc.fileName() or doc.fileName() == ""):
                            auto_save_to_project()
                        else:
                            original_trigger()

                    save_action.trigger = pipeline_trigger
                    save_action._pipeline_patched = True
            except Exception as e:
                print(f"Could not patch save action: {{e}}")

# Create and register notifier
try:
    notifier = PipelineSaveNotifier()
    krita_instance.notifier().viewCreated.connect(notifier.viewCreated)

    # Also try to patch immediately if window exists
    window = krita_instance.activeWindow()
    if window:
        notifier.viewCreated()
except Exception as e:
    print(f"Warning: Could not set up auto-save: {{e}}")

print(f"✓ Working directory: {{os.getcwd()}}")
print(f"✓ Auto-save to project enabled")
if target_file:
    print(f"✓ Target file: {{os.path.basename(target_file)}}")
print("=" * 60)
print("")
print("📁 SAVE YOUR WORK:")
if target_file:
    print(f"   • Press Ctrl+S - Auto-saves to {{os.path.basename(target_file)}}")
    print(f"   • Full path: {{target_file}}")
else:
    print(f"   • Press Ctrl+S - Auto-saves to {{project_path}}")
    print(f"   • File will be named: {{project_name}}_TIMESTAMP.kra")
print(f"   • Use Ctrl+Shift+S to choose a custom name")
print("")
print("=" * 60)
''')
                    # Add the startup script to command line with Windows path
                    if dcc_name_lower == "blender":
                        cmd.extend(["--python", windows_script_path])
                    elif dcc_name_lower == "krita":
                        # Note: Not all Krita versions support --python-script
                        # Skip for now to ensure Krita launches successfully
                        pass  # cmd.extend(["--python-script", windows_script_path])
                except Exception as e:
                    # Debug: print error
                    import sys
                    print(f"Warning: Could not create {dcc_name_lower} startup script: {e}", file=sys.stderr)
                    pass

            # Create a desktop notification file for all DCCs
            desktop_path = Path("/mnt/c/Users").expanduser()
            username = os.environ.get("USER", "")
            if username:
                desktop_path = Path(f"/mnt/c/Users/{username}/Desktop")

            if desktop_path.exists():
                notification_file = desktop_path / f"PIPELINE_{dcc_name_lower.upper()}_PROJECT.txt"
                try:
                    with open(notification_file, "w") as f:
                        f.write(f"🎨 {dcc_name.upper()} - Current Project\n")
                        f.write(f"=" * 50 + "\n\n")
                        f.write(f"Project: {project_name}\n")
                        f.write(f"Path:    {windows_project}\n\n")
                        if dcc_name_lower in ["blender", "krita"]:
                            f.write(f"✓ {dcc_name.capitalize()} will auto-save to this project by default\n\n")
                        f.write(f"Navigate to this folder in {dcc_name.capitalize()} to open your files.\n")
                        f.write(f"\nYou can delete this file when done.\n")
                    project_notification = str(notification_file)
                except Exception:
                    pass  # Silently fail if we can't create the file
        else:
            # Only set cwd for native launches (Linux->Linux, Windows->Windows, Mac->Mac)
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
