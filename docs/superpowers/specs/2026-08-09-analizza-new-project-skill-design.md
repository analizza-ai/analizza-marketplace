# Design: skill `analizza-new-project` no plugin `analizza-skills`

Data: 2026-08-09

## Objetivo

Copiar a skill `ralvin-new-project` de `../ralvin-ai/plugins/ralvin-skills/skills/` para o plugin
`analizza-skills`, renomeando-a para `analizza-new-project`. O repositório de origem, `ralvin-ai`,
não é alterado.

## Achado que orienta o trabalho

A skill tem 10 arquivos e 1043 linhas, mas a string "ralvin" aparece em apenas **5 linhas, todas no
`SKILL.md`**. Os 4 arquivos de `references/` e os 5 de `templates/` não a contêm — copiam sem
qualquer edição.

As 5 ocorrências se dividem em duas naturezas:

- **Identidade** (renomear é obrigatório): o `name:` do frontmatter e o slash command citado na
  `description`.
- **Conteúdo** (escolha do usuário): duas referências cruzadas a `ralvin-new-simple-project` e o
  valor default de `group`.

## Decisões

| Questão | Decisão |
|---|---|
| Default de `group` | Trocar `br.com.ralvin` por `br.com.analizza` |
| Refs a `ralvin-new-simple-project` | Remover, preservando a ideia sem citar a skill ausente |
| Versão do plugin | Manter `0.1.0`, sem tag nova |
| Origem | `ralvin-ai` intocado |

### Sobre as referências cruzadas

`ralvin-new-simple-project` não faz parte do plugin `analizza-skills`. Ela está instalada
globalmente na máquina do usuário, então a referência resolveria no ambiente dele — mas ficaria
morta para qualquer terceiro que instalasse apenas `analizza-skills`. Por isso a remoção.

A referência a `setup-kotlin-gradle` (linhas 14 e 40) **permanece**: é skill que o usuário tem e
não pertence ao domínio "ralvin" sendo renomeado.

### Sobre manter a versão em 0.1.0

Consequência aceita: a tag `analizza-skills--v0.1.0`, já publicada, deixa de corresponder ao
conteúdo do repositório. Decisão explícita do usuário após o ponto ser levantado.

## Execução

**1. Copiar e renomear a pasta**

`../ralvin-ai/plugins/ralvin-skills/skills/ralvin-new-project`
→ `plugins/analizza-skills/skills/analizza-new-project`

Cópia recursiva, excluindo `.DS_Store`. Nenhum arquivo de `references/` ou `templates/` é editado.

**2. Editar o `SKILL.md` — exatamente 5 pontos**

| Linha | De | Para |
|---|---|---|
| 2 | `name: ralvin-new-project` | `name: analizza-new-project` |
| 13 | `invocar /ralvin-new-project` | `invocar /analizza-new-project` |
| 13-14 | `Para o monorepo simples de dois módulos, use ralvin-new-simple-project;` | frase removida da `description` |
| 38-39 | bullet `**Não** use para o monorepo simples de dois módulos — essa é a `ralvin-new-simple-project`` | `**Não** use para o monorepo simples de dois módulos` |
| 47 | `br.com.ralvin` | `br.com.analizza` |

As edições são pontuais (`Edit`), não um `sed s/ralvin/analizza/g`: substituições dirigidas ficam
auditáveis no diff, e o `sed` global atingiria a palavra em prosa onde a troca não é desejada.

**3. Atualizar metadados do plugin**

- `.claude-plugin/marketplace.json`: a `description` do entry hoje cita só
  `analizza-kotlin-integration-test`; passa a citar as duas skills.
- `README.md`: nova linha na tabela de skills do plugin.
- `plugin.json`: inalterado, `0.1.0`.

## Verificação

1. `diff -r` entre a skill de origem e a cópia: exatamente 5 linhas de diferença, todas em
   `SKILL.md`, correspondendo à tabela acima.
2. `grep -ri ralvin` na pasta da skill nova: saída vazia.
3. `claude plugin validate .` e `claude plugin validate plugins/analizza-skills`: ambos passam.
4. `git -C ../ralvin-ai status --short`: limpo, confirmando que a origem não foi tocada.

## Entrega

Um commit em `main` e push para `origin`. Sem tag de release.

## Fora de escopo

- Copiar `ralvin-new-simple-project`
- Subir a versão do plugin ou criar tag
- Qualquer alteração em `ralvin-ai`
