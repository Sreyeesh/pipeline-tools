A tiny filesystem-only CLI for creating project folder trees from templates.

- Creates projects under `/mnt/c/Projects/` with a name like `AN_<SHOWCODE>_<ProjectNameNoSpaces>`.
- Currently ships a single `animation_short` template (Admin, Prepro, Assets, Shots, Post, Delivery).
- Intentionally small and local-only: no ShotGrid/API/database integrations yet.

Basic usage (from repo root, with the venv active or after `pip install -e .`):

```
python -m pipeline_tools.tools.project_creator.main -c PKS -n "Poku Short 30s"
```

Artist-friendly entrypoint (installs a `pipeline-tools` command):

- Interactive guided creation: `pipeline-tools create --interactive`
- Quick create: `pipeline-tools create -c PKS -n "Poku Short 30s"`
- Preview only: `pipeline-tools create -c PKS -n "Poku Short 30s" --dry-run`
- Health check: `pipeline-tools doctor` (verifies mounts/permissions/db path)
- Examples anytime: `pipeline-tools examples` or `pipeline-tools --examples`

Templates available:

- `animation_short` (default): film/animation short pipeline folders.
- `game_dev_small`: lean game dev layout (design docs, art, tech, builds, QA, release).
- `drawing_single`: lightweight setup for individual drawings (refs, sketches, finals).

Override the template with `-t <template_key>` (default: `animation_short`).

Add a character thumbnails folder (defaults to Assets location):

```
python -m pipeline_tools.tools.character_thumbnails.main -c PKS -n "Poku Short 30s" --character courierA
```

Use `-l prepro` to place it under `02_PREPRO/designs/characters/`.

Show-level commands (SQLite DB in `~/.pipeline_tools/db.sqlite3` by default, override with `PIPELINE_TOOLS_DB`):

- Create & register a show: `python -m pipeline_tools.tools.shows.main create -c PKS -n "Poku Short 30s"`
- List shows: `python -m pipeline_tools.tools.shows.main list`
- Set current show: `python -m pipeline_tools.tools.shows.main use -c PKS`
- Show info: `python -m pipeline_tools.tools.shows.main info` (defaults to current)
- Show root path: `python -m pipeline_tools.tools.shows.main root -c PKS`
- Delete show record: `python -m pipeline_tools.tools.shows.main delete -c PKS`
- Templates list: `python -m pipeline_tools.tools.shows.main templates`
- Summary: `python -m pipeline_tools.tools.shows.main summary -c PKS`

Asset commands (per-show, creates folders under 03_ASSETS):

- Add asset: `python -m pipeline_tools.tools.assets.main add -t CH -n Poku` (uses current show or pass `-c`)
- List assets: `python -m pipeline_tools.tools.assets.main list`
- Asset info: `python -m pipeline_tools.tools.assets.main info PKS_CH_Poku`
- Update status: `python -m pipeline_tools.tools.assets.main status PKS_CH_Poku model`
- Delete asset (DB only): `python -m pipeline_tools.tools.assets.main delete PKS_CH_Poku`
- Rename asset (DB only): `python -m pipeline_tools.tools.assets.main rename PKS_CH_Poku "New Name"`
- Tag/untag/find/recent: `assets tag|untag|find|recent ...`

Shot commands:

- Add shot: `python -m pipeline_tools.tools.shots.main add SH010 "Description"`
- List shots: `python -m pipeline_tools.tools.shots.main list`
- Update status: `python -m pipeline_tools.tools.shots.main status PKS_SH010 blocking`
- Generate range: `python -m pipeline_tools.tools.shots.main generate_range 10 60 --step 10`

Tasks (per asset/shot):

- Add/list/status: `python -m pipeline_tools.tools.tasks.main add|list|status ...`

Versions:

- New version: `python -m pipeline_tools.tools.versions.main new PKS_CH_Poku design`
- Latest: `python -m pipeline_tools.tools.versions.main latest --asset PKS_CH_Poku --kind design`
- Tag version: `python -m pipeline_tools.tools.versions.main tag <version_id> review`

Admin:

- Config show/set: `python -m pipeline_tools.tools.admin.main config_show` / `config_set <key> <value>`
- Doctor: `python -m pipeline_tools.tools.admin.main doctor`

Notes:

- The DB path can be overridden with `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Asset status options: design, model, rig, surfacing, done.

Docker usage:

- Build the image: `docker build -t pipeline-tools .`
- Create a project (default entrypoint): `docker run --rm -v /path/to/projects:/mnt/c/Projects -v pipeline-tools-db:/root/.pipeline_tools pipeline-tools -c PKS -n "Poku Short 30s"`
- Run other modules by overriding the command: `docker run --rm -v /path/to/projects:/mnt/c/Projects -v pipeline-tools-db:/root/.pipeline_tools pipeline-tools pipeline_tools.tools.shows.main list`
- The container expects a writable `/mnt/c/Projects` mount for folder creation and `/root/.pipeline_tools` (or `PIPELINE_TOOLS_DB`) for the SQLite DB.

Short Docker commands via Makefile:

- Build: `make build` (override `IMAGE=name` if desired)
- Generic wrapper: `make pt ARGS="create --interactive"`
- Quick create: `make pt-create SHOW_CODE=PKS NAME="Poku Short 30s" TEMPLATE=game_dev_small`
- Interactive create: `make pt-create-i SHOW_CODE=PKS NAME="Poku Short 30s"`
- Doctor: `make doctor`
- Customize mounts with `PROJECTS_ROOT=/path/to/projects` and DB volume with `DB_VOLUME=name` (defaults: `/mnt/c/Projects`, `pipeline-tools-db`).
