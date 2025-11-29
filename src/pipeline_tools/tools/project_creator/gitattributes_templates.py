"""Git LFS attributes templates for different project types."""

# Common LFS patterns for large binary files
COMMON_LFS_ATTRIBUTES = """# Git LFS tracking patterns

# Archives
*.zip filter=lfs diff=lfs merge=lfs -text
*.rar filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text

# Large documents
*.pdf filter=lfs diff=lfs merge=lfs -text
"""

# Animation project LFS patterns
ANIMATION_LFS_ATTRIBUTES = COMMON_LFS_ATTRIBUTES + """
# Blender files
*.blend filter=lfs diff=lfs merge=lfs -text

# Krita files
*.kra filter=lfs diff=lfs merge=lfs -text

# Photoshop files
*.psd filter=lfs diff=lfs merge=lfs -text

# Video files
*.mov filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text
*.flv filter=lfs diff=lfs merge=lfs -text

# Image sequences and high-res images
*.exr filter=lfs diff=lfs merge=lfs -text
*.dpx filter=lfs diff=lfs merge=lfs -text
*.tif filter=lfs diff=lfs merge=lfs -text
*.tiff filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text

# Audio files
*.wav filter=lfs diff=lfs merge=lfs -text
*.aiff filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text

# After Effects
*.aep filter=lfs diff=lfs merge=lfs -text

# 3D files
*.fbx filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.abc filter=lfs diff=lfs merge=lfs -text
*.usd filter=lfs diff=lfs merge=lfs -text
*.usda filter=lfs diff=lfs merge=lfs -text
*.usdc filter=lfs diff=lfs merge=lfs -text
"""

# Game development LFS patterns
GAME_DEV_LFS_ATTRIBUTES = COMMON_LFS_ATTRIBUTES + """
# 3D Models
*.fbx filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.gltf filter=lfs diff=lfs merge=lfs -text
*.glb filter=lfs diff=lfs merge=lfs -text

# Textures and images
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.tga filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text
*.hdr filter=lfs diff=lfs merge=lfs -text

# Audio
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text

# Video
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text

# Game engine specific
*.unity filter=lfs diff=lfs merge=lfs -text
*.unitypackage filter=lfs diff=lfs merge=lfs -text
*.asset filter=lfs diff=lfs merge=lfs -text
"""

# Drawing project LFS patterns (minimal, mostly images)
DRAWING_LFS_ATTRIBUTES = COMMON_LFS_ATTRIBUTES + """
# Source files
*.kra filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text
*.clip filter=lfs diff=lfs merge=lfs -text

# High-res exports
*.tif filter=lfs diff=lfs merge=lfs -text
*.tiff filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
"""

# Template mapping
GITATTRIBUTES_TEMPLATES = {
    "animation_short": ANIMATION_LFS_ATTRIBUTES,
    "game_dev_small": GAME_DEV_LFS_ATTRIBUTES,
    "drawing_single": DRAWING_LFS_ATTRIBUTES,
}
