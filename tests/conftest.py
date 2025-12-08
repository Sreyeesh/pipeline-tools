"""
Test setup helpers.

We add the user site-packages path to sys.path so that locally installed
dependencies (e.g., typer, prompt_toolkit, rich) are available even when running
inside an isolated venv that lacks network access.
"""

import site
import sys

USER_SITE = site.getusersitepackages()
if USER_SITE not in sys.path:
    sys.path.append(USER_SITE)
