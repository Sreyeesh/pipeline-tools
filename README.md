A tiny filesystem-only CLI for creating project folder trees from templates. Use the Makefile for all commands (it wraps Docker with the right mounts).

For artists (just these):

- Build once: `make build`
- Guided create (recommended): `make pt-create-i SHOW_CODE=PKS NAME="Poku Short 30s"`
- If something breaks: `make doctor` (copy the output to a TD)
- Your folders appear under `/mnt/c/Projects` by default (set `PROJECTS_ROOT` to change).

Quick start (Makefile first):

- Build the image: `make build` (override `IMAGE=your-tag`)
- Guided create (prompts): `make pt-create-i SHOW_CODE=PKS NAME="Poku Short 30s"`
- Quick create: `make pt-create SHOW_CODE=PKS NAME="Poku Short 30s" TEMPLATE=game_dev_small`
- Health check: `make doctor`
- Anything else via launcher: `make pt ARGS="create --interactive"` (passes args to `pipeline_tools.cli`)
- Customize mounts/volumes: `PROJECTS_ROOT=/path/to/projects DB_VOLUME=pipeline-tools-db`

Templates:

- `animation_short` (default): film/animation short pipeline folders.
- `game_dev_small`: lean game dev layout (design docs, art, tech, builds, QA, release).
- `drawing_single`: lightweight setup for individual drawings (refs, sketches, finals).

Other tools via Makefile (`make pt ARGS="..."`):

- Character thumbnails: `make pt ARGS="character_thumbnails -c PKS -n 'Poku Short 30s' --character courierA -l prepro"`
- Shows: `make pt ARGS="shows create -c PKS -n 'Poku Short 30s'"` or `make pt ARGS="shows list"`
- Assets: `make pt ARGS="assets add -t CH -n Poku"`; status/list/tag/etc. use the same pattern.
- Shots: `make pt ARGS="shots add SH010 'Description'"`
- Tasks: `make pt ARGS="tasks add PKS_SH010 Layout"`
- Versions: `make pt ARGS="versions new PKS_SH010 anim"`
- Admin: `make pt ARGS="admin doctor"` or `make pt ARGS='admin config_set creative_root /mnt/c/Projects'`

Docker notes:

- The Makefile wraps `docker run --rm` with mounts to `/mnt/c/Projects` and `/root/.pipeline_tools` (SQLite DB). Override with `PROJECTS_ROOT` and `DB_VOLUME`.
- Default entrypoint is `python -m`, so `make pt ...` runs `pipeline_tools.cli` and you pass subcommands through `ARGS`.

Config:

- Override DB path: `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Asset status options: design, model, rig, surfacing, done.
