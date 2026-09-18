Montados pela skill `analizza-integration-test`.

- **Todo entrypoint tem os dois tipos de teste, e nenhum substitui o outro.**
  Regra de domínio e handler: teste unitário, sem Spring e sem banco, com
  dublê da dependência externa cobrindo exaustivamente os ramos de erro.
  Route, job, tool MCP e infraestrutura: teste de integração em `{it-module}`,
  classe terminada em `IT`, estendendo `BaseIntegrationTest`, sobre um único
  container de banco para a suíte inteira, provando o fluxo contra o sistema
  de verdade.
- **`{it-module}` é o único módulo com Testcontainers.** É ele quem sobe os containers e testa
  a infraestrutura de ponta a ponta através do `BaseIntegrationTest`.
- Serviço de saída sem container (e-mail, gateway de terceiro) ganha um dublê `@Primary` no
  `TestConfig`: nenhuma mensagem nem chamada sai da suíte.
- `EntrypointHasIntegrationTestIT` tem **um único trabalho**: todo entrypoint — `@RestController`,
  método `@Scheduled`, `@KafkaListener` ou `@Tool` — precisa de um `<Nome>IT` que estenda
  `BaseIntegrationTest`. Ela garante só a metade de integração do par acima — o unitário do
  handler não tem guardrail automático, é revisão de quem mexe. Um job entra pelo mesmo motivo
  que um controller, e com mais razão: ninguém recebe um 500 quando um agendamento para de rodar.
  Uma tool MCP entra pelo mesmo motivo: quem chama por MCP também não vê stack trace, só a
  resposta que a tool devolveu.
- `./gradlew test` roda só o que não precisa de banco; `./gradlew integrationTest` sobe o
  container. Os dois se separam pelo sufixo `IT`, não por tag.
