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

### Dev bootstrap playbook

For contributors, you can spin up a local venv and install dev deps:

```sh
ansible-playbook -i localhost, -c local ansible/dev.yml
source .venv/bin/activate
```

## GitHub release installs (no PyPI)

- Install from the latest GitHub release asset with pipx (recommended for users):
  ```sh
  pipx install https://github.com/<your-org>/pipeline-tools/releases/download/vX.Y.Z/pipeline_tools-X.Y.Z-py3-none-any.whl
  ```
  Or via pip (user site):
  ```sh
  pip install --user https://github.com/<your-org>/pipeline-tools/releases/download/vX.Y.Z/pipeline_tools-X.Y.Z-py3-none-any.whl
  ```
- Cut a release: bump `version` in `pyproject.toml`, tag it (`git tag vX.Y.Z && git push origin vX.Y.Z`), and GitHub Actions will run tests/build and publish the wheel/tarball to the tag’s release.
- Ansible release helper (main branch only): `ansible-playbook -i localhost, -c local ansible/release.yml -e repo=<your-org>/pipeline-tools -e version=vX.Y.Z` (requires `GITHUB_TOKEN` env and `community.general` collection).
- PyPI publish: tag a release and GitHub Actions will build and upload to PyPI using `PYPI_API_TOKEN` secret. Manual fallback: `make pypi-release PYPI_TOKEN=...`.
- Install latest main locally (pipx) via Ansible: `make release-local` (must be on `main`; uses `ansible/pipeline-tools.yml`).

### Local env loading (direnv)

- Copy `.envrc.example` to `.envrc` and set your token:
  ```sh
  cp .envrc.example .envrc
  echo 'export GITHUB_TOKEN="ghp_your_token_here"' > .envrc
  direnv allow
  ```
  With direnv installed and hooked into your shell, `GITHUB_TOKEN` will auto-load when you `cd` into the repo, so release playbooks and scripts work without manual `export`.

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

### Conventional commits

- Enforce locally: `make install-hooks` installs a commit-msg hook that blocks non-conventional messages (allowed types: build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test).
- CI enforcement: commit messages are linted on push/PR via GitHub Actions (`.github/workflows/commitlint.yml`).

## Config

- Override DB path: `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Asset status options: design, model, rig, surfacing, done.

## Observability and diagnostics

- Logs: `--log-format json` for structured output; `--log-level DEBUG|INFO|WARNING|ERROR` to tune verbosity.
- Request tracing: pass `--request-id abc123` or set `PIPELINE_TOOLS_REQUEST_ID`.
- Metrics: set `--metrics-endpoint statsd://host:8125` or `PIPELINE_TOOLS_METRICS` to emit StatsD counters/timings (doctor emits `doctor.run` and `doctor.duration_ms`).
- Health check: `pipeline-tools doctor --json` for machine-readable checks (db path, creative root, env, templates). Exits non-zero on failure.
