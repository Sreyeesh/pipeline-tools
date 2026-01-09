# Build the Pipely Docker Image via Ansible

Use the bundled playbook when you want Ansible to build (or rebuild) the Docker image that Pipely runs inside. No pip/pipx installs touch your host—everything happens inside the container.

## Prerequisites

- Docker CLI installed and able to run `docker build`
- Ansible (`python3 -m pip install --user ansible`)

## Quick Start

From the project root:

```sh
make ansible-install
```

That runs:

```sh
ansible-playbook -i localhost, -c local ansible/pipely.yml -e pipely_image=pipely-loop
```

### What the playbook does

1. Checks that `docker` is available.
2. Builds the Pipely image from the current source tree (uses Docker cache when possible).
3. Runs a quick smoke test inside the container (`python -m pipeline_tools.cli --version`).

Override the image tag if you like:

```sh
make ansible-install IMAGE=pipely-dev
# or directly
ansible-playbook -i localhost, -c local ansible/pipely.yml -e pipely_image=pipely-dev
```

> The Makefile now creates a local `.ansible-venv/` automatically, pinning `ansible-core` and `Jinja2` versions so you don't run into system-level dependency issues. Run `make ansible-deps` if you just want to bootstrap that venv ahead of time.

## Local dev setup (uv)

To configure a local WSL2 or Windows dev environment with `uv`, use:

```sh
ansible-playbook -i localhost, -c local ansible/dev.yml
```

On Windows, ensure your Python `Scripts` directory is on `PATH` so `uv` is available in Command Prompt.

## Windows via SSH (local host)

When running Ansible from WSL2, set your Windows SSH host/user in env vars and run:

```sh
export WIN_HOST=YOUR_WINDOWS_HOST
export WIN_USER="YOUR_WINDOWS_USER"
make ansible-win-ssh
```

Find your Windows host IP and username:

```bat
ipconfig | findstr /R /C:"IPv4 Address"
echo %USERNAME%
```

Note: if you move networks or reboot, the Windows host IP can change. Re-run the command above before setting `WIN_HOST`.

Pass a custom repo path if you cloned elsewhere:

```sh
export WIN_REPO_PARENT="C:\\Users\\sgari\\projects"
export WIN_REPO_PATH="C:\\Users\\sgari\\projects\\pipeline-tools"
make ansible-win-ssh
```

## Use the image

Once built, run Pipely via Docker (or the repo’s `./pipely` wrapper):

```sh
./pipely loop --help
./pipely loop create --project Demo --target Hero
```

## Docker dev workflow

The Docker setup uses `docker-compose.yml` and the `pipely-shell` service for a repeatable dev environment.

Common commands:

```sh
make build    # build the dev image
make up       # start the container in the background
make sh       # open an interactive shell (fresh container)
make run ARGS="init --name Demo --type art"
make down     # stop containers
make clean    # remove containers and volumes
```

Use `make sh` when you want a container with the repo mounted and ready for `pip install -e .` and tests.

## Docker vs Ansible local setup

Use Docker when you want isolation and repeatability without touching host Python. Use Ansible when you want `uv` and `pipely` installed natively on WSL2/Windows with PATH configured for local shells.
