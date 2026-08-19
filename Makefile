REPO        := analizza-ai/analizza-marketplace
MARKETPLACE := analizza-marketplace
PLUGIN      := analizza-skills
PLUGIN_DIR  := plugins/analizza-skills

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
install: ## Instala o plugin a partir do marketplace
	claude plugin install $(PLUGIN)@$(MARKETPLACE)

.PHONY: agy-install
agy-install: ## Instala o plugin no Antigravity (agy)
	agy plugin install https://github.com/$(REPO)

##@ Atualização

.PHONY: update
update: ## Atualiza o marketplace e depois o plugin
	claude plugin marketplace update $(MARKETPLACE) && claude plugin update $(PLUGIN)

.PHONY: agy-update
agy-update: ## Atualiza o plugin no Antigravity (agy) reinstalando
	agy plugin install https://github.com/$(REPO)

##@ Release

.PHONY: validate
validate: ## Valida os manifestos do marketplace, Claude e Codex
	claude plugin validate . && claude plugin validate $(PLUGIN_DIR) && python3 tools/validate_plugin_manifests.py

.PHONY: tag
tag: validate ## Cria a tag {plugin}--v{version} validando os manifestos
	claude plugin tag $(PLUGIN_DIR)

##@ Qualidade

.PHONY: check
check: ## Roda a suíte de testes dos validadores
	python3 -m pytest tools/tests -q
