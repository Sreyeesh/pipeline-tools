# Pipely developer shortcuts for Docker/Compose

COMPOSE ?= docker compose
SERVICE ?= pipely-shell
COMPOSE_FILE ?= docker-compose.yml
ARGS ?= loop --help
ANSIBLE_VENV ?= .ansible-venv
ANSIBLE_BIN := $(ANSIBLE_VENV)/bin/ansible-playbook
ANSIBLE_LOCAL_TEMP ?= $(CURDIR)/.ansible-tmp
ANSIBLE_REMOTE_TEMP ?= $(CURDIR)/.ansible-remote-tmp

.PHONY: build up sh run down clean ansible ansible-deps

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

ansible-deps: $(ANSIBLE_BIN)
	@echo "Ansible virtualenv ready at $(ANSIBLE_VENV)"

$(ANSIBLE_BIN):
	@echo "Setting up Ansible virtualenv with pinned deps..."
	@python3 -m venv $(ANSIBLE_VENV)
	@$(ANSIBLE_VENV)/bin/pip install --upgrade pip >/dev/null
	@$(ANSIBLE_VENV)/bin/pip install \"ansible-core>=2.13,<2.17\" \"Jinja2<3.1\" >/dev/null
