# Pipely Artist Loop CLI

Lightweight redesign of Pipely as an artist-first tool. Works on Windows, macOS, and Linux with zero services or databases—only folders, filenames, and guided prompts.

## Core Principle

Single workflow: **Create → Work → Version → Deliver**

Each command mirrors that mental model, so artists always know the next step. Commands are short (`pipely create`, `pipely work`, etc.), accept optional arguments, and prompt whenever data is missing.

## Shared Behavior

1. **Filesystem only** – Pipely operates inside a project root (default: current directory). Data lives in predictable folders such as `assets/`, `shots/`, `tasks/`, `versions/`, and `deliveries/`.
2. **Safe defaults** – Never overwrite silently. New folders/files get incrementing suffixes; confirmations appear before destructive actions.
3. **Guided prompts** – Missing arguments trigger questions with sensible defaults (shown in brackets). Artists can press Enter to accept.
4. **Audit trail** – Each command appends a short entry to `_pipely_log.txt` so supervisors can review actions without digging through databases.
5. **OS-aware without OS flags** – Pipely detects Windows/macOS/Linux internally, picks a sensible projects root (`PIPELY_ROOT` or `--root` override), and sanitizes folder names so the CLI behaves the same everywhere.

## Command Loop

| Command | Artist intent | Actions on disk |
| --- | --- | --- |
| `pipely create` | Start a task space | Prompts for project name and asset/shot (task folder defaults to `main`, override with `--task`). Creates `PROJECT/TARGET/TASK/{work,versions,deliveries}` plus `notes.md` and `refs/`. |
| `pipely work` | Begin/continue working | Lets artist pick a task or pass a path. Ensures `work/current.*` file exists, optionally clones latest version. Stores preferred DCC launch command in `launch.cmd`. |
| `pipely version` | Save progress | Prompts for description and source file (defaults to `work/current.ext`). Outputs `versions/TARGET_task_v###.ext`, copies snapshot to `previews/`, writes note to `versions/notes_v###.txt`. |
| `pipely deliver` | Package a version | Prompts for version, delivery target (dailies/client/archive), and recipients. Creates `deliveries/delivery_##/` containing version files, preview, manifest, and checksum. |

### Optional Helpers

- `pipely status` – summarizes the latest version, pending deliveries, and last activity per task.
- `pipely guide` – prints the four-step loop with friendly instructions for new artists.

## Experience Walkthrough

```text
$ pipely create
Project name? DemoReel
Asset or shot? HeroCreat
→ Created DemoReel/HeroCreat/main with work/, versions/, deliveries/

$ pipely work
Pick a task:
  [1] DemoReel/HeroCreat/sculpt
Selection? 1
Found latest version v002 (HeroCreat_sculpt_v002.obj). Copy into work/current.obj? [Y/n]
→ Session ready. Launch command saved in work/launch.cmd (edit to customize).

$ pipely version
Describe this save: refined horns
Source file [work/current.obj]:
→ Saved versions/HeroCreat_sculpt_v003.obj + previews/HeroCreat_sculpt_v003.png

$ pipely deliver
Choose version [latest v003]:
Delivery target? (dailies/client/archive) dailies
Notes? includes front horns polish
→ deliveries/delivery_001 ready with manifest.txt + checksum.md5
```

## Implementation Outline

- **Entrypoint**: New `pipely loop` subcommand that exposes `create`, `work`, `version`, `deliver`; alternatively keep top-level verbs for brevity.
- **Code size**: Single module (~300 lines) using `argparse` + helper utilities (`pathlib`, `shutil`, `textwrap`). No ORM, no HTTP.
- **Prompts**: Shared `ask(prompt, default=None)` helper to display `[default]` and validate responses.
- **Safety**: `_safe_create(path)` increments suffixes, `_safe_copy(src, dst_base)` appends `_001` etc., `confirm()` before any delete.
- **Testing**: Pytest suites with `tmp_path` to simulate flows and ensure no overwrites. Mock user input using `monkeypatch` to keep CLI deterministic.
- **Packaging**: Provide `pipely.bat` and `pipely.sh` wrappers that call `python -m pipeline_tools.tools.loop`.

## Why Artists Will Use It

- Mirrored to their workflow; each command maps to a step they already understand.
- Minimal typing—defaults, prompts, and short verbs remove the need to memorize flags.
- Transparent files/folders mean artists can explore with Finder/Explorer without hidden metadata.
- Works offline across OSes, so freelancers and studio users get the same experience.
