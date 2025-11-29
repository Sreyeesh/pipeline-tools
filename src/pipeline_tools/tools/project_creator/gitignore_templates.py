"""Git ignore templates for different project types."""

# Common ignores for all project types
COMMON_GITIGNORE = """# OS Files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
Desktop.ini

# Editor/IDE
.vscode/
.idea/
*.swp
*.swo
*~
.project
.settings/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/

# Temporary files
*.tmp
*.temp
*.bak
*.backup
*_backup
"""

# Animation project specific ignores
ANIMATION_GITIGNORE = COMMON_GITIGNORE + """
# Blender
*.blend1
*.blend2
*.blend@
*.blend#
*.blend~

# Krita
*~*.kra
*.kra~
.directory

# After Effects
*.aep Logs/
*.aep lockfile.txt

# Renders and cache (use LFS or don't track)
renders/
cache/
*.exr
*.dpx

# Large media files not in LFS
z_TEMP/
*.avi
*.mov
*.mp4
*.mkv
*.webm
"""

# Game development specific ignores
GAME_DEV_GITIGNORE = COMMON_GITIGNORE + """
# Unity
[Ll]ibrary/
[Tt]emp/
[Oo]bj/
[Bb]uild/
[Bb]uilds/
[Ll]ogs/
[Uu]ser[Ss]ettings/
*.csproj
*.unityproj
*.sln
*.suo
*.tmp
*.user
*.userprefs
*.pidb
*.booproj
*.svd
*.pdb
*.mdb
*.opendb
*.VC.db

# Godot
.import/
export.cfg
export_presets.cfg
*.translation

# Unreal
Binaries/
DerivedDataCache/
Intermediate/
Saved/
*.VC.opendb
*.opensdf
*.sdf
*.sln
*.suo
*.xcodeproj
*.xcworkspace

# Build artifacts
*.exe
*.app
*.x86_64
*.pck
"""

# Simple drawing project ignores
DRAWING_GITIGNORE = COMMON_GITIGNORE + """
# Krita
*~*.kra
*.kra~

# Photoshop
*.psd~

# Large exports (use LFS if needed)
03_FINAL/export/*.tif
03_FINAL/export/*.tiff
"""

# Template mapping
GITIGNORE_TEMPLATES = {
    "animation_short": ANIMATION_GITIGNORE,
    "game_dev_small": GAME_DEV_GITIGNORE,
    "drawing_single": DRAWING_GITIGNORE,
}
