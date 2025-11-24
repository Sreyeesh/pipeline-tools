IMAGE ?= pipeline-tools
PROJECTS_ROOT ?= /mnt/c/Projects
DB_VOLUME ?= pipeline-tools-db

# Base docker run command with mounts; CMD is passed after.
RUN := docker run --rm -v $(PROJECTS_ROOT):/mnt/c/Projects -v $(DB_VOLUME):/root/.pipeline_tools $(IMAGE)

.PHONY: help build pt pt-create pt-create-i doctor examples

help:
	@echo "Targets:"
	@echo "  build          - docker build -t $(IMAGE) ."
	@echo "  pt             - run arbitrary args via pipeline_tools.cli (ARGS=\"create --interactive\")"
	@echo "  pt-create      - quick create (requires SHOW_CODE and NAME; optional TEMPLATE)"
	@echo "  pt-create-i    - guided interactive create (optional SHOW_CODE/NAME/TEMPLATE)"
	@echo "  doctor         - run environment health check"
	@echo "  examples       - show common commands"
	@echo ""
	@echo "Variables: IMAGE (default: pipeline-tools), PROJECTS_ROOT (default: /mnt/c/Projects), DB_VOLUME (default: pipeline-tools-db)"

build:
	docker build -t $(IMAGE) .

# Generic passthrough to the launcher CLI.
pt:
	$(RUN) pipeline_tools.cli $(ARGS)

# Quick create; requires SHOW_CODE and NAME. Example:
# make pt-create SHOW_CODE=PKS NAME="Poku Short 30s" TEMPLATE=game_dev_small
pt-create:
	@if [ -z "$(SHOW_CODE)" ] || [ -z "$(NAME)" ]; then echo "Usage: make pt-create SHOW_CODE=PKS NAME=\"Project Name\" [TEMPLATE=animation_short]"; exit 1; fi
	$(RUN) pipeline_tools.cli create -c $(SHOW_CODE) -n "$(NAME)" $(if $(TEMPLATE),-t $(TEMPLATE))

# Interactive creation (prompts). Example:
# make pt-create-i SHOW_CODE=PKS NAME="Poku Short 30s"
pt-create-i:
	$(RUN) pipeline_tools.cli create --interactive $(if $(SHOW_CODE),-c $(SHOW_CODE)) $(if $(NAME),-n "$(NAME)") $(if $(TEMPLATE),-t $(TEMPLATE))

doctor:
	$(RUN) pipeline_tools.tools.admin.main doctor

examples:
	$(RUN) pipeline_tools.cli examples
