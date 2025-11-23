A tiny filesystem-only CLI for creating project folder trees from templates.

- Creates projects under `/mnt/c/Projects/` with a name like `AN_<SHOWCODE>_<ProjectNameNoSpaces>`.
- Currently ships a single `animation_short` template (Admin, Prepro, Assets, Shots, Post, Delivery).
- Intentionally small and local-only: no ShotGrid/API/database integrations yet.

Basic usage (from repo root, with the venv active or after `pip install -e .`):

```
python -m pipeline_tools.tools.project_creator.main -c PKS -n "Poku Short 30s"
```

Override the template with `-t <template_key>` (default: `animation_short`).
