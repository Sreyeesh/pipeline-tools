# Pipeline Tools

Artist-friendly CLI for creating and managing pipeline folder structures for creative production workflows (animation, game dev, drawing projects).

**Version:** 0.1.7 | **License:** MIT | **Python:** 3.8+

## Overview

Pipeline Tools provides a database-driven system for managing production pipelines with:
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
SQLite database (`~/.pipeline_tools/db.sqlite3`) tracks:
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

## Quick Start (Users)

### Installation
Install from GitHub release (recommended):
```sh
pipx install https://github.com/Sreyeesh/pipeline-tools/releases/download/v0.1.7/pipeline_tools-0.1.7-py3-none-any.whl
# or
pip install --user https://github.com/Sreyeesh/pipeline-tools/releases/download/v0.1.7/pipeline_tools-0.1.7-py3-none-any.whl
```

### Basic Usage

**Create a new project:**
```sh
pipeline-tools create --interactive
# Or non-interactive:
pipeline-tools create --template animation_short --show-code DMO --project-name DemoShort30s
```

**Manage shows:**
```sh
pipeline-tools shows list                          # List all shows
pipeline-tools shows use DMO                       # Set current show context
pipeline-tools shows info DMO                      # Show details
pipeline-tools shows templates                     # List available templates
```

**Manage assets:**
```sh
pipeline-tools assets add character Hero           # Add character asset
pipeline-tools assets add environment ForestPath   # Add environment
pipeline-tools assets list                         # List all assets
pipeline-tools assets status Hero model            # Update asset status
pipeline-tools assets tag Hero --tags protagonist,main
pipeline-tools assets find-by-tag protagonist      # Search by tag
```

**Manage shots:**
```sh
pipeline-tools shots add SH010 "Hero enters forest"
pipeline-tools shots list
pipeline-tools shots status SH010 layout
```

**Track tasks:**
```sh
pipeline-tools tasks add asset Hero "Model character"
pipeline-tools tasks add shot SH010 "Animate shot"
pipeline-tools tasks list asset Hero
pipeline-tools tasks update-status <task-id> in_progress
```

**Track versions:**
```sh
pipeline-tools versions create asset Hero model v001
pipeline-tools versions list asset Hero
pipeline-tools versions latest asset Hero model
pipeline-tools versions tag <version-id> --tags approved,final
```

**Health check:**
```sh
pipeline-tools doctor --json                       # System diagnostics
pipeline-tools --version                           # Show version
```

---

## Developer Setup

### Local Development Environment
Set up a local Python virtual environment:
```sh
ansible-playbook -i localhost, -c local ansible/dev.yml
source .venv/bin/activate
```

### Docker Workflow
Build and test with Docker:
```sh
make build                              # Build Docker image
make compose-list                       # List available commands
make compose-test                       # Run pytest suite in container
make compose-shell                      # Interactive shell in container
make pt ARGS="create --interactive"     # Run pipeline-tools in container
```

### Testing
Run the test suite:
```sh
pytest tests/                           # Run all tests
pytest tests/test_project_creator.py    # Specific test file
```

Test coverage includes:
- Project creation and show registration
- Asset, shot, task, and version management
- Character thumbnail generation
- Tag-based search functionality
- CLI entry point validation

### Conventional Commits
This project enforces [Conventional Commits](https://www.conventionalcommits.org/):
```sh
make install-hooks                      # Install commit-msg hook
```
CI also validates commit messages. Format: `type(scope): message`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`

---

## Release Flow (GitHub Assets)

Pipeline Tools releases are distributed via GitHub releases (PyPI is optional).

### Release Process

1. **Set up GitHub token** (for release automation):
   ```sh
   # Copy example and add your token
   cp .envrc.example .envrc
   # Edit .envrc and set GITHUB_TOKEN
   direnv allow
   ```

2. **Bump version:**
   ```sh
   make set-version VERSION=0.1.7
   git add pyproject.toml
   git commit -m "chore: bump version to 0.1.7"
   git push origin main
   ```

3. **Create and push tag:**
   ```sh
   git tag v0.1.7
   git push origin v0.1.7
   ```

4. **Upload artifacts to GitHub release:**
   ```sh
   make release-ansible VERSION=v0.1.7 REPO=Sreyeesh/pipeline-tools
   ```

5. **Install latest release locally:**
   ```sh
   make release-local
   # If apt needs sudo:
   ANSIBLE_PLAYBOOK="ansible-playbook -K" make release-local
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
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml

# Install with pip:
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml -e pipeline_tools_installer=pip

# If pipx needs sudo packages:
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml -K

# No sudo available:
make ansible-install-nosudo
```

### Environment Variables

**Database location:**
```sh
export PIPELINE_TOOLS_DB=/path/to/custom/db.sqlite3
```
Default: `~/.pipeline_tools/db.sqlite3`

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
pipeline-tools --log-format json --log-level DEBUG <command>
```
Formats: `console` (default), `json`
Levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Metrics (StatsD):**
```sh
pipeline-tools --metrics-endpoint statsd://localhost:8125 <command>
```

**Request tracking:**
```sh
pipeline-tools --request-id my-custom-id <command>
```

### Health Check & Diagnostics
```sh
pipeline-tools doctor --json
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

List templates:
```sh
pipeline-tools shows templates
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
pipeline-tools/
├── src/pipeline_tools/
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

This is private/proprietary software owned by Sreyeesh Garimella. A license will need to be purchased for use.

Contact Sreyeesh Garimella for licensing and commercial inquiries.

---

## Contributing

1. Fork the repository
2. Create a feature branch following conventional commits
3. Run tests: `pytest tests/`
4. Install commit hooks: `make install-hooks`
5. Submit a pull request

For bug reports and feature requests, please open an issue on GitHub.
