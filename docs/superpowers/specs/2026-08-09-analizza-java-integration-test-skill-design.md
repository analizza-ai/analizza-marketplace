# Design: skill `analizza-java-integration-test` no plugin `analizza-skills`

Data: 2026-08-09

## Objetivo

Trazer a skill `analizza-java-integration-test` do repositório `ai-showcase-skills` para o plugin
`analizza-skills` deste marketplace, ao lado da irmã `analizza-kotlin-integration-test`.

## Decisões

**Skill separada, não fundida com a Kotlin.** As duas skills fazem a mesma coisa em stacks
diferentes: Kotlin DSL (`settings.gradle.kts`, templates `.kt`) e Groovy DSL (`settings.gradle`,
templates `.java`). Comparando os dois `SKILL.md` com os tokens de linguagem normalizados, restam
~165 linhas de divergência real — a versão Java é posterior e evoluiu além da Kotlin. Fundir as duas
numa skill única com detecção de linguagem seria reescrita, não cópia, e arriscaria a Kotlin que já
está publicada. Cada skill separada também mantém sua `description` disparando com precisão.

**Cópia, não move.** O `ai-showcase-skills` mantém sua cópia, como já aconteceu com a Kotlin. Nada
quebra para quem consome aquele repositório hoje.

**Cópia literal, sem adaptação.** A skill referencia apenas caminhos relativos à própria pasta
(`references/`, `templates/`). Verificado: a Kotlin no marketplace é byte-a-byte idêntica à do
`ai-showcase-skills`, provando que nenhuma adaptação ao contexto de plugin é necessária.

**Versão minor.** `plugins/analizza-skills/.claude-plugin/plugin.json` sobe de `0.1.0` para `0.2.0`
— skill nova, nada removido nem alterado nas existentes. A tag de release (`make tag`) não faz parte
desta mudança; é ação do mantenedor.

## Mudanças

| Arquivo | Mudança |
| --- | --- |
| `plugins/analizza-skills/skills/analizza-java-integration-test/` | Cópia literal dos 10 arquivos (SKILL.md, `references/wiremock.md`, 8 templates) |
| `.claude-plugin/marketplace.json` | `description` do plugin passa a enumerar as duas skills de teste de integração |
| `plugins/analizza-skills/.claude-plugin/plugin.json` | `version`: `0.1.0` → `0.2.0` |
| `README.md` | Nova linha na tabela "Skills do plugin `analizza-skills`" |

## Verificação

- `diff -r` entre origem e destino: cópia byte-a-byte idêntica.
- `make validate`: `claude plugin validate` no marketplace e no plugin.

## Fora de escopo

Fundir as duas skills, mexer no `ai-showcase-skills`, criar tag ou release.

## Risco assumido

Java e Kotlin passam a existir em dois repositórios cada uma e vão divergir com o tempo — a Java já
é a mais nova das duas. A consolidação (mover ambas para cá e deixar o `ai-showcase-skills` sem elas)
e a eventual fusão numa skill única com detecção de linguagem ficam registradas como decisões
adiadas, não descartadas.
