from typing import Dict, List

# Folder structure for an animation short project
ANIMATION_SHORT_TEMPLATE: List[str] = [
    "01_ADMIN",
    "02_PREPRO/script",
    "02_PREPRO/boards",
    "02_PREPRO/designs/characters",
    "02_PREPRO/designs/environments",
    "02_PREPRO/designs/props",
    "03_ASSETS/characters",
    "03_ASSETS/environments",
    "03_ASSETS/props",
    "04_SHOTS",
    "05_POST/comp",
    "05_POST/edit/project",
    "05_POST/edit/shots_for_edit",
    "05_POST/sound",
    "06_DELIVERY/video",
    "06_DELIVERY/stills",
    "z_TEMP",
]

TEMPLATES: Dict[str, List[str]] = {
    "animation_short": ANIMATION_SHORT_TEMPLATE,
    # later: "unreal_game_small": [...],
}
