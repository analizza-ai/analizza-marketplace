# `yeroon-play-plug` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `yeroon-play-plug`, num plugin novo `yeroon-play` deste marketplace, que detecta back (Spring Boot Java/Kotlin) e front (Next, Expo, Flutter) de um projeto cliente, gera a chave do yeroon play sem o agente ver a senha, implementa a integração com a `/v1` a partir de moldes e termina com o norte de produção.

**Architecture:** Mesmo formato das skills do `analizza-skills`: `SKILL.md` com vocabulário de marcadores e procedimento, `references/` com o que a skill lê ou entrega, `templates/` com moldes `.template` (marcadores `{nome}`, blocos `<!-- se x -->…<!-- fim se x -->`), e `scripts/yeroon-key.sh`. Os moldes de back Java e de front Next saem do analizza-tube; Kotlin, Expo e Flutter saem do contrato. Cada conjunto de moldes é **provado** renderizando num projeto descartável e rodando a suíte dele. O validador do repositório passa a cobrir todos os plugins do `marketplace.json`, e um teste novo trava os anti-objetivos (marcador não declarado, chave literal, referência a repositório privado).

**Tech Stack:** Markdown, Bash (script da chave), Python 3 + pytest (validadores e teste do script), `claude plugin validate`. Moldes alvejam Spring Boot 4.x com `RestClient`, Flyway, Testcontainers; Next.js (App Router, Vitest); Expo (`expo-video`, `expo-file-system`, `jest-expo`); Flutter (`http`, `video_player`, `file_picker`, `flutter_test`).

**Spec:** [`docs/superpowers/specs/2026-10-22-yeroon-play-plug-design.md`](../specs/2026-10-22-yeroon-play-plug-design.md)

## Global Constraints

- Skill em `plugins/yeroon-play/skills/yeroon-play-plug/`; plugin `yeroon-play` próprio, **não** dentro do `analizza-skills`.
- Frontmatter do `SKILL.md` só com `name` e `description` (compatível com skills.sh).
- **A skill se basta:** nenhum arquivo dela cita `bjjdream`, `yeroon-stream-poc`, `analizza-tube`, `docs/api/v1.md` de outro repo ou `CLAUDE.md` deste repo.
- `YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` só no `.env` do back. Nunca em front, app, log, molde com valor, ou git.
- O agente nunca vê nem digita a senha da conta yeroon: quem roda `yeroon-key.sh` é a pessoa.
- `YEROON_API_URL` padrão `https://api.dev.play.yeroon.video`.
- Signup: `POST /account/signup` `{name,email,password,origin,webhookUrl,acceptedTerms}` → `201 {tenantId,name,apiKey,webhookSecret,sessionToken,sessionExpiresAt}`; e-mail repetido → `409`; regra quebrada → `422` `application/problem+json` com `errors[].code`.
- O cliente guarda só `video(id uuid = videoId, created_at)` e `webhook_receipt(delivery_id pk, event_type, video_id, received_at)`.
- Erros da `/v1` no cliente: `422` repassa `errors[]`; `404`→`404`; `409`→`409`; `401`/rede → `502` genérico, logando só o prefixo da chave.
- Webhook: `X-Yeroon-Signature: t=<epoch>,v1=<hex>`, `HMAC-SHA256(secret, "<epoch>.<corpo bruto>")`, comparação em tempo constante, recusa epoch fora de ±5 min (`401`) e recusa tudo sem segredo; dedupe por `X-Yeroon-Delivery`; responde `2xx` rápido.
- Playback devolve ao front só `embedUrl`, `hlsUrl`, `expiresAt`; o token é pedido a cada abertura e nunca guardado.
- Front web e app falam **só** com o back do cliente (e com o R2 nas URLs assinadas), nunca com a `/v1`.
- Back não Spring Boot → a skill para. Front não reconhecido → avisa e segue com o resto.
- Testes dos moldes usam dublê `@Primary` do cliente; nenhum teste chama a `/v1` de verdade.

## Review Focus

1. **Nome `video` já existe no projeto cliente** (tabela ou entidade de mesmo nome, comum em plataforma de cursos): a skill não pode sobrescrever nem colidir; espera-se que detecte e use outro nome confirmado com a pessoa (marcador `{video-entity}`/`{video-table}`). Teste: Task 9, passo de prova com tabela `video` pré-existente.
2. **`.env` existe e já tem `YEROON_API_KEY`**: rodar o script de novo não pode apagar a chave anterior em silêncio. Teste: Task 3, `test_chave_existente_nao_e_sobrescrita`.
3. **Front fora da porta 3000**: o upload do navegador falha no CORS do R2. Espera-se o aviso explícito no plano mostrado e no norte. Teste: Task 9, prova com `next dev -p 3005`.
4. **Webhook com corpo re-serializado** (framework lê JSON antes do filtro): a assinatura tem que ser calculada sobre os bytes brutos. Teste: Task 5 e 6, IT que envia corpo com espaços/ordem de campos incomuns e espera `200`.
5. **Projeto sem Flyway** (usa Liquibase ou `ddl-auto`): a skill não deve criar `db/migration` solta. Espera-se seguir o mecanismo encontrado ou parar perguntando. Teste: Task 9, regra em `detectar-stack.md` e prova de leitura.

---

### Task 0: Branch, spec e validador multi-plugin

**Files:**
- Create: `docs/superpowers/specs/2026-10-22-yeroon-play-plug-design.md` (movido de `yeroon-stream-poc/docs/superpowers/specs/`, onde não é versionado)
- Modify: `tools/validate_plugin_manifests.py` (`main()` lê `.claude-plugin/marketplace.json` e valida cada `plugins[].source`)
- Modify: `tools/tests/test_validate_plugin_manifests.py`
- Modify: `Makefile` (`validate` e `tag` para todos os plugins; variável `PLUGINS := analizza-skills yeroon-play`)

**Interfaces:**
- Produces: `validar_marketplace(raiz: Path) -> list[str]` — erros prefixados com o nome do plugin (`"yeroon-play: version diverge entre os manifestos"`); `main()` passa a chamá-la. `validar_manifestos(claude, codex, plugin_dir)` não muda.

- [ ] **Step 1:** `git switch main && git pull && git switch -c feat/yeroon-play-plug`. Mover o spec para `docs/superpowers/specs/` e apagar a cópia não versionada do `yeroon-stream-poc`.
- [ ] **Step 2: teste falhando** em `test_validate_plugin_manifests.py`:

```python
def test_marketplace_valida_todos_os_plugins(tmp_path: Path):
    # marketplace.json com dois plugins; o segundo com version divergente
    erros = validar_marketplace(tmp_path)
    assert erros == ["p2: version diverge entre os manifestos"]

def test_plugin_sem_codex_e_reportado(tmp_path: Path):
    assert any(e.startswith("p1: ") for e in validar_marketplace(tmp_path))
```

- [ ] **Step 3:** `make check` → FAIL (`validar_marketplace` não existe).
- [ ] **Step 4:** implementar `validar_marketplace` e trocar o `plugin_dir` fixo de `main()`.
- [ ] **Step 5:** `make check` → PASS; `python3 tools/validate_plugin_manifests.py` → `manifestos multi-harness válidos`.
- [ ] **Step 6:** commit `Validador e Makefile cobrem todos os plugins do marketplace`.

### Task 1: Plugin `yeroon-play` e guarda da skill

**Files:**
- Create: `plugins/yeroon-play/.claude-plugin/plugin.json`, `plugins/yeroon-play/.codex-plugin/plugin.json` (version `0.1.0`, mesmos campos do `analizza-skills`, `interface.displayName` `"Yeroon Play"`, `brandColor` `#4A1FB8`), `plugins/yeroon-play/assets/icon.png` (ícone do yeroon: `logo-yeroom.png` do export de design, redimensionado)
- Modify: `.claude-plugin/marketplace.json` (entrada `yeroon-play`, `source: ./plugins/yeroon-play`, `category: development`)
- Create: `plugins/yeroon-play/skills/yeroon-play-plug/SKILL.md` (só frontmatter e título por enquanto)
- Create: `tools/check_skill_guards.py`, `tools/tests/test_check_skill_guards.py`

**Interfaces:**
- Produces: `verificar_skill(skill_dir: Path) -> list[str]`. Regras: (a) todo `{marcador}` em `templates/**` está na tabela *Vocabulário* do `SKILL.md`; (b) nenhum arquivo contém `yk_` ou `whsec_` seguidos de 8+ caracteres alfanuméricos; (c) nenhum arquivo contém `bjjdream`, `yeroon-stream-poc`, `analizza-tube`; (d) frontmatter do `SKILL.md` tem exatamente `name` e `description`. `make check` roda isso para `plugins/yeroon-play/skills/*`.

- [ ] **Step 1: testes falhando**, um por regra: `test_marcador_nao_declarado`, `test_chave_literal`, `test_referencia_privada`, `test_frontmatter_com_campo_extra`, e `test_skill_valida_sem_erros`.
- [ ] **Step 2:** `make check` → FAIL.
- [ ] **Step 3:** implementar `verificar_skill`; ligar no alvo `check`. Marcador = `\{[a-z][a-z0-9-]*\}` não precedido de `$` (interpolação TS/Kotlin/Dart não conta), exceto `{id}`, que é variável de rota (`@PostMapping("/videos/{id}")`) e fica numa lista de permitidos. Teste extra: `test_variavel_de_rota_id_nao_e_marcador`.
- [ ] **Step 4:** `make check` e `make validate` → PASS.
- [ ] **Step 5:** commit `Plugin yeroon-play e guarda da skill yeroon-play-plug`.

### Task 2: `references/contrato.md`, `detectar-stack.md`, `norte.md`

**Files:**
- Create: `plugins/yeroon-play/skills/yeroon-play-plug/references/contrato.md` — resumo da `/v1` que o cliente usa: as 9 rotas (`POST /v1/videos/uploads`, `POST …/upload/part-urls` até 20, `GET …/upload/parts`, `POST …/upload/complete`, `DELETE …/upload`, `GET /v1/videos`, `GET /v1/videos/{id}`, `DELETE /v1/videos/{id}`, `POST /v1/videos/{id}/playback-token`) com corpos e respostas; status (`PENDENTE ENVIADO PROCESSANDO PRONTO FALHOU CANCELADO ABANDONADO`); webhook e erros como em *Global Constraints*; `postMessage` do player (`ready`, `error`); o signup. Linha final: "Fonte: contrato público v1 do yeroon play; atualize esta página quando a v1 mudar."
- Create: `references/detectar-stack.md` — comandos de detecção (os do spec, *Fluxo* 1), decisão por tabela (back Spring Java/Kotlin, Maven/Gradle Groovy/KTS, módulos `-api`/`-core`/único; front Next/Expo/Flutter; migração Flyway/Liquibase/nenhuma; porta do front), conflito de nome `video`, e o que fazer quando não reconhece.
- Create: `references/norte.md` — o checklist do spec (*O norte*), com marcadores `{front-origin}`, `{back-public-url}` para a skill preencher.

- [ ] **Step 1:** escrever os três arquivos.
- [ ] **Step 2:** conferir o `contrato.md` linha a linha contra o `docs/api/v1.md` do yeroon (leitura local, sem copiar o arquivo) — nenhuma rota, campo ou código a mais ou a menos.
- [ ] **Step 3:** `make check` → PASS (guarda da Task 1).
- [ ] **Step 4:** commit.

### Task 3: `scripts/yeroon-key.sh`

**Files:**
- Create: `plugins/yeroon-play/skills/yeroon-play-plug/scripts/yeroon-key.sh`
- Create: `tools/tests/test_yeroon_key.py` (sobe um `http.server` local fingindo o signup)

**Interfaces:**
- Produces: `yeroon-key.sh [--env <caminho do .env>] [--api <url>] [--origin <url>] [--webhook <url>]`. Pergunta nome, e-mail, senha (`read -rs`) e aceite dos termos pelo terminal. Saída 0 ao gravar; 2 se `.env` fora do `.gitignore`; 3 se e-mail já tem conta (`409`); 4 em `422` (imprime cada `errors[].code`); 5 se a chave já existe no `.env` sem `--force`. Nunca imprime a chave nem o segredo; imprime só o prefixo (`yk_abcd…`).

- [ ] **Step 1: testes falhando** (entrada pelo stdin, `--api` apontando ao servidor falso):
  - `test_grava_chave_e_segredo` → `.env` contém `YEROON_API_KEY=yk_…` e `YEROON_WEBHOOK_SECRET=whsec_…`; stdout sem os valores inteiros.
  - `test_env_fora_do_gitignore_para_sem_chamar_api` → saída 2, servidor sem requisição.
  - `test_email_ja_cadastrado` → saída 3, mensagem cita alias `nome+projeto@`, `.env` intacto.
  - `test_422_lista_codigos` → saída 4, `tenant.allowed-origins` no stderr.
  - `test_chave_existente_nao_e_sobrescrita` → saída 5 sem `--force`.
  - `test_corpo_enviado` → JSON recebido tem `origin` igual ao `--origin` e `acceptedTerms: true`.
- [ ] **Step 2:** `make check` → FAIL.
- [ ] **Step 3:** implementar com `curl` e `python3 -c` só para ler o JSON (sem `jq`, que não é garantido).
- [ ] **Step 4:** `make check` → PASS.
- [ ] **Step 5:** commit.

### Task 4: `SKILL.md`

**Files:**
- Modify: `plugins/yeroon-play/skills/yeroon-play-plug/SKILL.md`

O `description` cita os gatilhos: "plugar o yeroon play", "integrar yeroon", "hospedar vídeo das aulas no yeroon", "yeroon play no meu projeto", e diz o que **não** faz ("não constrói plataforma de vídeo própria"). Corpo, em passos numerados como nas skills do `analizza-skills`:

0. Pré-requisitos e o que a skill entrega (1 parágrafo).
1. **Detectar** — segue `references/detectar-stack.md`; resultado é a tabela de valores do *Vocabulário*.
2. **Mostrar o plano e esperar o ok** — stack, arquivos por camada, migração, variáveis, testes, runbook (só se o projeto tiver regra de runbook em `CLAUDE.md`/`AGENTS.md`), avisos (porta ≠ 3000, nome `video` em uso).
3. **Chave** — copiar `scripts/yeroon-key.sh` para `scripts/` do projeto, pedir que **a pessoa** rode no terminal (`bash scripts/yeroon-key.sh --origin {front-origin}`), interpretar o código de saída; ou conferir que a pessoa colou as variáveis (`grep -c '^YEROON_API_KEY=' .env`, sem imprimir valor).
4. **Implementar em fatias**, cada uma com a suíte do projeto verde: back (`templates/back-{language}-spring/`), web (`templates/front-next/`), mobile (`templates/mobile-expo/` ou `templates/mobile-flutter/`), testes, runbook.
5. **Norte** — preencher `references/norte.md` e entregar.

Tabela *Vocabulário* com todos os marcadores usados nos moldes (a guarda da Task 1 obriga): `{language}`, `{base-package}`, `{base-package-path}`, `{api-module}`, `{core-module}`, `{it-module}`, `{base-integration-test-fqn}`, `{migration-dir}`, `{migration-version}`, `{video-entity}`, `{video-table}`, `{back-url-env}`, `{front-origin}`, `{back-public-url}`, `{api-routes-prefix}`. Tarefas seguintes acrescentam marcadores aqui quando precisarem.

- [ ] **Step 1:** escrever. **Step 2:** `make check` → PASS. **Step 3:** commit.

### Task 5: Moldes `back-java-spring`

**Files:** `plugins/yeroon-play/skills/yeroon-play-plug/templates/back-java-spring/`, espelhando camadas:
- `core/` ← analizza-tube `analizza-tube-core/src/main/java/.../`: `infrastructure/configuration/YeroonProperties`, `infrastructure/data/anticorruptionLayer/yeroon/*` + `impl/YeroonClientImpl`, `application/video/*` (os 8 casos de uso) + **`deleteVideo` novo**, `application/webhook/receiveYeroonEvent/*`, `domain/Video`, `domain/repositories/*`, `infrastructure/repositories/*`, migração `V{migration-version}__yeroon_video_e_webhook.sql`.
- `api/` ← `analizza-tube-api`: `presenter/configuration/security/YeroonWebhookSignature`, `presenter/routes/video/*` (+ `deleteVideo`), `presenter/routes/webhook/receiveYeroonWebhook/*`, trecho para o `GlobalExceptionHandler` (`global-exception-handler.snippet.java.template`) e para `application.properties`.
- `it/` ← `analizza-tube-integration-tests`: `support/FakeYeroonClient`, trecho do `TestConfig`, um IT por rota.

Regras de generalização: pacote → `{base-package}`; `Video`/`video` → `{video-entity}`/`{video-table}`; nomes `Analizza*`/URLs do analizza-tube removidos; `IssuePlaybackResult` ganha `hlsUrl`; `YeroonClient` ganha `delete(UUID videoId)`; `GET /v1/videos` filtrado aos ids da tabela como no original.

**Interfaces (Produces, usados pelas Tasks 6 a 9):** rotas do back cliente — `POST /videos/uploads`, `POST /videos/{id}/upload/part-urls`, `GET /videos/{id}/upload/parts`, `POST /videos/{id}/upload/complete`, `DELETE /videos/{id}/upload`, `GET /videos`, `GET /videos/{id}`, `DELETE /videos/{id}`, `POST /videos/{id}/playback` → `{embedUrl,hlsUrl,expiresAt}`, `POST /webhooks/yeroon`. Respostas de upload no formato da v1 (`videoId`, `partSizeBytes`, `partCount`, `urls[]`, `parts[]`).

- [ ] **Step 1: prova descartável.** `git -C ~/Documents/Github/analizza-tube worktree add $SCRATCH/java-proof ed0ca43` (scaffold + guardrails, antes da integração). Escrever um renderizador descartável em `$SCRATCH/render.py` (troca `{marcador}` e resolve `<!-- se x -->`), **não versionado**.
- [ ] **Step 2: ITs primeiro.** Renderizar só `it/` na prova; `./gradlew test integrationTest` → FAIL de compilação (classes ausentes).
- [ ] **Step 3:** escrever os moldes `core/` e `api/`; renderizar; `./gradlew test integrationTest` → PASS, incluindo `EntrypointHasIntegrationTestIT` (todo entrypoint com IT) e o IT de webhook com corpo de espaçamento incomum (Review Focus 4).
- [ ] **Step 4:** `make check` → PASS (marcadores declarados).
- [ ] **Step 5:** commit. Remover o worktree de prova.

### Task 6: Moldes `back-kotlin-spring`

**Files:** `templates/back-kotlin-spring/` com a mesma árvore e os mesmos nomes da Task 5, em Kotlin idiomático (data classes, `RestClient` com extensões, sem `!!`).

- [ ] **Step 1:** gerar a prova com `/analizza-new-project` em Kotlin em `$SCRATCH/kt-proof` (só back; recusar web/mobile se a skill perguntar) e aplicar `/analizza-integration-test` com módulo dedicado.
- [ ] **Step 2:** renderizar `it/` → `./gradlew test integrationTest` FAIL.
- [ ] **Step 3:** escrever `core/` e `api/` → PASS, mesmos ITs da Task 5.
- [ ] **Step 4:** `make check` → PASS. **Step 5:** commit.

### Task 7: Moldes `front-next`

**Files:** `templates/front-next/` ← analizza-tube-web: `src/app/api/videos/**/route.ts` (Route Handlers de repasse, + `DELETE`), `src/lib/repasse.ts` (base `{back-url-env}`), `src/lib/upload.ts` (multipart com retomada, sem mudança de comportamento), `src/lib/videoStatus.ts`, e componentes **sem estilo próprio**: `VideoList`, `UploadForm`, `VideoPlayer` (iframe `allow="autoplay; fullscreen; picture-in-picture"`, `allowFullScreen`, mensagem em `postMessage` `type:"error"`). Os testes `.test.ts(x)` correspondentes do analizza-tube vão junto.

- [ ] **Step 1:** na prova Java da Task 5 (recriar o worktree), renderizar só os testes → `npm test` FAIL.
- [ ] **Step 2:** renderizar o resto → `npm test` e `npm run typecheck` PASS.
- [ ] **Step 3:** `npm run build` e `grep -rl 'yk_' .next/` → vazio.
- [ ] **Step 4:** `make check` → PASS. **Step 5:** commit.

### Task 8: Moldes `mobile-expo` e `mobile-flutter`

Sem implementação de referência: os dois saem do `contrato.md` e espelham o comportamento do `front-next`.

**Files:**
- `templates/mobile-expo/`: `src/lib/api.ts` (base `process.env.EXPO_PUBLIC_{back-url-env}`), `src/lib/upload.ts` (partes lidas por faixa com `expo-file-system`, PUT nas URLs assinadas, retomada via `GET /videos/{id}/upload/parts`), `src/components/VideoList.tsx`, `src/components/VideoPlayer.tsx` (`expo-video` com `hlsUrl`), `src/app/videos/[id].tsx`, testes `jest-expo`.
- `templates/mobile-flutter/`: `lib/yeroon/api.dart` (`http`, base por `--dart-define=BACK_URL`), `lib/yeroon/upload.dart` (mesmo algoritmo de partes), `lib/yeroon/video_list.dart`, `lib/yeroon/video_player_screen.dart` (`video_player` com `hlsUrl`; WebView com `embedUrl` em comentário como alternativa), `test/yeroon/*_test.dart`.

**Interfaces:** consomem as rotas da Task 5. `upload` nas duas: `uploadVideo(file, onProgress) -> Future/Promise<videoId>`; partes de `partSizeBytes`, no máximo 20 URLs por pedido, retoma pulando `partNumber` já listados.

- [ ] **Step 1:** Expo: na prova Java (`-mobile` do scaffold), renderizar testes → `npm test` FAIL; resto → PASS.
- [ ] **Step 2:** Flutter: `flutter create $SCRATCH/flutter-proof`; renderizar testes → `flutter test` FAIL; resto → PASS; `flutter analyze` sem erro.
- [ ] **Step 3:** `make check` → PASS. **Step 4:** commit.

### Task 9: Runbook da skill, provas ponta a ponta e release

**Files:**
- Create: `docs/checkpoints/yeroon-play-plug.md` (tipo `skill`): instalação pelos dois canais (`make marketplace-add && claude plugin install yeroon-play@analizza-marketplace`; `npx skills add analizza-ai/analizza-marketplace --skill yeroon-play-plug`), as três execuções do spec e o que olhar em cada uma; linha de manutenção: "mudou a v1 → atualizar `references/contrato.md` e os moldes".
- Create: `plugins/yeroon-play/skills/yeroon-play-plug/templates/runbook-yeroon-play.md.template` (o runbook que a skill escreve no projeto cliente quando ele tem regra de runbook).
- Modify: `README.md` (seção *Skills do plugin `yeroon-play`* e instalação), `Makefile` (`install` aceita `PLUGIN=`).

- [ ] **Step 1:** confirmar o pré-requisito do spec: `POST /account/signup` no ar em `https://api.dev.play.yeroon.video` (pedir à pessoa que rode `yeroon-key.sh` uma vez com e-mail alias; o agente não roda com senha).
- [ ] **Step 2: execução Java + Next + Expo** em cópia limpa do scaffold `ed0ca43`, invocando `/yeroon-play-plug` de verdade: o plano aparece antes de qualquer escrita; ao fim, enviar, listar e assistir no web e no app contra o yeroon dev; `yk_` ausente dos bundles. Repetir com o front em `-p 3005` e com uma tabela `video` pré-existente (Review Focus 1 e 3).
- [ ] **Step 3: execução Kotlin + Flutter** na prova da Task 6 com o projeto Flutter ao lado.
- [ ] **Step 4: execução em projeto não Spring** (`npx create-next-app` sozinho): a skill para e explica.
- [ ] **Step 5:** `make check && make validate` → PASS; `npx skills add ./plugins/yeroon-play/skills/yeroon-play-plug` instala localmente.
- [ ] **Step 6:** commit, push, PR. Depois do merge: `make tag` para `yeroon-play--v0.1.0` e `npx skills add analizza-ai/analizza-marketplace --skill yeroon-play-plug -y` instalando da `main`.

### Task 10: Descrição da `yeroon-video-streaming` (repo `yeroon-stream-poc`)

**Files:** Modify `yeroon-stream-poc/.claude/skills/yeroon-video-streaming/SKILL.md` (só o `description`).

- [ ] **Step 1:** branch nova a partir da `main` do `yeroon-stream-poc` (`chore/skill-video-streaming-escopo`), não a do tema.
- [ ] **Step 2:** o `description` passa a começar por "Para construir ou manter a própria plataforma de vídeo (o yeroon play)…" e termina com "Para usar o yeroon play num projeto cliente, use a yeroon-play-plug."
- [ ] **Step 3:** commit e PR no `bjjdream/yeroon-play`.
