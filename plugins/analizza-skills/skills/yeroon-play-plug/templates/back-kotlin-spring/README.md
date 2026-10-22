# Moldes do back Spring Boot (Kotlin)

Gêmeo em Kotlin de [`../back-java-spring/`](../back-java-spring/README.md):
mesma árvore, mesmos nomes (`.kt` no lugar de `.java`), mesmo comportamento e
os mesmos testes. Leia o README do Java para o que é comum — *Trechos*, *O que
cada parte entrega* e *Ajustes que dependem do projeto* valem aqui tal como
estão. Este arquivo diz só o que muda.

## Convenção de caminhos

| Molde | Destino no projeto |
|---|---|
| `core/kotlin/<resto>` | `{core-module}/src/main/kotlin/{base-package-path}/<resto>` |
| `core/migration/<arquivo>` | `{migration-dir}/<arquivo>` (o mesmo SQL do Java) |
| `api/kotlin/<resto>` | `{api-module}/src/main/kotlin/{base-package-path}/<resto>` |
| `api/resources/<arquivo>` | trecho para `{api-module}/src/main/resources/` |
| `it/kotlin/<resto>` | `{it-module}/src/test/kotlin/{base-package-path}/<resto>` |

Tire o `.template`, troque os marcadores (no nome do arquivo também) e confira
que nenhum sobrou. `{id}` é variável de rota do Spring e fica; `$x` e `${...}`
são templates de string do Kotlin, não marcadores. Módulo único: `core/` e
`api/` vão para o mesmo módulo (`{api-module}` = `{core-module}` = `.`).

Os trechos têm a mesma função dos do Java, em Kotlin:
`global-exception-handler.snippet.kt.template` (vira `GlobalExceptionHandler.kt`
se o projeto não tem advice), `security.snippet.kt.template` (só com Spring
Security) e `it/kotlin/support/test-config.snippet.kt.template` (o `@Bean
@Primary` do dublê). `application.snippet.properties.template` é idêntico.

A autenticação das rotas `{api-routes-prefix}/videos/**` segue a seção
*Autenticação das rotas de vídeo* do README do Java: a do projeto, sem nada
próprio; sem nenhuma, o plano avisa e o norte pede para proteger.

## Build do `{core-module}`

Além do cliente HTTP (README do Java, *Dependência do cliente HTTP*), o Kotlin
precisa, no classpath de execução:

- **`kotlin("plugin.spring")`** (abre `@Component`/`@Repository` para proxy) e
  **`kotlin("plugin.jpa")`** (construtor sem argumentos das `@Entity`); o
  `allOpen` de `jakarta.persistence.Entity` que o Initializr já gera basta.
- **`kotlin-reflect`**: o `@ConfigurationProperties` usa os valores padrão do
  construtor de `YeroonProperties`.
- **módulo Kotlin do Jackson** — Boot 4: `tools.jackson.module:jackson-module-kotlin`;
  Boot 3: `com.fasterxml.jackson.module:jackson-module-kotlin`. Sem ele o
  `RestClient` não desserializa as `data class` da `/v1`. O Initializr já o põe
  no módulo web; num `-core` separado, confira que chega ao classpath de quem
  roda (o `-api` e o módulo de IT).

## Diferenças de forma (o comportamento é o mesmo)

- **Tipos anuláveis em vez de texto-sentinela:** o webhook lê `id`, `type` e
  `data.videoId` como `String?`; nulo, ausente, não-texto ou em branco viram
  `null` e dão `400`. O tipo vem do corpo e, sem ele, de `X-Yeroon-Event`.
- **Entrada ausente → `422`, não `400`:** os `Request` das rotas têm campos
  anuláveis com padrão `null`; o handler responde `required.<campo>`. Só
  `parts[].partNumber`/`etag` são obrigatórios no próprio JSON.
- **`YeroonProperties` é classe comum, não `data class`:** o `toString()`
  gerado imprimiria a chave e o segredo.
- **JPA:** anotações com `@field:` (acesso por campo, independente do
  `-Xannotation-default-target` do módulo); repositórios `internal`.
- **`YeroonWebhookSignature` é `object`**; a chamada fica igual à do Java.
- **`YeroonRepositoriesIT`:** como `eventType` não aceita `null` em Kotlin, a
  violação que não é duplicidade é provada com valor longo demais nas duas
  colunas (`delivery_id` e `event_type`).
- Sem `!!`: corpo vazio onde a `/v1` deveria responder um vira
  `YeroonUnavailableException` (`502`).
