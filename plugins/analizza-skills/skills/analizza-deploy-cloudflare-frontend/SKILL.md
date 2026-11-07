---
name: analizza-deploy-cloudflare-frontend
description: Leva o web Next.js a um ambiente no Cloudflare Workers, via OpenNext. Implementa no repositório o wrangler.jsonc (Worker, domínio próprio, variáveis), o open-next.config.ts e os scripts de preview e deploy; o pipeline de GitHub Actions (testes, deploy, CORS do bucket R2 quando o navegador sobe arquivos direto), disparado só à mão de qualquer branch, com "gerar_tag" na branch padrão; a versão única do produto com a tag v<versão> compartilhada entre os deploys; e o runbook. Depois conduz a preparação no painel do Cloudflare e no GitHub e o primeiro deploy. Use quando pedirem "deploy do web no Cloudflare", "Next.js no Cloudflare Workers", "OpenNext", "publicar o frontend no Cloudflare", "pipeline do web" ou invocarem /analizza-deploy-cloudflare-frontend.
---

# analizza-deploy-cloudflare-frontend

Monta, num web **Next.js**, o deploy de um ambiente (normalmente `dev`) como
**Cloudflare Worker**, via **OpenNext**:

- **Disparo só manual** (Run workflow), de qualquer branch. Push nenhum publica.
- **gerar_tag**, só na branch padrão: depois do deploy, um job separado (o único
  com permissão de escrita) cria `v<versão>`. A tag só marca o commit.
- **Versão única do produto:** o `package.json` do web e, se o produto tiver, o
  `gradle.properties` do backend e o `app.json` dos apps carregam a mesma
  `X.Y.Z` (lista em `.github/versao.fontes`). `make version V=X.Y.Z` grava em
  todas; todo deploy recusa versões divergentes. A tag `v<versão>` é a mesma para
  web, backend e apps: o primeiro deploy que a cria vence, os outros no mesmo
  commit a acham pronta.
- **Domínio próprio** pelo `custom_domain` do Worker (o deploy cria o DNS e o
  certificado) e **CORS do bucket R2** versionado e aplicado pelo próprio
  workflow, quando o navegador sobe arquivos direto ao R2. Detalhes:
  [references/cloudflare.md](references/cloudflare.md).

A pessoa assiste. Ela grava os segredos pelo terminal dela e aprova cada passo
que muda algo fora do repositório. A skill **nunca** lê nem digita token,
Access Key ou valor de secret.

**Não faz:** Cloudflare Pages, sites estáticos sem Next.js, Vite/Remix/Astro,
ambiente de produção com promoção por tag (só o ambiente disparado à mão),
`wrangler secret` (registra no relatório), cache incremental (R2/KV), CI fora do
GitHub Actions. O backend na VPS é a `analizza-deploy-vps-backend`; os apps
móveis, a `analizza-expo-testflight` e a `analizza-expo-play`.

## Vocabulário dos moldes

Marcadores `{nome}` e blocos em linhas próprias: `# se <bloco>` … `# fim se <bloco>`
(YAML), `// se <bloco>` … `// fim se <bloco>` (JSON, JSONC) e
`<!-- se <bloco> -->` … `<!-- fim se <bloco> -->` (Markdown). Mantenha só os
blocos que valem, remova as linhas de abertura e fechamento e troque todos os
marcadores. Blocos `por …` se **repetem**, um por item; em JSON, o último item
fica sem vírgula (e `"vars": {}` quando não há variável). Nenhum marcador pode
sobrar (confira com `grep -nE '\{[a-z][a-z0-9-]*\}|\{Env\}' <arquivo>`), e o JSON
gerado precisa ser válido (`node -e 'JSON.parse(require("fs").readFileSync(0))' < deploy/r2-cors.json`).

**Blocos:**
- `dominio`: o web responde num domínio próprio da zona do Cloudflare.
- `r2-cors`: o navegador sobe ou lê arquivos direto de um bucket R2.
- `pnpm`: o projeto usa pnpm.
- `por verificacao`: uma vez por script de verificação (`lint`, `typecheck`, `test`).
- `por variavel`: uma vez por variável pública do Worker.
- `por origem`: uma vez por origem permitida no CORS.

| Marcador | Valor | Exemplo |
|---|---|---|
| `{env}` / `{Env}` | ambiente, minúsculo / com inicial maiúscula | `dev` / `Dev` |
| `{default-branch}` | branch padrão | `main` |
| `{github-repo}` | `dono/repo` do `origin` | `empresa/meu-app` |
| `{github-environment}` | environment do GitHub | `development` |
| `{web-dir}` | pasta do web, relativa à raiz | `meu-app-web` |
| `{node-version}` | versão do Node | `22` |
| `{node-cache}` | `npm`, `yarn` ou `pnpm` | `npm` |
| `{lockfile}` | lockfile, relativo à raiz | `meu-app-web/package-lock.json` |
| `{install-dir}` | pasta onde a instalação roda: a do lockfile | `meu-app-web` |
| `{install-command}` | `npm ci`, `yarn install --frozen-lockfile` ou `pnpm install --frozen-lockfile` | `npm ci` |
| `{check-command}` | um script de verificação | `npm test` |
| `{deploy-command}` | `npm run deploy`, `yarn deploy` ou `pnpm run deploy` | `npm run deploy` |
| `{preview-command}` | `npm run preview` (ou equivalente) | `npm run preview` |
| `{worker-name}` | nome do Worker | `meu-app-web-dev` |
| `{compatibility-date}` | a data de hoje, `AAAA-MM-DD` | `2026-11-07` |
| `{web-host}` / `{web-url}` | host e URL pública do web (sem `dominio`: a URL `*.workers.dev`) | `app.dev.exemplo.com` |
| `{zone}` | zona do Cloudflare | `exemplo.com` |
| `{var}` / `{value}` | variável pública e o valor em `{env}` | `API_URL` / `https://api.dev.exemplo.com` |
| `{r2-bucket}` | bucket R2 | `meu-app-bucket-dev` |
| `{r2-cors-file}` | arquivo do CORS, relativo à raiz | `deploy/r2-cors.json` |
| `{r2-cors-path}` | o mesmo, relativo a `{web-dir}` (o passo roda lá) | `../deploy/r2-cors.json` |
| `{origin}` | origem permitida no CORS | `https://app.dev.exemplo.com` |

## Fase 0 — ler e entrevistar

1. **É Next.js?** `next` no `package.json` do web. Sem Next.js, pare e diga por
   quê. Com `output: 'export'` (site estático), avise que o Worker funciona, mas
   que Pages seria mais simples, e pergunte se segue.
2. **O que já existe.** `wrangler.jsonc`/`wrangler.toml`, `open-next.config.ts`,
   `.github/workflows/web-deploy*.yml`, `deploy/r2-cors.json`,
   `.github/scripts/version.sh`, `.github/versao.fontes`,
   `docs/checkpoints/deploy-web-*.md`. Um deploy que já existe **não é
   reescrito**: aponte as diferenças e ofereça a migração como passo separado,
   só com o ok da pessoa.
3. **Os dados.** Siga [references/dados-de-entrada.md](references/dados-de-entrada.md):
   tudo o que falta numa pergunta só. Grave a spec descrita lá.

## Fase 1 — implementar no repositório

Numa branch nova (`feat/deploy-web-<env>`):

| Molde | Destino | Como |
|---|---|---|
| [templates/github/scripts/version.sh](templates/github/scripts/version.sh) e `version.test.sh` | `.github/scripts/` | cópia, `chmod +x`; só se não existir |
| [templates/github/scripts/release-tag.sh](templates/github/scripts/release-tag.sh) e `release-tag.test.sh` | `.github/scripts/` | cópia, `chmod +x`; só se não existir |
| (sem molde) | `.github/versao.fontes` | um caminho por linha: `{web-dir}/package.json` e as outras fontes combinadas; se já existir, acrescente o que falta |
| (sem molde) | `{web-dir}/package.json` | `version` com a versão combinada (a das outras fontes, se houver; senão `1.0.0`); scripts `preview` e `deploy` (ver a referência); devDependencies `@opennextjs/cloudflare` e `wrangler` instaladas pelo gerenciador do projeto |
| [templates/web/wrangler.jsonc.template](templates/web/wrangler.jsonc.template) | `{web-dir}/wrangler.jsonc` | blocos `dominio`, `por variavel` |
| [templates/web/open-next.config.ts](templates/web/open-next.config.ts) | `{web-dir}/open-next.config.ts` | cópia; só se não existir |
| (sem molde) | `{web-dir}/.gitignore` | `.open-next/`, `.wrangler/`, `.dev.vars` |
| [templates/deploy/r2-cors.json.template](templates/deploy/r2-cors.json.template) | `{r2-cors-file}` | só com `r2-cors`; bloco `por origem` (o domínio, o `*.workers.dev` e o `http://localhost:<porta>` do dev local) |
| [templates/github/workflows/web-deploy.yml.template](templates/github/workflows/web-deploy.yml.template) | `.github/workflows/web-deploy-{env}.yml` | blocos `r2-cors`, `pnpm`, `por verificacao` |
| [templates/makefile/deploy-web.mk.template](templates/makefile/deploy-web.mk.template) | fim do `Makefile` da raiz | só se o alvo `version` não existir; cria o `Makefile` se não houver |
| [templates/docs/deploy-web.md.template](templates/docs/deploy-web.md.template) | `docs/checkpoints/deploy-web-{env}.md` | blocos como acima |

**Regras:**
- Rode antes do commit: `bash .github/scripts/version.test.sh`,
  `bash .github/scripts/release-tag.test.sh`, `make version`, as verificações do
  web e o build do OpenNext (`npx opennextjs-cloudflare build` em `{web-dir}`),
  que pega cedo uma API do Node que o Worker não tem. Rode o actionlint no
  workflow se houver Docker
  (`docker run --rm -v "$PWD:/repo" --workdir /repo rhysd/actionlint:latest`).
- O runbook gerado cumpre a regra de runbook por funcionalidade, se o projeto
  tiver; a `test-runbook` conduz a conferência.
- Commits pequenos. **Push e PR só com o ok da pessoa.**

## Fase 2 — Cloudflare e GitHub

Siga a seção **Preparação, uma vez** do runbook gerado, um bloco por vez, e espere
a confirmação de cada um.

**Ferramenta, em ordem:** o navegador embutido do app Claude
(`mcp__Claude_Browser__*`); o Claude in Chrome se a pessoa pedir; sem nenhum dos
dois, entregue os passos e espere a confirmação de cada um. O painel do navegador
fica visível.

1. **Login** em dash.cloudflare.com — *a pessoa* entra no painel.
2. **Token de API** — a skill navega até Criar token e preenche as permissões do
   runbook; **com o ok**, clica em Criar. *A pessoa* copia o token direto para o
   `gh secret set` no terminal dela: a skill não lê o valor da tela.
3. **Account ID** — a skill lê da tela (não é segredo) e mostra à pessoa.
4. **DNS** (bloco `dominio`) — a skill confere que **não** existe registro com o
   nome do web; se existir, pare e pergunte (apagar é decisão da pessoa).
5. **Secrets** — entregue o laço `gh secret set` do runbook; **a pessoa roda no
   terminal dela**.

## Fase 3 — primeiro deploy e conferência

1. Merge do PR pela pessoa: o botão "Run workflow" só aparece com o workflow na
   branch padrão.
2. Peça o disparo (ou rode `gh workflow run`, com o ok) e acompanhe com
   `gh run watch`.
3. Proponha a conferência do runbook `docs/checkpoints/deploy-web-{env}.md`
   (pela `test-runbook`, se o projeto tiver): ela tem tela, então vale o
   navegador embutido.

## Retomada

- Token: já existe um token com o nome combinado na lista de tokens.
- Domínio: `dig +short {web-host}` já responde depois do primeiro deploy.
- GitHub: `gh secret list --env {github-environment}` mostra
  `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ACCOUNT_ID` (só nomes).

Nunca crie uma segunda cópia do que já existe.

## Segurança

- A skill nunca digita nem lê token, Access Key ou valor de secret.
- O workflow passa `github.ref`, `inputs` e secrets por `env:`, nunca
  interpolados num `run:`.
- As actions ficam fixadas por SHA.
- Nada existente no Cloudflare (Worker, DNS, bucket, token) é apagado ou
  rebaixado.
- Nenhum valor de cliente (conta, domínio) entra nesta skill; tudo vem da spec do
  projeto.

## Relatório final

Em poucas linhas:
- **Pronto:** arquivos gerados, testes e build do OpenNext, PR, o que foi feito
  no Cloudflare e no GitHub.
- **Pendente e com quem:** token, secrets, merge, primeiro disparo.
- **Débitos:** segredo do servidor que ficou sem `wrangler secret`, rota que usa
  API do Node fora do `nodejs_compat`.
- **Próximo:** o backend (`analizza-deploy-vps-backend`), se o produto tiver API
  na VPS.
