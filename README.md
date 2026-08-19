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
| `analizza-kotlin-integration-test` | Configura a infraestrutura de testes de integração em projetos Kotlin + Spring Boot. Detecta o layout: em multi-módulo cria um módulo dedicado `{base}-integration-tests`; em single-module configura tudo dentro de `src/test/`. Centraliza o `BaseIntegrationTest`, isola libs pesadas de teste, configura jacoco, as tasks Gradle `test`/`integrationTest` e a regra ArchUnit de cobertura de entrypoints. O CI fica por conta do projeto que consome a skill. |
| `analizza-java-integration-test` | Mesma infraestrutura da skill acima, para projetos Java + Spring Boot com Gradle Groovy DSL (`settings.gradle`, templates `.java`). Detecta o layout multi-módulo ou single-module da mesma forma. |
| `analizza-new-project` | Cria do zero um monorepo de quatro módulos: backend Java Spring Boot separado em `{project}-api` (controllers) e `{project}-core` (Clean Architecture + CQRS), mais `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, com Postgres em docker-compose e migrations Flyway no core. |

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
