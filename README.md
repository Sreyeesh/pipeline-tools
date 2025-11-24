# Pipeline Tools

Artist-friendly CLI for creating and managing pipeline folder trees (shows, assets, shots, tasks). The Typer UI now ships with a prettier, colorized home screen so end users can discover commands without touching Docker or Makefiles.

## End-user quick start (no Docker)

```sh
# Install locally (pipx recommended)
pipx install .
# or
pip install .

# Launch the CLI
pipeline-tools

# Add --help to any command
pipeline-tools create --help
```

What the home screen looks like:

```
$ pipeline-tools
Pipeline Tools · artist-friendly pipeline CLI
Common commands
  pipeline-tools create -c PKS -n "Poku Short 30s"
  pipeline-tools create --interactive
  pipeline-tools shows list
  pipeline-tools assets add -c PKS -t CH -n Poku
  pipeline-tools shots add PKS_SH010 "First pass layout"
  pipeline-tools doctor
Commands
  create               Create project folder trees from templates.
  doctor               Run environment checks.
  admin                Admin/config commands (config_show, config_set, doctor).
  shows                Show-level commands (create/list/use/info/etc.).
  assets               Asset-level commands (add/list/info/status/etc.).
  shots                Shot-level commands (add/list/info/status/etc.).
  tasks                Task commands for assets/shots.
  versions             Version tracking commands.
  character-thumbnails Generate thumbnail sheets for characters.
  examples             Show common commands.
```

## Common commands (copy/paste)

```sh
pipeline-tools create -c DRW -n "City Sketches" --interactive
pipeline-tools create -c ANM -n "ShortFilm01" -t animation_short
pipeline-tools shows list
pipeline-tools assets add -c PKS -t CH -n Hero
pipeline-tools shots add PKS_SH010 "Layout pass"
pipeline-tools tasks add PKS_SH010 Layout
pipeline-tools versions new PKS_SH010 anim
pipeline-tools doctor
```

## Ansible install (pipx or pip)

From the repo root (WSL/Linux):

```sh
# Install Ansible if needed (Debian/Ubuntu)
sudo apt-get update && sudo apt-get install -y ansible

# Install with pipx (default)
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml

# Or install with pip --user
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml -e pipeline_tools_installer=pip
```

After pipx/pip --user installs, ensure `~/.local/bin` is on your PATH.

If apt can install pipx (Debian/Ubuntu), the playbook will use `python3-pipx`; otherwise it falls back to a user-level pip install.

## Templates

- `animation_short` (default): film/animation short pipeline folders.
- `game_dev_small`: lean game dev layout (design docs, art, tech, builds, QA, release).
- `drawing_single`: lightweight setup for individual drawings (refs, sketches, finals).

## Developer workflow (Docker/Makefile)

For contributors who prefer containerized tooling:

```sh
# Build the image (override IMAGE=your-tag if desired)
make build

# List commands via docker compose
make compose    # alias: make compose-list

# Run the CLI inside the container
make pt ARGS="create --interactive"

# Run tests in Docker
make compose-test    # alias: make test

# Shell with mounts
make compose-shell
```

Mount overrides: `PROJECTS_ROOT=/path/to/projects DB_VOLUME=pipeline-tools-db`

The container entrypoint is the unified CLI (`python -m pipeline_tools.cli`), so `make pt ...` and `docker compose run --rm pipeline-tools ...` append arguments to that CLI.

## Config

- Override DB path: `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Asset status options: design, model, rig, surfacing, done.
