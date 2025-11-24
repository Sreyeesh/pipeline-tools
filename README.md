# Pipeline Tools

A tiny filesystem-only CLI for creating project folder trees from templates. Run everything via Docker/compose with the Makefile so no local Python setup is needed.

## Quick Start (containerized)

```sh
# Build the image (override IMAGE=your-tag if desired)
make build

# Discover commands
make compose    # alias: make compose-list

# Guided create (prompts)
# (attaches a TTY via docker run -it)
make pt-create-i SHOW_CODE=DRW NAME="City Sketches"

# Quick create
make pt-create SHOW_CODE=ANM NAME="ShortFilm01" TEMPLATE=animation_short

# Health check
make doctor

# Anything else (arguments appended to python -m pipeline_tools.cli)
# If ARGS contains --interactive, the Makefile allocates a TTY automatically.
make pt ARGS="create --interactive"

# Run tests in Docker
make compose-test    # alias: make test

# Shell with mounts
make compose-shell
```

Mount overrides: `PROJECTS_ROOT=/path/to/projects DB_VOLUME=pipeline-tools-db`

Per-command help (from inside the container entrypoint): `pipeline-tools create --help`, `pipeline-tools shows --help`, etc.

## Templates

- `animation_short` (default): film/animation short pipeline folders.
- `game_dev_small`: lean game dev layout (design docs, art, tech, builds, QA, release).
- `drawing_single`: lightweight setup for individual drawings (refs, sketches, finals).

## Other Tools via Makefile

Use `make pt ARGS="..."` to pass args to the CLI (copy/paste ready):

```sh
# Character thumbnails
make pt ARGS="character_thumbnails -c PKS -n 'City Sketches' --character courierA -l prepro"

# Shows
make pt ARGS="shows create -c PKS -n 'City Sketches'"
make pt ARGS="shows list"

# Assets
make pt ARGS="assets add -t CH -n Hero"

# Shots
make pt ARGS="shots add SH010 'Description'"

# Tasks
make pt ARGS="tasks add PKS_SH010 Layout"

# Versions
make pt ARGS="versions new PKS_SH010 anim"

# Admin
make pt ARGS="admin doctor"
make pt ARGS='admin config_set creative_root /mnt/c/Projects'
```

## Common Commands (copy/paste)

```sh
# List available commands
make compose

# Dry-run a create
make pt ARGS='create -c DRW -n "City Sketches" --dry-run'

# Guided create (interactive TTY)
make pt-create-i SHOW_CODE=DRW NAME="City Sketches"

# Show templates
make pt ARGS="shows templates"

# Create a show and set current
make pt ARGS='shows create -c DRW -n "City Sketches"'

# Add an asset
make pt ARGS='assets add -t CH -n Hero'

# Add a shot
make pt ARGS='shots add SH010 "Layout pass"'

# Run doctor
make doctor
```

## Docker Notes

- The Makefile wraps `docker run`/`docker compose` with mounts to `/mnt/c/Projects` and `/root/.pipeline_tools` (SQLite DB). Override with `PROJECTS_ROOT` and `DB_VOLUME`.
- The container entrypoint is the unified CLI (`python -m pipeline_tools.cli`), so `make pt ...` and `docker compose run --rm pipeline-tools ...` append arguments to that CLI.
- The Dockerfile uses a multi-stage build: installs deps and runs tests in a builder stage, then copies a slim virtualenv into the runtime image.

## Config

- Override DB path: `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Asset status options: design, model, rig, surfacing, done.
