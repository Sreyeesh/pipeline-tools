# Pipeline Tools

Artist-friendly CLI for creating and managing pipeline folder trees (shows, assets, shots, tasks).

---
## Quick start (users)
- Install from GitHub release (recommended):
  ```sh
  pipx install https://github.com/Sreyeesh/pipeline-tools/releases/download/v0.1.5/pipeline_tools-0.1.5-py3-none-any.whl
  # or
  pip install --user https://github.com/Sreyeesh/pipeline-tools/releases/download/v0.1.5/pipeline_tools-0.1.5-py3-none-any.whl
  ```
- Run common commands:
  ```sh
  pipeline-tools create --interactive
  pipeline-tools shows list
  pipeline-tools doctor --json
  ```

## Developer setup
- Local dev venv:
  ```sh
  ansible-playbook -i localhost, -c local ansible/dev.yml
  source .venv/bin/activate
  ```
- Docker workflow:
  ```sh
  make build
  make compose-list      # list commands
  make compose-test      # run tests in compose
  make compose-shell     # shell in container
  make pt ARGS="create --interactive"
  ```
- Conventional commits: `make install-hooks` installs the commit-msg hook; CI also checks commit messages.

## Release flow (GitHub assets)
1) Ensure `GITHUB_TOKEN` is loaded (direnv: copy `.envrc.example` to `.envrc`, set token, `direnv allow`).
2) Set version in `pyproject.toml` via Make:
   ```sh
   make set-version VERSION=0.1.5
   git add pyproject.toml
   git commit -m "chore: bump version to 0.1.5"
   git push origin main
   ```
3) Tag and push:
   ```sh
   git tag v0.1.5
   git push origin v0.1.5
   ```
4) Upload artifacts to the GitHub release:
   ```sh
   make release-ansible VERSION=v0.1.5 REPO=Sreyeesh/pipeline-tools
   ```
5) Install the latest main locally (pipx via Ansible):
   ```sh
   make release-local
   # if apt needs sudo: ANSIBLE_PLAYBOOK="ansible-playbook -K" make release-local
   ```

## Ansible install (pipx/pip)
From repo root (WSL/Linux):
```sh
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml          # pipx (default)
ansible-playbook -i localhost, -c local ansible/pipeline-tools.yml -e pipeline_tools_installer=pip
```
If pipx needs sudo packages, rerun with `-K` (sudo prompt). If sudo isn’t available, use `make ansible-install-nosudo`.

## Config and diagnostics
- Override DB path: `PIPELINE_TOOLS_DB=/path/to/db.sqlite3`.
- Templates: `animation_short` (default), `game_dev_small`, `drawing_single`.
- Logs/observability: `--log-format json`, `--log-level DEBUG|INFO|WARNING|ERROR`, `--request-id ...`, `--metrics-endpoint statsd://host:8125`.
- Health check: `pipeline-tools doctor --json` (exits non-zero on failure).

## GitHub releases only (no PyPI)
- Releases are built and attached to GitHub tags. PyPI is optional; to skip PyPI, just tag and run `make release-ansible`.
- Manual install from release asset:
  ```sh
  pipx install https://github.com/Sreyeesh/pipeline-tools/releases/download/vX.Y.Z/pipeline_tools-X.Y.Z-py3-none-any.whl
  ```
