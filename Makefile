REPO        := analizza-ai/analizza-marketplace
MARKETPLACE := analizza-marketplace
PLUGIN      ?= analizza-skills
PLUGINS     := analizza-skills

.DEFAULT_GOAL := help
SHELL := /bin/bash

##@ Geral

.PHONY: help
help: ## Mostra esta ajuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""

##@ Instalação

.PHONY: marketplace-add
marketplace-add: ## Registra este repositório como marketplace
	claude plugin marketplace add $(REPO)

.PHONY: install
install: ## Instala o plugin (PLUGIN=analizza-skills) a partir do marketplace
	claude plugin install $(PLUGIN)@$(MARKETPLACE)

.PHONY: agy-install
agy-install: ## Instala o plugin no Antigravity (agy)
	agy plugin install https://github.com/$(REPO)

##@ Atualização

.PHONY: update
update: ## Atualiza o marketplace e depois o plugin (PLUGIN=...)
	claude plugin marketplace update $(MARKETPLACE) && claude plugin update $(PLUGIN)

.PHONY: agy-update
agy-update: ## Atualiza o plugin no Antigravity (agy) reinstalando
	agy plugin install https://github.com/$(REPO)

##@ Release

.PHONY: validate
validate: ## Valida os manifestos do marketplace, Claude e Codex
	claude plugin validate . && \
	for p in $(PLUGINS); do \
		[ -d plugins/$$p ] || continue; \
		claude plugin validate plugins/$$p || exit 1; \
	done && python3 tools/validate_plugin_manifests.py

# PLUGIN=... na linha de comando (ou no ambiente) escolhe um plugin só; sem ele, todos.
TAG_EXPLICIT := $(filter command line environment,$(origin PLUGIN))
TAG_PLUGINS  := $(if $(TAG_EXPLICIT),$(PLUGIN),$(PLUGINS))

.PHONY: tag
tag: validate ## Cria a tag {plugin}--v{version} (PLUGIN=... para um só; sem ele, todos, pulando as tags que já existem)
	@for p in $(TAG_PLUGINS); do \
		manifest=plugins/$$p/.claude-plugin/plugin.json; \
		[ -f $$manifest ] || { echo "plugin $$p sem $$manifest" >&2; exit 1; }; \
		version=$$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' $$manifest) || exit 1; \
		tag="$$p--v$$version"; \
		if [ -z "$(TAG_EXPLICIT)" ] && git rev-parse -q --verify "refs/tags/$$tag" >/dev/null; then \
			echo "skip $$tag: a tag já existe"; continue; \
		fi; \
		claude plugin tag plugins/$$p || exit 1; \
	done

##@ Qualidade

.PHONY: check
check: ## Roda a suíte de testes dos validadores
	python3 -m pytest tools/tests -q
