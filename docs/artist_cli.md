# Pipely Init CLI

Simple, predictable scaffolder for individual artists. It creates a clean folder tree and stops—no versioning, databases, or tracking systems.

## Workflow

1. Run `pipely init`
2. Answer two prompts:
   - Project name
   - Project type (`animation`, `game`, or `art`)
3. Open the generated folders in Finder/Explorer and start working.

## Templates

| Type | Folders (under `PROJECT_NAME/`) |
| --- | --- |
| animation | `01_ADMIN`, `02_PREPRO`, `03_ASSETS`, `04_SHOTS`, `05_WORK`, `06_DELIVERY`, `z_TEMP` |
| game | `01_DESIGN`, `02_ART`, `03_TECH`, `04_AUDIO`, `05_QA`, `06_RELEASE`, `z_TEMP` |
| art | `01_REFERENCE`, `02_WIP`, `03_EXPORTS`, `04_DELIVERY`, `z_TEMP` |

## Flags

- `pipely init --name "Demo Reel" --type animation`
- `pipely init --root ~/Projects --name Demo --type art`

## Design Principles

- Filesystem only; no files are created, just folders.
- Same prompts on Windows, macOS, and Linux.
- Defaults to the current directory (override with `PIPELY_ROOT` or `--root`).
