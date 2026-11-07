# Dados de entrada

Procure primeiro no projeto: o `package.json` do web (Next.js, scripts,
`@opennextjs/cloudflare`, `wrangler`), `next.config.*`, um `wrangler.jsonc` ou
`wrangler.toml` existente, o lockfile, `.env*` (nomes das variáveis, nunca os
valores), `process.env.<NOME>` no código e `.github/workflows/`. O que faltar vira
**uma pergunta só**, no começo, com todos os itens juntos.

Nunca peça nem aceite na conversa: token do Cloudflare, Access Key do R2 ou
qualquer valor de secret.

## Do projeto

| Dado | Como obter | Marcador |
|---|---|---|
| Pasta do web | o app com `next` no `package.json`; num monorepo com mais de um, pergunte | `{web-dir}` |
| Gerenciador | lockfile, subindo de `{web-dir}` até a raiz: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | `{node-cache}`, `{lockfile}`, `{install-dir}`, `{install-command}`, bloco `pnpm` |
| Versão do Node | `engines.node`, `.nvmrc`; senão `22` | `{node-version}` |
| Verificações | os scripts que existem entre `lint`, `typecheck`, `test` | `{check-command}` (uma por bloco) |
| Variáveis do servidor | `process.env.<NOME>` lidas no servidor (route handlers, server components) | `{var}` / `{value}` |
| Upload direto ao R2 | o web envia arquivos com URL pré-assinada ao R2? → bloco `r2-cors` | `r2-cors` |
| Repositório e branch padrão | `git remote get-url origin`, `git symbolic-ref refs/remotes/origin/HEAD` | `{github-repo}`, `{default-branch}` |
| Fontes de versão | o `package.json` do web; mais `gradle.properties` e `app.json` se o produto versiona junto (pergunte) | `.github/versao.fontes` |

## Do ambiente

| Dado | Pergunta | Exemplo |
|---|---|---|
| Ambiente | "Qual ambiente montar agora?" (sugira `dev`) | `dev` |
| Nome do Worker | sugira `<projeto>-web-<env>` | `meu-app-web-dev` |
| Domínio próprio | "O web responde num domínio seu? Qual?" A zona precisa estar na mesma conta Cloudflare → bloco `dominio` | `app.dev.exemplo.com` |
| Zona | o domínio registrado da zona no Cloudflare | `exemplo.com` |
| Valores das variáveis | para cada `{var}`: o valor em `{env}` (só não secretos; segredo vira `wrangler secret`, fora deste molde) | `API_URL=https://api.dev.exemplo.com` |
| Bucket e origens do CORS | nome do bucket R2 e as origens que sobem arquivos | `meu-app-bucket-dev` |
| Environment do GitHub | o mesmo do backend, se houver; senão sugira `<env>` | `development` |

## A spec que a skill grava

Quando os dados vieram da entrevista, grave
`docs/superpowers/specs/AAAA-MM-DD-deploy-web-<env>-design.md` com: a pasta do
web, o Worker, o domínio, as variáveis (nomes e valores não secretos), o bucket e
as origens do CORS, o environment do GitHub com os **nomes** dos secrets e as
fontes de versão. Nenhum segredo entra nesse arquivo.
