# Pipely

Artist-first CLI that does one thing well: scaffold project folders with predictable layouts. No databases, no tracking systems—just real directories you can open in Finder/Explorer.

- **Filesystem only** – creates folders inside the root you choose (current directory by default, override with `PIPELY_ROOT` or `--root`).
- **Three templates** – animation, game development, and generic art.
- **Identical prompts everywhere** – works the same on Windows, macOS, and Linux.

## Install (end users)

WSL2 (Linux):

```sh
python3 -m pip install --upgrade uv
python3 -m uv pip install pipely
```

Windows (Command Prompt):

```bat
python -m pip install --upgrade uv
python -m uv pip install pipely
```

Note: on Windows, ensure your Python `Scripts` directory is on `PATH` so `uv` is available in Command Prompt.

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

### Flags

- `--name` / `-n` – skip the project-name prompt.
- `--type` / `-t` – `animation`, `game`, or `art`.
- `--describe` / `-d` – describe the project in plain language to infer name/type.
- `--root` – base folder for the project (defaults to current directory / `PIPELY_ROOT`).

### Templates

| Type | Folders |
| --- | --- |
| animation | `01_ADMIN`, `02_PREPRO`, `03_ASSETS`, `04_SHOTS`, `05_WORK`, `06_DELIVERY`, `z_TEMP` |
| game | `01_DESIGN`, `02_ART`, `03_TECH`, `04_AUDIO`, `05_QA`, `06_RELEASE`, `z_TEMP` |
| art | `01_REFERENCE`, `02_WIP`, `03_EXPORTS`, `04_DELIVERY`, `z_TEMP` |

No files are created—just the directories above under `PROJECT_NAME/`.

## Development

```sh
git clone https://github.com/Sreyeesh/pipeline-tools.git
cd pipeline-tools
python3 -m pip install -e .
python3 -m pip install -r requirements-dev.txt
pytest
```

### Docker (optional)

Use the helper targets:

```sh
make build      # docker compose build
make sh         # open a dev shell (pip install -e . runs automatically)
make run ARGS="init --name Demo --type art --root /home/dev/projects"
```

### Ansible shortcut

```sh
make ansible-deps   # one-time venv bootstrap
make ansible        # rebuild Docker image + preinstall dev deps
```
