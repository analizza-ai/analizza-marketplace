# Contrato do yeroon play (v1) — o que o projeto cliente usa

Resumo para quem integra. Endereços de desenvolvimento: API `https://api.dev.play.yeroon.video`
(variável `YEROON_API_URL`), web e player `https://play.dev.yeroon.video`.

## Fluxo

```
back ──chave──► POST /v1/videos/uploads             → videoId, partSizeBytes, partCount
front ────────► PUT nas URLs de /part-urls           (bytes direto ao storage)
back ──chave──► POST /v1/videos/{id}/upload/complete
yeroon ─webhook► back: video.ready (ou video.failed)
back ──chave──► POST /v1/videos/{id}/playback-token → embedUrl, hlsUrl
front ────────► <iframe src="{embedUrl}">
```

Regras que não mudam:

- A chave (`yk_…`) e o segredo (`whsec_…`) ficam só no back. O front e o app falam **só** com o back do cliente (e com o storage nas URLs assinadas), nunca com a `/v1`.
- O cliente guarda só o `videoId`. Arquivo, partes, status, renditions e URLs de mídia são da plataforma.

## Autenticação

`Authorization: Bearer yk_…` em toda chamada `/v1`. Chave ausente, errada ou fora do formato: `401` sem corpo.

## Rotas de upload

Partes do mesmo tamanho (`partSizeBytes`), menos a última.

| Chamada | Corpo | Resposta |
|---|---|---|
| `POST /v1/videos/uploads` | `{"fileName","contentType","sizeBytes"}` | `201 {"videoId","partSizeBytes","partCount"}` |
| `POST /v1/videos/{id}/upload/part-urls` | `{"partNumbers":[1,2,…]}` (até 20 por chamada) | `{"urls":[{"partNumber","url"}]}` |
| `GET /v1/videos/{id}/upload/parts` | — | `{"parts":[{"partNumber","etag","sizeBytes"}]}` (partes já enviadas, para retomar) |
| `PUT {url}` (direto ao storage, não é `/v1`) | bytes da parte | cabeçalho `ETag` |
| `POST /v1/videos/{id}/upload/complete` | `{"parts":[{"partNumber","etag"}]}` | `{"videoId","status":"ENVIADO"}` |
| `DELETE /v1/videos/{id}/upload` | — | `204` |

O `PUT` sai do navegador direto para o storage (R2): o CORS do bucket precisa liberar a origem do front e expor o `ETag`. Hoje o CORS do yeroon só libera `https://play.dev.yeroon.video`, o worker do yeroon e `http://localhost:3000`; um front em outra origem não consegue enviar partes pelo navegador até o time do yeroon incluí-la. App nativo (Expo, Flutter) não passa por CORS.

## Rotas de consulta e exclusão

| Chamada | Resposta |
|---|---|
| `GET /v1/videos` | `{"videos":[{"videoId","fileName","status","createdAt","thumbnailUrl","sizeBytes"}]}` |
| `GET /v1/videos/{id}` | `{"videoId","fileName","status","failureReason","renditions","thumbnailUrl"}` |
| `DELETE /v1/videos/{id}` | `204`. Só `PRONTO` ou `FALHOU` (senão `422` com `video.deletable`). Apaga original, HLS e miniatura e libera a vaga da conta de teste |

Vídeo de outro cliente responde `404`, igual a um que não existe.

### Status

`PENDENTE` → `ENVIADO` → `PROCESSANDO` → `PRONTO` | `FALHOU`; ou `CANCELADO` / `ABANDONADO` (upload não concluído em 24 h).

## Reprodução

`POST /v1/videos/{id}/playback-token` — só com o vídeo `PRONTO`; antes disso, `409`.

```json
{ "videoId": "…", "token": "eyJ…", "expiresAt": "2026-10-22T04:00:00Z",
  "embedUrl": "https://play…/embed/eyJ…",
  "hlsUrl": "https://play…/api/play/eyJ…/master.m3u8" }
```

- O token vale 6 h. Peça um novo a cada abertura da página do vídeo; não guarde. Ao front, devolva só `embedUrl`, `hlsUrl` e `expiresAt`.
- **Web:** `<iframe src="{embedUrl}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen>`. Só abre nas `allowedOrigins` da conta.
- **App nativo:** toque o `hlsUrl` direto (Expo: `expo-video`; Flutter: `video_player`).

### postMessage do player

O player avisa a página de fora:

```js
window.addEventListener("message", (e) => {
  if (e.data?.source !== "yeroon-player") return;
  // e.data.type: "ready" | "play" | "pause" | "timeupdate" | "ended" | "error"
  // e.data.currentTime, e.data.duration, e.data.videoId
});
```

Aceita comandos, só das `allowedOrigins`:

```js
iframe.contentWindow.postMessage({ source: "yeroon-host", command: "seek", value: 120 }, "*");
// command: "play" | "pause" | "seek" (value em segundos) | "mute" | "unmute"
```

`ready` e `error` bastam para o estado da tela (carregando / falhou). `timeupdate` chega no máximo uma vez por segundo de vídeo.

## Webhook

`POST` na `webhookUrl` quando o vídeo termina a conversão. Sem `webhookUrl`, nenhum aviso é enviado.

```
Content-Type: application/json
X-Yeroon-Event: video.ready            (ou video.failed)
X-Yeroon-Delivery: <id do aviso>
X-Yeroon-Signature: t=<epoch>,v1=<hex>

{"id":"…","type":"video.ready","createdAt":"…","data":{"videoId":"…","status":"PRONTO","renditions":["720p","480p"]}}
```

| Regra | O que fazer |
|---|---|
| Assinatura | `HMAC-SHA256(webhookSecret, "<epoch>.<corpo bruto>")` em hex; comparar com `v1` em tempo constante. Usar o corpo bruto, antes de qualquer parse |
| Janela | Recomendação do cliente (não faz parte do texto da v1): recusar (`401`) se `epoch` tiver mais de 5 minutos de diferença (±5 min) |
| Sem segredo | Recomendação do cliente: recusar tudo (`401`) |
| Dedupe | O mesmo aviso pode chegar mais de uma vez: deduplicar por `X-Yeroon-Delivery` |
| `id` do corpo | É o mesmo valor de `X-Yeroon-Delivery`. Os moldes deduplicam pelo `id` (que está sob a assinatura) e respondem `400` quando ele difere do cabeçalho, ou quando `id`, `type` ou `data.videoId` faltam |
| Resposta | Qualquer `2xx` em até 10 s |
| Retentativas | Fora disso, o aviso volta com espera crescente (30 s, 1 min, 2 min… até 6 h), no máximo 8 vezes |

## Erros

`application/problem+json` (RFC 9457).

| Status | Quando | No cliente |
|---|---|---|
| `422` | Regra quebrada, com `errors[].code` (ex.: `video.content-type`, `video.size`, `video.deletable`, `trial.video-limit`, `tenant.allowed-origins`) | Repassa `errors[]` |
| `404` | Vídeo inexistente ou de outro cliente | `404` |
| `409` | Playback antes de `PRONTO` | `409` |
| `401` | Chave ausente/errada na chamada `/v1` | `502` genérico, logando só o prefixo da chave (mapeamento recomendado ao cliente, não é da v1) |
| `401` do player | Token de reprodução inválido ou vencido: diz respeito ao player/`embedUrl`, não a uma chamada `/v1`. Resolva pedindo novo `playback-token` | — |
| rede/timeout | — | `502` genérico |

## Conta de teste e cadastro

Cadastro self-service: `POST {YEROON_API_URL}/account/signup`

```json
{ "name": "…", "email": "…", "password": "…", "origin": "http://localhost:3000",
  "webhookUrl": "https://…/webhooks/yeroon", "acceptedTerms": true }
```

| Status | Corpo / significado |
|---|---|
| `201` (`Cache-Control: no-store`) | `{"tenantId","name","apiKey","webhookSecret","sessionToken","sessionExpiresAt"}` — única vez em que chave e segredo aparecem |
| `409` | problem+json "Já existe uma conta com este e-mail". Não há rota para recuperar a chave |
| `422` | problem+json com `errors[].code` (regra quebrada) |

- Conta de teste (plano `TESTE`): no máximo **3 vídeos** de até **1 GB**. Contam `PENDENTE`, `ENVIADO`, `PROCESSANDO`, `PRONTO` e `FALHOU`; `CANCELADO` e `ABANDONADO` não contam, e excluir libera a vaga. A conferência é ao iniciar o upload: o 4º envio dá `422` `trial.video-limit`; `sizeBytes` acima de 1 GB dá `422` `video.size`.
- O signup aceita **uma** origem (`http(s)://host[:porta]`, sem caminho). Não existe rota para mudar `allowedOrigins` nem `webhookUrl` depois: mudança é pedido ao administrador do yeroon.
- `webhookUrl` é opcional; em desenvolvimento local, só alcançável por túnel.

Fonte: contrato público v1 do yeroon play; atualize esta página quando a v1 mudar.
