# Alvos de teste do Makefile

Se o projeto tem `Makefile` na raiz, os alvos abaixo substituem os de mesmo
nome e são acrescentados ao `test`. Receitas com **TAB**, não espaço. Se o
`Makefile` ainda não definir `GRADLEW ?= ./gradlew`, `WEB_DIR`, `MOBILE_DIR`
e as regras `$(WEB_DIR)/node_modules: …` / `$(MOBILE_DIR)/node_modules: …`
(`npm ci` sobre o `package.json` de cada frontend), acrescente-as também. Se
não há `Makefile`, os mesmos comandos entram como `scripts` no
`package.json` de cada frontend (`"test"`, `"typecheck"`) e nada é criado na
raiz — ver a seção abaixo.

```makefile
GRADLEW ?= ./gradlew
WEB_DIR := {web-dir}
MOBILE_DIR := {mobile-dir}

$(WEB_DIR)/node_modules: $(WEB_DIR)/package.json
	cd $(WEB_DIR) && npm ci

$(MOBILE_DIR)/node_modules: $(MOBILE_DIR)/package.json
	cd $(MOBILE_DIR) && npm ci

.PHONY: test
test: test-backend test-integration test-web test-mobile ## Roda todos os testes

.PHONY: test-backend
test-backend: ## Testes unitarios do backend (nao sobe banco)
	$(GRADLEW) test

.PHONY: test-integration
test-integration: ## Testes de integracao (*IT) sobre Testcontainers
	$(GRADLEW) integrationTest

.PHONY: test-web
test-web: $(WEB_DIR)/node_modules ## Lint, tipos e testes do web
	cd $(WEB_DIR) && npm run lint
	cd $(WEB_DIR) && npm run typecheck
	cd $(WEB_DIR) && npm test

.PHONY: test-mobile
test-mobile: $(MOBILE_DIR)/node_modules ## Tipos e testes do mobile
	cd $(MOBILE_DIR) && npm run typecheck
	cd $(MOBILE_DIR) && npm test
```

Retire do `test` o que não existir no projeto (sem `-mobile`, sem
`test-mobile`; sem backend, sem os dois primeiros). `test-backend` **não**
depende de `db-up`: depois desta skill, `./gradlew test` não sobe banco.
Tire a linha `cd $(WEB_DIR) && npm run lint` de `test-web` se o
`package.json` do `-web` não tiver um script `lint`.

## `scripts` do `package.json`

Com `Makefile`, o alvo já orquestra lint/typecheck/test — o `test` do
`package.json` só chama o comando do frontend:

| Frontend | `test` | `typecheck` |
|---|---|---|
| `-web` (Next) | `vitest run` | `next typegen && tsc --noEmit` |
| `-mobile` (Expo) | `jest --ci` | `tsc --noEmit` |

Sem `Makefile`, não há um alvo separado que rode `typecheck` antes: o
`test` encadeia os dois para não depender de um segundo comando —

| Frontend | `test` |
|---|---|
| `-web` (Next) | `npm run typecheck && vitest run` |
| `-mobile` (Expo) | `npm run typecheck && jest --ci` |

`typecheck` continua igual à primeira tabela nos dois casos.

O `next typegen` gera os tipos de rota que o `next build` geraria; sem ele, o
`tsc` sozinho acusa import de tipos que ainda não existem.

O `typecheck` existe porque lint e teste não fazem checagem de tipo: uma
mudança num tipo compartilhado pode quebrar um arquivo que nenhum teste
importa, e o alvo que as pessoas rodam fica verde com a regressão dentro.
