IMAGE ?= pipely
PYTHON ?= python3
ANSIBLE_PLAYBOOK ?= ansible-playbook
ANSIBLE_VENV ?= .ansible-venv
ANSIBLE_BIN := $(ANSIBLE_VENV)/bin/ansible-playbook
PIPELINE_TOOLS_PIP_FLAGS ?=
INSTALLER ?= pipx
VERSION ?= v0.1.0
# Derive org/name from origin URL; override with REPO=org/name.
REPO ?= $(shell git config --get remote.origin.url | sed -E 's#.*/([^/]+/[^/.]+)(\.git)?#\1#')

# Auto-detect a sensible creative root; override with PROJECTS_ROOT or PIPELINE_TOOLS_ROOT.
PROJECTS_ROOT ?= $(shell if [ -n "$(PIPELINE_TOOLS_ROOT)" ]; then printf "%s" "$(PIPELINE_TOOLS_ROOT)"; elif [ -d /mnt/c/Projects ]; then printf "%s" "/mnt/c/Projects"; else printf "%s" "$$HOME/Projects"; fi)
DB_VOLUME ?= pipely-db

# Base docker run command with mounts; CMD is passed after.
RUN := docker run --rm -v "$(PROJECTS_ROOT)":/mnt/c/Projects -v $(DB_VOLUME):/root/.pipeline_tools $(IMAGE)
RUN_INTERACTIVE := docker run --rm -it -v "$(PROJECTS_ROOT)":/mnt/c/Projects -v $(DB_VOLUME):/root/.pipeline_tools $(IMAGE)

.PHONY: help build test test-docker pt pt-i pt-create pt-create-i doctor examples compose compose-list compose-test compose-shell list ansible-install ansible-pip ansible-dev doctor-json ansible-install-nosudo release-tag release-ansible install-hooks commit-check release-local check-monday deploy-local

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
	@echo "  ansible-install- install the CLI locally via Ansible (INSTALLER=pipx|pip, default pipx)"
	@echo "  ansible-pip    - shortcut for ansible-install with INSTALLER=pip"
	@echo "  ansible-dev    - bootstrap local dev venv and dev deps"
	@echo "  doctor-json    - run doctor with JSON output for automation"
	@echo "  ansible-install-nosudo - install without managing system packages (set pipeline_tools_manage_system_packages=false)"
	@echo "  release-tag    - tag current main with VERSION (default $(VERSION)) and push"
	@echo "  release-ansible- run Ansible release playbook for VERSION (default $(VERSION))"
	@echo "  release-local  - install current main locally via Ansible (pipx)"
	@echo "  install-hooks  - install commit-msg hook to enforce conventional commits"
	@echo "  commit-check   - lint commit messages in BASE..HEAD (defaults origin/main..HEAD)"
	@echo "  pypi-release   - build and upload to PyPI (requires PYPI_TOKEN env)"
	@echo "  set-version    - set version in pyproject.toml (VERSION=x.y.z)"
	@echo "  check-monday   - check if today is Monday (for releases)"
	@echo "  deploy-local   - deploy to local using Ansible (INSTALLER=pip|pipx, default pip)"
	@echo ""
	@echo "Variables: IMAGE (default: pipely), PROJECTS_ROOT (default: /mnt/c/Projects or $$HOME/Projects), DB_VOLUME (default: pipely-db)"
	@echo "           VERSION (default: $(VERSION)), REPO (default: $(REPO)), INSTALLER (default: $(INSTALLER))"

build:
	docker build -t $(IMAGE) .

test:
	$(MAKE) test-docker

test-docker: build
	docker run --rm -v "$(PWD)":/app -w /app --entrypoint /bin/sh $(IMAGE) -c "python3 -m pip install -e . -r requirements-dev.txt && python3 -m pytest"

compose-list:
	docker compose run --rm pipely --list

compose-test:
	docker compose run --rm pipely-test

compose-shell:
	docker compose run --rm pipely-shell

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
# make pt-create SHOW_CODE=DMO NAME="Demo Short 30s" TEMPLATE=game_dev_small
pt-create:
	@if [ -z "$(SHOW_CODE)" ] || [ -z "$(NAME)" ]; then echo "Usage: make pt-create SHOW_CODE=DMO NAME=\"Project Name\" [TEMPLATE=animation_short]"; exit 1; fi
	$(RUN) create -c $(SHOW_CODE) -n "$(NAME)" $(if $(TEMPLATE),-t $(TEMPLATE))

# Interactive creation (prompts). Example:
# make pt-create-i SHOW_CODE=DMO NAME="Demo Short 30s"
pt-create-i:
	$(RUN_INTERACTIVE) create --interactive $(if $(SHOW_CODE),-c $(SHOW_CODE)) $(if $(NAME),-n "$(NAME)") $(if $(TEMPLATE),-t $(TEMPLATE))

doctor:
	$(RUN) doctor

doctor-json:
	$(RUN) doctor --json

examples:
	$(RUN) --examples

ansible-install:
	$(ANSIBLE_PLAYBOOK) -i localhost, -c local ansible/pipely.yml -e pipeline_tools_installer=$(INSTALLER)

ansible-pip:
	$(MAKE) ansible-install INSTALLER=pip

ansible-dev:
	$(ANSIBLE_PLAYBOOK) -i localhost, -c local ansible/dev.yml

ansible-install-nosudo:
	$(ANSIBLE_PLAYBOOK) -i localhost, -c local ansible/pipely.yml -e pipeline_tools_installer=$(INSTALLER) -e pipeline_tools_manage_system_packages=false

release-tag:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then echo "Release tags must be created from main"; exit 1; fi
	@if ! git diff --quiet; then echo "Working tree not clean; commit or stash first"; exit 1; fi
	@if [ "$$(date -u +%u)" != "1" ]; then echo "Releases can only be published on Mondays (UTC). Today is day $$(date -u +%u) (1=Monday, 7=Sunday)."; exit 1; fi
	git tag $(VERSION)
	git push origin $(VERSION)

release-ansible:
	$(ANSIBLE_PLAYBOOK) -i localhost, -c local ansible/release.yml -e repo=$(REPO) -e version=$(VERSION)

release-local:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then echo "Release install should be run from main"; exit 1; fi
	$(ANSIBLE_PLAYBOOK) -i localhost, -c local ansible/pipely.yml -e pipeline_tools_installer=$(INSTALLER)

install-hooks:
	@if [ ! -d .git/hooks ]; then echo ".git/hooks not found; run inside a git clone."; exit 1; fi
	cp commitlint.py .git/hooks/commit-msg
	chmod +x .git/hooks/commit-msg

commit-check:
	BASE=$${BASE:-$$(git merge-base origin/main HEAD 2>/dev/null || git rev-parse HEAD^)}; \
	HEAD=$${HEAD:-$$(git rev-parse HEAD)}; \
	python commitlint.py range $$BASE $$HEAD

pypi-release:
	@if [ -z "$(PYPI_TOKEN)" ]; then echo "PYPI_TOKEN not set; aborting"; exit 1; fi
	python3 -m pip install --upgrade pip build twine
	rm -rf dist
	python3 -m build
	TWINE_USERNAME=__token__ TWINE_PASSWORD=$(PYPI_TOKEN) twine upload dist/*

set-version:
	@if [ -z "$(VERSION)" ]; then echo "VERSION not set; pass VERSION=x.y.z"; exit 1; fi
	python3 -c "import pathlib,sys; p=pathlib.Path('pyproject.toml'); lines=p.read_text().splitlines(); out=[]; found=False; \
  [out.append(f'version = \"{sys.argv[1]}\"') if ln.strip().startswith('version') else out.append(ln) or None for ln in lines or [None]]; \
  found=any(ln.strip().startswith('version') for ln in lines); \
  (sys.exit('version key not found in pyproject.toml') if not found else p.write_text('\\n'.join(out)+'\\n'))" "${VERSION}"

check-monday:
	@DAY=$$(date -u +%u); \
	if [ "$$DAY" = "1" ]; then \
		echo "✅ Today is Monday (UTC). You can publish releases."; \
	else \
		echo "❌ Today is NOT Monday (UTC). Day of week: $$DAY (1=Monday, 7=Sunday)"; \
		echo "Releases can only be published on Mondays."; \
		exit 1; \
	fi

deploy-local: $(ANSIBLE_BIN)
	$(ANSIBLE_BIN) ansible/pipely.yml -e pipeline_tools_installer=pip -e pipeline_tools_manage_system_packages=false -e "pipeline_tools_pip_flags=$(PIPELINE_TOOLS_PIP_FLAGS)"

$(ANSIBLE_BIN):
	@echo "Creating Ansible venv with pinned Jinja (avoids system Jinja3 issues)..."
	@$(PYTHON) -m venv $(ANSIBLE_VENV)
	@$(ANSIBLE_VENV)/bin/pip install --upgrade pip >/dev/null
	@$(ANSIBLE_VENV)/bin/pip install "ansible-core>=2.13,<2.17" "Jinja2<3.1" >/dev/null
