---
name: analizza-expo-play
description: Leva um app Expo ao teste interno do Google Play por ambiente. Implementa no repositório o pipeline Android (GitHub Actions, identidade do app, app.config.ts e config plugins de nome e assinatura, credenciais por environment, runbook) para Dev, disparado à mão de qualquer branch, e para Prod, disparado por tag; depois conduz a configuração no Play Console e no Google Cloud pelo navegador embutido, com a pessoa assistindo, fazendo login e aprovando cada passo sem volta. Use quando pedirem "pipeline Android", "Google Play", "teste interno", "publicar o app Expo no Android sem cabo", "configurar o Play Console", "service account do Play", "app de produção Android", "deploy Android por tag" ou invocarem /analizza-expo-play.
---

# analizza-expo-play

Monta, num projeto **Expo**, o caminho até o **teste interno** do Google Play, um
ambiente por vez, nos mesmos conceitos da `analizza-expo-testflight`:

- **Dev:** um app próprio no Play (ex.: "Meu App Dev"), apontando para o
  backend de desenvolvimento, disparado à mão de qualquer branch, a padrão
  inclusive. Só na branch padrão dá para marcar **gerar_tag**, que cria
  `v<versão>` no commit depois do upload (a tag só marca o commit).
- **Prod:** outro app (ex.: "Meu App"), apontando para produção, disparado por
  push da tag `v<versão>` num commit da branch padrão, ou à mão nessa tag (a
  criada pelo **gerar_tag** do Dev não dispara sozinha). Do teste interno, a
  promoção para fechado, aberto ou produção é manual no Play Console.

Cada ambiente é uma **fatia completa**: código no repositório, Play Console e
Google Cloud configurados, credenciais no GitHub, primeiro build no teste
interno e conferência pelo runbook. Normalmente se começa por Dev.

A pessoa assiste a tudo. Ela faz login, decide e cuida dos segredos. A skill
preenche o que a spec já define e **nunca** digita, gera nem lê senha, código de
dois fatores, keystore ou JSON de service account.

**Não faz:** Flutter, Kotlin nativo, React Native sem Expo, iOS (é a
`analizza-expo-testflight`), publicação em produção, CI fora do GitHub Actions,
e projetos Expo com `android/` versionada (bare) ou com build pelo EAS.

## Vocabulário dos moldes

Os moldes em `templates/` usam marcadores `{nome}` e blocos condicionais em
linhas próprias: `# se <bloco>` … `# fim se <bloco>` no YAML e
`<!-- se <bloco> -->` … `<!-- fim se <bloco> -->` no Markdown. Mantenha só os
blocos que valem, remova as linhas de abertura e fechamento, e troque todos os
marcadores. Nenhum marcador pode sobrar (`grep -n '{[a-z-]*}'` no arquivo gerado
volta vazio, fora `${{ }}` do Actions).

**Blocos:**
- `dev` ou `prod`: o ambiente da fatia (exatamente um).
- `primeira-service-account` ou `reaproveita-service-account` (exatamente um, só
  no runbook): a service account do produto é criada nesta fatia, ou já existe
  (o outro ambiente do mesmo produto) e só ganha acesso ao app novo.
- `pnpm`: só quando o projeto usa pnpm.

| Marcador | Valor | Exemplo |
|---|---|---|
| `{env}` | `dev` ou `prod` | `dev` |
| `{app-dir}` | pasta do app Expo, relativa à raiz | `apps/mobile` |
| `{properties-slug}` | `<slug-do-app>-<env>-android` | `meu-app-dev-android` |
| `{properties-file}` | `.github/apps/{properties-slug}.properties` | `.github/apps/meu-app-dev-android.properties` |
| `{github-environment}` | environment do GitHub do ambiente (o mesmo do iOS, se houver) | `meu-app-dev` |
| `{github-repo}` | `dono/repo` do `git remote get-url origin` | `empresa/meu-app` |
| `{default-branch}` | branch padrão | `main` |
| `{app-name}` | nome no ícone e no Play | `Meu App Dev` |
| `{android-package}` | pacote do app do ambiente | `com.empresa.app.dev` |
| `{play-account}` | conta Google dona da conta de desenvolvedor | `dono@empresa.com` |
| `{gcp-project}` | ID do projeto do Google Cloud da service account | `meu-projeto-123` |
| `{service-account-name}` | nome da service account | `play-publisher-meu-app` |
| `{service-account}` | e-mail da service account | `play-publisher-meu-app@meu-projeto-123.iam.gserviceaccount.com` |
| `{key-alias}` | alias da upload key (e nome do `.jks`) | `meu-app-dev-upload` |
| `{secrets-dir}` | pasta segura, fora de qualquer repositório | `~/empresa-segredos` |
| `{testers-list}` | lista de e-mails do teste interno | `Equipe` |
| `{node-cache}`, `{lockfile}`, `{install-dir}`, `{install-command}` | como na `analizza-expo-testflight` (lockfile subindo de `{app-dir}`) | `npm`, `package-lock.json`, `.`, `npm ci` |
| `{public-urls}` | lista Markdown, uma linha por `EXPO_PUBLIC_*` | `` - `EXPO_PUBLIC_API_URL`: https://… `` |

**Por que um `.properties` só do Android:** o `ios-identity.sh` da TestFlight
recusa chave desconhecida, de propósito. Cada plataforma tem o seu arquivo, e
os endereços `EXPO_PUBLIC_*` se repetem nos dois; mudar um endereço é mudar os
dois no mesmo PR.

## Fase 0 — ler, entrevistar, decidir o ambiente

1. **É Expo?** `app.json`/`app.config.*` com `expo` e o pacote `expo`. Num
   monorepo, pergunte qual app. Se não for Expo, pare.
2. **Pare** se `<app>/android` estiver versionada (`git ls-files <app>/android`
   não vazio) ou se existir `eas.json`: o `prebuild --clean` do workflow
   apagaria o código nativo.
3. **O que já existe.** `.github/workflows/mobile-android-play-*.yml`,
   `.github/apps/*.properties`, `docs/checkpoints/play-android-*.md`, specs. Uma
   fatia que já existe **não é reescrita**, mesmo em outro formato: aponte as
   diferenças e ofereça migração só com o ok da pessoa.
4. **Gerenciador de pacotes**, como na TestFlight. Sem lockfile versionado de
   npm, yarn ou pnpm, pare.
5. **Qual ambiente**: Dev, Prod ou os dois (sugira Dev). Os dois = duas fatias.
6. **Os dados.** Siga [references/dados-de-entrada.md](references/dados-de-entrada.md).
   Levante as `EXPO_PUBLIC_*` com o mesmo `grep` da TestFlight. Junte tudo o que
   falta numa pergunta só.

## Fase 1 — implementar no repositório

Numa branch nova (`feat/play-android-<env>`), gere:

| Molde | Destino | Como |
|---|---|---|
| [templates/github/scripts/android-identity.sh](templates/github/scripts/android-identity.sh) | `.github/scripts/android-identity.sh` | cópia, `chmod +x`; só se não existir |
| [templates/github/scripts/android-identity.test.sh](templates/github/scripts/android-identity.test.sh) | `.github/scripts/android-identity.test.sh` | cópia, `chmod +x`; só se não existir |
| [templates/github/workflows/mobile-android-play.yml.template](templates/github/workflows/mobile-android-play.yml.template) | `.github/workflows/mobile-android-play-{env}.yml` | blocos `dev` ou `prod` |
| (sem molde) | `{properties-file}` | `APP_NAME`, `ANDROID_PACKAGE`, `PLAY_TRACK=internal` e uma linha por `EXPO_PUBLIC_*` |
| [templates/app/plugins/android-display-name.js](templates/app/plugins/android-display-name.js) e [android-release-signing.js](templates/app/plugins/android-release-signing.js) | `{app-dir}/plugins/` | cópia; só se não existirem |
| [templates/app/app.config.ts.template](templates/app/app.config.ts.template) | `{app-dir}/app.config.ts` | ver abaixo |
| [templates/app/app-config-android-test.ts.template](templates/app/app-config-android-test.ts.template), [templates/app/__tests__/android-plugins-test.ts](templates/app/__tests__/android-plugins-test.ts) | `{app-dir}/__tests__/` | só se o app roda jest com `jest-expo` |
| [templates/app/__tests__/fixtures/app-build.gradle](templates/app/__tests__/fixtures/app-build.gradle) | `{app-dir}/__tests__/fixtures/` | substitua pelo trecho `signingConfigs`/`buildTypes` do `android/app/build.gradle` gerado por `npx expo prebuild --platform android --no-install` neste projeto |
| [templates/makefile/mobile-android-secrets.mk.template](templates/makefile/mobile-android-secrets.mk.template) | fim do `Makefile` | só se o alvo não existir |
| [templates/docs/play-android.md.template](templates/docs/play-android.md.template) | `docs/checkpoints/play-android-{env}.md` | `dev`/`prod` e um dos blocos de service account |

**`app.config.ts`:**
- não existe: copie o molde;
- existe (o da TestFlight, ou outro): **acrescente** o bloco `android` e os dois
  `plugins` ao objeto que ele já devolve, sem apagar nada; o `APP_DISPLAY_NAME`
  é o mesmo nome que o iOS usa;
- existe `app.config.js`: a mesma lógica, sem os tipos.

**Regras:**
- `name` e `scheme` do Expo não mudam.
- `<app>/android` precisa estar no `.gitignore`.
- Rode antes do commit: `bash .github/scripts/android-identity.test.sh`, o jest
  dos dois testes do app e o `tsc --noEmit`. Sem jest-expo no app, não copie os
  testes; diga no relatório que a `analizza-integration-test` configura.
- Confira a assinatura de verdade:
  `APP_DISPLAY_NAME="{app-name}" ANDROID_PACKAGE={android-package} npx expo prebuild --clean --platform android --no-install`
  e então `grep signingConfigs.release android/app/build.gradle` e
  `grep "{app-name}" android/app/src/main/res/values/strings.xml`.
- actionlint no workflow, se houver Docker.
- Runbook por funcionalidade (`CLAUDE.md`): o runbook gerado cumpre; a
  `test-runbook`, se existir, conduz a conferência.
- Commits pequenos. **Push e PR só com o ok da pessoa.**

**Build pelo cabo (opcional, antes da Fase 2):** se o projeto tem
`make mobile-android-device` (da `analizza-new-project`), use-o para provar o
Release no aparelho antes do Play. Ele precisa passar `--device <serial>` (sem
valor, o Expo abre um seletor que aborta fora de terminal interativo) e
`ORG_GRADLE_PROJECT_reactNativeArchitectures=<ABI do aparelho>` (o Expo compila
o Release para as quatro ABIs). JDK: Temurin 17 ou 21, **nunca GraalVM** (o
`jlink` dele quebra o `JdkImageTransform`). No aparelho, o **Play Protect** pode
perguntar se envia o app para análise: a pergunta é da pessoa, e a instalação
segue com qualquer resposta.

## Fase 2 — configurar Play Console e Google Cloud

Guia de telas, armadilhas dos campos e bloqueios:
[references/play-console.md](references/play-console.md). Leia antes de abrir o
navegador.

**Ferramenta, em ordem:** o navegador embutido (`mcp__Claude_Browser__*`); o
Claude in Chrome se a pessoa pedir; sem nenhum dos dois, entregue os passos da
Preparação única do runbook gerado, um bloco por vez.

**O painel fica visível.** Antes de pedir qualquer ação, confira que o painel
do navegador está à mostra.

**Cada passo começa olhando se já foi feito** (Retomada). Quem faz cada um:

1. **Login** no Play Console: *a pessoa*. Depois, a skill abre Usuários e
   permissões: se a lista aparece, o papel serve; anote as service accounts que
   já existem (não toque em nenhuma) e o tipo da conta (pessoal ou organização).
2. **Criar app**: a skill preenche nome e pacote, clica em "Ver
   disponibilidade" e escolhe App e Grátis. As **duas declarações** são aceites
   em nome da pessoa: ela marca, ou dá um ok explícito para a skill marcar.
   **Com o ok**, Criar app.
3. **Service account** (bloco `primeira-service-account`): a skill escolhe com a
   pessoa o projeto do Google Cloud (prefira um com a API já ativa) e, **com o
   ok**, cria a conta **sem papel** ("Criar e fechar"). Uma service account por
   produto: a de outro produto nunca é reaproveitada, mesmo que esteja ali.
4. **Chave JSON**: *a pessoa* baixa, ou dá o ok para a skill clicar em Criar. O
   arquivo cai nos Downloads; a skill o move pelo nome exato para
   `{secrets-dir}` com `chmod 600`, **sem abrir**.
5. **Convite**: a skill preenche e-mail, app e permissões (as duas de leitura
   que vêm marcadas + "Liberar apps para as faixas de teste") e confere o e-mail
   no campo antes; **com o ok**, Convidar e Enviar convite.
6. **Testers**: listas são da conta inteira. Se uma existente serve, mostre os
   e-mails e pergunte; senão, **com o ok**, crie. Salvar.

Um ok vale para **um** clique. Antes de cada Criar, Convidar, Enviar ou Salvar,
mostre o que vai ser enviado e espere a resposta.

## Fase 3 — segredos e GitHub

1. **Keystore**: *a pessoa* gera no terminal dela com o `keytool` do runbook (o
   comando pode ser aberto numa aba do terminal do app; o `keytool` não ecoa a
   senha). A skill confere só que o arquivo existe e aplica `chmod 600`.
2. **Secrets**: abra numa aba do terminal da pessoa
   `bash <esta skill>/scripts/gravar-secrets-android.sh {github-environment} <jks> {key-alias} <json> <raiz> [keytool]`.
   Ele lê a senha sem eco, **confere contra o keystore** e só então chama o
   `make mobile-android-secrets`. Depois, a skill confere **os nomes** com
   `gh secret list --env {github-environment}`, nunca os valores.
3. **Revisores obrigatórios**: confira
   `gh api repos/{github-repo}/environments/{github-environment} -q '[.protection_rules[].type]'`.
   Lista vazia: diga à pessoa, antes do primeiro disparo, que o environment
   guarda keystore e service account sem aprovação e peça que ligue Required
   reviewers. Não desligue proteção para "destravar" o job, e não mude
   configuração do repositório sem o ok.
4. **Merge do PR** pela pessoa. "Run workflow" e o gatilho de tag só existem
   com o workflow na branch padrão.

## Fase 4 — primeiro build e conferência

1. App novo fica em rascunho e a API só aceita `draft` nele. Dev: disparo com
   **status = draft**. Prod: `PLAY_FIRST_UPLOAD=true` como variável do environment
   antes da primeira tag. Depois do run: Teste interno → Versões → **Revisar e
   lançar** (pela pessoa ou com o ok dela). Recusa da API mesmo assim: o `.aab`
   está nos artefatos do run, para envio pela tela.
2. Acompanhe com `gh run watch` (o run espera a aprovação do environment).
3. Depois do lançamento, pegue o **link de participação** em Testadores e passe
   para a pessoa: no celular, logado numa conta da lista, abrir o link →
   Tornar-se testador → Baixar no Google Play.
4. Proponha a conferência pelo runbook `docs/checkpoints/play-android-{env}.md`
   (pela `test-runbook`, se o projeto tiver).

## Retomada

Antes de cada passo, olhe se já foi feito:

- App: está na lista "Todos os apps" com o pacote certo.
- Service account: aparece em Contas de serviço e em Usuários e permissões com
  acesso ao app; a chave já está em `{secrets-dir}`.
- Keystore: `{secrets-dir}/{key-alias}.jks` existe.
- GitHub: `gh secret list --env` mostra os cinco nomes.
- Testers: a lista está marcada no teste interno.

Nunca crie uma segunda cópia do que já existe.

## Segurança

- A skill nunca digita, gera nem lê senha, código de dois fatores, senha do
  keystore, conteúdo do `.jks` ou do JSON. Gerar a senha "para ajudar" também
  é proibido: quem gera vê.
- Arquivos secretos ficam fora de qualquer repositório
  (`git -C {secrets-dir} rev-parse --show-toplevel` precisa falhar).
- Nada existente no Play Console ou no Google Cloud é revogado, apagado ou
  rebaixado; service accounts de outros produtos não são tocadas.
- Service account sem papel IAM e só com "Liberar apps para as faixas de teste"
  no app do ambiente.
- O workflow passa `github.ref` e inputs por `env:`, nunca interpolados num
  `run:`; actions fixadas por SHA.
- Nenhum valor de cliente entra nesta skill; tudo vem da spec do projeto.

## Relatório final

- **Pronto:** arquivos, PR, o que foi criado no Play Console, no Google Cloud e
  no GitHub.
- **Pendente e com quem:** PR por mergear, revisores obrigatórios, primeiro
  lançamento em draft, tarefas do Painel, comerciante.
- **Diferenças das telas** em relação ao guia, para atualizar
  `references/play-console.md`.
- **Próxima fatia:** o outro ambiente; em conta pessoal, lembre o teste fechado
  de 12 testers por 14 dias antes da produção.
