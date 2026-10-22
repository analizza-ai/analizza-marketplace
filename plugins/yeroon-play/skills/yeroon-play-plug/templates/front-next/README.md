# Moldes do web Next.js

Ponto de partida da fatia *Web* do Passo 4 da skill: Route Handlers que repassam
ao back do projeto, upload em partes com retomada, lista com status e player em
`<iframe>`. O navegador fala **só** com o Next (rotas `/api/videos/**`) e com o
storage, nas URLs assinadas; quem fala com o back é o servidor do Next. Nada
daqui toca a `/v1` do yeroon nem usa `YEROON_API_KEY`.

Pressupõe **App Router** (Next 15 ou 16, React 19) e o alias `@/*` apontando
para `src/`. Os componentes vêm sem estilo próprio: encaixe-os nos componentes
e no estilo do projeto.

## Convenção de caminhos

O caminho de um molde é relativo ao `src/` do app web (a pasta do Next que o
Passo 1 achou). Tire o `.template`, troque os
marcadores e confira que nenhum sobrou. Se o app não usa `src/`, grave na raiz do
app (`app/`, `lib/`, `components/`) e ajuste o alias nos imports.

| Molde | Destino |
|---|---|
| `lib/repasse.ts.template` | `src/lib/repasse.ts` |
| `lib/upload.ts.template` | `src/lib/upload.ts` |
| `lib/videoStatus.ts.template` | `src/lib/videoStatus.ts` |
| `lib/videoId.ts.template` | `src/lib/videoId.ts` — valida o `[id]` (UUID) antes do repasse |
| `app/api/videos/route.ts.template` | `src/app/api/videos/route.ts` — `GET` da lista |
| `app/api/videos/uploads/route.ts.template` | `POST` que inicia o upload |
| `app/api/videos/[id]/route.ts.template` | `GET` do vídeo e `DELETE` (exclui) |
| `app/api/videos/[id]/playback/route.ts.template` | `POST` que devolve `embedUrl`, `hlsUrl`, `expiresAt` |
| `app/api/videos/[id]/upload/route.ts.template` | `DELETE` que cancela o upload |
| `app/api/videos/[id]/upload/{complete,parts,part-urls}/route.ts.template` | completar, listar partes enviadas, URLs assinadas |
| `components/VideoList.tsx.template` | `src/components/VideoList.tsx` |
| `components/UploadForm.tsx.template` | `src/components/UploadForm.tsx` |
| `components/VideoPlayer.tsx.template` | `src/components/VideoPlayer.tsx` |

Cada `*.test.ts(x).template` vai ao lado do arquivo que testa, com o mesmo
tratamento. Os testes usam o runner que o projeto já tem (Vitest +
Testing Library + jsdom nos moldes); se o projeto usa Jest, troque `vi` por
`jest` e `vitest` pelo import equivalente. Nenhum chama o back nem a `/v1`: o
`fetch` é substituído.

## Novos × mesclados

Tudo acima é arquivo **novo**. Se o projeto já tiver um destes caminhos
(`src/lib/repasse.ts`, `src/app/api/videos/...`, um componente `VideoList`),
**não sobrescreva**: pare e pergunte, ou mescle e diga no plano. Mesclados, de
fato, só estes pontos do projeto:

- **Páginas existentes** ganham os componentes (abaixo); a skill não cria layout, menu nem rota de página — se a pessoa não tem onde encaixar, proponha `src/app/videos/page.tsx` e `src/app/videos/[id]/page.tsx` mínimas no plano.
- **`.env.example`** (e a documentação de variáveis do projeto) ganha `{back-url-env}=` com valor vazio.
- **`next.config`**: nada a mudar. Não declare a variável em `env:` nem em `publicRuntimeConfig`.

## Variável de ambiente

`{back-url-env}` — URL de origem do back (esquema + host + porta, sem
`{context-path}` e sem barra no fim), lida só em `repasse.ts`, no servidor.
**Nunca** com prefixo `NEXT_PUBLIC_`: ela não pode ir para o bundle do
navegador. Sem a variável, o molde cai em `http://localhost:8080`. O
`{context-path}` do back e o `{api-routes-prefix}` entram como constante em
`repasse.ts` (`BACK_PREFIX`), então a URL final é
`{back-url-env}` + `{context-path}` + `{api-routes-prefix}` + `/videos/...`.

`YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` não existem no web.

## Como encaixar os componentes

- **`UploadForm`** — `<UploadForm onDone={(videoId) => ...} />`. Um envio por vez, com progresso, cancelamento e retomada (a chave do upload pendente fica no `localStorage`). Em `onDone`, navegue para a página do vídeo ou recarregue a lista (`refreshKey` do `VideoList`). Se o projeto tem modal/diálogo, ponha o formulário dentro dele.
- **`VideoList`** — `<VideoList hrefFor={(id) => ...} currentId={...} query={...} refreshKey={...} onDeleted={...} />`. Consulta `/api/videos` a cada 5 s enquanto algum vídeo converte. `hrefFor` (padrão `/videos/<id>`) aponta para a página de assistir do projeto. O botão *Excluir* pede confirmação e chama `DELETE /api/videos/<id>`; `422` (vídeo ainda processando) mostra aviso e mantém a linha.
- **`VideoPlayer`** — `<VideoPlayer id={videoId} />` na página de assistir; em Next 16 com `cacheComponents`, envolva em `<Suspense>` se `id` vier de `params`. Pede o status a cada 5 s até um estado final; quando `PRONTO`, pede `POST /api/videos/<id>/playback` **a cada abertura** (o token nunca é guardado) e abre `<iframe src={ embedUrl } allow="autoplay; fullscreen; picture-in-picture" allowFullScreen>`. Mensagem `postMessage` com `type: "error"` só vale se `event.origin` for a origem do `embedUrl`.

Classes são só ganchos (`video-list__item`, `video-player__frame`, `upload-form`…):
estilize pelo sistema de design do projeto ou troque o markup, mantendo os
`aria-label`/`role` que os testes usam.

## Se for Pages Router

Os componentes e `lib/*` servem como estão (`next/link` funciona nos dois; o
`"use client"` é ignorado). Muda só o repasse:

- `app/api/videos/**/route.ts` vira `pages/api/videos/**.ts` com `export default function handler(req, res)`; reaproveite a lógica de `repasse.ts` adaptando `Request`/`Response` para `NextApiRequest`/`NextApiResponse` (corpo cru em `req.body` com `bodyParser` desligado ou reserializado, status e `content-type` repassados do back).
- `RouteContext<...>` não existe: o `id` vem de `req.query.id`.
- `connection()` do `GET /api/videos` não se aplica.

Avise a pessoa no plano antes de adaptar.

## Segurança do repasse

- Todo handler com `[id]` passa por `repasseVideo` (`lib/videoId.ts`): id que não é UUID responde `400` e o back não é chamado. Sem isso, `..` (que `encodeURIComponent` não altera) faria o `fetch` colapsar o caminho para outras rotas do back, com qualquer método.
- `repasse` devolve o corpo do back só em respostas abaixo de 500; falha de rede vira `502` e erro `5xx` do back vira o mesmo status com corpo genérico.

## Estilo dos moldes: `{ x }` com espaços

Em JSX e em objetos, os moldes escrevem `src={ embedUrl }` e `{ error }` com
espaços. É de propósito: a guarda dos moldes lê chaves com uma só palavra em minúsculas como
marcador não declarado. Ao adaptar ao estilo do projeto, tire os espaços depois
de gravar o arquivo (o marcador já foi trocado), se quiser.

## Dois cuidados

- **CORS do storage:** o `PUT` das partes sai do navegador direto para o R2 do yeroon, que hoje só libera `http://localhost:3000` em dev. Porta diferente de 3000 → upload falha no navegador (avise no plano; veja `references/contrato.md`).
- **Segredo no bundle:** depois de `next build`, `grep -rl 'yk_' .next/` e `grep -rl YEROON_ .next/static` têm de sair vazios (o Passo 4 já pede o primeiro); rode também `grep -rl <nome de {back-url-env}> .next/static`, com o nome que o projeto usa — a URL do back não pode estar no bundle.
