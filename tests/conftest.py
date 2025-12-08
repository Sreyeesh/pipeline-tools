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
# Prefer local sources over any globally installed package.
for path in (SRC, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
