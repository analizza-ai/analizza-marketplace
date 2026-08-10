# Design: marketplace `analizza-marketplace` com o plugin `analizza-skills`

Data: 2026-08-09

## Objetivo

Transformar o repositório vazio `analizza-marketplace` em um marketplace de plugins do Claude
Code, espelhando o layout já validado em `ralvin-ai`. O marketplace nasce com um plugin,
`analizza-skills`, contendo uma skill: `analizza-kotlin-integration-test`, copiada de
`../ai-showcase-skills/skills/analizza-kotlin-integration-test`.

Estado inicial: repositório com `.git` inicializado, sem commits, remote
`git@github.com:analizza-ai/analizza-marketplace.git`.

## Decisões

| Questão | Decisão |
|---|---|
| Skill de origem | `analizza-kotlin-integration-test` (o caminho pedido, `kotlin-test-integration`, não existe) |
| Nome do marketplace | `analizza-marketplace` (igual ao nome do repositório) |
| Nome do plugin | `analizza-skills` |
| Origem da skill | Copiar sem alterar `ai-showcase-skills` |
| Escopo da entrega | Estrutura + commit + push para `origin main` |
| Layout | Espelho fiel do `ralvin-ai`, com nível `plugins/` |

### Layout: por que o nível `plugins/`

A alternativa era o repositório ser ele próprio um único plugin, com `.claude-plugin/` e `skills/`
na raiz. Custa o mesmo para montar, mas amarra o repositório a um plugin só: adicionar um segundo
(ex.: `analizza-mcp`) exigiria mover tudo. O nível `plugins/` já resolve esse caso.

### Validação: Makefile em vez de CI

Um workflow de GitHub Actions rodando `claude plugin validate` foi considerado e descartado por
YAGNI — repositório novo, um mantenedor. A mesma checagem fica disponível como alvo `make validate`.

## Estrutura final

```
analizza-marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── analizza-skills/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── analizza-kotlin-integration-test/
│               ├── SKILL.md
│               ├── references/
│               │   └── wiremock.md
│               └── templates/            (8 arquivos .template)
├── docs/superpowers/specs/               (este documento)
├── Makefile
├── .gitignore
└── README.md
```

## Manifestos

**`.claude-plugin/marketplace.json`**

- `$schema`: `https://anthropic.com/claude-code/marketplace.schema.json`
- `name`: `analizza-marketplace`
- `description`: marketplace de skills e plugins da Analizza
- `owner`: Diego Lirio / diegolirio.dl@gmail.com
- `plugins`: um entry — `name: analizza-skills`, `source: ./plugins/analizza-skills`,
  `category: development`, mesmo autor

**`plugins/analizza-skills/.claude-plugin/plugin.json`**

- `name`: `analizza-skills`
- `version`: `0.1.0` — repositório novo; a numeração do `ralvin-skills` (0.2.1) é histórico dele
- `description` e `author`: análogos ao `ralvin-skills`

O campo `name` do `plugin.json` e o do entry em `marketplace.json` precisam ser idênticos; é o que
`claude plugin tag` valida na hora do release.

## Skill copiada

Cópia byte a byte de `../ai-showcase-skills/skills/analizza-kotlin-integration-test`, sem renomear
a pasta, sem editar o frontmatter, sem tocar em templates. O repositório de origem permanece
inalterado.

**Efeito colateral aceito:** a skill continua instalada globalmente via
`put-or-update-global-skills.sh` do `ai-showcase-skills`. Ao instalar o plugin, existirão duas
cópias de `analizza-kotlin-integration-test` disponíveis no Claude, e elas podem divergir com o
tempo. Consequência conhecida da decisão de não mexer na origem.

## Makefile

Mesmo formato do `ralvin-ai`: `.DEFAULT_GOAL := help`, help auto-documentado por awk sobre os
comentários `##`, seções `##@`, alvos `.PHONY`.

Variáveis:

```make
REPO        := analizza-ai/analizza-marketplace
MARKETPLACE := analizza-marketplace
PLUGIN      := analizza-skills
PLUGIN_DIR  := plugins/analizza-skills
```

Alvos:

| Alvo | Comando |
|---|---|
| `help` | ajuda auto-documentada |
| `marketplace-add` | `claude plugin marketplace add $(REPO)` |
| `install` | `claude plugin install $(PLUGIN)@$(MARKETPLACE)` |
| `update` | `claude plugin marketplace update $(MARKETPLACE) && claude plugin update $(PLUGIN)` |
| `tag` | `claude plugin tag $(PLUGIN_DIR)` |
| `validate` | `claude plugin validate . && claude plugin validate $(PLUGIN_DIR)` |

`validate` é o único alvo que não existe no `ralvin-ai`.

## Arquivos de apoio

**`.gitignore`** — copiado do `ralvin-ai`: `.DS_Store`, `.worktrees/`, `.superpowers/`.

**`README.md`** — o que é o marketplace; instalação (`make marketplace-add && make install`, com os
comandos `claude` crus como alternativa); tabela de skills disponíveis (uma linha por ora); como
publicar uma versão (`make tag`).

## Verificação

Executar antes do commit, exigindo saída limpa em cada passo:

1. `diff -r` recursivo entre a skill de origem e a cópia — saída vazia.
2. `claude plugin validate .` e `claude plugin validate plugins/analizza-skills` — ambos passam.
3. Leitura dos dois manifestos como JSON, conferindo que
   `marketplace.json.plugins[0].name == plugin.json.name`.

Falha em qualquer passo: corrigir e repetir antes de commitar.

## Entrega

Um commit em `main` com a estrutura completa
(`chore: bootstrap analizza-marketplace com plugin analizza-skills`), seguido de
`git push -u origin main`.

## Fora de escopo

- Criar a tag de release `analizza-skills--v0.1.0`
- Instalar ou ativar o plugin localmente
- Qualquer alteração em `ai-showcase-skills`
- Desinstalar a cópia global da skill
