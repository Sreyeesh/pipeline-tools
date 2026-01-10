# Pipely Init CLI

Simple, predictable scaffolder for individual artists. It creates a clean folder tree and records the project in a local SQLite database for lightweight tracking.

## Workflow

1. Run `pipely init` (or `pipely init --wizard` for guided setup).
2. Answer two prompts:
   - Project name
   - Project type (`animation`, `game`, or `art`)
3. Optional: the wizard can add a starter shot, asset, and task.
4. Open the generated folders in Finder/Explorer and start working.

## Templates

| Type | Folders (under `PROJECT_NAME/`) |
| --- | --- |
| animation | `01_ADMIN`, `02_PREPRO`, `03_ASSETS`, `04_SHOTS`, `05_WORK`, `06_DELIVERY`, `z_TEMP` |
| game | `01_DESIGN`, `02_ART`, `03_TECH`, `04_AUDIO`, `05_QA`, `06_RELEASE`, `z_TEMP` |
| art | `01_REFERENCE`, `02_WIP`, `03_EXPORTS`, `04_DELIVERY`, `z_TEMP` |

## Flags

- `pipely init --name "Demo Reel" --type animation`
- `pipely init --root ~/Projects --name Demo --type art`
- `pipely init --wizard` (prompts for starter shot/asset/task)
- `pipely init --code DMO` (stores project code in the DB)
- `pipely init --db ~/custom/pipely.db` (use a custom DB path)

## Design Principles

- Filesystem first; no files are created, just folders.
- Local DB created on init for optional tracking.
- Same prompts on Windows, macOS, and Linux.
- Defaults to the current directory (override with `PIPELY_ROOT` or `--root`).

## Shot & asset folders

When you add a shot or asset, Pipely also creates standard subfolders based on project type.

- **Animation shots:** `plates`, `layout`, `anim`, `fx`, `lighting`, `comp`, `renders`
- **Animation assets:** `model`, `rig`, `surfacing`, `textures`, `lookdev`, `publish`
- **Game levels:** `blockout`, `lighting`, `setdress`, `gameplay`, `fx`, `build`
- **Game assets:** `model`, `rig`, `textures`, `materials`, `prefab`, `export`
- **Art assets:** `refs`, `wip`, `final` (under `02_WIP/<asset>`)

## Tracking commands (CRUD)

```
pipely project add|list|update|delete|purge
pipely shot add|list|update|delete
pipely asset add|list|update|delete
pipely task add|list|update|delete
pipely approve set|list|update|delete
pipely schedule add|list|update|delete
pipely report summary
```

`pipely project purge --all` removes projects plus related shots/assets/tasks/schedules/approvals (with confirmation).
