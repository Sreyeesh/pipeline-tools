# Pipely developer shortcuts for Docker/Compose

COMPOSE ?= docker compose
SERVICE ?= pipely-shell
COMPOSE_FILE ?= docker-compose.yml
ARGS ?= loop --help
ANSIBLE_VENV ?= .ansible-venv
ANSIBLE_BIN := $(ANSIBLE_VENV)/bin/ansible-playbook
ANSIBLE_LOCAL_TEMP ?= $(CURDIR)/.ansible-tmp
ANSIBLE_REMOTE_TEMP ?= $(CURDIR)/.ansible-remote-tmp

.PHONY: build up sh run down clean ansible ansible-dev ansible-win-ssh ansible-install-local ansible-deps

# Build the dev image (docker compose build)
build:
	$(COMPOSE) -f $(COMPOSE_FILE) build $(SERVICE)

# Start the dev environment in the background
up:
	$(COMPOSE) -f $(COMPOSE_FILE) up -d $(SERVICE)

# Open an interactive shell (new container each time)
sh:
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm $(SERVICE) bash

# Run pipely inside the container (pass ARGS="loop create ...")
run:
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm $(SERVICE) pipely $(ARGS)

# Stop the running containers
down:
	$(COMPOSE) -f $(COMPOSE_FILE) down

# Remove containers and volumes for a clean slate
clean:
	$(COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans

# Run the Ansible playbook to rebuild Docker image + dev deps
ansible: $(ANSIBLE_BIN)
	@mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ANSIBLE_FORKS=1 $(ANSIBLE_BIN) -i localhost, -c local ansible/pipely.yml

# Run the Ansible playbook to set up a local dev environment (uv + deps)
ansible-dev: $(ANSIBLE_BIN)
	@mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ANSIBLE_FORKS=1 $(ANSIBLE_BIN) -i localhost, -c local ansible/dev.yml

# Configure uv + pipely on Windows via SSH
ansible-win-ssh: $(ANSIBLE_BIN)
	@test -n "$(WIN_HOST)" || (echo "Set WIN_HOST (e.g. 172.27.176.1)"; exit 1)
	@test -n "$(WIN_USER)" || (echo "Set WIN_USER (e.g. GL1-I9-16\\sgari)"; exit 1)
	@mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ANSIBLE_FORKS=1 \
	$(ANSIBLE_BIN) -i ansible/inventory/windows_ssh.ini ansible/windows_ssh.yml \
	-e "ansible_host=$(WIN_HOST) ansible_user=$(WIN_USER) pipely_repo_parent=$(WIN_REPO_PARENT) pipely_repo_path=$(WIN_REPO_PATH)"

# Run the Ansible playbook and install Pipely locally without a venv
ansible-install-local: $(ANSIBLE_BIN)
	@mkdir -p $(ANSIBLE_LOCAL_TEMP) $(ANSIBLE_REMOTE_TEMP)
	ANSIBLE_LOCAL_TEMP=$(ANSIBLE_LOCAL_TEMP) ANSIBLE_REMOTE_TEMP=$(ANSIBLE_REMOTE_TEMP) ANSIBLE_FORKS=1 $(ANSIBLE_BIN) -i localhost, -c local ansible/pipely.yml -e pipely_install_local=true -e pipely_install_mode=user

ansible-deps: $(ANSIBLE_BIN)
	@echo "Ansible virtualenv ready at $(ANSIBLE_VENV)"

$(ANSIBLE_BIN):
	@echo "Setting up Ansible virtualenv with pinned deps..."
	@python3 -m venv $(ANSIBLE_VENV)
	@$(ANSIBLE_VENV)/bin/pip install --upgrade pip >/dev/null
	@$(ANSIBLE_VENV)/bin/pip install \"ansible-core>=2.13,<2.17\" \"Jinja2<3.1\" >/dev/null
