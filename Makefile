# Pipely developer shortcuts for Docker/Compose

COMPOSE ?= docker compose
SERVICE ?= pipely-shell
COMPOSE_FILE ?= docker-compose.yml
ARGS ?= loop --help

.PHONY: build up sh run down clean

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
