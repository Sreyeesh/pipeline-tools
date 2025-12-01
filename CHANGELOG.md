# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.8] - 2025-12-01

### Added
- Context-aware tab autocomplete with project/DCC suggestions
- Git workflow integration with `status` and `commit` commands
- Display git branch in project selection menu
- Beautiful status display with branch, remote, and file tracking
- PureRef DCC launcher support (Linux/Windows/macOS)
- Loading bar animations for app launches
- Visual indicators for git status (📝 Modified, ➕ Added, etc.)

### Changed
- **Rebranded from "Pipeline Tools" to "Pipely"** - New name, tagline, and branding across all interfaces
- Package name changed from `pipeline-tools` to `pipely`
- CLI command changed from `pipeline-tools` to `pipely`
- Updated tagline: "Pipeline management made lovely"
- Log level from INFO to WARNING for cleaner end-user output
- All prompts updated to encourage TAB autocomplete usage

## [0.1.7] - 2024-11-30

### Added
- GUI-like interface as default mode
- Database registration for all projects
- Interactive shell mode with autocomplete
- DCC launcher for Krita and Blender
- Git and Git LFS support in project creator
- Automatic starter file creation for animation projects

### Changed
- Interactive mode now default (instead of CLI commands)
- Projects always registered to database, not just disk

### Fixed
- prompt-toolkit dependency for Docker builds

## [0.1.6] - 2024-11-25

### Added
- Version flag (--version)
- Set-version helper target

### Changed
- Internal code cleanup (removed Poku references)

## [0.1.5] - 2024-11-23

### Added
- Observability with structured logging and StatsD metrics
- Release automation with Monday-only policy
- Commitlint for conventional commits

## [0.1.0] - 2024-11-22

### Added
- Initial project creator CLI
- Three project templates (animation_short, game_dev_small, drawing_single)
- SQLite-backed show and asset workflows
- Cross-platform creative root support
- Docker containerized CLI workflow
- Ansible installation playbooks
- Asset, shot, task, and version tracking
- Character thumbnail generation
- Tag-based search functionality

[Unreleased]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.7...HEAD
[0.1.7]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.0...v0.1.5
[0.1.0]: https://github.com/Sreyeesh/pipeline-tools/releases/tag/v0.1.0
