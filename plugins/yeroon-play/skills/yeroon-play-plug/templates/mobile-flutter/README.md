# Moldes do app Flutter

Ponto de partida da fatia *Mobile* (Flutter) do Passo 4 da skill: cliente das
rotas de vídeo do back, upload em partes com retomada, lista com status e
exclusão, e player nativo com `video_player` tocando o `hlsUrl`. O app fala
**só** com o back do projeto (rotas `{context-path}{api-routes-prefix}/videos/**`)
e com o storage, nas URLs assinadas do upload. Nada daqui toca a `/v1` do yeroon
nem usa `YEROON_API_KEY`. App nativo não passa por CORS.

Testado com Flutter 3.44 / Dart 3.12. Os widgets vêm sem estilo próprio
(Material básico: `ListTile`, `TextButton`).

## Convenção de caminhos

O caminho de um molde é relativo à **raiz do app Flutter** (a pasta do
`pubspec.yaml`). Tire o `.template`, troque os marcadores e confira que nenhum
sobrou. `{flutter-package}` é o `name:` do `pubspec.yaml` (usado nos imports dos
testes: `package:{flutter-package}/yeroon/api.dart`).

| Molde | Destino |
|---|---|
| `lib/yeroon/api.dart.template` | `lib/yeroon/api.dart` — base do back, `isVideoId`, `YeroonApi` (lista, detalhe, exclusão, playback) |
| `lib/yeroon/upload.dart.template` | `lib/yeroon/upload.dart` — `uploadVideo(file, onProgress, {...}) → Future<String>` |
| `lib/yeroon/video_status.dart.template` | `lib/yeroon/video_status.dart` — rótulos dos status |
| `lib/yeroon/video_upload_button.dart.template` | `lib/yeroon/video_upload_button.dart` — escolher arquivo, progresso, cancelar |
| `lib/yeroon/video_list.dart.template` | `lib/yeroon/video_list.dart` |
| `lib/yeroon/video_player_screen.dart.template` | `lib/yeroon/video_player_screen.dart` — tela de assistir + `HlsPlayer` |
| `lib/yeroon/videos_screen.dart.template` | `lib/yeroon/videos_screen.dart` — enviar + listar |
| `test/yeroon/*_test.dart.template` | `test/yeroon/*_test.dart` |

Os testes usam `flutter_test` e o `MockClient` de `package:http/testing.dart`;
o upload lê um arquivo temporário de verdade; a tela do player recebe um
`playerBuilder` falso (o `video_player` precisa de plataforma). Nenhum teste
chama o back nem a `/v1`.

## Novos × mesclados

Tudo em `lib/yeroon/` e `test/yeroon/` é **novo**. Se o projeto já tiver essa
pasta ou classes com estes nomes, **não sobrescreva**: pare e pergunte, ou
renomeie e diga no plano. Mesclados, de fato, só:

- **`pubspec.yaml`**: as dependências abaixo.
- **Navegação:** a skill não cria menu. Abra `VideosScreen` de onde fizer
  sentido no app (abaixo).
- **Permissões:** `video_player` com URL `https` não pede nada; se o back de dev
  for `http://` (ex.: `10.0.2.2`), o Android precisa de
  `android:usesCleartextTraffic="true"` (só em debug, via
  `android/app/src/debug/AndroidManifest.xml`) e o iOS de exceção no ATS.
  Diga no plano; não mexa no manifest de release.

## Dependências

Na raiz do app:

```bash
flutter pub add http video_player file_picker shared_preferences
```

`shared_preferences` guarda o upload pendente para retomar depois de fechar o
app; sem ele, troque o padrão por `MemoryPendingUploadStore` (retoma só com o
app aberto). A API do `file_picker` muda entre versões maiores: o molde usa
`FilePicker.pickFile(type: FileType.video)` (v13); em versões antigas é
`FilePicker.platform.pickFiles(...)`.

## URL do back (`--dart-define`)

A URL de origem do back (esquema + host + porta, sem `{context-path}` e sem
barra no fim) entra no build, com o mesmo nome da variável do web:

```bash
flutter run --dart-define={back-url-env}=http://10.0.2.2:8080
flutter build apk --dart-define={back-url-env}=https://api.exemplo.com
```

Lida em `api.dart` com `const String.fromEnvironment('{back-url-env}')`; sem
ela, cai em `http://localhost:8080` (no emulador Android, `localhost` é o
próprio emulador: use `10.0.2.2`; no aparelho físico, o IP da máquina). Não é
segredo — é a URL do próprio back. Se o projeto já usa `--dart-define-from-file`
ou `flutter_dotenv`, siga o que ele usa. O `{context-path}` e o
`{api-routes-prefix}` entram como constante em `api.dart`.

`YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` não existem no app.

## Como encaixar

- **`VideosScreen`** — tela pronta com `VideoUploadButton` + `VideoList`; tocar
  num vídeo faz `Navigator.push` para `VideoPlayerScreen(videoId: id)`.
  Com `go_router`: `GoRoute(path: '/videos', builder: (_, _) => const VideosScreen())`
  e `GoRoute(path: '/videos/:id', builder: (_, s) => VideoPlayerScreen(videoId: s.pathParameters['id']!))`,
  trocando o `Navigator.push` por `context.push('/videos/$id')`.
- **`VideoUploadButton`** — `VideoUploadButton(onDone: (videoId) => ...)`.
  Progresso, *Cancelar* e retomada; `pick`/`upload` podem ser trocados.
- **`VideoList`** — `VideoList(onOpen: ..., refreshKey: ..., onDeleted: ...)`.
  Consulta a cada 5 s enquanto algum vídeo está `PENDENTE`/`ENVIADO`/`PROCESSANDO`;
  *Excluir* pede *Confirmar exclusão* / *Manter*; `422` mostra aviso e mantém a linha.
- **`VideoPlayerScreen`** — pede o status a cada 5 s até um estado final;
  quando `PRONTO`, pede `POST …/videos/<id>/playback` **a cada abertura** (o
  token nunca é guardado) e toca o `hlsUrl` com
  `VideoPlayerController.networkUrl(..., formatHint: VideoFormat.hls)`.
  Alternativa com `embedUrl` em WebView: só em comentário no molde.

## Upload: o que o molde faz

Mesmo algoritmo do web: início → `partSizeBytes`/`partCount`; URLs com no máximo
20 partes por pedido; cada parte lida por faixa com `RandomAccessFile`
(`setPosition` + `read`) e enviada num `PUT` à URL assinada; `ETag`
obrigatório; `complete` com `[{partNumber, etag}]`. Duas partes em paralelo,
três novas tentativas por parte (0,5 s, 1 s, 2 s). Retomada por nome + tamanho
via `GET …/upload/parts`, pulando as partes já enviadas. `UploadCancelToken`
para de começar partes novas e chama `DELETE …/upload` (o `PUT` em voo termina).
Todo `videoId` passa por `isVideoId` (UUID) e `Uri.encodeComponent` antes de
entrar num caminho.
