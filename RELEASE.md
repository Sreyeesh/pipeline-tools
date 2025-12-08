# Release Workflow

This document describes the development and release workflow for pipeline-tools.

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code. All releases are tagged from here. |
| `dev` | Integration branch for features and fixes. |
| `feature/*` | Feature branches (optional, for larger features). |

## Development Workflow

### 1. Make Changes on `dev`

```bash
# Ensure you're on dev and up to date
git checkout dev
git pull origin dev

# Make your changes
# ... edit files ...

# Stage and commit with conventional commit format
git add .
git commit -m "feat: add new feature description"
```

### 2. Conventional Commits

All commits **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]
```

#### Commit Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor (0.X.0) |
| `fix` | Bug fix | Patch (0.0.X) |
| `docs` | Documentation only | None |
| `chore` | Maintenance tasks | None |
| `refactor` | Code refactoring | None |
| `test` | Adding/updating tests | None |
| `style` | Code style changes | None |
| `perf` | Performance improvements | Patch |

#### Examples

```bash
# Feature
git commit -m "feat: add batch export for assets"

# Bug fix
git commit -m "fix: resolve Krita launcher crash on WSL"

# Documentation
git commit -m "docs: update installation instructions"

# Chore
git commit -m "chore: bump version to 0.1.14"
```

### 3. Push to Dev

```bash
git push origin dev
```

## Release Process

### Quick Release (Single Command)

```bash
# From dev branch - merges to main, tags, and deploys
git checkout main && git pull origin main && git merge dev && git push origin main
```

Then create a release:

```bash
# Set the new version
make set-version VERSION=0.1.14

# Commit version bump
git add pyproject.toml
git commit -m "chore: bump version to 0.1.14"
git push origin main

# Create and push tag (triggers GitHub Actions)
git tag v0.1.14
git push origin v0.1.14

# Switch back to dev
git checkout dev
git merge main
git push origin dev
```

### Step-by-Step Release

#### 1. Merge Dev to Main

```bash
git checkout main
git pull origin main
git merge dev
git push origin main
```

#### 2. Update Version

```bash
# Update pyproject.toml
make set-version VERSION=0.1.14

# Also update __init__.py
# Edit src/pipeline_tools/__init__.py and change __version__

git add pyproject.toml src/pipeline_tools/__init__.py
git commit -m "chore: bump version to 0.1.14"
git push origin main
```

#### 3. Create Release Tag

```bash
git tag v0.1.14
git push origin v0.1.14
```

This triggers the GitHub Actions workflow which:
- Runs tests
- Builds the wheel package
- Creates a GitHub Release
- Updates CHANGELOG.md
- Updates website changelog

#### 4. Deploy Locally

```bash
make release-local
```

#### 5. Sync Dev with Main

```bash
git checkout dev
git merge main
git push origin dev
```

## Automated Release (GitHub Actions)

When you push a tag matching `v*`, the release workflow automatically:

1. **Tests** - Runs the test suite
2. **Builds** - Creates wheel package (`pipely-X.Y.Z-py3-none-any.whl`)
3. **Releases** - Creates GitHub Release with artifacts
4. **Changelog** - Updates CHANGELOG.md from commit history
5. **Website** - Updates docs/index.html changelog section

### Workflow File

See [.github/workflows/release.yml](.github/workflows/release.yml)

## Local Development

### Install Development Dependencies

```bash
make ansible-dev
```

### Run Tests

```bash
# Via Docker
make test-docker

# Or locally with pytest
pytest
```

### Install Locally for Testing

```bash
# Install current branch locally
make release-local

# Verify installation
pipely --version
```

## Makefile Reference

| Command | Description |
|---------|-------------|
| `make release-local` | Install current branch locally via Ansible |
| `make set-version VERSION=X.Y.Z` | Update version in pyproject.toml |
| `make test-docker` | Run tests in Docker |
| `make ansible-dev` | Set up local dev environment |
| `make install-hooks` | Install commit message linting hook |
| `make commit-check` | Validate commit messages |

## Troubleshooting

### Git Push Rejected

```bash
# Pull and rebase before pushing
git pull --rebase origin main
git push origin main
```

### Version Mismatch

Ensure version is updated in both files:
- `pyproject.toml` - `version = "X.Y.Z"`
- `src/pipeline_tools/__init__.py` - `__version__ = "X.Y.Z"`

### Failed Release Workflow

Check GitHub Actions logs at:
`https://github.com/Sreyeesh/pipeline-tools/actions`

### Monday Release Restriction

The `release-tag` target only works on Mondays (UTC). To bypass:

```bash
# Use release-ansible with override
make release-ansible VERSION=v0.1.14 ALLOW_NON_MONDAY=true
```

Or create tags manually:

```bash
git tag v0.1.14
git push origin v0.1.14
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for the complete version history.
