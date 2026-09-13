Montados pela skill `analizza-integration-test`.

- Regra de domínio e handler: teste unitário, sem Spring e sem banco.
- Route, job e infraestrutura: teste de integração em `{it-module}`, classe terminada em `IT`,
  estendendo `BaseIntegrationTest`, sobre um único container de banco para a suíte inteira.
- **`{it-module}` é o único módulo com Testcontainers.** É ele quem sobe os containers e testa
  a infraestrutura de ponta a ponta através do `BaseIntegrationTest`.
- Serviço de saída sem container (e-mail, gateway de terceiro) ganha um dublê `@Primary` no
  `TestConfig`: nenhuma mensagem nem chamada sai da suíte.
- `EntrypointHasIntegrationTestIT` tem **um único trabalho**: todo entrypoint — `@RestController`,
  método `@Scheduled` ou `@KafkaListener` — precisa de um `<Nome>IT` que estenda
  `BaseIntegrationTest`. Um job entra pelo mesmo motivo que um controller, e com mais razão:
  ninguém recebe um 500 quando um agendamento para de rodar.
- `./gradlew test` roda só o que não precisa de banco; `./gradlew integrationTest` sobe o
  container. Os dois se separam pelo sufixo `IT`, não por tag.
