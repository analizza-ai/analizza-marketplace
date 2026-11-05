# `analizza-expo-testflight` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `analizza-expo-testflight` no plugin `analizza-skills`. Ela implementa, num projeto Expo qualquer, o pipeline iOS → TestFlight por ambiente: Dev por disparo manual de branch, Prod por tag. Depois conduz a configuração da Apple pelo navegador embutido, com a pessoa assistindo.

**Architecture:** Mesmo formato das outras skills do `analizza-skills`:
- `SKILL.md` com o procedimento (fases 0–4) e a tabela de marcadores;
- `references/` com o guia de telas da Apple e o guia de dados de entrada;
- `templates/` com moldes `.template` (marcadores `{nome}`, blocos `<!-- se prod -->…<!-- fim se prod -->`) e scripts copiados sem mudança.

Os moldes generalizam o que o yeroon-play já tem revisado. Cada molde com comportamento é provado por teste neste repositório:
- bash para o script de identidade;
- pytest para o Makefile (com `gh` falso) e para o workflow renderizado (actionlint e estrutura);
- jest-expo, num app Expo de verdade, para o `app.config.ts`.

Um teste de conteúdo trava os anti-objetivos: nada de cliente nos arquivos da skill e nenhum marcador sem declaração.

**Tech Stack:**
- Markdown e Bash (script de identidade e teste dele);
- GitHub Actions (`macos-26`, `xcodebuild`, `Apple-Actions/upload-testflight-build@v1`);
- TypeScript (`app.config.ts`, jest-expo);
- Python 3 com pytest e PyYAML (testes do repositório);
- actionlint (Docker `rhysd/actionlint`) e `claude plugin validate`.

**Spec:** [`docs/superpowers/specs/2026-11-05-analizza-expo-testflight-skill-design.md`](../specs/2026-11-05-analizza-expo-testflight-skill-design.md)

**Referência viva**, para ler e não copiar nomes: `/Users/diegolirio/Documents/Github/yeroon-stream-poc`, branch `feat/pipeline-ios-testflight-dev`. Arquivos:
- `.github/workflows/mobile-ios-testflight-dev.yml`
- `.github/scripts/ios-dev-identity.sh` e `.test.sh`
- `yeroon-play-mobile/app.config.ts` e `__tests__/app-config-test.ts`
- alvo `mobile-ios-secrets` do `Makefile`
- `docs/checkpoints/testflight-ios-dev.md`

## Global Constraints

- **Local:** a skill fica em `plugins/analizza-skills/skills/analizza-expo-testflight/`. O frontmatter do `SKILL.md` só tem `name` e `description`.
- **Sem cliente:** nenhum arquivo da skill contém `yeroon`, `XF98CA5PDT`, `bjjdream` ou `analizza-tube`, sem diferenciar maiúscula de minúscula.
- **Escopo:** só Expo com geração nativa. Com `ios/` versionada ou `eas.json`, a skill para e explica.
- **`name` e `scheme` do Expo intocados:** só muda o `CFBundleDisplayName`.
- **Identidade:** fica em `.github/apps/<app-slug>.properties`, com `APP_NAME`, `IOS_BUNDLE_ID`, `APPLE_TEAM_ID` e uma linha para cada `EXPO_PUBLIC_*` que o app lê. O arquivo é **lido como texto, nunca executado com `source`**.
- **Ambientes:**

  | | Dev | Prod |
  |---|---|---|
  | Workflow | `mobile-ios-testflight-dev.yml` | `mobile-ios-testflight-prod.yml` |
  | Disparo | `workflow_dispatch`, qualquer branch menos a padrão | push de tag `v*` |
  | Guarda | — | tag igual a `v<version do app.json>` e commit da tag contido na branch padrão |

- **Ordem do workflow:** a guarda roda antes de qualquer passo que leia `secrets.*`. `github.ref`/`github.ref_name` só entram em script por `env:`, nunca interpolados num `run:`.
- **Build number:** `github.run_number` do workflow do ambiente.
- **Credenciais:** cinco secrets por environment, gravados por `make mobile-ios-secrets ENV=<environment>`: `APPLE_API_KEY_ID`, `APPLE_API_ISSUER_ID`, `APPLE_API_KEY_P8`, `IOS_DISTRIBUTION_CERT_BASE64`, `IOS_CERTIFICATE_PASSWORD`. O alvo só cria o environment se ele não existir.
- **Chave da API:** acesso **Administrador** como padrão sugerido. A pessoa confirma na tela.
- **Segredos:** a skill nunca digita nem lê senha, código 2FA, `.p8`, `.p12` ou chave privada. Arquivos secretos ficam fora do repositório.
- **Cliques sem volta:** ok da pessoa a cada passo (Register, Criar, Gerar, Concordar, convidar). Nada existente na Apple é revogado, apagado ou rebaixado.
- **Navegador:**
  1. o embutido (`mcp__Claude_Browser__*`);
  2. o Claude in Chrome, se pedido;
  3. sem navegador: passos à mão, um bloco por vez.
- **Versão:** o plugin vai para `0.12.0` nos dois manifestos.
- **Instalação documentada:** pelo plugin do harness e por `npx skills add analizza-ai/analizza-marketplace --skill analizza-expo-testflight`.

## Review Focus

1. **Projeto com `ios/` versionada ou `eas.json`:** a skill tem de parar na Fase 0 antes de gerar qualquer arquivo, porque o `prebuild --clean` apagaria código nativo. Teste: Task 6, `test_skill_para_em_bare_e_eas`.
2. **Valor do `.properties` com `$(...)`, aspas ou espaços:** é lido literalmente e nada executa. Teste: Task 1, casos `valor_com_subshell_nao_executa` e `aspas_e_espacos`.
3. **Tag `v1.2.3` com `app.json` em `1.2.4`, ou tag num commit fora da branch padrão:** o run falha na guarda, antes de qualquer credencial. Teste: Task 1, casos `tag_diferente_da_versao` e `commit_fora_da_padrao`. Task 2, `test_guarda_antes_dos_secrets`.
4. **Environment já existe com aprovação obrigatória:** `make mobile-ios-secrets` não pode fazer PUT nele. Teste: Task 4, `test_environment_existente_nao_recebe_put`.
5. **Segundo ambiente no mesmo time:** a skill não pode gerar uma segunda chave nem um segundo certificado, e sim reaproveitar os arquivos e gravar no segundo environment. Teste: Task 6, `test_skill_reaproveita_credenciais_do_time`.

---

### Task 0: Teste descartável do navegador embutido nas páginas da Apple

Só verifica. Nenhum código. Decide se o navegador é o caminho principal ou opcional da Fase 2.

**Files:** nenhum. O resultado vai para o ledger e, na Task 5, para o topo de `references/apple-console.md`.

- [ ] **Step 1:** `preview_start {url: "https://developer.apple.com/account"}`, com o painel visível. Pedir à pessoa que faça login com a conta da empresa (usuário, senha e 2FA) no painel. O agente não digita nada.
- [ ] **Step 2:** com a pessoa logada, `navigate` para `https://developer.apple.com/account/resources/identifiers/list` e `get_page_text`.
  Esperado: o texto contém "Identifiers" e o Team ID da pessoa.
- [ ] **Step 3:** `navigate` para `https://appstoreconnect.apple.com/apps` e `get_page_text`.
  Esperado: a lista de apps aparece sem um novo login. Se pedir login, anotar.
- [ ] **Step 4:** `find "Adicionar apps"` ou `find "New App"`, sem clicar.
  Esperado: um `ref_N` encontrado, o que prova que o agente consegue localizar botões.
- [ ] **Step 5:** registrar no ledger: `Task 0: navegador embutido <funciona|falha em X> em developer.apple.com e appstoreconnect.apple.com, idioma da UI <en|pt-BR> em cada um, data`.
  Se falhar, registrar `Ruling: modo manual é o caminho principal` e seguir.

### Task 1: Script de identidade com guarda de branch e de tag

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-expo-testflight/templates/github/scripts/ios-identity.sh`, copiado sem mudança para `.github/scripts/ios-identity.sh` do projeto de destino.
- Test: `plugins/analizza-skills/skills/analizza-expo-testflight/templates/github/scripts/ios-identity.test.sh`, copiado junto.

**Interfaces:**
- Produces, todos com saída `0` = ok e `1` = erro com `::error::<mensagem>` no stderr:
  - `ios-identity.sh guard-branch <ref> <default-branch>`: aceita `refs/heads/*` desde que não seja `refs/heads/<default-branch>`.
  - `ios-identity.sh guard-tag <ref> <app-version>`: aceita só `refs/tags/v<app-version>`.
  - `ios-identity.sh on-default <default-branch>`: verifica, no repositório do diretório atual, `git merge-base --is-ancestor HEAD origin/<default-branch>`.
  - `ios-identity.sh load <file>`: imprime `app_name=…`, `ios_bundle_id=…` e `apple_team_id=…`, uma por linha, para o `$GITHUB_OUTPUT`.
  - `ios-identity.sh public-env <file>`: imprime as linhas `EXPO_PUBLIC_*=<valor>`, para o `$GITHUB_ENV`.
- Regras de `load` e `public-env`:
  - linhas `CHAVE=valor`; `#` é comentário; aspas simples ou duplas em volta do valor são removidas;
  - o valor é literal, sem expansão;
  - `APP_NAME`, `IOS_BUNDLE_ID` e `APPLE_TEAM_ID` são obrigatórias e não podem ficar vazias. O erro cita **todas** as que faltam;
  - `APPLE_TEAM_ID` casa `^[A-Z0-9]{10}$`, e `IOS_BUNDLE_ID` casa `^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$`;
  - chave fora dessas três e fora de `^EXPO_PUBLIC_[A-Z0-9_]+$` é erro.

- [ ] **Step 1: teste falhando.** O `ios-identity.test.sh` cria arquivos temporários com `mktemp -d`, roda cada caso e termina com `OK (<n> casos)`, ou sai com `1` no primeiro que falhar. Casos, com nome e esperado:
  - `branch_feature_aceita`: `guard-branch refs/heads/feat/x main` → 0
  - `branch_padrao_recusada`: `guard-branch refs/heads/main main` → 1, a mensagem cita `main`
  - `branch_recusa_tag`: `guard-branch refs/tags/v1.0.0 main` → 1
  - `tag_igual_a_versao`: `guard-tag refs/tags/v1.2.3 1.2.3` → 0
  - `tag_diferente_da_versao`: `guard-tag refs/tags/v1.2.3 1.2.4` → 1, a mensagem cita as duas
  - `tag_recusa_branch`: `guard-tag refs/heads/v1.2.3 1.2.3` → 1
  - `commit_na_padrao`: repositório temporário com `origin/main` apontando para o HEAD → `on-default main` sai 0
  - `commit_fora_da_padrao`: HEAD num commit que não está em `origin/main` → 1
  - `load_completo`: `APP_NAME="Meu App Dev"` → a saída contém `app_name=Meu App Dev`
  - `aspas_e_espacos`: `APP_NAME='A B'` → `app_name=A B`
  - `valor_com_subshell_nao_executa`: `EXPO_PUBLIC_X=$(touch $TMP/pwn)` → `public-env` imprime o texto literal e `$TMP/pwn` não existe
  - `faltando_lista_todas`: o arquivo só tem `APP_NAME` → 1, e a mensagem cita `IOS_BUNDLE_ID` e `APPLE_TEAM_ID`
  - `team_invalido`: `APPLE_TEAM_ID=TEAM` → 1
  - `chave_desconhecida`: `API_URL=x` → 1, a mensagem cita `API_URL`
  - `public_env_so_publicas`: `public-env` não imprime `APP_NAME`
- [ ] **Step 2:** `bash plugins/analizza-skills/skills/analizza-expo-testflight/templates/github/scripts/ios-identity.test.sh`
  Esperado: falha, porque o `ios-identity.sh` ainda não existe.
- [ ] **Step 3:** implementar o `ios-identity.sh` com `set -euo pipefail` e compatível com o bash 3.2 do macOS, sem arrays associativos. A leitura usa `while IFS= read -r` com `${linha%%=*}` e `${linha#*=}`, sem `source` nem `eval`.
- [ ] **Step 4:** rodar o teste de novo. Esperado: `OK (15 casos)`. Depois, `shellcheck` nos dois arquivos, se o comando existir. Esperado: nenhum aviso.
- [ ] **Step 5: commit.** `feat(expo-testflight): script de identidade com guarda de branch e de tag`

### Task 2: Workflows Dev e Prod

**Files:**
- Create: `templates/github/workflows/mobile-ios-testflight.yml.template`. É um molde só, com os blocos `# se dev`…`# fim se dev` e `# se prod`…`# fim se prod`. A skill gera um arquivo por ambiente.
- Create: `tools/tests/test_expo_testflight_workflow.py`
- Modify: `requirements-dev.txt` (acrescentar `pyyaml`)

**Interfaces:**
- Consumes: os subcomandos da Task 1.
- Produces, os marcadores do workflow:
  - `{env}` (`dev` ou `prod`)
  - `{app-dir}` (pasta do app Expo, relativa à raiz)
  - `{github-environment}`
  - `{properties-file}` (`.github/apps/<app-slug>.properties`)
  - `{default-branch}`
  - `{xcode-workspace}` e `{xcode-scheme}` (o `name` do Expo normalizado, como o prebuild gera)
- Produces, a função de teste `renderizar(template: str, valores: dict[str, str], blocos: set[str]) -> str`, em `tools/tests/expo_testflight_render.py`. Ela troca `{marcador}` (regex `(?<![{$])\{[a-z][a-z0-9-]*\}(?!\})`), mantém os blocos pedidos e remove os outros com os comentários de abertura e fechamento. As Tasks 4 e 6 reaproveitam essa função.

O corpo segue o workflow do yeroon-play, com estas mudanças:
- a guarda usa `ios-identity.sh` com `REF: ${{ github.ref }}` em `env:`;
- no Prod, o checkout usa `fetch-depth: 0`, e os passos `guard-tag` (versão lida do `{app-dir}/app.json`) e `on-default` vêm antes de qualquer `secrets.*`;
- as variáveis públicas são carregadas uma vez com `public-env >> "$GITHUB_ENV"`, e por isso chegam ao prebuild e ao archive;
- o archive também recebe `APP_DISPLAY_NAME` e `IOS_BUNDLE_ID` (corrige o M5 do yeroon-play);
- `concurrency.group: ios-testflight-{env}`.

- [ ] **Step 1: testes falhando** em `test_expo_testflight_workflow.py`. Valores de exemplo: `{"env":"dev","app-dir":"apps/mobile","github-environment":"exemplo-dev","properties-file":".github/apps/exemplo-dev.properties","default-branch":"main","xcode-workspace":"exemplomobile","xcode-scheme":"exemplomobile"}`.

```python
def test_dev_dispara_so_manual(): assert set(wf("dev")["on"]) == {"workflow_dispatch"}
def test_prod_dispara_por_tag(): assert wf("prod")["on"]["push"]["tags"] == ["v*"]
def test_guarda_antes_dos_secrets():  # para dev e prod
    # índice do primeiro step cujo texto contém "secrets." > índice de todo step que roda ios-identity.sh guard-*/on-default
def test_ref_nao_interpolado_em_run():  # nenhum step["run"] contém "${{ github.ref"
def test_publicas_vao_para_github_env():  # algum run contém 'public-env' e '>> "$GITHUB_ENV"'
def test_sem_marcador_sobrando():  # renderizado não casa a regex de marcador
def test_actionlint_limpo():  # pytest.skip se não houver docker; roda rhysd/actionlint no arquivo renderizado, returncode 0
```

- [ ] **Step 2:** `python3 -m pytest tools/tests/test_expo_testflight_workflow.py -q`. Esperado: falha, porque o molde ainda não existe.
- [ ] **Step 3:** escrever o molde e o `expo_testflight_render.py`.
- [ ] **Step 4:** rodar de novo. Esperado: `7 passed`, ou `6 passed, 1 skipped` sem Docker. Neste caso, rodar o actionlint à mão uma vez e registrar no ledger.
- [ ] **Step 5: commit.** `feat(expo-testflight): workflows Dev e Prod do TestFlight`

### Task 3: `app.config.ts` com a identidade vinda do ambiente

**Files:**
- Create: `templates/app/app.config.ts.template`. Sem marcadores, por isso é copiado sem mudança.
- Create: `templates/app/app-config-test.ts.template`, copiado para `{app-dir}/__tests__/app-config-test.ts`.

**Interfaces:**
- Produces: o `export default ({ config }: ConfigContext): ExpoConfig`, que lê:
  - `APP_DISPLAY_NAME` → `ios.infoPlist.CFBundleDisplayName`
  - `IOS_BUNDLE_ID` → `ios.bundleIdentifier`
  - `APPLE_TEAM_ID` → `ios.appleTeamId`
  - `IOS_BUILD_NUMBER`, só dígitos → `ios.buildNumber`

  E sempre declara `ITSAppUsesNonExemptEncryption: false`. Variável vazia conta como ausente. Mantém o comportamento do `app.config.ts` que a `analizza-new-project` gera (`appleTeamId` vindo do ambiente). Se o destino só tem esse arquivo da `analizza-new-project`, o molde o substitui. Se o `app.config.ts` tem outra coisa, a skill acrescenta a leitura ao que existe e não apaga nada (regra no `SKILL.md`, Task 6).

- [ ] **Step 1: teste falhando.** Os mesmos cinco casos do yeroon-play, com nomes genéricos: `semVariaveisMantemAppJson`, `identidadeVemDoAmbiente`, `variavelVaziaContaComoAusente`, `buildNumberInvalidoEhIgnorado`, `declaraCriptografiaIsenta`. Usar `name: "exemplo"` e o bundle `com.exemplo.app.dev`.
- [ ] **Step 2: prova num app Expo real.**

  ```bash
  P=$(mktemp -d)
  rsync -a --exclude node_modules /Users/diegolirio/Documents/Github/yeroon-stream-poc/yeroon-play-mobile/ "$P/app/"
  ln -s /Users/diegolirio/Documents/Github/yeroon-stream-poc/yeroon-play-mobile/node_modules "$P/app/node_modules"
  ```

  Copiar só o teste para `$P/app/__tests__/`, apagar `$P/app/app.config.ts` e rodar `npx jest __tests__/app-config-test.ts` dentro de `$P/app`.
  Esperado: falha, porque não há `app.config.ts`.
- [ ] **Step 3:** escrever o `app.config.ts.template` e copiá-lo para `$P/app/app.config.ts`.
- [ ] **Step 4:** rodar o jest de novo. Esperado: `5 passed`. Depois, rodar `npx tsc --noEmit` em `$P/app`. Esperado: nenhum erro. Por fim, `rm -rf "$P"`.
- [ ] **Step 5: commit.** `feat(expo-testflight): app.config.ts lê a identidade do ambiente`

### Task 4: Alvo `mobile-ios-secrets` do Makefile

**Files:**
- Create: `templates/makefile/mobile-ios-secrets.mk.template`. É acrescentado ao `Makefile` do destino; se não houver `Makefile`, é criado só com esse alvo.
- Create: `tools/tests/test_expo_testflight_makefile.py`

**Interfaces:**
- Consumes: `renderizar` da Task 2.
- Produces:
  - marcador `{github-repo}`, padrão de `GH_REPO ?=`;
  - alvo `mobile-ios-secrets`, com `ENV` obrigatório e `GH_REPO` sobrescrevível.

  Comportamento do alvo:
  - sem `ENV`, sai com `1` e a mensagem `ENV=<environment> obrigatório`;
  - lista **todas** as cinco variáveis que faltam antes de chamar o `gh`;
  - confere se o `gh` existe;
  - faz GET em `repos/$(GH_REPO)/environments/$(ENV)` e só faz PUT se o retorno for 404;
  - grava cada secret com `printf '%s' "$$VAR" | gh secret set NOME --env $(ENV) --repo $(GH_REPO)` e para na primeira falha.

- [ ] **Step 1: testes falhando.** Cada teste renderiza o fragmento num `Makefile` em `tmp_path` e põe no `PATH` um `gh` falso. O falso registra cada chamada num arquivo e só lê o stdin em `secret set`. A variável `FAKE_GH_ENV_EXISTS=1|0` controla o GET, e `FAKE_GH_FAIL_ON=<NOME>` faz um `secret set` falhar.

```python
def test_sem_env_falha_sem_chamar_gh()
def test_lista_todas_as_variaveis_faltando()        # 5 nomes na saída, log do gh vazio
def test_environment_existente_nao_recebe_put()     # nenhuma chamada com "PUT"
def test_environment_ausente_e_criado()             # uma chamada PUT, antes do primeiro secret set
def test_valor_multilinha_chega_inteiro()           # .p8 de 3 linhas chega byte a byte ao gh
def test_falha_num_secret_para()                    # returncode != 0, nenhum secret depois do que falhou
```

- [ ] **Step 2:** `python3 -m pytest tools/tests/test_expo_testflight_makefile.py -q`. Esperado: falha.
- [ ] **Step 3:** escrever o fragmento a partir do alvo do yeroon-play, com `ENV` no lugar do environment fixo.
- [ ] **Step 4:** rodar de novo. Esperado: `6 passed`.
- [ ] **Step 5: commit.** `feat(expo-testflight): alvo mobile-ios-secrets por environment`

### Task 5: Runbook, guia da Apple e guia de dados

**Files:**
- Create: `templates/docs/testflight-ios.md.template`. Gera `docs/checkpoints/testflight-ios-{env}.md` com `type: screen-mobile` e as quatro seções do formato da `test-runbook`, mais a "Preparação única". Blocos `<!-- se dev -->` e `<!-- se prod -->`, e `<!-- se primeiro-do-time -->` para a chave e o certificado. Marcadores: `{env}`, `{app-name}`, `{bundle-id}`, `{team-id}`, `{sku}`, `{github-environment}`, `{github-repo}`, `{default-branch}`, `{testers-group}` e `{public-urls}` (lista em markdown).
- Create: `references/apple-console.md`. É o guia de telas do design, seção "Guia da Apple", com os rótulos em inglês e em português. Leva no topo a data e o resultado da Task 0, e registra que a distribuição automática não muda depois de criado o grupo.
- Create: `references/dados-de-entrada.md`. Traz as tabelas "Do time" e "Do ambiente" do design, a pergunta de entrevista para cada dado e o formato da spec que a skill grava (`docs/superpowers/specs/AAAA-MM-DD-testflight-ios-<env>-design.md`).

**Interfaces:**
- Consumes: `renderizar`; os nomes dos workflows e do alvo (Tasks 2 e 4).
- Produces: os marcadores do runbook, listados acima, para a tabela do `SKILL.md`.

O runbook já sai com as correções da comparação com o gist:
- os termos do App Store Connect;
- o "Solicitar acesso" da API;
- a criação do usuário antes de adicioná-lo como tester;
- o campo "Nome da empresa", só no primeiro app do time;
- o campo "Acesso de usuário";
- o `openssl` para a chave e o CSR, e o `openssl pkcs12 -export` rodado pela pessoa;
- a chave como Administrador, com o motivo da aprovação obrigatória.

- [ ] **Step 1:** escrever os três arquivos.
- [ ] **Step 2:** acrescentar ao `test_expo_testflight_workflow.py`:

```python
def test_runbook_renderizado_dev_e_prod():
    # renderizar com blocos {"dev","primeiro-do-time"} e {"prod"}: sem marcador sobrando,
    # começa com "---\ntype: screen-mobile\n---", contém "## 1. O que precisa bater" … "## 4. O que este checkpoint já pegou";
    # prod contém "v<versão>" e não contém "workflow_dispatch"
```

- [ ] **Step 3:** rodar a suíte. Esperado: os testes novos passam.
- [ ] **Step 4: commit.** `docs(expo-testflight): runbook por ambiente e guias da Apple e de dados`

### Task 6: `SKILL.md`

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-expo-testflight/SKILL.md`
- Create: `tools/tests/test_expo_testflight_skill.py`

**Interfaces:**
- Consumes: todos os moldes e marcadores das Tasks 1–5.

Seções, na ordem do design:
1. O que a skill faz e o que não faz.
2. **Fase 0.** Detectar Expo e parar em `ios/` versionada ou `eas.json`. Reconhecer as fatias existentes pelo `mobile-ios-testflight-*.yml` e pelo `.properties`. Perguntar o ambiente, com Dev sugerido. Juntar os dados que faltam numa pergunta só, com `references/dados-de-entrada.md`. Levantar as `EXPO_PUBLIC_*` com `grep -rhoE 'process\.env\.EXPO_PUBLIC_[A-Z0-9_]+' {app-dir} --include='*.ts' --include='*.tsx' --include='*.js' --exclude-dir=node_modules`. Gravar a spec.
3. **Fase 1.** Tabela molde → destino, tabela de marcadores (cada marcador de cada molde) e regras herdadas. Um `app.config.js` existente recebe a mesma lógica, sem os tipos. Branch, commits, e push e PR só com o ok da pessoa.
4. **Fase 2.** Ordem de preferência do navegador, painel visível, a sequência de 8 passos dizendo quem faz cada um, o ok a cada clique sem volta e a parada quando o limite de certificados está cheio. No segundo ambiente do mesmo time, pular a chave e o certificado.
5. **Fase 3.** Bloco de `export` com os caminhos e `make mobile-ios-secrets ENV=…` rodado pela pessoa, aprovação obrigatória e merge.
6. **Fase 4.** Disparo ou tag, `gh run watch`, `/test-runbook` e o relatório (pronto, pendente e com quem, próxima fatia).
7. **Retomada.** O que olhar antes de cada passo.
8. **Segurança.** As restrições do design, literais.

- [ ] **Step 1: testes falhando** em `test_expo_testflight_skill.py`:

```python
SKILL = Path("plugins/analizza-skills/skills/analizza-expo-testflight")
def test_frontmatter_so_name_e_description()
def test_sem_cliente_nos_arquivos():          # nenhum arquivo sob SKILL casa (?i)yeroon|XF98CA5PDT|bjjdream|analizza-tube
def test_todo_marcador_esta_declarado():      # cada {marcador} de templates/** aparece como `{marcador}` no SKILL.md
def test_todo_molde_e_citado():               # cada arquivo de templates/** e references/** é linkado no SKILL.md
def test_skill_para_em_bare_e_eas():          # SKILL.md cita "eas.json" e "ios/" na seção da Fase 0, com instrução de parar
def test_skill_reaproveita_credenciais_do_time():  # SKILL.md, seção Fase 2, diz que no segundo ambiente pula chave e certificado
```

- [ ] **Step 2:** `python3 -m pytest tools/tests/test_expo_testflight_skill.py -q`. Esperado: falha, porque não há `SKILL.md`.
- [ ] **Step 3:** escrever o `SKILL.md`. A `description` cobre os gatilhos: "pipeline iOS", "TestFlight", "publicar app Expo no iPhone", "configurar App Store Connect", "app de produção iOS".
- [ ] **Step 4:** rodar a suíte inteira, `python3 -m pytest tools/tests -q`. Esperado: tudo passa.
- [ ] **Step 5: commit.** `feat(expo-testflight): SKILL.md com as fases, a retomada e a segurança`

### Task 7: Distribuição e validação do repositório

**Files:**
- Modify: `.claude-plugin/marketplace.json` (descrição do `analizza-skills` cita a skill nova)
- Modify: `plugins/analizza-skills/.claude-plugin/plugin.json` e `.codex-plugin/plugin.json` (`version: "0.12.0"`; no Codex, `keywords` e `longDescription` citam Expo e TestFlight)
- Modify: `README.md` (linha da skill na lista e o comando `npx skills add … --skill analizza-expo-testflight`)

- [ ] **Step 1:** fazer as edições.
- [ ] **Step 2:** `make validate`. Esperado: sai com `0`.
- [ ] **Step 3:** `make check`, num venv com `pip install -r requirements-dev.txt`. Esperado: tudo passa.
- [ ] **Step 4: commit.** `chore(analizza-skills): 0.12.0 com a analizza-expo-testflight`

### Depois do plano: validação real (com a pessoa, fora do loop de tasks)

Isto não é uma task do executor. É o "Pronto quando" do design, e depende de merge e de ações sem volta na Apple.

1. A pessoa revisa e mergeia o PR do marketplace e instala a skill pelo GitHub (`npx skills add analizza-ai/analizza-marketplace --skill analizza-expo-testflight`, ou pelo plugin).
2. No yeroon-play, com a fatia Dev já na `main`, invoca a skill e escolhe Prod. A skill deve:
   - reconhecer a fatia Dev no formato antigo e não mexer nela;
   - montar o app "Yeroon Play" na Apple pelo navegador;
   - reaproveitar a chave e o certificado;
   - abrir o PR da fatia Prod;
   - levar a primeira tag ao TestFlight;
   - propor o `/test-runbook`.
3. O que a validação mostrar de errado volta como correção no marketplace.
