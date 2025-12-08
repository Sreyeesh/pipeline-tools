"""
Test setup helpers.

Ensure dependencies and project imports resolve in CI and offline venvs:
- add user site-packages (for locally installed deps)
- add project root and src/ to sys.path so `import pipeline_tools` works without install
"""

import site
import sys
from pathlib import Path

USER_SITE = site.getusersitepackages()
if USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.append(str(path))
