"""
Test setup helpers.

Ensure dependencies and project imports resolve in CI and offline venvs:
- add user site-packages (for locally installed deps)
- add project root and src/ to sys.path so `import pipeline_tools` works without install
"""

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Force local sources to avoid site-packages shadowing the workspace code.
preferred_paths = [str(SRC), str(ROOT)]
sys.path[:] = [*preferred_paths, *[p for p in sys.path if p not in set(preferred_paths)]]
importlib.invalidate_caches()

# Ensure local sources are imported even if a site-packages install was loaded early.
for module_name in list(sys.modules):
    if module_name == "pipeline_tools" or module_name.startswith("pipeline_tools."):
        del sys.modules[module_name]
