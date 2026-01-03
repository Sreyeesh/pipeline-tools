# Pipely

Minimal, cross-platform CLI that mirrors how individual artists already work: **Create → Work → Version → Deliver**. Pipely now focuses entirely on that loop. No databases, no servers, no hidden files—just folders, predictable prompts, and a tiny Typer application.

- **Filesystem only** – everything happens inside a project root. Commands never delete or overwrite without confirmation; new files get `_001`, `_002`, etc.
- **Guided prompts** – leave flags off and Pipely will ask for the missing value with sensible defaults.
- **Always logged** – each action appends a line to `_pipely_log.txt` inside the project root so artists can see what changed.
- **Cross-platform smart defaults** – detects Windows/macOS/Linux, picks a sensible projects root (`PIPELY_ROOT` or `--root` overrides), and keeps folder names safe everywhere.

## Install

```sh
python3 -m pip install pipely
# or just clone the repo and run it with:
python3 -m pip install -e .
```

## Commands

All commands live under `pipely loop`:

| Command | What it does |
| --- | --- |
| `pipely loop create` | Create `PROJECT/TARGET/main` (or custom `--task`) with `work/`, `versions/`, `previews/`, `deliveries/`, and `notes.md`. |
| `pipely loop work` | Pick a task, copy the latest version into `work/current.ext`, and seed a `launch.txt` file for custom DCC commands. |
| `pipely loop version` | Save a new version from `work/current.*` (or any path), incrementing filenames like `Hero_sculpt_v003.ext` plus per-version notes and preview placeholders. |
| `pipely loop deliver` | Package a chosen version into `deliveries/delivery_###/` with a manifest, checksum, and optional preview copy. |

## Example Session

```text
$ pipely loop create
Project name? Demo Reel
Asset or Shot? HeroCreature
→ Created workspace at /Projects/Demo_Reel/HeroCreature/main

$ pipely loop work --task Demo_Reel/HeroCreature/sculpt
Copy latest version (...) into work/current.obj? [Y/n] y
→ Copied to /Projects/Demo_Reel/HeroCreature/sculpt/work/current.obj

$ pipely loop version --task Demo_Reel/HeroCreature/sculpt
Describe this save: refined horns
→ Saved .../versions/HeroCreature_sculpt_v003.obj

$ pipely loop deliver --task Demo_Reel/HeroCreature/sculpt
Choose version
  [1] HeroCreature_sculpt_v003.obj
Delivery target (dailies/client/archive) [dailies]:
→ Delivery ready at .../deliveries/delivery_001
```

## Development

```sh
git clone https://github.com/Sreyeesh/pipeline-tools.git
cd pipeline-tools
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m pip install -r requirements-dev.txt
pytest
```

Tip: set `PIPELY_ROOT=/path/to/projects` (or pass `--root`) if you want a consistent default folder no matter which OS you’re on.

### Run everything inside Docker

Use the bundled wrapper script so `pipely` commands always execute inside Docker:

```sh
./pipely loop --help
./pipely loop create --project Demo --target Hero --task sculpt
```

The first run builds the `pipely-loop` image (runs pytest during build) and mounts `~/Projects` (or `/mnt/c/Projects` on WSL) plus a persistent `pipely-db` volume for `_pipely_log.txt`.

Run the CLI directly with `pipely loop --help` or `python -m pipeline_tools`.
