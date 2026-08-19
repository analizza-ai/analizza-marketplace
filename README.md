# analizza-marketplace

Marketplace de plugins do Claude Code da Analizza.

| Plugin | Descrição |
| --- | --- |
| `analizza-skills` | Skills para scaffolding e qualidade de projetos |

## Instalação por harness

### Claude Code

```bash
make marketplace-add   # claude plugin marketplace add analizza-ai/analizza-marketplace
make install           # claude plugin install analizza-skills@analizza-marketplace
```

Para atualizar depois:

```bash
make update
```

### Codex

O Codex não tem um comando de instalação de plugin via CLI. Abra o app Codex, vá em **Plugins**, localize **Analizza Skills** depois que o marketplace Codex publicar o plugin e siga o fluxo da interface para instalar.

Para desenvolvimento local, o plugin mantém o manifesto `plugins/analizza-skills/.codex-plugin/plugin.json` na mesma pasta do plugin; use o fluxo de instalação local que o app Codex suporta para plugins nesse formato.

Como não existe CLI, atualizar segue o mesmo caminho da instalação: volte à tela **Plugins** do app Codex e reinstale (ou deixe o app re-checar) **Analizza Skills** depois que uma nova versão for publicada no marketplace Codex.

## Skills do plugin `analizza-skills`

| Skill | O que faz |
| --- | --- |
| `analizza-kotlin-integration-test` | Configura a infraestrutura de testes de integração em projetos Kotlin + Spring Boot. Detecta o layout: em multi-módulo cria um módulo dedicado `{base}-integration-tests`; em single-module configura tudo dentro de `src/test/`. Centraliza o `BaseIntegrationTest`, isola libs pesadas de teste, configura jacoco, as tasks Gradle `test`/`integrationTest` e a regra ArchUnit de cobertura de entrypoints. O CI fica por conta do projeto que consome a skill. |
| `analizza-java-integration-test` | Mesma infraestrutura da skill acima, para projetos Java + Spring Boot com Gradle Groovy DSL (`settings.gradle`, templates `.java`). Detecta o layout multi-módulo ou single-module da mesma forma. |
| `analizza-new-project` | Cria do zero um monorepo de quatro módulos: backend Java Spring Boot separado em `{project}-api` (controllers) e `{project}-core` (Clean Architecture + CQRS), mais `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, com Postgres em docker-compose e migrations Flyway no core. |

### Fluxo de desenvolvimento assistido por IA

Adaptadas de [obra/superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent) — só as skills, sem hooks nem agents do projeto original. As referências cruzadas entre elas usam o prefixo `analizza-skills:`.

| Skill | O que faz |
| --- | --- |
| `brainstorming` | Ajuda a transformar ideias em designs e specs através de diálogo colaborativo, antes de qualquer implementação. |
| `dispatching-parallel-agents` | Use quando houver 2+ tarefas independentes que podem ser trabalhadas sem estado compartilhado ou dependências sequenciais. |
| `executing-plans` | Use quando houver um plano de implementação escrito para executar em uma sessão separada, com checkpoints de revisão. |
| `finishing-a-development-branch` | Use quando a implementação estiver completa, todos os testes passarem, e for preciso decidir como integrar o trabalho. |
| `receiving-code-review` | Use ao receber feedback de code review, antes de implementar sugestões — exige rigor técnico e verificação, não concordância performática. |
| `requesting-code-review` | Use ao completar tarefas, implementar features importantes, ou antes de fazer merge, para verificar se o trabalho atende aos requisitos. |
| `subagent-driven-development` | Use ao executar planos de implementação com tarefas independentes na sessão atual. |
| `systematic-debugging` | Use ao encontrar qualquer bug, falha de teste ou comportamento inesperado, antes de propor correções. |
| `test-driven-development` | Use ao implementar qualquer feature ou correção de bug, antes de escrever o código de implementação. |
| `using-git-worktrees` | Use ao iniciar trabalho em uma feature que precisa de isolamento do workspace atual. |
| `using-superpowers` | Skill de entrada: como encontrar e usar as demais skills antes de qualquer resposta ou ação. |
| `verification-before-completion` | Use antes de declarar um trabalho completo, corrigido ou passando, antes de commitar ou criar PRs. |
| `writing-plans` | Use quando houver uma spec ou requisitos para uma tarefa de múltiplas etapas, antes de tocar em código. |
| `writing-skills` | Use ao criar novas skills, editar skills existentes, ou verificar skills antes do deploy. |

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
