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

Para atualizar depois:

```bash
claude plugin marketplace update analizza-marketplace
claude plugin update analizza-skills
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

## Skills do plugin `analizza-skills`

| Skill | O que faz |
| --- | --- |
| `analizza-integration-test` | Configura testes de integração e guardrails de teste em projetos Spring Boot, em Java ou Kotlin, com Gradle Groovy ou Kotlin DSL. Detecta e pergunta linguagem, banco (Postgres, Oracle, MySQL) e layout: módulo dedicado `{base}-integration-tests` (recomendado) ou o módulo existente. Cria o `BaseIntegrationTest` com um container por suíte, as tasks `test`/`integrationTest` separadas pelo sufixo `IT`, a regra ArchUnit que exige IT para todo entrypoint e o relatório JaCoCo. No frontend, acrescenta typecheck, Vitest no Next.js e jest-expo no Expo. Grava as regras de projeto: variáveis de ambiente, checkpoints com runbook por funcionalidade e débitos técnicos. O CI fica por conta do projeto que consome a skill. |
| `analizza-new-project` | Cria do zero, em Java ou Kotlin, um monorepo de cinco módulos: `buildingBlocks` com os contratos base, `{project}-api` (Spring Boot, entrada), `{project}-core` (domínio, casos de uso e saída), `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, na DSL da linguagem escolhida, com Postgres em docker-compose e migrations Flyway no core. As convenções da arquitetura em camadas são gravadas no arquivo do framework de Spec-Driven Development em uso. |

## Publicando uma versão

Suba a mesma `version` em `plugins/analizza-skills/.claude-plugin/plugin.json` e em `plugins/analizza-skills/.codex-plugin/plugin.json`, valide e crie a tag:

Pré-requisito de `make check`: `pip install -r requirements-dev.txt`.

```bash
make validate
make check
make tag        # cria a tag analizza-skills--v{version}
```

## Estrutura

```
.claude-plugin/marketplace.json     # manifesto do marketplace
plugins/analizza-skills/
├── .claude-plugin/plugin.json      # manifesto do plugin (Claude Code)
├── .codex-plugin/plugin.json       # manifesto do plugin (Codex)
└── skills/                         # uma pasta por skill, fonte única para os dois harnesses
tools/                              # validador dos manifestos multi-harness
requirements-dev.txt                # dependência de teste (pytest)
docs/superpowers/specs/             # decisões de design
docs/superpowers/plans/             # planos de implementação
```
