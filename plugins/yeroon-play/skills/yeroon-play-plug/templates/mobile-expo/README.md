# Moldes do app Expo

Ponto de partida da fatia *Mobile* (Expo) do Passo 4 da skill: cliente das rotas
de vídeo do back, upload em partes com retomada, lista com status e exclusão, e
player nativo com `expo-video` tocando o `hlsUrl`. O app fala **só** com o back
do projeto (rotas `{context-path}{api-routes-prefix}/videos/**`) e com o storage,
nas URLs assinadas do upload. Nada daqui toca a `/v1` do yeroon nem usa
`YEROON_API_KEY`. App nativo não passa por CORS: o aviso de origem do web não
vale aqui.

Pressupõe **Expo Router** com as telas em `src/app/` e o alias `@/*` apontando
para `src/` (o padrão do `create-expo-app`). Testado no SDK 58 (React Native
0.88, `@testing-library/react-native` 14, em que `render` e `fireEvent` são
assíncronos). Os componentes vêm sem estilo próprio.

## Convenção de caminhos

O caminho de um molde é relativo à **raiz do app Expo** (a pasta do
`package.json` que o Passo 1 achou). Tire o `.template`, troque os marcadores e
confira que nenhum sobrou. Se o app não usa `src/`, grave em `app/`,
`lib/`, `components/` na raiz e ajuste o alias.

| Molde | Destino |
|---|---|
| `src/lib/api.ts.template` | `src/lib/api.ts` — base do back, `isVideoId`, lista, detalhe, exclusão, playback |
| `src/lib/upload.ts.template` | `src/lib/upload.ts` — `uploadVideo(file, onProgress, opts?) → Promise<videoId>` |
| `src/lib/videoStatus.ts.template` | `src/lib/videoStatus.ts` — rótulos dos status |
| `src/components/UploadVideo.tsx.template` | `src/components/UploadVideo.tsx` — escolher arquivo, progresso, cancelar |
| `src/components/VideoList.tsx.template` | `src/components/VideoList.tsx` |
| `src/components/VideoPlayer.tsx.template` | `src/components/VideoPlayer.tsx` |
| `src/app/videos/_layout.tsx.template` | `src/app/videos/_layout.tsx` — `Stack` das duas telas |
| `src/app/videos/index.tsx.template` | `src/app/videos/index.tsx` — enviar + listar |
| `src/app/videos/[id].tsx.template` | `src/app/videos/[id].tsx` — assistir |

Cada `*.test.ts(x).template` de `src/lib` e `src/components` vai ao lado do
arquivo que testa. O teste da rota (`__tests__/videos-screen.test.tsx.template`)
vai em `__tests__/`: **nunca ponha teste dentro de `src/app/`** — o Expo Router
trataria o arquivo como tela. Os testes usam `jest-expo` + Testing Library;
`fetch`, `expo-video`, `expo-file-system` e `expo-document-picker` são
substituídos por dublês (nenhum teste chama o back nem a `/v1`).

## Novos × mesclados

Tudo acima é arquivo **novo**. `src/lib/api.ts` é um nome comum: se o projeto já
tiver um (ou `src/app/videos/`, ou componentes com estes nomes), **não
sobrescreva** — grave com outro nome (ex.: `src/lib/videoApi.ts`, ajustando os
imports) ou pare e pergunte, e diga no plano. Mesclados, de fato, só:

- **Navegação:** se a raiz é `Stack`, nada a fazer — `/videos` já é rota. Se é
  `Tabs`/`NativeTabs`, acrescente uma aba para `videos` (ou um `Link
  href="/videos"` numa tela existente); a skill não cria menu por conta própria.
- **`.env` / `.env.example`** do app: `EXPO_PUBLIC_{back-url-env}=` (vazio no exemplo).
- **`package.json`**: as dependências abaixo.

## Dependências

Na raiz do app (sempre `npx expo install`, que escolhe a versão do SDK):

```bash
npx expo install expo-file-system expo-video expo-document-picker
```

`expo-video` acrescenta o config plugin no `app.json`. Os três têm código
nativo: depois de instalar, o app precisa de um *development build*
(`npx expo run:ios|android` ou `eas build --profile development`); o Expo Go só
serve se já trouxer os módulos.

Testes, se o projeto ainda não tem: `npx expo install jest-expo jest @types/jest
@testing-library/react-native -- --save-dev`, `"jest": { "preset": "jest-expo" }`
e `"test": "jest"` no `package.json`.

## Variável de ambiente

`EXPO_PUBLIC_{back-url-env}` — URL de origem do back (esquema + host + porta,
sem `{context-path}` e sem barra no fim). No Expo, só variáveis com prefixo
`EXPO_PUBLIC_` chegam ao app, e vão **para o bundle**: aqui isso é aceitável
porque é a URL do próprio back, não um segredo. Por isso o nome aqui é
diferente do web (onde `{back-url-env}` fica só no servidor do Next). Leia
sempre como `process.env.EXPO_PUBLIC_...` literal — o Expo só substitui esse
formato. Sem a variável, o molde cai em `http://localhost:8080`; no emulador
Android use `http://10.0.2.2:<porta>` e, no aparelho físico, o IP da máquina na
rede (o back precisa escutar nele). O `{context-path}` e o `{api-routes-prefix}`
entram como constante em `api.ts` (`API_BASE`).

`YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` não existem no app.

## Como encaixar

- **`UploadVideo`** — `<UploadVideo onDone={(videoId) => ...} />`. Abre o
  seletor (`expo-document-picker`, `type: "video/*"`, `copyToCacheDirectory:
  true`), envia com progresso e botão *Cancelar*. Se o seletor não informar o
  tamanho, `pickVideo` lê `new File(uri).size` (expo-file-system); se ainda
  assim não souber, mostra "Não foi possível ler o tamanho do vídeo escolhido."
  em vez de enviar. Em `onDone`, recarregue a
  lista (`refreshKey`) ou abra o vídeo. Para usar outro seletor (ex.:
  `expo-image-picker` na galeria), passe `pick` devolvendo `{ uri, name, size,
  mimeType }` com `uri` `file://`.
- **`VideoList`** — `<VideoList onOpen={(id) => router.push({ pathname: "/videos/[id]", params: { id } })} refreshKey={...} onDeleted={...} />`.
  Consulta a cada 5 s enquanto algum vídeo está `PENDENTE`/`ENVIADO`/`PROCESSANDO`.
  *Excluir* mostra *Confirmar exclusão* / *Manter* antes do `DELETE`; recusa
  (`422`, vídeo ainda processando) mostra aviso e mantém a linha.
- **`VideoPlayer`** — `<VideoPlayer id={videoId} />`. Pede o status a cada 5 s
  até um estado final; quando `PRONTO`, pede `POST …/videos/<id>/playback`
  **a cada montagem** (o token nunca é guardado) e toca o `hlsUrl` com
  `useVideoPlayer` + `VideoView` (controles nativos). Erro do player
  (`statusChange` com `error`) mostra aviso. A tela `[id].tsx` usa `key={id}`
  para remontar ao trocar de vídeo.

Os textos e o markup são mínimos (`View`, `Text`, `Pressable`): troque pelos
componentes do projeto mantendo os `accessibilityLabel`/`role` que os testes usam.

## Autenticação do app no back

As rotas `{api-routes-prefix}/videos/**` do back seguem a autenticação que ele
já tem; o app precisa mandar a credencial do usuário que já usa nas outras
chamadas. Os moldes não inventam login: injete o cabeçalho pelo `fetch`.

- **`src/lib/api.ts`:** toda função recebe `fetchImpl` (padrão: `fetch` global).
  Crie um `authFetch` no projeto que acrescenta o cabeçalho do app (ex.:
  `Authorization: Bearer <token da sessão>`) e passe-o nas chamadas, ou troque o
  `globalFetch` do arquivo por ele.
- **`src/lib/upload.ts`:** passe `fetchImpl: authFetch` **e** `putFetch`
  explícito (o `fetch` de `expo/fetch`). Sem `putFetch`, o molde usa o
  `fetchImpl` também no `PUT` das partes, e a credencial do usuário iria para o
  storage do yeroon nas URLs assinadas. Se preferir um `fetch` só, acrescente o
  cabeçalho apenas quando a URL começa com `API_BASE`.
- Back sem autenticação nenhuma: as rotas ficam abertas a qualquer um — o plano
  avisa (Passo 2) e o norte pede para protegê-las antes de produção.

## Upload: o que o molde faz

Mesmo algoritmo do web: `POST …/videos/uploads` → `partSizeBytes`/`partCount`;
`POST …/upload/part-urls` com no máximo 20 partes por pedido; cada parte é lida
por faixa de bytes com `File(uri).open(FileMode.ReadOnly)` + `offset` +
`readBytes(length)` do `expo-file-system` (API nova do SDK 54+; no legado seria
`readAsStringAsync` com `position`/`length` em base64) e vai num `PUT` à URL
assinada; leitura que devolve menos bytes que a parte (arquivo mudou ou
encolheu) falha a parte antes do `PUT`; o `ETag` da resposta é obrigatório; no
fim, `POST …/upload/complete` com `[{ partNumber, etag }]`. Duas partes em
paralelo, três novas tentativas por parte (0,5 s, 1 s, 2 s).

**`PUT` com `expo/fetch`.** As chamadas ao back usam o `fetch` global; o `PUT`
das partes usa o `fetch` de `expo/fetch` (opção `putFetch`, injetável). Conferido
nas tipagens do SDK 58: ele aceita `BodyInit` e entrega um `Uint8Array`/
`ArrayBuffer` ao código nativo como está (`normalizeBodyInitAsync`), sem passar
por base64. Com o `fetch` global do React Native, cada parte viraria base64 no
JS antes de cruzar para o nativo — cerca de 2,3 a 3 vezes `partSizeBytes` de
heap por parte em voo, vezes as 2 em paralelo — e aparelho com pouca memória
fecharia o app no meio do envio. Se trocar `putFetch` pelo global, mantenha a
concorrência em 2 (ou baixe para 1). Mesmo com `expo/fetch`, cada parte em voo
ocupa `partSizeBytes` na memória.

**Retomada.** O upload pendente (nome + tamanho → `videoId`, tamanho da parte e
uma impressão digital: tamanho + FNV-1a dos primeiros 64 KB, lidos com o mesmo
leitor por faixa) fica num JSON em `Paths.document`. Reabrir o mesmo arquivo
confere a impressão digital e só então chama `GET …/upload/parts` e envia o que
falta. Plano sem impressão digital, ou outro conteúdo com o mesmo nome e
tamanho, não retoma: o upload antigo é cancelado no back (`DELETE …/upload`,
libera a vaga da conta de teste) e começa um novo. Cancelar chama
`DELETE …/upload`. Todo `videoId` passa por
`isVideoId` (UUID) antes de entrar num caminho; o que não for UUID é recusado
sem chamar o back.

## Se for React Navigation

Os componentes e `src/lib/*` servem como estão. Não grave `src/app/videos/*`:
registre duas telas no navigator do projeto — uma com `UploadVideo` +
`VideoList` (com `onOpen={(id) => navigation.navigate("Video", { id })}`) e
outra com `<VideoPlayer id={route.params.id} />` — e troque o teste da rota por
um que renderize a tela com o `NavigationContainer` do projeto.
