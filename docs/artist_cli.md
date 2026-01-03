# Artist Loop CLI

Small, cross-platform helper for individual artists. No servers, no databases—just folders and files with safe, predictable defaults.

## Core Loop

`Create → Work → Version → Deliver`

All commands run under a single project directory (default: current working directory). Every action writes a short log (`_artlog.txt`) inside the project root so artists can see what the tool did.

### Shared Defaults

- Prompts appear when required arguments are missing, so artists can hit Enter to accept defaults or type new values.
- Nothing is ever overwritten without confirmation; new folders/files get incrementing suffixes (`_001`, `_002`, …).
- All data lives inside the filesystem; no hidden databases, cloud sync, or background services.
- Pipely auto-detects Windows/macOS/Linux, picks a sensible project root (override with `PIPELY_ROOT` or `--root`), and quietly handles OS quirks so the CLI stays identical everywhere.

## Command Overview

| Command | Description | Key Prompts & Behavior |
| --- | --- | --- |
| `art create` | Start a new asset/shot folder with task scaffolding. | Prompts for project name and asset/shot label (task folder defaults to `main`, override with `--task`). Creates `PROJECT/ASSET/TASK/work`, `.../versions`, `.../deliveries` plus a `notes.md`. |
| `art work` | Prepare a working session. | Prompts for path or lets user pick recent task. Copies latest version into `work` as `current.ext` (never deletes). Launch command stored in `launch.txt` (optional). |
| `art version` | Save out a new version. | Prompts for notes and file pattern (defaults to last used extension). Writes to `versions/ASSET_task_v###.ext` and copies optional low-res preview into `previews/`. |
| `art deliver` | Package a selected version for review/delivery. | Prompts to choose a version, delivery target (dailies, client, archive). Copies files into `deliveries/delivery_##/` with checksum file and summary txt. |

## Example Session

```text
$ art create
Project name? Demo Reel
Asset/Shot? HeroCreature
→ Created Demo Reel/HeroCreature/main with work/, versions/, deliveries/

$ art work
Pick a task [1] Demo Reel/HeroCreature/sculpt
Copy latest version into work/current.obj? y
→ You're ready to sculpt. Remember to `art version` when you're done.

$ art version
Describe this save: refined horns
File to version (default work/current.obj): 
→ Saved HeroCreature_sculpt_v003.obj and notes in versions/

$ art deliver
Select version: v003
Delivery target? dailies
→ Packed deliveries/delivery_001 with version, preview, README.txt
```

## Implementation Notes

- Single Python file (`src/pipeline_tools/tools/artloop.py`) using `argparse`; commands are short functions (<40 lines).
- Uses `pathlib` for portability; tested on Win/macOS/Linux.
- File copies use `shutil.copy2` to keep metadata; prompts run through `input()` with defaults displayed.
- Logging helper appends human-readable lines to `_artlog.txt` so support can audit actions.
- Unit tests mock filesystem with `tmp_path` (pytest). Integration test covers the full loop to ensure no command overwrites or deletes unexpectedly.

## Why This Fits Artists

- Friendly prompts and obvious folder layouts reduce training time.
- Short command names (`art create`, `art work`, etc.) match the mental model.
- No silent changes: every copy is additive, and the log explains what happened.
- Minimal Python dependency means artists can run it via the bundled `art.bat`/`art.sh` wrappers or `python -m pipeline_tools.tools.artloop`.
