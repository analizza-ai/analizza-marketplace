# Cloudflare: o que o molde assume

## OpenNext

- `@opennextjs/cloudflare` e `wrangler` como devDependencies do web; os scripts
  `preview` (`opennextjs-cloudflare build && opennextjs-cloudflare preview`) e
  `deploy` (`opennextjs-cloudflare build && opennextjs-cloudflare deploy`) no
  `package.json`.
- `.open-next/`, `.wrangler/` e `.dev.vars` no `.gitignore` do web.
- O Worker precisa de `nodejs_compat` e de uma `compatibility_date` recente (use a
  data do dia da geração).
- O `next build` do OpenNext roda no CI dentro do `deploy`; os testes e o
  typecheck rodam antes, em passos próprios, para falhar cedo.
- Se o `next.config` já chama `initOpenNextCloudflareForDev()`, mantenha; não é
  obrigatório.

## Variáveis

- `vars` do `wrangler.jsonc` são **públicas** (ficam no repositório): URLs,
  nomes, flags. Segredo do servidor vai por `wrangler secret put`, fora deste
  molde; registre no relatório se houver.
- Localmente, o `preview` lê o `.dev.vars` (não versionado) no lugar de `vars`.

## Domínio próprio

Com `"custom_domain": true`, o deploy cria o registro DNS e o certificado sozinho.
Um registro manual com o mesmo nome faz o deploy falhar: a preparação pede para
**não** criá-lo. O token precisa de Workers Routes: Edit e DNS: Edit na zona.

## CORS do R2

Só quando o navegador envia (ou lê) arquivos direto do bucket, com URL
pré-assinada. O arquivo versionado é a fonte da verdade, aplicado pelo próprio
workflow a cada deploy; nunca à mão no painel ou com `wrangler` local, senão o
próximo deploy desfaz. `ETag` exposto é obrigatório para o upload multipart
fechar; `PUT`, `GET` e `HEAD` para subir e tocar.
