# analizza-marketplace

Marketplace de plugins do Claude Code da Analizza.

| Plugin | Descrição |
| --- | --- |
| `analizza-skills` | Skills para projetos Kotlin + Spring Boot |

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
| `analizza-kotlin-integration-test` | Configura a infraestrutura de testes de integração em projetos Kotlin + Spring Boot. Detecta o layout: em multi-módulo cria um módulo dedicado `{base}-integration-tests`; em single-module configura tudo dentro de `src/test/`. Centraliza o `BaseIntegrationTest`, isola libs pesadas de teste, configura jacoco, as tasks Gradle `test`/`integrationTest`, o stage no Jenkinsfile e a regra ArchUnit de cobertura de entrypoints. |

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
