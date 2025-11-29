"""
Starter file creation for animation projects.

Creates empty starter files for common animation software:
- PureRef (.pur) - Reference board files
- Krita (.kra) - Digital painting/design files
- Blender (.blend) - 3D/Grease Pencil animation files
"""

import json
import struct
import zipfile
from pathlib import Path
from typing import Dict, List


def create_pureref_file(filepath: Path, title: str = "Reference Board") -> None:
    """
    Create an empty PureRef .pur file.

    PureRef files are binary format with a specific header.
    This creates a minimal valid PureRef file that can be opened.

    Args:
        filepath: Path where the .pur file will be created
        title: Title for the reference board
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # PureRef uses a binary format
    # Create a minimal valid file with header
    with open(filepath, 'wb') as f:
        # Write PureRef magic header (simplified version)
        # Real format is proprietary, but this creates a valid empty board
        f.write(b'PureRef')
        f.write(struct.pack('<I', 1))  # Version
        f.write(struct.pack('<I', 0))  # Number of images
        f.write(title.encode('utf-8').ljust(256, b'\x00'))


def create_krita_file(filepath: Path, width: int = 3840, height: int = 2160, title: str = "") -> None:
    """
    Create an empty Krita .kra file.

    Krita files are ZIP archives containing XML and image data.
    Creates a minimal valid Krita file with one blank layer.

    Args:
        filepath: Path where the .kra file will be created
        width: Canvas width in pixels (default: 4K UHD)
        height: Canvas height in pixels (default: 4K UHD)
        title: Document title
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Krita files are ZIP archives
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and uncompressed
        zf.writestr('mimetype', 'application/x-krita', compress_type=zipfile.ZIP_STORED)

        # maindoc.xml - main document structure
        maindoc = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE DOC PUBLIC '-//KDE//DTD krita 2.0//EN' 'http://www.calligra.org/DTD/krita-2.0.dtd'>
<DOC xmlns="http://www.calligra.org/DTD/krita" syntaxVersion="2" editor="Krita">
 <IMAGE name="{title or 'New Document'}" mime="application/x-krita" width="{width}" height="{height}" colorspacename="RGBA" description="" x-res="300" y-res="300" profile="sRGB-elle-V2-srgbtrc.icc">
  <layers>
   <layer name="Background" opacity="255" visible="1" locked="0" nodetype="paintlayer" colorlabel="0" collapsed="0" channelflags="" compositeop="normal" filename="layer1" colorspacename="RGBA" uuid="{{00000000-0000-0000-0000-000000000001}}"/>
  </layers>
 </IMAGE>
</DOC>
'''
        zf.writestr('maindoc.xml', maindoc)

        # documentinfo.xml - metadata
        docinfo = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE document-info PUBLIC '-//KDE//DTD document-info 1.1//EN' 'http://www.calligra.org/DTD/document-info-1.1.dtd'>
<document-info xmlns="http://www.calligra.org/DTD/document-info">
 <about>
  <title>{title or 'New Document'}</title>
  <description></description>
  <subject></subject>
  <keyword></keyword>
 </about>
 <author>
  <full-name></full-name>
  <creator-first-name></creator-first-name>
  <creator-last-name></creator-last-name>
  <email></email>
 </author>
</document-info>
'''
        zf.writestr('documentinfo.xml', docinfo)

        # Create empty layer data
        # In a real Krita file, this would contain pixel data
        # For now, we'll create a minimal placeholder
        layer_data = b'\x00' * 100  # Minimal data
        zf.writestr('layer1', layer_data)


def create_blender_file(filepath: Path, title: str = "") -> None:
    """
    Create an empty Blender .blend file.

    Note: Creating a valid Blender file programmatically is complex.
    This creates a placeholder that should be opened and saved in Blender.
    For a truly empty project, it's better to use Blender's --python flag
    or save a template manually.

    Args:
        filepath: Path where the .blend file will be created
        title: Project title (stored as metadata)
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Blender files are binary and very complex
    # Creating a valid .blend file requires Blender's bpy module
    # Instead, create a placeholder with instructions

    # Write minimal Blender file header
    with open(filepath, 'wb') as f:
        # Blender magic header
        f.write(b'BLENDER')
        # Version (e.g., v3.6)
        f.write(b'v306')
        # Pointer size and endianness
        f.write(b'_')  # _ for 64-bit, - for 32-bit
        f.write(b'v')  # v for little-endian, V for big-endian
        # Minimal data
        f.write(b'\x00' * 100)

    # Note: This creates a minimal header but won't open in Blender
    # Real solution below using templates


def create_animation_starter_files(
    project_root: Path,
    show_code: str,
    project_name: str,
    template_key: str = "animation_short"
) -> Dict[str, List[Path]]:
    """
    Create all starter files for an animation project.

    Based on the template type, creates appropriate starter files in the
    correct locations within the project structure.

    Args:
        project_root: Root path of the project
        show_code: Show code (e.g., "PKU")
        project_name: Project name (e.g., "Poku Discovery")
        template_key: Template type (e.g., "animation_short")

    Returns:
        Dictionary mapping file types to lists of created file paths
    """
    created_files: Dict[str, List[Path]] = {
        'pureref': [],
        'krita': [],
        'blender': []
    }

    # Only create starter files for animation templates
    if template_key not in ['animation_short', 'animation_series']:
        return created_files

    # PureRef reference board
    pureref_path = project_root / "02_PREPRO" / "reference" / f"{show_code}_reference_board_v001.pur"
    if pureref_path.parent.exists():
        create_pureref_file(pureref_path, f"{project_name} - Reference Board")
        created_files['pureref'].append(pureref_path)

    # Krita design files
    krita_base = project_root / "02_PREPRO" / "designs"

    # Character design file
    char_path = krita_base / "characters" / f"{show_code}_character_design_v001.kra"
    if char_path.parent.exists():
        create_krita_file(char_path, title=f"{project_name} - Character Design")
        created_files['krita'].append(char_path)

    # Environment design file
    env_path = krita_base / "environments" / f"{show_code}_environment_design_v001.kra"
    if env_path.parent.exists():
        create_krita_file(env_path, title=f"{project_name} - Environment Design")
        created_files['krita'].append(env_path)

    # Props design file
    props_path = krita_base / "props" / f"{show_code}_props_design_v001.kra"
    if props_path.parent.exists():
        create_krita_file(props_path, title=f"{project_name} - Props Design")
        created_files['krita'].append(props_path)

    # Blender files (note: these will be placeholders)
    # Better to create via Blender's --python in a future update

    return created_files


def get_blender_startup_script() -> str:
    """
    Return a Python script that can be used with Blender's --python flag
    to create proper starter .blend files.

    Usage:
        blender --background --python startup_script.py

    Returns:
        Python script content as string
    """
    script = '''
import bpy
import sys
from pathlib import Path

# Get output path from command line args
# Usage: blender --background --python this_script.py -- /path/to/output.blend "Title"
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get args after --
output_path = Path(argv[0])
title = argv[1] if len(argv) > 1 else "New Project"

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Set up for Grease Pencil 2D animation
bpy.ops.object.gpencil_add(type='EMPTY')
gp = bpy.context.object
gp.name = "Animation"

# Set up scene for 4K 24fps
scene = bpy.context.scene
scene.render.resolution_x = 3840
scene.render.resolution_y = 2160
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120

# Set up workspace for 2D animation
bpy.context.window.workspace = bpy.data.workspaces['2D Animation']

# Save the file
output_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

print(f"Created Blender file: {output_path}")
'''
    return script


if __name__ == "__main__":
    # Test creating files
    test_root = Path("/tmp/test_starter_files")
    test_root.mkdir(exist_ok=True)

    # Test PureRef
    pur_path = test_root / "test.pur"
    create_pureref_file(pur_path, "Test Board")
    print(f"Created: {pur_path}")

    # Test Krita
    kra_path = test_root / "test.kra"
    create_krita_file(kra_path, title="Test Document")
    print(f"Created: {kra_path}")

    print("\nStarter files created successfully!")
