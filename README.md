# Pipely

Artist-friendly CLI for creating and managing pipeline folder structures for creative production workflows (animation, game dev, drawing projects).

**Version:** 0.1.17 | **License:** MIT | **Python:** 3.8+

🌐 **[Visit the Official Website](https://sreyeesh.github.io/pipeline-tools/)** | 📦 **[Download Latest Release](https://github.com/Sreyeesh/pipeline-tools/releases/latest)**

## Overview

Pipely provides a database-driven system for managing production pipelines with:
- **Template-based project scaffolding** - Create standardized folder structures
- **Show management** - Track multiple projects with contextual command execution
- **Asset tracking** - Manage characters, environments, and props with status workflows
- **Shot management** - Organize shots with lifecycle tracking
- **Task tracking** - Attach tasks to assets/shots with progress monitoring
- **Version control** - Track versions with kinds (model, rig, anim, comp, etc.)
- **Cross-platform support** - WSL, Windows, macOS, Linux with smart path detection
- **Built-in observability** - Structured logging, StatsD metrics, request tracing

## Features

### Project Templates
Three built-in templates for quick project setup:
- **animation_short (AN)** - prepro (reference, script, boards, designs), assets, shots, post-production, delivery
- **game_dev_small (GD)** - design docs, art, tech, audio, QA, release
- **drawing_single (DR)** - reference, sketches, final, temp

### Database-Driven Tracking
SQLite database (`~/.pipely/db.sqlite3`) tracks:
- Shows (top-level projects)
- Assets (characters/CH, environments/ENV, props/PR)
- Shots with descriptions and status
- Tasks attached to assets or shots
- Versions with tagging and kind classification

### Status Workflows
- **Assets:** design → model → rig → surfacing → done
- **Shots:** not_started → layout → blocking → final → done
- **Tasks:** not_started → in_progress → done

### Smart Folder Naming
Projects follow convention: `{PREFIX}_{SHOW_CODE}_{PROJECT_NAME}`
- Example: `AN_DMO_DemoShort30s` (animation short)
- Example: `GD_RPG_MyRPGProject` (game dev)

---

## Quick Start for Artists (Natural Language Friendly)

### Install
Use the latest GitHub release (pipx recommended):
```sh
pipx install https://github.com/Sreyeesh/pipeline-tools/releases/latest/download/pipely-0.1.13-py3-none-any.whl
# or
pip install --user https://github.com/Sreyeesh/pipeline-tools/releases/latest/download/pipely-0.1.13-py3-none-any.whl
```

### Use the interactive shell - Artist Workflow
Run `pipely` (no args) to open the interactive prompt with quick actions and natural phrases:

#### Step 1: Pick Your Project
- Type a number to select from existing projects
- Type `projects` to refresh the list
- Type `info` to view current project details (branch, status) without opening an app

#### Step 2: Pick Your App
- Select Blender, Krita, PureRef, Godot, Unity, Unreal, or other installed DCCs by number
- Or type the app name directly (e.g., `blender`, `krita`)

#### Step 3: Pick Your File (New Interactive Picker!)
After selecting an app, you get an interactive workfile menu:
- **Browse existing files**: See all your workfiles for this app with timestamps
- **Open by number**: Type `1`, `2`, etc. to open that file
- **Create new version**: Type `n` to create a new versioned workfile (e.g., `PKU_CH_Poku_Main_blender_w001.blend`)
- **Open app without file**: Type `o` to open the app without loading a file
- **Go back**: Press Enter to return to app selection

**Auto-save magic** (Blender): When you create a new file, press Ctrl+S and it automatically saves to the correct versioned filename in `05_WORK/` - no "Save As" dialog needed!

#### Natural phrases you can use
- “open project 1 with blender” (or krita)  
- “add environment asset called Forest_BG for show DMO”  
- “add shot SH010 Opening scene for show DMO”  
- “work on Forest_BG in krita” (adds/updates a task and opens workfiles)  
- “add task Paint for DMO_ENV_Forest_BG”; “mark task Paint for DMO_ENV_Forest_BG done”  
- “list assets for show DMO”; “list tasks for DMO_ENV_Forest_BG”  
- “show workspace”; “show project structure”

#### Other Commands
- Tasks: `tasks add DMO_SH010 Layout`, `tasks list DMO_SH010`, `tasks status DMO_SH010 Layout in_progress`
- Assets/shots/shows: `assets list -c DMO`, `shows info -c DMO`, `shots list -c DMO`
- Admin docs: `admin template -t animation_bible`, then `admin files --open animation_bible.md`

### If you prefer direct CLI
```sh
pipely create --interactive                      # Create a project
pipely shows list                                # Manage shows
pipely assets add -t CH -n Hero                  # Add an asset
pipely shots add SH010 "Hero enters forest"         # Add a shot
pipely tasks add DMO_SH010 Layout                # Attach a task to a shot
pipely versions new DMO_SH010 anim               # Create a version
pipely doctor --json                             # Health check
pipely admin template -t animation_bible         # Drop the animation bible into 01_ADMIN
pipely workfiles add DMO_SH010 --kind krita      # Create a Krita workfile under 05_WORK
```

### Supported Workfile Types
Pipely creates **valid, openable files** for these formats:
- **Blender** (`.blend`) - Creates proper Blender files, auto-saves to versioned filename
- **Krita** (`.kra`) - Creates valid ZIP-based Krita documents with layer data and color profile
- **PureRef** (`.pur`) - Creates PureRef board files
- **Photoshop** (`.psd`) - Creates Photoshop documents
- **After Effects** (`.aep`) - Creates After Effects projects
- **Fountain** (`.fountain`) - Screenplay/script files
- **Markdown** (`.md`) - Documentation and notes

All workfiles are automatically versioned (e.g., `_w001`, `_w002`) and organized by target (asset/shot) in `05_WORK/`.

---

## Standard Project Layout (animation_short)
```
AN_DMO_DemoShort/
├─ 01_ADMIN/               # Animation bible, screenplay, production notes
├─ 02_PREPRO/
│  ├─ boards/
│  ├─ designs/
│  └─ reference/
├─ 03_ASSETS/
│  ├─ characters/
│  ├─ environments/
│  └─ props/
├─ 04_SHOTS/
│  └─ SH010/
├─ 05_WORK/                # New: workfiles created via `pipely workfiles add`
│  ├─ assets/
│  └─ shots/
├─ 05_POST/
├─ 06_DELIVERY/
└─ z_TEMP/
```

## Developer Setup

### Prerequisites
- Python 3.8+
- git, pip or pipx
- Optional: make, Docker, and Ansible (for playbooks)

### Local environment
```sh
git clone https://github.com/Sreyeesh/pipeline-tools.git
cd pipeline-tools
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
pytest tests/                                    # run tests
pipely --help                                    # sanity check
```

### Docker workflow (optional)
```sh
make build                                      # Build image
make compose-test                               # Run pytest in container
make compose-shell                              # Shell into container
make pt ARGS="create --interactive"               # Run pipely inside container
```

### Conventional commits
```sh
make install-hooks                              # Install commit-msg hook
# commit messages: feat|fix|chore|docs|refactor|test(scope): message
```

---
## Release Flow (Fully Automated)

Pipely uses **release-please** for fully automated releases. Just commit with conventional commits and merge to main!

### Automated Release Process

**What happens automatically:**
1. 🤖 **release-please** analyzes your commits and determines the next version
2. 🤖 Creates a "Release PR" with version bumps and CHANGELOG updates
3. 👤 **You review and merge** the Release PR
4. 🤖 Automatically creates a GitHub release with the new tag
5. 🤖 Runs tests, builds packages, uploads artifacts
6. 🤖 Updates website changelog

**What you do:**
```sh
# 1. Make your changes and commit with conventional commits
git add .
git commit -m "feat: add awesome new feature"
git commit -m "fix: resolve critical bug"
git push origin main

# 2. Wait for release-please to create a Release PR
# 3. Review and merge the Release PR
# 4. Done! Release is automatic after merge
```

### Conventional Commit Format
- `feat:` - New features (minor version bump)
- `fix:` - Bug fixes (patch version bump)
- `feat!:` or `BREAKING CHANGE:` - Breaking changes (major version bump)
- `docs:`, `chore:`, `refactor:`, `test:` - No version bump

### Manual Release (if needed)
```sh
# Bump version manually (run from dev if you're staging a local-only build;
# switch to main before tagging/publishing)
make set-version VERSION=0.1.13

# Update CHANGELOG.md with the new highlights
$EDITOR CHANGELOG.md

# Create tag and push
git checkout main
git pull
git cherry-pick <your-dev-commit>
git add pyproject.toml src/pipeline_tools/__init__.py
git commit -m "chore: bump version to 0.1.13"
git push origin main
git tag v0.1.13
git push origin v0.1.13

# Install locally
make release-local

# Local builds
# Run these from dev (local release staging branch)
git checkout dev
make release-local

# Automate dev → main release (local install, merge, tag, Ansible release)
# VERSION must include the leading v (e.g., v0.1.17)
git checkout dev
make release-dev-cycle VERSION=v0.1.17

# Scheduling notes
# - Hotfixes / patch releases can run any day. Set ALLOW_NON_MONDAY=true when calling make release-ansible.
# - Minor releases (new features) should also run immediately once ready.
# - Major releases are Monday-only unless explicitly overridden (policy safety valve).
```

### GitHub Actions CI/CD
Automated workflows in `.github/workflows/`:
- **commitlint.yml** - Validates conventional commit messages
- **release.yml** - Builds wheel and creates GitHub release on tag push
- **pypi-publish.yml** - Optional PyPI publishing
- **testpypi-publish.yml** - Test PyPI publishing

---

## Configuration & Diagnostics

### Ansible Installation
Install using Ansible playbooks (WSL/Linux):
```sh
# Install with pipx (recommended):
ansible-playbook -i localhost, -c local ansible/pipely.yml

# Install with pip:
ansible-playbook -i localhost, -c local ansible/pipely.yml -e pipely_installer=pip

# If pipx needs sudo packages:
ansible-playbook -i localhost, -c local ansible/pipely.yml -K

# No sudo available:
make ansible-install-nosudo
```

### Environment Variables

**Database location:**
```sh
export PIPELINE_TOOLS_DB=/path/to/custom/db.sqlite3
```
Default: `~/.pipely/db.sqlite3`

**Creative root (where projects are created):**
```sh
export PIPELINE_TOOLS_ROOT=/path/to/projects
```
Defaults:
- WSL: `/mnt/c/Projects`
- Windows: `C:/Projects`
- macOS/Linux: `~/Projects`

**Request tracing:**
```sh
export PIPELINE_TOOLS_REQUEST_ID=custom-request-id
```
Auto-generated UUID if not set.

### Observability Flags

**Logging:**
```sh
pipely --log-format json --log-level DEBUG <command>
```
Formats: `console` (default), `json`
Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Metrics (StatsD):**
```sh
pipely --metrics-endpoint statsd://localhost:8125 <command>
```

**Request tracking:**
```sh
pipely --request-id my-custom-id <command>
```

### Health Check & Diagnostics
```sh
pipely doctor --json
```
Returns system diagnostics including:
- Database path and connectivity
- Creative root location
- Available templates
- Metrics endpoint configuration
- Exit code: 0 (healthy), non-zero (failure)

### Available Templates
- `animation_short` (prefix: AN) - Animation production pipeline
- `game_dev_small` (prefix: GD) - Small game development workflow
- `drawing_single` (prefix: DR) - Single drawing project structure

### Admin Docs & Workfiles (Artist QoL)
- `admin template -t animation_bible --name <FILE>`: copy the bundled bible into `01_ADMIN` for the current show.
- `admin add <path> [--name <FILE>]`: copy any doc into `01_ADMIN` so artists can open it via Pipely.
- `workfiles add <TARGET_ID> --kind <dcc> [--open]`: create a versioned workfile under `05_WORK/...` and optionally launch the DCC.
- `workfiles open --target-id <TARGET_ID> --kind <dcc>`: open the latest workfile for that asset/shot.
- `open <dcc> --project <PROJECT_FOLDER>`: DCC launcher now passes file paths again when invoked via workfiles.

List templates:
```sh
pipely shows templates
```

---

## Architecture

### Technology Stack
- **Runtime:** Python 3.8+
- **CLI Framework:** Typer (built on Click)
- **Database:** SQLite (embedded, no external DB)
- **Terminal UI:** Rich library for formatting
- **Deployment:** Docker, Ansible, GitHub Actions

### Database Schema
**Tables:**
- `config` - Key-value settings (creative_root, current_show)
- `shows` - Top-level projects (code, name, template, root, timestamps)
- `assets` - Asset records (id, show_code, type, name, status, path, tags)
- `shots` - Shot records (code, show_code, description, status, path)
- `tasks` - Tasks for assets/shots (target_id, name, status, updated_at)
- `versions` - Version tracking (version_id, target_id, kind, tags, timestamps)

### Project Structure
```
pipely/
├── src/pipely/
│   ├── cli.py                      # Main Typer CLI entry point
│   ├── __init__.py                 # Version and status enums
│   ├── __main__.py                 # Module runner
│   └── core/
│       ├── cli.py                  # FriendlyArgumentParser base
│       ├── db.py                   # SQLite operations
│       ├── paths.py                # Path resolution logic
│       ├── observability.py        # Logging, metrics, tracing
│       └── fs_utils.py             # File system utilities
│   └── tools/                      # Feature modules
│       ├── project_creator/        # Template scaffolding
│       ├── shows/                  # Show management
│       ├── assets/                 # Asset tracking
│       ├── shots/                  # Shot management
│       ├── tasks/                  # Task tracking
│       ├── versions/               # Version control
│       ├── admin/                  # Config and health checks
│       └── character_thumbnails/   # Thumbnail generation
├── tests/                          # Pytest test suite
├── ansible/                        # Deployment automation
├── .github/workflows/              # CI/CD pipelines
├── Dockerfile                      # Multi-stage container build
├── docker-compose.yml              # Container orchestration
├── Makefile                        # Build and release targets
└── pyproject.toml                  # Python project metadata
```

---

## Backlog / Future Features

See [docs/backlog.md](docs/backlog.md) for detailed roadmap.

**Planned templates:**
- `vfx_episodic` - VFX pipeline (plates, matchmove, layout, FX, lighting, comp, delivery)
- `marketing_campaign` - Marketing and advertising workflows

**Planned features:**
- Custom template configuration via config/environment
- Flexible status/phase definitions per project
- Advanced filtering by tags and kinds
- Pre-flight validation for creative root permissions
- Optional DCC integration hooks (file naming helpers, publish stubs)
- Export summaries in JSON/CSV for downstream tools

---

## License

Pipeline Tools is currently free for artists to use. No purchase or activation required for personal/individual creative work.

- **Free use (artists):** You can download and run the tool as-is for your own projects.
- **Teams/commercial:** Please contact Sreyeesh Garimella if you plan to bundle, redistribute, or use it in a studio/production setting.

Contact Sreyeesh Garimella for licensing and commercial inquiries.

---

## Contributing

1. Fork the repository
2. Create a feature branch following conventional commits
3. Run tests: `pytest tests/`
4. Install commit hooks: `make install-hooks`
5. Submit a pull request

For bug reports and feature requests, please open an issue on GitHub.
