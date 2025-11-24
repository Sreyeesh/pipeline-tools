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

GAME_DEV_SMALL_TEMPLATE: List[str] = [
    "01_PRODUCTION/design_docs",
    "01_PRODUCTION/gdd",
    "02_ART/concepts",
    "02_ART/characters",
    "02_ART/environments",
    "02_ART/ui",
    "02_ART/exports",
    "03_TECH/prototypes",
    "03_TECH/source",
    "03_TECH/builds",
    "04_AUDIO/sfx",
    "04_AUDIO/music",
    "05_QA/test_plans",
    "05_QA/bug_reports",
    "06_RELEASE/builds",
    "06_RELEASE/marketing",
    "z_TEMP",
]

DRAWING_TEMPLATE: List[str] = [
    "01_REFERENCE",
    "02_SKETCHES",
    "03_FINAL",
    "03_FINAL/export",
    "z_TEMP",
]

TEMPLATES: Dict[str, List[str]] = {
    "animation_short": ANIMATION_SHORT_TEMPLATE,
    "game_dev_small": GAME_DEV_SMALL_TEMPLATE,
    "drawing_single": DRAWING_TEMPLATE,
}
