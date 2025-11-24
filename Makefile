IMAGE ?= pipeline-tools
PYTHON ?= python3

# Auto-detect a sensible creative root; override with PROJECTS_ROOT or PIPELINE_TOOLS_ROOT.
PROJECTS_ROOT ?= $(shell if [ -n "$(PIPELINE_TOOLS_ROOT)" ]; then printf "%s" "$(PIPELINE_TOOLS_ROOT)"; elif [ -d /mnt/c/Projects ]; then printf "%s" "/mnt/c/Projects"; else printf "%s" "$$HOME/Projects"; fi)
DB_VOLUME ?= pipeline-tools-db

# Base docker run command with mounts; CMD is passed after.
RUN := docker run --rm -v "$(PROJECTS_ROOT)":/mnt/c/Projects -v $(DB_VOLUME):/root/.pipeline_tools $(IMAGE)
RUN_INTERACTIVE := docker run --rm -it -v "$(PROJECTS_ROOT)":/mnt/c/Projects -v $(DB_VOLUME):/root/.pipeline_tools $(IMAGE)

.PHONY: help build test test-docker pt pt-i pt-create pt-create-i doctor examples compose compose-list compose-test compose-shell list

help:
	@echo "Targets:"
	@echo "  build          - docker build -t $(IMAGE) ."
	@echo "  pt             - run arbitrary args via the Typer CLI (ARGS=\"--list\" or \"create --interactive\")"
	@echo "  pt-create      - quick create (requires SHOW_CODE and NAME; optional TEMPLATE)"
	@echo "  pt-create-i    - guided interactive create (optional SHOW_CODE/NAME/TEMPLATE)"
	@echo "  doctor         - run environment health check"
	@echo "  examples       - show common commands"
	@echo "  test           - run tests inside docker (alias of test-docker)"
	@echo "  test-docker    - run tests inside docker"
	@echo "  compose-list   - list CLI commands via docker-compose"
	@echo "  compose-test   - run pytest via docker-compose"
	@echo "  compose-shell  - open a shell in the container with mounts"
	@echo "  compose        - alias for compose-list"
	@echo "  list           - alias for compose-list"
	@echo ""
	@echo "Variables: IMAGE (default: pipeline-tools), PROJECTS_ROOT (default: /mnt/c/Projects or $$HOME/Projects), DB_VOLUME (default: pipeline-tools-db)"

build:
	docker build -t $(IMAGE) .

test:
	$(MAKE) test-docker

test-docker: build
	docker run --rm -v "$(PWD)":/app -w /app --entrypoint /bin/sh $(IMAGE) -c "python3 -m pip install -e . -r requirements-dev.txt && python3 -m pytest"

compose-list:
	docker compose run --rm pipeline-tools --list

compose-test:
	docker compose run --rm pipeline-tools-test

compose-shell:
	docker compose run --rm pipeline-tools-shell

compose: compose-list

list: compose-list

# Generic passthrough to the launcher CLI.
# If ARGS includes --interactive, allocate a TTY.
pt:
	@if echo "$(ARGS)" | grep -q -- "--interactive"; then \
		$(RUN_INTERACTIVE) $(ARGS); \
	else \
		$(RUN) $(ARGS); \
	fi

# Interactive passthrough (allocates TTY).
pt-i:
	$(RUN_INTERACTIVE) $(ARGS)

# Quick create; requires SHOW_CODE and NAME. Example:
# make pt-create SHOW_CODE=PKS NAME="Poku Short 30s" TEMPLATE=game_dev_small
pt-create:
	@if [ -z "$(SHOW_CODE)" ] || [ -z "$(NAME)" ]; then echo "Usage: make pt-create SHOW_CODE=PKS NAME=\"Project Name\" [TEMPLATE=animation_short]"; exit 1; fi
	$(RUN) create -c $(SHOW_CODE) -n "$(NAME)" $(if $(TEMPLATE),-t $(TEMPLATE))

# Interactive creation (prompts). Example:
# make pt-create-i SHOW_CODE=PKS NAME="Poku Short 30s"
pt-create-i:
	$(RUN_INTERACTIVE) create --interactive $(if $(SHOW_CODE),-c $(SHOW_CODE)) $(if $(NAME),-n "$(NAME)") $(if $(TEMPLATE),-t $(TEMPLATE))

doctor:
	$(RUN) doctor

examples:
	$(RUN) --examples
