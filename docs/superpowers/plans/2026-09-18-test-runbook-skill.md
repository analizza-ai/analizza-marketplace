# Skill `test-runbook` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `test-runbook` em `plugins/analizza-skills/skills/test-runbook/`, generalizando o `eaf-runbook` do `documents-eaf-system`, e ligá-la ao Passo 8 da `analizza-integration-test` para que toda implantação futura já receba o mecanismo de checkpoint.

**Architecture:** Só Markdown e um script de shell template — nenhum código de aplicação. A skill nova segue o mesmo padrão das demais (`SKILL.md` + `references/` + `templates/`): o `SKILL.md` instrui o agente que a invoca a **detectar** o ambiente do projeto de destino lendo seus próprios arquivos (compose, config, Makefile) e a **gerar** três artefatos ali, nunca sobrescrevendo o que já existir. A `analizza-integration-test` passa a chamar essa implantação ao final do seu próprio Passo 8.

**Tech Stack:** Markdown (skills, templates), Bash (script de preflight), JSON (manifestos do plugin).

**Spec:** `docs/superpowers/specs/2026-09-18-test-runbook-skill-design.md` (decisões D1–D8).

## Global Constraints

- Repositório: `analizza-marketplace` (remoto `git@github.com:analizza-ai/analizza-marketplace.git`), branch base `main`, commit `f6883f0` (spec já commitada) — trabalhe num worktree isolado via `superpowers:using-git-worktrees`, nunca direto no checkout principal.
- Raiz da skill nova (abreviada `$TR` nos comandos): `plugins/analizza-skills/skills/test-runbook`.
- Raiz da skill existente (abreviada `$IT` nos comandos): `plugins/analizza-skills/skills/analizza-integration-test`.
- D1: `test-runbook` é skill própria, não templates internos da `analizza-integration-test`.
- D2: geração dirigida pelo agente que implanta — sem script de detecção/parser dedicado.
- D3: a `analizza-integration-test` sempre implanta `test-runbook` no Passo 8, sem perguntar.
- D4: os três artefatos gerados no projeto de destino (`docs/checkpoints/README.md`,
  `.claude/skills/test-runbook/SKILL.md`, `.claude/skills/test-runbook/scripts/preflight.sh`) só
  são escritos se ainda não existirem — nunca sobrescreve.
- D5: o `SKILL.md` implantado generaliza o `eaf-runbook`; nada específico do
  `documents-eaf-system` (`eaf`, `Azurite`, `DocuSign`, `código de acesso`, SMTP real) entra nos
  templates.
- D6: o `preflight.sh` implantado tem bloco de containers/portas sempre presente, bloco de banco
  como health-check genérico (nunca query de negócio), e bloco de e-mail que só existe se
  detectado — senão é removido por completo, não deixado com placeholder.
- D7: `claude-md-obligation.md` ganha uma frase dizendo que a conferência é conduzida por
  `/test-runbook`.
- D8: `checkpoints-readme.md` migra de `$IT/references/` para `$TR/references/` (fonte única).
- Placeholders de template usam chave simples `{nome-com-hifen}`, igual às demais skills deste
  marketplace — nunca `{{duplo}}`.
- Comentários em script bash: português sem acento (mesma convenção do `preflight.sh` original).
  Markdown: português com acento.
- Commits em português, 3ª pessoa do presente, terminando com
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- Bump de versão (`0.3.1` → `0.3.2`) só na Task 5, depois de tudo mais pronto.

---

## File Structure

| Arquivo | Responsabilidade | Task |
|---|---|---|
| `$TR/SKILL.md` | instrui o agente a implantar os 3 artefatos num projeto de destino | 1 |
| `$TR/references/checkpoints-readme.md` | guia de formato do runbook (migrado de `$IT`) | 1 |
| `$TR/templates/conducting-skill.md.template` | `SKILL.md` que vira `.claude/skills/test-runbook/SKILL.md` no projeto de destino | 2 |
| `$TR/templates/preflight.sh.template` | vira `.claude/skills/test-runbook/scripts/preflight.sh` no projeto de destino | 3 |
| `$IT/SKILL.md` (Passo 8) | chama a implantação de `test-runbook`; referência a `checkpoints-readme.md` atualizada | 4 |
| `$IT/references/claude-md-obligation.md` | frase de D7 | 4 |
| `.claude-plugin/marketplace.json` | descrição do plugin cita `test-runbook` | 5 |
| `plugins/analizza-skills/.claude-plugin/plugin.json` | `version` `0.3.2` | 5 |
| `plugins/analizza-skills/.codex-plugin/plugin.json` | `version` `0.3.2` | 5 |

---

### Task 1: Criar a skill `test-runbook` (esqueleto + `SKILL.md` de implantação)

**Files:**
- Create: `plugins/analizza-skills/skills/test-runbook/SKILL.md`
- Move: `plugins/analizza-skills/skills/analizza-integration-test/references/checkpoints-readme.md` → `plugins/analizza-skills/skills/test-runbook/references/checkpoints-readme.md`

**Interfaces:**
- Consumes: nada.
- Produces: a pasta `$TR/` existe, com `SKILL.md` e `references/checkpoints-readme.md` — Tasks 2/3
  criam `$TR/templates/`, referenciado pelo `SKILL.md` desta task.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd plugins/analizza-skills/skills
c() { local ok=0
  [ -f test-runbook/SKILL.md ] || { echo "sem SKILL.md"; ok=1; }
  [ -f test-runbook/references/checkpoints-readme.md ] || { echo "checkpoints-readme.md nao migrado"; ok=1; }
  [ -f analizza-integration-test/references/checkpoints-readme.md ] && { echo "checkpoints-readme.md ainda na IT"; ok=1; }
  grep -q '^name: test-runbook$' test-runbook/SKILL.md 2>/dev/null || { echo "sem frontmatter name"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: as quatro linhas "sem …"/"…ainda na IT", `EXIT=1`.

- [ ] **Step 3: Mover o arquivo e criar o `SKILL.md`**

```bash
mkdir -p test-runbook/references test-runbook/templates
git mv analizza-integration-test/references/checkpoints-readme.md test-runbook/references/checkpoints-readme.md
```

```bash
cat > test-runbook/SKILL.md <<'SKILLMD_EOF'
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
  passo 2 (ex.: `("8080:api" "3000:web")`).
- `{BANCO_CHECK}` — um comando de "está pronto" para o banco detectado.
  Prontos para copiar:
  - Postgres: `docker exec {container} pg_isready -U {usuario} >/dev/null 2>&1`
  - MySQL: `docker exec {container} mysqladmin ping -s >/dev/null 2>&1`
  - Oracle: `docker exec {container} healthcheck.sh >/dev/null 2>&1`
  Troque `{container}`/`{usuario}` pelos valores reais encontrados no
  `docker-compose.yml`. Nunca escreva uma query de negócio aqui — é
  health-check de infraestrutura, não conferência de dado.

O bloco `== email ==` do template vem marcado com o comentário
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
SKILLMD_EOF
```

- [ ] **Step 4: Rodar de novo e ver passar**

Repita o comando do Step 1. Expected: nenhuma linha impressa, `EXIT=0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/test-runbook plugins/analizza-skills/skills/analizza-integration-test/references/checkpoints-readme.md
git commit -m "$(cat <<'EOF'
feat: cria a skill test-runbook

Generaliza o eaf-runbook do documents-eaf-system numa skill própria do
marketplace, que implanta o mecanismo de checkpoint (README + SKILL.md
local + preflight) em qualquer projeto sem sobrescrever o que já existir.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Template `conducting-skill.md.template`

**Files:**
- Create: `plugins/analizza-skills/skills/test-runbook/templates/conducting-skill.md.template`

**Interfaces:**
- Consumes: nada (é conteúdo estático).
- Produces: o arquivo que a Task 1 (`SKILL.md`, seção 4) referencia e instrui a copiar/preencher.

- [ ] **Step 1: Checagem que deve falhar**

```bash
T=plugins/analizza-skills/skills/test-runbook/templates/conducting-skill.md.template
c() { local ok=0
  [ -f "$T" ] || { echo "arquivo nao existe"; return 1; }
  grep -q '^name: test-runbook$' "$T" || { echo "sem frontmatter name"; ok=1; }
  grep -q 'IA executa pelo navegador e você assiste' "$T" || { echo "sem rotulo 1 literal"; ok=1; }
  grep -q 'Você executa passo a passo, eu te forneço a sequência' "$T" || { echo "sem rotulo 2 literal"; ok=1; }
  grep -q '{comando-de-subida}' "$T" || { echo "sem placeholder comando-de-subida"; ok=1; }
  grep -q 'Cuidados específicos deste projeto' "$T" || { echo "sem secao de cuidados"; ok=1; }
  grep -qi 'eaf\|azurite\|docusign\|documents-eaf-system\|código de acesso' "$T" && { echo "residuo especifico do projeto original"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `arquivo nao existe`, `EXIT=1`.

- [ ] **Step 3: Criar o template**

```bash
cat > plugins/analizza-skills/skills/test-runbook/templates/conducting-skill.md.template <<'TEMPLATE_EOF'
---
name: test-runbook
description: Conduz um checkpoint de conferência manual a partir dos runbooks em docs/checkpoints/ deste projeto. Lista os runbooks disponíveis, pergunta qual executar, e então ou entrega os passos prontos para a pessoa seguir, ou executa pelo navegador embutido se ela pedir. Use sempre que alguém invocar /test-runbook, disser que vai conferir ou testar uma funcionalidade na mão, perguntar "qual runbook", quiser rodar o checkpoint de uma fatia, ou quando você acabar de implementar algo e for propor a conferência — mesmo que a palavra "runbook" não apareça.
---

# Conduzir um checkpoint pelo runbook

Um checkpoint é uma parada onde **uma pessoa olha o resultado rodando**. Ele
existe para o que teste nenhum pega — tela que sumiu com a suíte verde, CORS
que só quebra no navegador, migration que não casou uma linha.

Isso define o seu papel: você encurta o caminho, mostra o que olhar e diz o
que **não** conseguiu verificar. Quem olha e quem aprova é a pessoa. Rodar o
fluxo e apresentar a saída como se fosse a conferência troca julgamento por
carimbo, e é exatamente o que não se quer aqui.

## Escreva pouco

Quem vai conferir quer agir, não ler. O porquê das coisas já está no runbook
e em `docs/checkpoints/README.md` — não repita nada disso na conversa. Vale
lista curta, comando pronto, e o mínimo de prosa que ainda faça sentido.

Leia `docs/checkpoints/README.md` uma vez antes de começar.

## 1. Veja o estado do ambiente antes de falar

```bash
.claude/skills/test-runbook/scripts/preflight.sh
```

Rode isso primeiro, sempre. Descobrir no meio do caminho que um serviço está
parado é o tipo de atrito que faz a pessoa desistir de conferir.

Se algo estiver fora do ar, o comando para subir o ambiente deste projeto é:

```bash
{comando-de-subida}
```

## 2. Liste os runbooks e pergunte qual

Os runbooks são os `.md` de `docs/checkpoints/`, menos o `README.md`.
Descubra por listagem, nunca por uma lista fixa dentro desta skill.

**Pergunte com `AskUserQuestion`, não com uma lista numerada em texto.** Monte
as opções a partir dos arquivos encontrados — `label` é o nome do runbook,
`description` é o que ele cobre em umas oito palavras, e vale dizer ali se
tem tela ou não.

Antes da pergunta, uma linha de ambiente, só com o que está fora do lugar.

Pergunte mesmo quando só houver um runbook — a escolha é dela.

Se a funcionalidade citada **não tiver** runbook, diga isso em vez de
improvisar passos — a falta de um é um achado por si só. Ofereça escrevê-lo.

## 3. O tipo do runbook decide se há segunda pergunta

Todo runbook declara no topo onde a conferência acontece:

```markdown
---
type: screen-web
---
```

`screen-web`/`screen-mobile` têm tela; `api` é terminal e HTTP; `inbox` é
numa caixa de entrada. **O navegador embutido só vale para `screen-web` e
`inbox`.**

- **`screen-web`/`inbox`** → uma **segunda** `AskUserQuestion`, com estes
  dois `label` **literais**:

  1. `IA executa pelo navegador e você assiste`
  2. `Você executa passo a passo, eu te forneço a sequência`

- **qualquer outro tipo** → não pergunte. Diga numa linha que ali é terminal
  e vá para o caminho manual.

**Use esses rótulos como estão, sem reescrever.** Cada opção precisa dizer
quem faz e quem olha, com o sujeito explícito — "eu" e "você" trocam de dono
conforme quem lê, e uma pergunta que exige decifrar quem é quem é uma
pergunta que se aprende a pular.

As duas perguntas são separadas quando existem: juntá-las obriga a decidir
como conferir antes de saber o que conferir.

**Um runbook `api` ainda pode precisar de tela no setup.** Isso não muda o
tipo, porque o tipo descreve onde se confere. Se a preparação for mais
rápida pela API, faça pela API e diga.

## 4a. Caminho manual: entregue passos, não um resumo

Traduza a seção 1 do runbook numa sequência numerada, em ordem de execução,
com os comandos prontos para colar e o que observar em cada um.

Três coisas que fazem a diferença:

- **O que precisa ser feito antes não pode aparecer depois.** Ordene por
  dependência, não pela ordem do arquivo.
- **Preencha o que o runbook deixou genérico.** Se pede "um arquivo de mais
  de 5 MB", procure um no sistema e cite o caminho.
- **Diga o que cada passo prova**, não só o que fazer.

Termine com as seções 2 e 3 do runbook — as provocações e o lembrete de
estranhar número que aparece sem ter sido pedido.

## 4b. Caminho navegador: execute, observe, e devolva o julgamento

Use o navegador embutido (`mcp__Claude_Browser__`).

**Abra o painel do navegador antes de qualquer passo, e deixe visível.**
`preview_start` com a URL inicial o abre; `tabs_context` diz em qual estado
ele está.

Vá num ritmo que dê para acompanhar. Diga o que vai fazer antes de fazer, e
prefira passos separados a um lote grande.

Execute os passos da seção 1 e relate o que viu, com evidência: print da
tela, o que apareceu na aba Network, a saída de comandos. Você consegue
**verificar** valor, formato, status — o que você não consegue é **julgar**
aparência. "A tela parece errada" não é verificação; mostre e devolva:

> Print abaixo. Se a tela está como você desenhou, eu não sei dizer — olhe e
> me diga.

E nunca aprove. A frase final é dela, não sua.

**Dicas gerais do navegador embutido (limitação da ferramenta, não do
projeto):**

- **Ele não sobe arquivo por clique.** Não há seletor de arquivo nativo
  visível. Contorno: sirva o arquivo pela mesma origem (ex.: pasta pública
  do frontend) e injete no input pelo `javascript_tool`:

  ```js
  const blob = await (await fetch('/arquivo.ext')).blob();
  const dt = new DataTransfer();
  dt.items.add(new File([blob], 'arquivo.ext', { type: 'application/octet-stream' }));
  const input = document.querySelector('input[type=file]');
  input.files = dt.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
  ```

  Diga no relatório que o clique/arraste do seletor em si não foi exercitado.
- **Campos separados que avançam sozinhos** (código em vários quadrados, por
  exemplo) não aceitam a string inteira de uma vez. Use `form_input` em
  cada um.
- **Limpe a rede antes do passo que interessa** (`read_network_requests` com
  `clear`), senão o que importa fica enterrado sob chamadas do próprio
  framework.

**Cuidados e armadilhas:**

- **A seção 2 do runbook pode ter passos destrutivos.** Derrubar um
  container no meio de um fluxo é um teste legítimo e também pode afetar
  algo que está sendo usado para outra coisa. Diga o que vai fazer e como
  desfazer, antes de fazer.
- **Não invente passos.** Se o runbook não cobre algo que você acha que
  deveria, diga isso — provavelmente o runbook está desatualizado, e isso é
  um achado.

## 5. Feche dizendo o que ficou sem verificação

Toda conferência termina com duas listas, e a segunda é a que importa:

```
Verifiquei:
- <o que você mediu, com o valor observado>

Não consegui verificar:
- <o que precisa do olho de quem está conferindo>

A decisão de seguir é sua.
```

Escreva a segunda lista sem que perguntem — é o que impede o checkpoint de
virar carimbo.

## 6. Se algo foi encontrado, o runbook muda

Achou defeito? A seção 4 do runbook (`O que este checkpoint já pegou`) ganha
uma entrada datada, com o achado real e **por que os testes não pegaram**.

Se a funcionalidade mudou, o runbook muda junto — desatualizado ele é pior
que ausente.

## Cuidados específicos deste projeto

Nenhum registrado ainda. Ao encontrar uma armadilha própria deste projeto
durante um checkpoint (um serviço externo que manda algo de verdade, um
contorno de tela específico daqui, um dado que precisa existir antes),
registre aqui — data e o que aprender evita repetir a mesma surpresa na
próxima conferência.
TEMPLATE_EOF
```

- [ ] **Step 4: Rodar de novo e ver passar** — Expected: nenhuma linha, `EXIT=0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/test-runbook/templates/conducting-skill.md.template
git commit -m "$(cat <<'EOF'
feat: adiciona o template do SKILL.md conduzido pela test-runbook

Generaliza o SKILL.md do eaf-runbook removendo tudo específico do
documents-eaf-system e deixando uma seção de cuidados vazia para o
projeto de destino acumular com o tempo.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Template `preflight.sh.template`

**Files:**
- Create: `plugins/analizza-skills/skills/test-runbook/templates/preflight.sh.template`

**Interfaces:**
- Consumes: nada.
- Produces: o arquivo que a Task 1 (`SKILL.md`, seção 5) referencia e instrui a preencher.

- [ ] **Step 1: Checagem que deve falhar**

```bash
T=plugins/analizza-skills/skills/test-runbook/templates/preflight.sh.template
c() { local ok=0
  [ -f "$T" ] || { echo "arquivo nao existe"; return 1; }
  grep -q '{PORTAS}' "$T" || { echo "sem placeholder PORTAS"; ok=1; }
  grep -q '{BANCO_CHECK}' "$T" || { echo "sem placeholder BANCO_CHECK"; ok=1; }
  grep -q '{MAIL_HOST_VAR}' "$T" || { echo "sem placeholder MAIL_HOST_VAR"; ok=1; }
  [ "$(grep -c 'BLOCO-EMAIL' "$T")" = "2" ] || { echo "marcador BLOCO-EMAIL nao esta em par"; ok=1; }
  grep -qi 'documents_eaf_system\|elasticsearch\|mailpit' "$T" && { echo "residuo especifico do projeto original"; ok=1; }
  bash -n "$T" 2>/dev/null || { echo "sintaxe bash invalida"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `arquivo nao existe`, `EXIT=1`.

- [ ] **Step 3: Criar o template**

```bash
cat > plugins/analizza-skills/skills/test-runbook/templates/preflight.sh.template <<'PREFLIGHT_EOF'
#!/usr/bin/env bash
# Estado do ambiente antes de um checkpoint, num tiro so.
#
# Existe porque descobrir no meio do caminho que um servico esta parado e o
# tipo de atrito que faz a pessoa desistir de conferir -- e a conferencia que
# nao acontece e o unico jeito garantido de nao achar nada.
#
# Nao muda nada: so olha. Roda da raiz do repositorio.
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "== containers =="
if docker compose ps --format '{{.Service}} {{.Status}}' 2>/dev/null | grep -q .; then
  docker compose ps --format '{{.Service}} {{.Status}}' | sed 's/^/  /'
else
  echo "  nenhum de pe -- confira o comando de subida deste projeto"
fi

echo
echo "== aplicacao =="
PORTAS=({PORTAS})
for porta in "${PORTAS[@]}"; do
  p="${porta%%:*}"; nome="${porta##*:}"
  if lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  $nome ($p): no ar"
  else
    echo "  $nome ($p): fora"
  fi
done

echo
echo "== runbooks =="
encontrou=0
for f in docs/checkpoints/*.md; do
  [ -e "$f" ] || continue
  case "$(basename "$f")" in README.md) continue ;; esac
  encontrou=1
  tipo=$(sed -n 's/^type: *//p' "$f" | head -1)
  titulo=$(grep -m1 '^# ' "$f" | sed 's/^# //')
  printf '  %-22s [%-10s] %s\n' "$(basename "$f" .md)" "${tipo:-sem tipo}" "$titulo"
done
[ "$encontrou" = 0 ] && echo "  nenhum em docs/checkpoints/"

echo
echo "== banco =="
if {BANCO_CHECK}; then
  echo "  no ar"
else
  echo "  fora do ar, ou comando de health-check precisa de ajuste"
fi
# Health-check de infraestrutura, nao de dado: uma query de negocio (contagem
# de linhas, status de um registro) pode entrar aqui depois, se ajudar uma
# conferencia especifica deste projeto.

# BLOCO-EMAIL
echo
echo "== e-mail =="
host_de_email=$(grep -i '^{MAIL_HOST_VAR}=' .env.local 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')
if [ -n "$host_de_email" ] && [ "$host_de_email" != "localhost" ] && [ "$host_de_email" != "127.0.0.1" ]; then
  echo "  .env.local -> $host_de_email"
  echo "  SMTP DE VERDADE: todo envio vira mensagem real."
else
  echo "  sem SMTP externo configurado, ou preso num capturador local"
fi
# BLOCO-EMAIL
PREFLIGHT_EOF
```

- [ ] **Step 4: Rodar de novo e ver passar** — Expected: nenhuma linha, `EXIT=0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/test-runbook/templates/preflight.sh.template
git commit -m "$(cat <<'EOF'
feat: adiciona o template do preflight.sh conduzido pela test-runbook

Generaliza o preflight.sh do eaf-runbook: containers e portas ficam
sempre presentes, banco vira health-check generico, e o bloco de
e-mail so entra no projeto de destino se algo de SMTP for detectado.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Ligar a `analizza-integration-test` à `test-runbook`

**Files:**
- Modify: `plugins/analizza-skills/skills/analizza-integration-test/SKILL.md` (Passo 8)
- Modify: `plugins/analizza-skills/skills/analizza-integration-test/references/claude-md-obligation.md`

**Interfaces:**
- Consumes: `test-runbook` (Tasks 1–3) já existe e pode ser invocada/seguida por outro agente.
- Produces: toda execução futura da `analizza-integration-test` implanta `test-runbook`.

- [ ] **Step 1: Checagem que deve falhar**

```bash
IT=plugins/analizza-skills/skills/analizza-integration-test
c() { local ok=0
  grep -q 'test-runbook' "$IT/SKILL.md" || { echo "Passo 8 nao cita test-runbook"; ok=1; }
  grep -q '\.\./test-runbook/references/checkpoints-readme\.md' "$IT/SKILL.md" || { echo "Passo 8 nao aponta pro novo caminho do checkpoints-readme"; ok=1; }
  grep -q '/test-runbook' "$IT/references/claude-md-obligation.md" || { echo "obrigacao nao cita /test-runbook"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: três linhas "nao cita/aponta", `EXIT=1`.

- [ ] **Step 3: Editar o Passo 8**

Leia `$IT/SKILL.md` e localize o parágrafo **Checkpoints** do Passo 8 (o que hoje termina em
"Os checkpoints entram também num projeto só com backend: um runbook `api` é tão devido quanto um
de tela."). Troque o link de `[checkpoints-readme.md](./references/checkpoints-readme.md)` por
`[checkpoints-readme.md](../test-runbook/references/checkpoints-readme.md)`, e acrescente, no fim
do parágrafo, o parágrafo abaixo:

```markdown
Em seguida, implante a skill `test-runbook`
(`plugins/analizza-skills/skills/test-runbook/SKILL.md`) neste mesmo projeto — ela gera
`.claude/skills/test-runbook/` (a skill que conduz o checkpoint no dia a dia) sem perguntar e sem
sobrescrever o que já existir. Isto vale para todo escopo, inclusive backend sem frontend.
```

- [ ] **Step 4: Editar `claude-md-obligation.md`**

Leia o arquivo e, no bloco de markdown que ele grava no `CLAUDE.md` da raiz, depois da frase que
cita `docs/checkpoints/README.md` e `{conventions-file}`, acrescente:

```markdown
**Quem conduz** a conferência é a skill implantada em `.claude/skills/test-runbook/` — invoque-a
(`/test-runbook`) em vez de seguir o runbook improvisando os passos.
```

- [ ] **Step 5: Rodar de novo e ver passar** — Expected: nenhuma linha, `EXIT=0`.

- [ ] **Step 6: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-integration-test/SKILL.md plugins/analizza-skills/skills/analizza-integration-test/references/claude-md-obligation.md
git commit -m "$(cat <<'EOF'
feat: analizza-integration-test implanta a test-runbook no Passo 8

Fecha a promessa da descricao da skill ("checkpoints com runbook por
funcionalidade"): todo projeto configurado a partir de agora ja recebe
o mecanismo de conducao do checkpoint, nao so o README do formato.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Manifestos, versão e validação final

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/analizza-skills/.claude-plugin/plugin.json`
- Modify: `plugins/analizza-skills/.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: Tasks 1–4 completas (a skill existe, está ligada, `make validate` precisa achar uma
  pasta por `SKILL.md` — regra de `tools/validate_plugin_manifests.py`).
- Produces: plugin `0.3.2`, publicável.

- [ ] **Step 1: Checagem que deve falhar**

```bash
c() { local ok=0
  grep -q '"version": "0.3.2"' plugins/analizza-skills/.claude-plugin/plugin.json || { echo "claude-plugin sem 0.3.2"; ok=1; }
  grep -q '"version": "0.3.2"' plugins/analizza-skills/.codex-plugin/plugin.json || { echo "codex-plugin sem 0.3.2"; ok=1; }
  grep -q 'test-runbook' .claude-plugin/marketplace.json || { echo "marketplace.json nao cita test-runbook"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: três linhas "sem/nao cita", `EXIT=1`.

- [ ] **Step 3: Editar os três manifestos**

Em `plugins/analizza-skills/.claude-plugin/plugin.json` e
`plugins/analizza-skills/.codex-plugin/plugin.json`, troque `"version": "0.3.1"` por
`"version": "0.3.2"` nos dois (precisam bater, conforme `validar_manifestos`).

Em `.claude-plugin/marketplace.json`, no campo `description` do plugin `analizza-skills`,
acrescente ao final: `" A test-runbook implanta, em qualquer projeto, o mecanismo de checkpoint de conferência manual conduzido por essa mesma skill."`

- [ ] **Step 4: Rodar de novo e ver passar** — Expected: nenhuma linha, `EXIT=0`.

- [ ] **Step 5: Validação completa do marketplace**

```bash
make validate > /tmp/tr-validate.log 2>&1; echo "EXIT=$?"; tail -30 /tmp/tr-validate.log
make check > /tmp/tr-check.log 2>&1; echo "EXIT=$?"; tail -30 /tmp/tr-check.log
```

Expected: `EXIT=0` nos dois, `manifestos multi-harness válidos` no log do `validate`.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/marketplace.json plugins/analizza-skills/.claude-plugin/plugin.json plugins/analizza-skills/.codex-plugin/plugin.json
git commit -m "$(cat <<'EOF'
chore: versão 0.3.2 — adiciona a test-runbook

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

- **Cobertura da spec:** D1 (Task 1, skill própria), D2 (SKILL.md das Tasks 1/2 instrui detecção
  pelo próprio agente, sem parser), D3 (Task 4, Passo 8 sempre implanta), D4 (regra de "nunca
  sobrescreve" nas seções 1 de cada `SKILL.md`/template), D5 (Task 2, negativo de resíduo
  específico verificado por grep), D6 (Task 3, blocos condicionais e health-check genérico), D7
  (Task 4, frase em `claude-md-obligation.md`), D8 (Task 1, `git mv`). Todas as oito decisões têm
  task e checagem correspondentes.
- **Placeholders:** nenhum "TBD"/"implementar depois" — todo conteúdo de arquivo está escrito por
  extenso nos heredocs. As chaves `{comando-de-subida}`, `{PORTAS}`, `{BANCO_CHECK}`,
  `{MAIL_HOST_VAR}` são placeholders **intencionais** do próprio mecanismo de template (mesma
  convenção de `{base-package}` etc. já usada nas outras skills deste marketplace), preenchidos
  pelo agente que implanta — não por esta plan.
- **Consistência de nomes:** `test-runbook` (nome da skill, do diretório, do frontmatter e do
  comando `/test-runbook`) é o mesmo em todas as cinco tasks; os três caminhos de artefato
  (`docs/checkpoints/README.md`, `.claude/skills/test-runbook/SKILL.md`,
  `.claude/skills/test-runbook/scripts/preflight.sh`) aparecem idênticos na Task 1 (tabela),
  Task 2/3 (o que cada template se torna) e na spec.

## Fora de escopo (fica para depois, não faz parte deste plano)

- Migrar `documents-eaf-system` para usar `test-runbook`.
- Sub-projeto 2: implantar `test-runbook` no `analizza-auction` e escrever
  `docs/checkpoints/cadastro-e-login.md` — plano próprio, no repositório `analizza-auction`,
  depois que este plano for mesclado e a skill estiver disponível via
  `claude plugin update analizza-skills`.
