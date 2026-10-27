# analizza-marketplace

Marketplace de plugins do Claude Code da Analizza.

| Plugin | Descrição |
| --- | --- |
| `analizza-skills` | Skills para scaffolding e qualidade de projetos |

## Instalação por harness

### Claude Code

```bash
claude plugin marketplace add analizza-ai/analizza-marketplace
claude plugin install analizza-skills@analizza-marketplace
```

Pelo Makefile:

```bash
make marketplace-add
make install
```

Para atualizar depois:

```bash
claude plugin marketplace update analizza-marketplace
claude plugin update analizza-skills   # no Makefile: make update
```

### Codex

O Codex não tem um comando de instalação de plugin via CLI. Abra o app Codex, vá em **Plugins**, localize **Analizza Skills** depois que o marketplace Codex publicar o plugin e siga o fluxo da interface para instalar.

Para desenvolvimento local, o plugin mantém o manifesto `plugins/analizza-skills/.codex-plugin/plugin.json` na mesma pasta do plugin; use o fluxo de instalação local que o app Codex suporta para plugins nesse formato.

Como não existe CLI, atualizar segue o mesmo caminho da instalação: volte à tela **Plugins** do app Codex e reinstale (ou deixe o app re-checar) **Analizza Skills** depois que uma nova versão for publicada no marketplace Codex.

### Antigravity

```bash
agy plugin install https://github.com/analizza-ai/analizza-marketplace
```

O `agy` reconhece direto a pasta `plugins/` deste repositório (mesmo formato usado pelo Claude Code), sem precisar de um passo separado de "adicionar marketplace". Para atualizar, rode o mesmo comando de novo:

```bash
agy plugin install https://github.com/analizza-ai/analizza-marketplace
```

### GitHub Copilot CLI

- Register the marketplace:   
```bash
copilot plugin marketplace add analizza-ai/analizza-marketplace
```
- Install the plugin:   
```bash
copilot plugin install analizza-skills@analizza-marketplace
```

### skills.sh (`npx skills`)

As skills deste repositório aparecem em [skills.sh](https://skills.sh). Para ver quais existem:

```bash
npx skills add analizza-ai/analizza-marketplace --list
```

Instala uma skill avulsa, sem plugin, em qualquer agente suportado:

```bash
npx skills add analizza-ai/analizza-marketplace --skill domain-context-map
```

Ou todas de uma vez:

```bash
npx skills add analizza-ai/analizza-marketplace
```

## Skills do plugin `analizza-skills`

| Skill | O que faz |
| --- | --- |
| `analizza-add-mcp-module` | Acrescenta um servidor MCP a um projeto Spring Boot em camadas já existente (Java ou Kotlin, Gradle Groovy ou Kotlin DSL) como módulo de biblioteca `{base}-mcp`, servido por HTTP sem sessão em `/mcp` no mesmo processo do `-api`. Detecta linguagem, DSL e pacote base, cria o módulo, liga a configuração STATELESS/SYNC, gera a ponte de autenticação que lê `Authentication` em vez do token, uma tool de exemplo a partir de um caso de uso de leitura do projeto, um teste de integração com cliente MCP real e o runbook de conferência. |
| `analizza-integration-test` | Configura testes de integração e guardrails de teste em projetos Spring Boot, em Java ou Kotlin, com Gradle Groovy ou Kotlin DSL. Detecta e pergunta linguagem, banco (Postgres, Oracle, MySQL) e layout: módulo dedicado `{base}-integration-tests` (recomendado) ou o módulo existente. Cria o `BaseIntegrationTest` com um container por suíte, as tasks `test`/`integrationTest` separadas pelo sufixo `IT`, a regra ArchUnit que exige IT para todo entrypoint e o relatório JaCoCo. No frontend, acrescenta typecheck, Vitest no Next.js e jest-expo no Expo. Grava as regras de projeto: variáveis de ambiente, checkpoints com runbook por funcionalidade e débitos técnicos. O CI fica por conta do projeto que consome a skill. |
| `analizza-new-agent` | Cria um agente conversacional de IA em Spring Boot, em Java ou Kotlin. Do zero: monorepo sem `-core`, com `{project}-agent` carregando as quatro camadas num módulo só, `buildingBlocks` e, se pedido, `{project}-web` com tela de chat, Postgres e memória de conversa. Em projeto existente: acrescenta `{base}-agent` como aplicação própria, que fala com o domínio por MCP. Entrega endpoint de chat (JSON e SSE), LLM OpenAI-compatível via LangChain4j atrás de uma interface, cliente MCP preguiçoso que falha em vez de responder sem ferramentas, observabilidade (OpenTelemetry, LangWatch local, Prometheus) e testes com LLM roteirizado e com Ollama em Testcontainers. |
| `domain-context-map` | Roda num projeto em disco e gera `docs/domain/domain-guide.md`: a descrição de uma linha e o guia do repositório (onde ficam specs, rotas, casos de uso, regras, como seguir uma regra e o glossário), sem resumo de regra de negócio. Um script faz o inventário do disco, outro valida o arquivo (tamanho, caminhos que existem, sem número de linha, sem segredo), e rodar de novo confere se o guia ficou velho. O texto é feito para colar no cadastro do alvo de um servidor MCP no Ólly. |
| `analizza-new-project` | Cria do zero, em Java ou Kotlin, um monorepo de cinco módulos: `buildingBlocks` com os contratos base, `{project}-api` (Spring Boot, entrada), `{project}-core` (domínio, casos de uso e saída), `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, na DSL da linguagem escolhida, com Postgres em docker-compose e migrations Flyway no core. As convenções da arquitetura em camadas são gravadas no arquivo do framework de Spec-Driven Development em uso. |
| `test-runbook` | Implanta num projeto o mecanismo de checkpoint de conferência manual: o guia de formato em `docs/checkpoints/README.md` e a skill local `.claude/skills/test-runbook/` que conduz o checkpoint, com `scripts/preflight.sh` ajustado ao ambiente detectado. Nunca sobrescreve o que já existe. |
| `yeroon-play-plug` | Pluga o yeroon play num projeto que já existe: back Spring Boot (Java ou Kotlin) e front Next.js, app Expo ou app Flutter. Detecta a stack e as convenções, mostra o plano e espera o ok, pede que a pessoa rode `yeroon-key.sh` (cria a conta de teste e grava a chave no `.env` do back; o agente não vê senha nem chave) e implementa em fatias: cliente da `/v1`, rotas de repasse, webhook assinado, migration e telas de enviar, listar e assistir, com testes que não chamam a `/v1`. Termina com o checklist do que falta para produção. Para quando o back não é Spring Boot. |

## Publicando uma versão

A versão é por plugin: suba a mesma `version` em `plugins/<plugin>/.claude-plugin/plugin.json` e em `plugins/<plugin>/.codex-plugin/plugin.json` do plugin que mudou, valide e crie as tags:

Pré-requisito de `make check`: `pip install -r requirements-dev.txt`.

```bash
make validate
make check
make tag PLUGIN=analizza-skills   # cria a tag do plugin que mudou (ex.: analizza-skills--v0.8.0)
make tag                      # sem PLUGIN: todos os plugins, pulando ("skip") os cuja tag já existe
```

A versão sai de `plugins/<plugin>/.claude-plugin/plugin.json`. Com `PLUGIN=`, a
tag é criada só para ele e falha se já existir (suba a `version` antes). Sem
`PLUGIN`, cada plugin cuja tag `<plugin>--v{version}` já existe é pulado, e os
outros são marcados.

## Estrutura

```
.claude-plugin/marketplace.json     # manifesto do marketplace
plugins/<plugin>/                   # analizza-skills
├── .claude-plugin/plugin.json      # manifesto do plugin (Claude Code)
├── .codex-plugin/plugin.json       # manifesto do plugin (Codex)
└── skills/                         # uma pasta por skill, fonte única para os dois harnesses
docs/checkpoints/                   # runbooks de conferência manual
tools/                              # validador dos manifestos multi-harness
requirements-dev.txt                # dependência de teste (pytest)
docs/superpowers/specs/             # decisões de design
docs/superpowers/plans/             # planos de implementação
```
