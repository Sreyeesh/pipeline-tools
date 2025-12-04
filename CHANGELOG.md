# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.10.3] - 2025-12-04
### :bug: Bug Fixes
- Fix Blender workfile crash caused by undefined `dcc_kind` variable.
- Create valid Krita files with proper ZIP structure, layer data (1920x1080 RGBA), and sRGB ICC profile.
- Improve error handling for Blender file creation with better path escaping for WSL.

### :sparkles: New Features
- Add `info` command to view current project information without opening app picker.
- Blender auto-saves to correct versioned filename when pressing Ctrl+S (via `target_file_path` parameter).

## [v0.1.10.2] - 2025-12-03
### :sparkles: New Features
- Interactive Step 3 artist picker: browse existing workfiles, open by number, or create+open a new version without typing commands.
- Add first-class Fountain (`.fountain`) and Markdown (`.md`) workfile kinds so scripts/docs show up in the app list.

### :wrench: Maintenance
- Projects now always get a `.gitignore` (with `05_WORK/` ignored) and auto git init when available; initial commits are skipped to keep the flow low-friction.

## [v0.1.10.1] - 2025-12-03
### :bug: Bug Fixes
- `admin files --open` now falls back to Windows Explorer on WSL when system openers are missing.

## [v0.1.10] - 2025-12-03
### :bug: Bug Fixes
- `admin files --open` now falls back gracefully when a system opener (e.g., xdg-open) is missing and prints the path to open manually.

## [v0.1.9] - 2025-12-03
### :sparkles: New Features
- Workfiles flow inside Pipely: add/list/open per asset/shot with versioned filenames.
- Admin helpers to copy files into 01_ADMIN and drop in the bundled animation bible template.
- DCC launcher accepts file paths again for seamless open from Pipely commands.

### :memo: Documentation
- Website/cards updated for 0.1.9 and the new workfile/admin flows.

### :test_tube: Tests
- Coverage added for admin template copy and workfile creation/opening.

## [v0.1.8.4] - 2025-12-03
### :sparkles: New Features
- Toggle workspace summaries in interactive to see shots/assets/tasks after commands.
- List or open 01_ADMIN reference files from the prompt with `admin files`.
- Optionally set a git remote and push to main when creating a project.

### :memo: Documentation
- Refresh docs/website for 0.1.8.4, including install links and changelog highlights.

### :wrench: Maintenance
- Default CLI log level set to WARNING for quieter artist-facing output.

### :test_tube: Tests
- Add coverage for the workspace summary toggle and admin file listing/opening.

## [v0.1.8.3] - 2025-12-03
### :sparkles: New Features
- Add `--delete-folders` to `shows delete` to remove the show folder and DB entry together.

### :bug: Bug Fixes
- Clear `current_show` when deleting a show to avoid stale selections.

### :test_tube: Tests
- Add coverage for show deletion with folder removal.


## [v0.1.8.2] - 2025-12-03
### :sparkles: New Features
- Add delete commands for tasks and versions (with interactive autocomplete support) to complete CRUD coverage.

### :bug: Bug Fixes
- Keep `shows create` shorthand together in interactive, accept multiword shot descriptions without quotes, and allow positional show codes for `shots list`.
- Improve changelog readability in light mode and ensure the dark-mode toggle is available across docs.

### :memo: Documentation
- Refresh the workflow demo with the standard artist flow and surface the theme toggle on the changelog page.

### :test_tube: Tests
- Add coverage for `shows create` shorthand and task/version delete commands.


## [0.1.8.2] - 2025-12-03
### :sparkles: Highlights
- Complete CRUD: add delete for tasks and versions; interactive autocomplete shows the new commands.
- Friendlier interactive: shorthand `shows create` works reliably; shots accept multiword descriptions; `shots list` accepts positional show codes.
- Docs polish: improved light-mode readability, theme toggle on changelog page, and refreshed workflow demo.
- Tests added for shorthand handling and the new delete commands.


## [v0.1.8.1] - 2025-12-02
### :sparkles: New Features
- [`ce25ced`](https://github.com/Sreyeesh/pipeline-tools/commit/ce25ced738d9962698e2118023cd03e97cc07b14) - rebrand from Pipeline Tools to Pipely *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`f4a704c`](https://github.com/Sreyeesh/pipeline-tools/commit/f4a704cb79e6923a50b7bfcb7951f04ba0da0305) - add professional landing page for Pipely with SEO optimization *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`249a481`](https://github.com/Sreyeesh/pipeline-tools/commit/249a481c540b154fa0877b682a4e07d5d70f31c2) - add smooth scrolling and scroll animations to landing page *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`cdbd7ee`](https://github.com/Sreyeesh/pipeline-tools/commit/cdbd7eeeec4a81c54e64069b1544a045ec72bb96) - add dark mode, mobile optimization, and smoother animations to landing page *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`6be8854`](https://github.com/Sreyeesh/pipeline-tools/commit/6be88543be87fcafc735aa8c3aa9baf9a79fc363) - add dark mode, mobile optimization, and smoother animations to landing page *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`fe0f116`](https://github.com/Sreyeesh/pipeline-tools/commit/fe0f116f6c0fe7f914b008f403903b3052c43dea) - forward core CLI commands in interactive *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :bug: Bug Fixes
- [`881f38c`](https://github.com/Sreyeesh/pipeline-tools/commit/881f38c8f1168c94cf9b42325172705d64f27292) - update __version__ to 0.1.8 in __init__.py *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`7543392`](https://github.com/Sreyeesh/pipeline-tools/commit/754339288f01789e86b5d9b41d3ef56f68703321) - improve dark mode readability on landing page *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`eab752f`](https://github.com/Sreyeesh/pipeline-tools/commit/eab752f5a67ddc2dacbc2ff463780805971cc75f) - make Pipely logo a clickable link *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :recycle: Refactors
- [`2e3e971`](https://github.com/Sreyeesh/pipeline-tools/commit/2e3e971a01d976955cd839b5d31a3f72680a2429) - modularize landing page assets *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :white_check_mark: Tests
- [`f3e9e2a`](https://github.com/Sreyeesh/pipeline-tools/commit/f3e9e2a7286e073fd5215be886b0d15b2e2eb172) - cover interactive passthrough and open auto-project *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`82a2aec`](https://github.com/Sreyeesh/pipeline-tools/commit/82a2aec4f66482f3be744b50b4d7ac76e5348f6e) - cover db helpers, paths, and dcc launcher *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*

### :wrench: Chores
- [`6eabcd3`](https://github.com/Sreyeesh/pipeline-tools/commit/6eabcd3516c2866c724a985058891ce9f1dd8945) - rename Ansible playbook to pipely.yml and update references *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`11bc45f`](https://github.com/Sreyeesh/pipeline-tools/commit/11bc45f6d403c175694480fef27be99847cc3465) - remove old pipeline-tools.yml playbook *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`b1f2d2d`](https://github.com/Sreyeesh/pipeline-tools/commit/b1f2d2d05920857f7c38a4a4c02e1de9e8724aaf) - merge dev to main - complete rebrand to Pipely *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`42ceee5`](https://github.com/Sreyeesh/pipeline-tools/commit/42ceee5b72360c4d61edabb251a72d7a08489040) - update contact email to toucan.sg@gmail.com *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`ad70dac`](https://github.com/Sreyeesh/pipeline-tools/commit/ad70dac62868df335093e8fb1d8c45d9728ab2cd) - remove testimonials section from landing page *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*
- [`288d348`](https://github.com/Sreyeesh/pipeline-tools/commit/288d34846cb0614c1e561030ce7fad1f37fdd571) - bump version to 0.1.8.1 *(commit by [@Sreyeesh](https://github.com/Sreyeesh))*


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

[Unreleased]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.3...HEAD
[0.1.8.3]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.2...v0.1.8.3
[0.1.8.2]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.1...v0.1.8.2
[0.1.8.1]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8...v0.1.8.1
[0.1.7]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.0...v0.1.5
[0.1.0]: https://github.com/Sreyeesh/pipeline-tools/releases/tag/v0.1.0
[v0.1.8.3]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.2...v0.1.8.3
[v0.1.8.2]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8.1...v0.1.8.2
[v0.1.8]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.7...v0.1.8
[v0.1.8.1]: https://github.com/Sreyeesh/pipeline-tools/compare/v0.1.8...v0.1.8.1
