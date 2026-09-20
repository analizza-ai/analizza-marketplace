### Servidor MCP

As tools MCP moram em `{base}-mcp`, módulo de biblioteca: sem `main()`, sem
`bootJar`, servido pelo mesmo Tomcat do `{api-module}` em `/mcp`. O módulo
**nunca** depende do `{api-module}` — quem precisar de algo que mora lá desce
esse algo para o `{core-module}`.

Quem chamou vem de `Authentication.getName()` e `getAuthorities()`, nunca do
objeto do token: é o que mantém a tool funcionando se o mecanismo de
autenticação mudar.

`spring.ai.mcp.server.type=SYNC` não é preferência. Em modo streaming o
`ThreadLocal` do `SecurityContextHolder` não é garantido, e a tool perderia a
identidade de quem chamou.

Toda classe de tools nova precisa de um teste de integração com o nome dela
mais `IT` (`<NomeDaClasseDeTools>IT`) — a regra ArchUnit
`EntrypointHasIntegrationTestIT` cobre `@McpTool` e é exatamente esse nome que
ela procura — e de uma passada pela seção 3 do runbook antes de ser liberada: o
que a tool devolve vai para um modelo de IA, e decidir isso é trabalho humano.

**Débito conhecido:** o MCP divide processo e pod com o `{api-module}`. Tráfego
de MCP mal-comportado degrada o app que pessoas usam. Fechar é módulo com
`main()`, Dockerfile, manifest e pipeline próprios.
