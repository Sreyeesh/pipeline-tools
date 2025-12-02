# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.8.1] - 2025-12-02
### :bug: Bug Fixes
- Ensure interactive shell forwards core CLI commands (tasks/assets/shows/versions/admin/project/open) so artists can work in one place

### :memo: Documentation
- Clarify quick start, developer setup, and licensing (free for artists; contact for commercial/studio use)

### :test_tube: Tests
- Add coverage for interactive passthrough, database helpers, path resolution, and DCC launcher executable lookup

## [v0.1.8] - 2025-12-01
### :sparkles: New Features
- [`03ad1c9`](https://github.com/Sreyeesh/pipeline-tools/commit/03ad1c932a8fd42a800304bb4d54528844036256) - add reference folder to animation template *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`b11e8d3`](https://github.com/Sreyeesh/pipeline-tools/commit/b11e8d3e00dc6ceb1b09d3eb46193abd32310fcb) - add Git and Git LFS support to project creator *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`bfe04f8`](https://github.com/Sreyeesh/pipeline-tools/commit/bfe04f8e14bf4a7acafe0b2d26ecf75442bd46c6) - add automatic starter file creation for animation projects *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`1cdb2f9`](https://github.com/Sreyeesh/pipeline-tools/commit/1cdb2f99b1c04aa76e5ac4e4d8db8c0e858de234) - enforce Monday-only release policy *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`13d3a1e`](https://github.com/Sreyeesh/pipeline-tools/commit/13d3a1e924eb72fac25bad2c0efd45939dc8eb46) - add Monday check to release-tag and deploy-local targets *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`824ad92`](https://github.com/Sreyeesh/pipeline-tools/commit/824ad92831a9e56df39d381f136887cf10dbc9b5) - add interactive shell mode with autocomplete and DCC launcher *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`c013652`](https://github.com/Sreyeesh/pipeline-tools/commit/c013652c31240531979a2e05b4a882f37ed09cb2) - add GUI-like interface and database registration for projects *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`9df4843`](https://github.com/Sreyeesh/pipeline-tools/commit/9df48430f9d5a42a6c4cc3db5bcafb1b234362bc) - enhance interactive UX with git workflow and PureRef support *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`7942867`](https://github.com/Sreyeesh/pipeline-tools/commit/79428670445ea7a0cdb97b8af426606a1a8d50e6) - add automatic changelog generation to release workflow *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :bug: Bug Fixes
- [`4c4dae9`](https://github.com/Sreyeesh/pipeline-tools/commit/4c4dae91e6056c8fafac0879bc547352e53b7fd6) - add prompt-toolkit to requirements.txt for Docker builds *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`fe2fe38`](https://github.com/Sreyeesh/pipeline-tools/commit/fe2fe387443f7817bc77a5b86bc3f3d8763989b7) - update test to match new interactive default mode *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :wrench: Chores
- [`7a03459`](https://github.com/Sreyeesh/pipeline-tools/commit/7a0345907a05852f339cc630b8ba6b67e17d07e2) - merge dev into main for v0.1.8 release *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`b869f19`](https://github.com/Sreyeesh/pipeline-tools/commit/b869f19f578a28c0cf56ea8af078d92ce0c8a3bc) - bump version to 0.1.8 *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`ee1439b`](https://github.com/Sreyeesh/pipeline-tools/commit/ee1439b031c6b5b6a5c2d423e4df4225bd566ca5) - disable automatic PyPI publish workflow *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`47c9e32`](https://github.com/Sreyeesh/pipeline-tools/commit/47c9e32aef2e26eedf82b50ae4505c5ad65b5259) - disable automatic PyPI publishing *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*


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

[Unreleased]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.1...HEAD
[0.1.8.1]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8...v0.1.8.1
[0.1.7]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.0...v0.1.5
[0.1.0]: https://github.com/Sreyeesh/pipeline-tools/releases/tag/v0.1.0
[v0.1.8]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.7...v0.1.8
