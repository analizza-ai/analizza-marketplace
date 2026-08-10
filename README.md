# analizza-marketplace

Marketplace de plugins do Claude Code da Analizza.

| Plugin | Descrição |
| --- | --- |
| `analizza-skills` | Skills para scaffolding e qualidade de projetos |

## Instalação

```bash
make marketplace-add   # claude plugin marketplace add analizza-ai/analizza-marketplace
make install           # claude plugin install analizza-skills@analizza-marketplace
```

Para atualizar depois:

```bash
make update
```

## Skills do plugin `analizza-skills`

| Skill | O que faz |
| --- | --- |
| `analizza-kotlin-integration-test` | Configura a infraestrutura de testes de integração em projetos Kotlin + Spring Boot. Detecta o layout: em multi-módulo cria um módulo dedicado `{base}-integration-tests`; em single-module configura tudo dentro de `src/test/`. Centraliza o `BaseIntegrationTest`, isola libs pesadas de teste, configura jacoco, as tasks Gradle `test`/`integrationTest` e a regra ArchUnit de cobertura de entrypoints. O CI fica por conta do projeto que consome a skill. |
| `analizza-java-integration-test` | Mesma infraestrutura da skill acima, para projetos Java + Spring Boot com Gradle Groovy DSL (`settings.gradle`, templates `.java`). Detecta o layout multi-módulo ou single-module da mesma forma. |
| `analizza-new-project` | Cria do zero um monorepo de quatro módulos: backend Java Spring Boot separado em `{project}-api` (controllers) e `{project}-core` (Clean Architecture + CQRS), mais `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, com Postgres em docker-compose e migrations Flyway no core. |

## Publicando uma versão

Suba a `version` em `plugins/analizza-skills/.claude-plugin/plugin.json`, valide e crie a tag:

```bash
make validate
make tag        # cria a tag analizza-skills--v{version}
```

## Estrutura

```
.claude-plugin/marketplace.json     # manifesto do marketplace
plugins/analizza-skills/
├── .claude-plugin/plugin.json      # manifesto do plugin
└── skills/                         # uma pasta por skill
docs/superpowers/specs/             # decisões de design
```
