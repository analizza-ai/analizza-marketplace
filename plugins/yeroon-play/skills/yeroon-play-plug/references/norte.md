# O norte — o que falta para produção

Entregue ao final, com os marcadores preenchidos para este projeto. Marcadores:

| Marcador | Preencher com |
|---|---|
| `{front-origin}` | A origem de dev do front (`http://localhost:{porta}`) e, no item 2, a origem de produção que a pessoa informar |
| `{back-public-url}` | A URL pública do back publicado (base do `webhookUrl`); se ainda não existe, escrever "a definir" |

## Checklist

1. **Conta real, não de teste.** A conta de teste guarda no máximo 3 vídeos de até 1 GB. Para produção, pedir uma conta ao administrador do yeroon.
2. **`allowedOrigins` no yeroon** com o domínio de produção do front: `{front-origin}`. O signup aceitou uma origem só e não há rota para trocar; é pedido ao administrador do yeroon (`/admin/tenants`). Sem isso o player (`embedUrl`) não abre em produção.
3. **CORS do R2 do yeroon.** O upload do navegador vai direto ao R2, que hoje só libera `https://play.dev.yeroon.video`, o worker do yeroon e `http://localhost:3000`. Uma origem nova (`{front-origin}` de produção, ou o front de dev fora da 3000) precisa entrar lá: pedido ao time do yeroon. Apps Expo e Flutter não dependem disso.
4. **`webhookUrl`** apontando para `{back-public-url}/webhooks/yeroon`. Também não há rota para trocar; é pedido ao administrador. Em dev, opcional via `cloudflared tunnel --url http://localhost:{porta-do-back}`.
5. **`YEROON_API_KEY`, `YEROON_WEBHOOK_SECRET` e `YEROON_API_URL` como secrets do ambiente de deploy**, nunca no repositório. Em produção, `YEROON_API_URL` aponta para a API de produção do yeroon, não para a de dev.
6. **Conferir que a chave não vazou:** `yk_` não pode aparecer nos bundles do front (`grep -r "yk_" .next/ out/ dist/`), no app, em log nem no git (`git log -p -S"yk_" | head`). Se aparecer, revogar e pedir nova chave.
7. **Webhook em produção:** conferir que o segredo está configurado (sem ele o back recusa tudo) e que o relógio do servidor está sincronizado (janela de 5 min).
8. **Dedupe e retentativas:** a tabela `webhook_receipt` cresce; definir limpeza dos registros antigos se o volume importar.
