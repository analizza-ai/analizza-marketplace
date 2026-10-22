# Moldes do back Spring Boot (Java)

Ponto de partida do Passo 4 da skill: cliente da `/v1`, casos de uso, rotas de
repasse, webhook assinado, migration e testes. Leve cada arquivo para o layout
e o estilo do projeto; os caminhos abaixo são o padrão quando o projeto segue
camadas `presenter/application/domain/infrastructure`.

## Convenção de caminhos

O caminho de um molde é `<subárvore>/<tipo>/<resto>`. Grave em:

| Molde | Destino no projeto |
|---|---|
| `core/java/<resto>` | `{core-module}/src/main/java/{base-package-path}/<resto>` |
| `core/migration/<arquivo>` | `{migration-dir}/<arquivo>` |
| `api/java/<resto>` | `{api-module}/src/main/java/{base-package-path}/<resto>` |
| `api/resources/<arquivo>` | trecho para `{api-module}/src/main/resources/` |
| `it/java/<resto>` | `{it-module}/src/test/java/{base-package-path}/<resto>` |

Em todos: tire o `.template`, troque os marcadores (no nome do arquivo também,
ex.: `{video-entity}Repository.java.template`) e confira que nenhum sobrou.
`{id}` não é marcador: é variável de rota do Spring e fica como está.

Módulo único: `core/` e `api/` vão para o mesmo módulo. Sem camadas, ponha as
classes nas pastas que o projeto já usa e ajuste os `package`/`import`.

## Trechos (`*.snippet.*.template`)

Não são arquivos novos: o cabeçalho de cada um diz onde entra.

- `api/java/presenter/configuration/exception/global-exception-handler.snippet.java.template`
  — handlers de `422`/`404`/`409`/`502`. Se o projeto já tem um
  `@RestControllerAdvice`, copie os imports e os métodos marcados "yeroon play"
  para ele; se não tem, grave o trecho como `GlobalExceptionHandler.java`
  (sem as linhas de comentário do cabeçalho).
- `api/resources/application.snippet.properties.template` — as três chaves
  `yeroon.*`; em `.yml`, a mesma coisa em árvore. Só referências a variável.
- `api/java/presenter/configuration/security/security.snippet.java.template`
  — **só se o projeto usa Spring Security.** `POST {api-routes-prefix}/webhooks/yeroon`
  precisa de `permitAll` e de ficar fora do CSRF (a assinatura HMAC é a
  autenticação dele); as rotas `{api-routes-prefix}/videos/**` seguem as regras
  de autenticação que o projeto já tem. Mescle na `SecurityFilterChain`
  existente, com o matcher do webhook antes dos mais amplos. Sem Spring
  Security, ignore o trecho.
- `it/java/support/test-config.snippet.java.template` — o `@Bean @Primary` do
  dublê, para a classe `@TestConfiguration` que a base de IT importa. Imports
  depois do `package`, membros dentro da classe.

## O que cada parte entrega

- **core:** `YeroonProperties` + `YeroonConfiguration` (registra as
  propriedades sem tocar na `@SpringBootApplication`); a porta `YeroonClient` e
  `impl/YeroonClientImpl` (`RestClient`, timeout de 10 s, `Bearer`, mapa de
  erros; o log leva só o prefixo da chave); casos de uso em
  `application/video/<caso>/` — `initUpload`, `presignParts`,
  `listUploadedParts`, `completeUpload`, `cancelUpload`, `listVideos` (filtra a
  lista da `/v1` aos ids da tabela), `getVideo`, `issuePlayback`
  (`embedUrl`, `hlsUrl`, `expiresAt`) e `deleteVideo` (apaga na `/v1` e depois a
  linha; `422 video.deletable` mantém a linha; `404` da `/v1` para um id que
  está na tabela apaga a linha e responde `204`) — e
  `application/webhook/receiveYeroonEvent/`; entidade `{video-entity}`,
  repositórios e a migration das tabelas `{video-table}` e `{webhook-table}`.
- **api:** uma rota por classe em `presenter/routes/video/<caso>/`, todas sob
  `{api-routes-prefix}/videos`; `presenter/routes/webhook/receiveYeroonWebhook/`
  em `{api-routes-prefix}/webhooks/yeroon`, com `YeroonWebhookSignature`
  (HMAC-SHA256 sobre os bytes brutos, tempo constante, ±5 min, sem segredo
  recusa tudo, dedupe pelo `id` assinado, que tem de bater com
  `X-Yeroon-Delivery`; `id` ou tipo ausente/nulo → `400`). O segredo vem só de
  `YeroonProperties`. O `{context-path}` não entra em mapeamento.
- **it:** `support/FakeYeroonClient` (dublê em memória), `support/YeroonIntegrationTest`
  (estende `{base-integration-test-fqn}`, zera o dublê, põe um segredo de teste
  e cria um `RestTestClient` próprio), um `<Rota>IT` por rota, `ReceiveYeroonWebhookWithoutSecretIT` (sem segredo → `401`), o IT dos
  repositórios e três unitários que rodam no `test`: `YeroonWebhookSignatureTest`,
  `YeroonClientImplTest` (servidor HTTP local do JDK) e `YeroonPropertiesTest`
  (o `toString()` do record não mostra chave nem segredo). Nenhum chama a `/v1`.

## Autenticação das rotas de vídeo

As rotas `{api-routes-prefix}/videos/**` não trazem autenticação própria: ficam
atrás da que o projeto já tem. O Passo 2 da skill põe no plano o mecanismo
detectado (Spring Security, sessão/cookie, JWT) e, sem nenhum, avisa que
`/videos` fica aberto a qualquer um e pode consumir a cota da conta de teste.
Com Spring Security, o trecho de segurança deixa só o webhook em `permitAll`.
O web repassa `authorization` e `cookie` do usuário ao back
(`front-next/lib/repasse.ts`); Expo e Flutter injetam o cabeçalho do app pelo
cliente HTTP (README de cada um). Proteger `/videos/**` antes de produção é
item do norte.

## Ajustes que dependem do projeto

- **Dependência do cliente HTTP** no `{core-module}`: Spring Boot 4 →
  `spring-boot-starter-restclient`; Boot 3 → o `RestClient` vem de
  `spring-web` (`spring-boot-starter-web` ou `spring-web` direto). O `{api-module}`
  já tem web e JPA.
- **Spring Boot 3:** `RestTestClient` não existe — troque, no
  `YeroonIntegrationTest`, por `TestRestTemplate`/`WebTestClient` ou pelo cliente
  que a base de IT já expõe, mantendo as mesmas asserções.
- **Base de IT sem servidor de verdade:** `YeroonIntegrationTest` usa
  `@LocalServerPort` e `RestTestClient.bindToServer`, o que exige
  `webEnvironment = RANDOM_PORT`. Se a base do projeto é `MOCK` (o padrão do
  `@SpringBootTest`) ou usa MockMvc, ponha
  `@SpringBootTest(webEnvironment = RANDOM_PORT)` no `YeroonIntegrationTest`
  ou troque o cliente por `RestTestClient.bindTo(mockMvc)` / o MockMvc que a
  base já injeta, mantendo as asserções.
- **Sem classe base de IT:** `YeroonIntegrationTest` leva
  `@SpringBootTest(webEnvironment = RANDOM_PORT)` e o `@Import` do
  `TestConfig` em vez do `extends`, e precisa de um banco: siga o que o
  projeto já usa nos testes (Testcontainers com `@ServiceConnection`, banco de
  `docker-compose`, perfil de teste). Sem nada disso, diga no plano que a base
  de IT falta, em vez de inventar uma.
- **Regra "todo entrypoint tem IT"** (ArchUnit ou similar): os ITs se chamam
  `<Rota>IT` e estendem a base por meio de `YeroonIntegrationTest`.
- **Banco que não é PostgreSQL:** troque `uuid`/`timestamptz` na migration
  (o comentário dela dá os equivalentes); o dedupe do webhook usa só a chave
  primária, sem SQL próprio de banco. Liquibase: as duas tabelas viram um
  changeset com o id `{migration-version}`.
- **Contratos próprios** (`Command`/`Handler` base, `BusinessRule`, exceção de
  regra quebrada): se o projeto tem, faça os casos de uso implementá-los e use a
  exceção dele no lugar de `{video-entity}RequestInvalidException`, mantendo o
  `422` com `errors[].code = required.<campo>`.
