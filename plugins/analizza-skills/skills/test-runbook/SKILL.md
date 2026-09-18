---
name: test-runbook
description: Implanta em um projeto a skill que conduz checkpoints de conferência manual a partir de docs/checkpoints/ (lista os runbooks, pergunta qual e como executar, e conduz pelo navegador embutido ou entrega os passos). Use quando um projeto ainda não tiver .claude/skills/test-runbook, quando a analizza-integration-test chegar ao passo de checkpoints, ou quando pedirem para "implantar a test-runbook", "registrar o checkpoint runbook aqui" ou similar.
---

# Implantar a skill `test-runbook` num projeto

Esta skill não conduz checkpoints — ela **implanta**, no projeto de destino, a
skill local que conduz (`.claude/skills/test-runbook/`), mais o guia de
formato dos runbooks (`docs/checkpoints/README.md`). Depois de implantada, é
a cópia local que roda o checkpoint no dia a dia; esta aqui só existe para
colocá-la lá.

## 1. Nunca sobrescreve

Antes de gerar qualquer coisa, confira o que já existe. Os três artefatos
abaixo são escritos **somente se ainda não existirem**; se já existir,
registre no relatório final que já existia e siga sem tocar.

| Artefato no projeto de destino | Fonte |
|---|---|
| `docs/checkpoints/README.md` | cópia direta de [checkpoints-readme.md](./references/checkpoints-readme.md) |
| `.claude/skills/test-runbook/SKILL.md` | [conducting-skill.md.template](./templates/conducting-skill.md.template) |
| `.claude/skills/test-runbook/scripts/preflight.sh` | [preflight.sh.template](./templates/preflight.sh.template) |

`.claude/skills/test-runbook/SKILL.md` acumula, com o tempo, uma seção de
cuidados específicos do projeto que alguém vai preencher à mão — sobrescrever
num redeploy destruiria esse conhecimento.

## 2. Detecte o ambiente do projeto de destino (sem perguntar)

Leia, nesta ordem, o que existir:

- `docker-compose.yml` (ou `compose.yaml`) — serviços, nomes de container,
  imagens, portas publicadas.
- `application.properties` / `application.yml` (backend) — porta do servidor
  (`server.port`, padrão `8080`), datasource (para reconhecer o banco:
  `postgresql`, `oracle`, `mysql`...).
- `package.json` / `next.config.*` do frontend — porta do dev server (padrão
  `3000`).
- `Makefile` / `README.md` — o comando que sobe o ambiente completo (ex.:
  `make run`, `docker compose up -d && ./gradlew bootRun`).
- Variáveis de ambiente (`.env`, `.env.local`, `application.yml`) — presença
  de algo como `MAIL_HOST`, `SMTP_*`, ou um serviço `mailhog`/`mailpit`/`smtp`
  no compose.

Isto não é uma pergunta ao usuário — é leitura de arquivo. Só pergunte se,
depois de ler tudo, ainda faltar algo essencial (ex.: nenhum Makefile e
nenhum README dizem como subir o ambiente).

## 3. Gere `docs/checkpoints/README.md`

Cópia literal de `references/checkpoints-readme.md` — o arquivo já é
genérico, sem placeholder.

## 4. Gere `.claude/skills/test-runbook/SKILL.md`

A partir de `templates/conducting-skill.md.template`. Um placeholder:

- `{comando-de-subida}` — o comando (ou sequência de comandos) encontrado no
  passo 2 para subir o ambiente. Se não achou nenhum, escreva uma instrução
  genérica ("suba os serviços que este projeto precisa — veja o README") e
  diga no relatório que não conseguiu detectar.

A seção "Cuidados específicos deste projeto" do template já vem vazia — não
preencha nada nela, é para a pessoa (ou um checkpoint futuro) preencher.

## 5. Gere `.claude/skills/test-runbook/scripts/preflight.sh`

A partir de `templates/preflight.sh.template`. Placeholders:

- `{PORTAS}` — array bash `("porta:nome" ...)` com o que foi detectado no
  passo 2 (ex.: `("8080:api" "3000:web")`). Se nenhuma porta for detectada,
  inclua ao menos uma entrada com a porta padrão do stack (ex.:
  `8080:api`) — um array vazio quebra o `set -u` do script no bash 3.2
  (padrão no macOS).
- `{BANCO_CHECK}` — um comando de "está pronto" para o banco detectado.
  Prontos para copiar:
  - Postgres: `docker exec {container} pg_isready -U {usuario} >/dev/null 2>&1`
  - MySQL: `docker exec {container} mysqladmin ping -s >/dev/null 2>&1`
  - Oracle: `docker exec {container} healthcheck.sh >/dev/null 2>&1`
  Troque `{container}`/`{usuario}` pelos valores reais encontrados no
  `docker-compose.yml`. Nunca escreva uma query de negócio aqui — é
  health-check de infraestrutura, não conferência de dado.

O bloco `== e-mail ==` do template vem marcado com o comentário
`# BLOCO-EMAIL`. Se o passo 2 **não** encontrou nada de e-mail/SMTP, remova o
bloco inteiro (do comentário de abertura ao de fechamento) — não deixe
metade dele nem um placeholder sem preencher. Se encontrou, preencha
`{MAIL_HOST_VAR}` com o nome real da variável de ambiente do projeto.

Depois de gravar, rode `chmod +x` no arquivo — o script precisa ser
executável no projeto de destino.

## 6. Relate

Termine dizendo, em poucas linhas: o que gerou, o que já existia (e por isso
não tocou), e o que não conseguiu detectar — para a pessoa completar à mão.
Não proponha rodar um checkpoint agora; isso é trabalho da skill implantada,
não desta.
