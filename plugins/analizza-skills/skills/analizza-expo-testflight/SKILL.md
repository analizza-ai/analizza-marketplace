---
name: analizza-expo-testflight
description: Leva um app Expo ao TestFlight por ambiente. Implementa no repositório o pipeline iOS (GitHub Actions, identidade do app, app.config.ts, credenciais por environment, runbook) para Dev, disparado à mão de qualquer branch, e para Prod, disparado por tag; depois conduz a configuração na Apple Developer e no App Store Connect pelo navegador embutido, com a pessoa assistindo, fazendo login e aprovando cada passo sem volta. Use quando pedirem "pipeline iOS", "TestFlight", "publicar o app Expo no iPhone sem cabo", "configurar o App Store Connect", "app de produção iOS", "deploy iOS por tag" ou invocarem /analizza-expo-testflight.
---

# analizza-expo-testflight

Monta, num projeto **Expo**, o caminho até o TestFlight de um ambiente por vez:

- **Dev:** um app próprio na Apple (ex.: "Meu App Dev"), apontando para o
  backend de desenvolvimento, disparado à mão de qualquer branch, a padrão
  inclusive. Só na branch padrão dá para marcar **gerar_tag**, que cria
  `v<versão>` no commit depois do upload (a tag só marca o commit).
- **Prod:** outro app (ex.: "Meu App"), apontando para produção, disparado por
  push da tag `v<versão>` num commit da branch padrão, ou à mão nessa tag (a
  criada pelo **gerar_tag** do Dev não dispara sozinha). Do TestFlight, a
  promoção para a App Store é manual.

Cada ambiente é uma **fatia completa**: código no repositório, Apple
configurada, credenciais no GitHub, primeiro build no TestFlight e conferência
pelo runbook. Normalmente se começa por Dev; ir direto para Prod é permitido.

A pessoa assiste a tudo. Ela faz login, decide e cuida dos segredos. A skill
preenche o que a spec já define e **nunca** digita senha, código de dois
fatores ou conteúdo de chave.

**Não faz:** Flutter, Swift nativo, React Native sem Expo, Android, publicação
na App Store, push notifications e outras capabilities, CI fora do GitHub
Actions, e projetos Expo com `ios/` versionada (bare) ou com build pelo EAS.

## Vocabulário dos moldes

Os moldes em `templates/` usam marcadores `{nome}` e blocos condicionais em
linhas próprias: `# se <bloco>` … `# fim se <bloco>` no YAML e
`<!-- se <bloco> -->` … `<!-- fim se <bloco> -->` no Markdown. Mantenha só os
blocos que valem, remova as linhas de abertura e fechamento, e troque todos os
marcadores. Nenhum marcador pode sobrar no arquivo gerado.

**Blocos:**
- `dev` ou `prod`: o ambiente da fatia (exatamente um).
- `primeiro-do-time` ou `reaproveita` (exatamente um, só no runbook): a chave da
  API e o certificado serão criados nesta fatia, ou já existem no time e são
  reaproveitados. Ir direto para Prod num time sem chave é `prod` +
  `primeiro-do-time`; Dev depois de Prod é `dev` + `reaproveita`.
- `pnpm`: só quando o projeto usa pnpm (acrescenta o `pnpm/action-setup`).

| Marcador | Valor | Exemplo |
|---|---|---|
| `{env}` | `dev` ou `prod` | `dev` |
| `{app-dir}` | pasta do app Expo, relativa à raiz do repositório | `apps/mobile` |
| `{properties-file}` | `.github/apps/<slug-do-app>-<env>.properties` | `.github/apps/meu-app-dev.properties` |
| `{github-environment}` | environment do GitHub do ambiente | `meu-app-dev` |
| `{github-repo}` | `dono/repo` do `git remote get-url origin` | `empresa/meu-app` |
| `{default-branch}` | branch padrão (`git symbolic-ref refs/remotes/origin/HEAD`) | `main` |
| `{xcode-workspace}` | nome do workspace que o `expo prebuild` gera: o `name` do `app.json` sem espaços, hífens nem acentos, mantendo maiúsculas e minúsculas | `meuappmobile` (de `meu-app-mobile`) |
| `{xcode-scheme}` | o mesmo que `{xcode-workspace}` | `meuappmobile` |
| `{app-name}` | nome no ícone e na App Store | `Meu App Dev` |
| `{bundle-id}` | bundle do app do ambiente | `com.empresa.app.dev` |
| `{team-id}` | Team ID da Apple | `ABCDE12345` |
| `{sku}` | SKU no App Store Connect | `meu-app-dev` |
| `{testers-group}` | grupo de testes interno | `Equipe` |
| `{node-cache}` | gerenciador de pacotes: `npm`, `yarn` ou `pnpm` | `yarn` |
| `{lockfile}` | lockfile, relativo à raiz (num monorepo com workspaces, o da raiz) | `yarn.lock` |
| `{install-dir}` | pasta onde a instalação roda: a do lockfile | `.` |
| `{install-command}` | `npm ci`, `yarn install --frozen-lockfile` ou `pnpm install --frozen-lockfile` | `yarn install --frozen-lockfile` |
| `{public-urls}` | lista Markdown, uma linha por `EXPO_PUBLIC_*`: `` - `NOME`: valor `` | `` - `EXPO_PUBLIC_API_URL`: https://… `` |

Confira `{xcode-workspace}` depois do primeiro `npx expo prebuild --platform ios`
local, se puder: é o nome do `.xcworkspace` dentro de `ios/`.

## Fase 0 — ler, entrevistar, decidir o ambiente

1. **É Expo?** Procure `app.json` ou `app.config.*` com `expo` e o pacote `expo`
   no `package.json`. Num monorepo com mais de um app, pergunte qual. Se não for
   Expo, pare e diga por quê.
2. **Pare** se a pasta `ios/` do app estiver versionada (`git ls-files <app>/ios`
   não vazio) ou se existir `eas.json`: o `expo prebuild --clean` do workflow
   apagaria o código nativo, e o EAS já é outro caminho de build. Explique e não
   gere nada.
3. **O que já existe.** Specs em `docs/superpowers/specs/`, `.github/apps/*.properties`,
   `.github/workflows/mobile-ios-testflight-*.yml` e
   `docs/checkpoints/testflight-ios-*.md`. Uma fatia que já existe é reconhecida
   pelo workflow e pelo `.properties` que ele lê, e **não é reescrita**, mesmo que
   esteja num formato diferente do destes moldes. Aponte as diferenças no
   relatório e ofereça a migração como passo separado, só com o ok da pessoa.
4. **Gerenciador de pacotes.** Procure o lockfile subindo de `<app-dir>` até a
   raiz: `package-lock.json` (npm), `yarn.lock` (yarn) ou `pnpm-lock.yaml`
   (pnpm). O primeiro achado define `{node-cache}`, `{lockfile}`,
   `{install-dir}` e `{install-command}`. Sem lockfile, ou com outro gerenciador
   (bun), pare e diga que o workflow precisa de um lockfile versionado de npm,
   yarn ou pnpm.
5. **Qual ambiente.** Pergunte: Dev, Prod ou os dois (sugira Dev, ou o que
   falta). Os dois = duas fatias, uma depois da outra.
6. **Os dados.** Siga [references/dados-de-entrada.md](references/dados-de-entrada.md).
   Levante as variáveis públicas que o app lê:

   ```bash
   grep -rhoE 'process\.env\.EXPO_PUBLIC_[A-Z0-9_]+' <app-dir> \
     --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' \
     --exclude-dir=node_modules | sort -u
   ```

   Junte tudo o que falta numa pergunta só. Se faltar a spec, faça a entrevista e
   grave a spec descrita no mesmo arquivo de referência.

## Fase 1 — implementar no repositório

Numa branch nova (`feat/testflight-ios-<env>`), gere:

| Molde | Destino | Como |
|---|---|---|
| [templates/github/scripts/ios-identity.sh](templates/github/scripts/ios-identity.sh) | `.github/scripts/ios-identity.sh` | cópia, `chmod +x`; só se não existir |
| [templates/github/scripts/ios-identity.test.sh](templates/github/scripts/ios-identity.test.sh) | `.github/scripts/ios-identity.test.sh` | cópia, `chmod +x`; só se não existir |
| [templates/github/workflows/mobile-ios-testflight.yml.template](templates/github/workflows/mobile-ios-testflight.yml.template) | `.github/workflows/mobile-ios-testflight-{env}.yml` | blocos `dev` ou `prod` |
| (sem molde) | `{properties-file}` | `APP_NAME`, `IOS_BUNDLE_ID`, `APPLE_TEAM_ID` e uma linha por `EXPO_PUBLIC_*`, valores entre aspas quando têm espaço |
| [templates/app/app.config.ts.template](templates/app/app.config.ts.template) | `{app-dir}/app.config.ts` | ver abaixo |
| [templates/app/app-config-test.ts.template](templates/app/app-config-test.ts.template) | `{app-dir}/__tests__/app-config-test.ts` | cópia, só se o app já roda jest com `jest-expo` |
| [templates/makefile/mobile-ios-secrets.mk.template](templates/makefile/mobile-ios-secrets.mk.template) | fim do `Makefile` da raiz | só se o alvo `mobile-ios-secrets` não existir; cria o `Makefile` se não houver |
| [templates/docs/testflight-ios.md.template](templates/docs/testflight-ios.md.template) | `docs/checkpoints/testflight-ios-{env}.md` | `dev` ou `prod`, mais `primeiro-do-time` ou `reaproveita` |

**`app.config.ts`:**
- não existe: copie o molde;
- existe e só estende o `appleTeamId` (o gerado pela `analizza-new-project`):
  troque pelo molde;
- existe com outra lógica: acrescente a leitura do ambiente (os quatro campos e o
  `ITSAppUsesNonExemptEncryption: false`) ao que já está lá, sem apagar nada;
- existe `app.config.js`: aplique a mesma lógica em JavaScript, sem os tipos.

**Regras:**
- O `name` e o `scheme` do Expo não mudam: o name gera o projeto do Xcode e o
  scheme costuma estar no retorno de login. Só o nome exibido muda.
- A pasta `ios/` do app precisa estar no `.gitignore`.
- Rode os testes antes do commit: `bash .github/scripts/ios-identity.test.sh` e o
  jest do app (`npx jest __tests__/app-config-test.ts`). Sem jest configurado no
  app (sem `jest-expo` no `package.json`), não copie o teste nem instale nada:
  diga no relatório que o `app.config.ts` ficou sem teste e que a
  `analizza-integration-test` configura o jest-expo. Rode o actionlint no
  workflow se houver Docker
  (`docker run --rm -v "$PWD:/repo" --workdir /repo rhysd/actionlint:latest`).
- Se o projeto exige runbook por funcionalidade (`CLAUDE.md`, convenções),
  o runbook gerado cumpre isso; se existir a skill `test-runbook`, ela conduz a
  conferência.
- Commits pequenos. **Push e PR só com o ok da pessoa.**

## Fase 2 — configurar a Apple

Guia de telas, rótulos nos dois idiomas e bloqueios conhecidos:
[references/apple-console.md](references/apple-console.md). Leia antes de abrir
o navegador.

**Ferramenta, em ordem:** o navegador embutido do app Claude
(`mcp__Claude_Browser__*`); o Claude in Chrome se a pessoa pedir; sem nenhum
dos dois (Codex, Antigravity, terminal), entregue os passos da Preparação única
do runbook gerado, um bloco por vez, e espere a confirmação de cada um.

**O painel fica visível.** Antes de pedir qualquer ação à pessoa, confira que o
painel do navegador está à mostra; se estiver oculto, peça para trazê-lo
(Cmd+Shift+B no Mac).

**Cada passo começa olhando se já foi feito** (veja Retomada). Quem faz cada um:

1. **Login** em developer.apple.com — *a pessoa* digita usuário, senha e o código
   de dois fatores no painel. A skill espera o "pronto" e confere o Team ID no
   canto da tela; se não bater com `{team-id}`, pare.
2. **Contrato** — se o App Store Connect mostrar o banner de contrato atualizado,
   pare: só o titular da conta aceita, em developer.apple.com/account.
3. **App ID** — a skill preenche; mostra o resumo; **com o ok da pessoa**, clica
   em Register.
4. **Termos do App Store Connect** — *a pessoa* marca e clica em Concordar.
5. **Novo app** — a skill preenche; **com o ok**, clica em Criar. Nome tomado:
   pergunte uma variação.
6. **Chave da API** (bloco `primeiro-do-time`) — a skill navega e preenche o
   nome; *a pessoa* clica em Solicitar acesso, confirma o nível de acesso
   (padrão Administrador), clica em Gerar e em **Baixar**, salvando o `.p8` na
   pasta segura. A skill lê da tela só o Key ID e o Issuer ID.
7. **Certificado** (bloco `primeiro-do-time`) — a skill conta os certificados de
   distribuição; **limite cheio: pare, sem revogar nada**. Com vaga, a skill gera
   a chave e o CSR com `openssl` na pasta segura (sem imprimir a chave); *a
   pessoa* envia o CSR no seletor de arquivos, baixa o `.cer` e gera o `.p12` no
   próprio terminal com o comando do runbook, digitando a senha.
8. **Grupo e testers** — a skill avisa que a distribuição automática não muda
   depois e, **com o ok**, cria o grupo. Quem ainda não é usuário do App Store
   Connect: **com o ok para cada convite**, a skill cria o usuário; o convidado
   aceita por e-mail (fica pendente, a skill segue). Quem já aceitou entra no
   grupo.

**No segundo ambiente do mesmo time, pule** os passos 6 e 7: a chave e o
certificado valem para o time inteiro. Reaproveite os mesmos arquivos `.p8` e
`.p12` da pasta segura e não gere outra chave nem outro certificado.

Um ok vale para **um** clique. Antes de cada Register, Criar, Gerar, Concordar
ou convite, mostre o que vai ser enviado e espere a resposta.

## Fase 3 — GitHub

1. **Credenciais.** Entregue o bloco de `export` do runbook com os caminhos da
   pasta segura e `make mobile-ios-secrets ENV={github-environment}`. **A
   pessoa roda no terminal dela**; a skill não vê os valores. Em Prod ou no
   segundo ambiente, os mesmos arquivos vão para o outro environment.
2. **Aprovação obrigatória** no environment (Settings → Environments →
   Required reviewers). Mudança de configuração do repositório: só com o ok da
   pessoa, pelo navegador ou com `gh api` que você mostra antes.
3. **Merge do PR** pela pessoa. Em Dev, o botão "Run workflow" só aparece com o
   workflow na branch padrão.

## Fase 4 — primeiro build e conferência

1. Dev: peça o disparo em Actions → Mobile iOS TestFlight Dev. Prod: peça a tag
   `v<version do app.json>` num commit da branch padrão (push da tag), ou o
   Dev na branch padrão com **gerar_tag** e depois Run workflow do Prod na tag.
2. Acompanhe com `gh run watch` (o run espera a aprovação do environment).
3. Proponha a conferência do runbook `docs/checkpoints/testflight-ios-{env}.md`
   (pela `test-runbook`, se o projeto tiver).

## Retomada

Antes de cada passo, olhe se ele já foi feito e pule o que estiver pronto:

- App ID: o bundle já aparece em Identifiers.
- App: já está na lista de Apps do App Store Connect.
- Chave: já existe chave ativa do CI, ou o acesso à API está esperando
  aprovação.
- Certificado: a pessoa já tem o `.p12` na pasta segura.
- Grupo: já existe; tester: já está no grupo ou com convite pendente.
- GitHub: o environment já existe; `gh secret list --env <environment>` mostra
  os cinco nomes (só nomes, nunca valores).

Nunca crie uma segunda cópia do que já existe.

## Segurança

- A skill nunca digita nem lê senha, código de dois fatores, conteúdo de `.p8`,
  `.p12` ou chave privada.
- Arquivos secretos ficam numa pasta **fora do repositório**, escolhida pela
  pessoa. Confira com `git -C <pasta> rev-parse --show-toplevel` que ela não
  pertence a nenhum repositório; o `.gitignore` não é proteção suficiente.
- Nada existente na Apple é revogado, apagado ou rebaixado.
- O workflow passa `github.ref` e outros valores por `env:`, nunca interpolados
  num `run:`.
- Nenhum valor de cliente (empresa, time, URL) entra nesta skill; tudo vem da
  spec do projeto.

## Relatório final

Em poucas linhas:
- **Pronto:** arquivos gerados, PR, o que foi criado na Apple e no GitHub.
- **Pendente e com quem:** convite não aceito, contrato por aceitar, PR por
  mergear, aprovação do environment, primeiro disparo.
- **Diferenças da Apple** em relação ao guia de telas, para atualizar
  `references/apple-console.md`.
- **Próxima fatia:** o outro ambiente, se ainda não existe.
