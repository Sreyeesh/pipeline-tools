# Pipely

Artist-first CLI that scaffolds predictable project folders and optionally tracks production data in a local SQLite database. You get real directories you can open in Finder/Explorer plus lightweight tracking when you want it.

- **Filesystem first** – creates folders inside the root you choose (current directory by default, override with `PIPELY_ROOT` or `--root`).
- **Three templates** – animation, game development, and generic art.
- **Local DB** – `pipely init` initializes the DB and records the project.
- **Identical prompts everywhere** – works the same on Windows, macOS, and Linux.

## Install (end users)

Install Pipely with pipx:

```sh
pipx install https://github.com/Sreyeesh/pipeline-tools/releases/download/v0.1.18/pipely-0.1.18-py3-none-any.whl
pipely --help
```

Use Docker and the repo wrapper script for local development.

Prerequisite: install Docker Desktop (Windows/macOS) or Docker Engine (Linux).

From the repo root:

```sh
./pipely --help
./pipely init --name Demo --type animation
```

This builds the Docker image on first run and executes Pipely inside the container.

### Install from source (developers)

```sh
python3 -m pip install -e .
```

## Usage

```sh
pipely init
# Project name? Demo Reel
# Project type? (animation/game/art) animation
# → Created animation project at /path/to/Demo_Reel
```

Optional guided setup:

```sh
pipely init --wizard
```

### Flags

- `--name` / `-n` – skip the project-name prompt.
- `--type` / `-t` – `animation`, `game`, or `art`.
- `--describe` / `-d` – describe the project in plain language to infer name/type.
- `--root` – base folder for the project (defaults to current directory / `PIPELY_ROOT`).
- `--code` / `-c` – project code stored in the local DB.
- `--db` – database path (defaults to `~/.pipely/pipely.db`).
- `--wizard` / `-w` – prompt for a starter shot/asset/task.

### Templates

| Type | Folders |
| --- | --- |
| animation | `01_ADMIN`, `02_PREPRO`, `03_ASSETS`, `04_SHOTS`, `05_WORK`, `06_DELIVERY`, `z_TEMP` |
| game | `01_DESIGN`, `02_ART`, `03_TECH`, `04_AUDIO`, `05_QA`, `06_RELEASE`, `z_TEMP` |
| art | `01_REFERENCE`, `02_WIP`, `03_EXPORTS`, `04_DELIVERY`, `z_TEMP` |

No files are created—just the directories above under `PROJECT_NAME/`.

### Shot & asset subfolders

When you add a shot or asset for a project, Pipely creates standard subfolders based on the project type:

- **Animation shots**: `plates`, `layout`, `anim`, `fx`, `lighting`, `comp`, `renders`
- **Animation assets**: `model`, `rig`, `surfacing`, `textures`, `lookdev`, `publish`
- **Game levels**: `blockout`, `lighting`, `setdress`, `gameplay`, `fx`, `build`
- **Game assets**: `model`, `rig`, `textures`, `materials`, `prefab`, `export`
- **Art assets**: `refs`, `wip`, `final` (under `02_WIP/<asset>`)

### Tracking commands (CRUD)

```sh
pipely project add|list|update|delete|purge
pipely shot add|list|update|delete
pipely asset add|list|update|delete
pipely task add|list|update|delete
pipely approve set|list|update|delete
pipely schedule add|list|update|delete
pipely report summary
```

`pipely project purge --all` removes projects plus related shots/assets/tasks/schedules/approvals (with confirmation).

### Project structure (repo)

```
.
├── .github/
├── CHANGELOG.md
├── Dockerfile
├── Dockerfile.dev
├── Makefile
├── README.md
├── ansible/
├── docs/
├── pipely
├── pyproject.toml
├── requirements-dev.txt
├── requirements.txt
├── src/
│   └── pipeline_tools/
└── tests/
```

## Development

```sh
git clone https://github.com/Sreyeesh/pipeline-tools.git
cd pipeline-tools
python3 -m pip install -e .
python3 -m pip install -r requirements-dev.txt
pytest
```

### Docker (required for developers)

Use the helper targets (Docker is required for development workflows):

```sh
make build      # docker compose build
make sh         # open a dev shell (pip install -e . runs automatically)
make run ARGS="init --name Demo --type art --root /home/dev/projects"
```

### Ansible shortcut

```sh
make ansible-deps   # one-time venv bootstrap
make ansible        # rebuild Docker image + preinstall dev deps
make ansible-install-local  # install Pipely locally on WSL2/Linux
make ansible-win-ssh        # deploy to Windows via SSH (prompts for password)
```

## Build Windows .exe (PyInstaller)

From a Windows shell in the repo root:

```bat
python -m pip install --upgrade pip pyinstaller
py -3 -m pip install -e .
py -3 -m PyInstaller build\pyinstaller\pipely.spec
```

The executable will be in `dist\pipely\pipely.exe`.
