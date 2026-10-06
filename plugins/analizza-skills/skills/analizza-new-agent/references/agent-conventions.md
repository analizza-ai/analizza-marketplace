### Agente

O `{agent-module}` é um agente conversacional: recebe uma mensagem por HTTP,
chama um LLM que pode usar ferramentas de um servidor MCP, e devolve a resposta
inteira (`POST /api/v1/agent/http`) ou em fluxo (`POST /api/v1/agent/stream`,
SSE).
<!-- se existente -->

É uma aplicação Spring Boot própria, com processo e porta (`{agent-port}`)
separados do `-api`, e **não depende do `-core`**: o que ele sabe do domínio,
sabe pelas tools do servidor MCP. O pacote raiz é `{base-package}`, para o
component scan dele não alcançar o resto do projeto. As quatro camadas —
`presenter/`, `application/`, `domain/`, `infrastructure/` — são pacotes do
mesmo módulo, e a seta entre elas é convenção, não regra de build.
<!-- fim se existente -->

#### Onde cada coisa mora

| O quê | Onde |
|---|---|
| Rota, request e response | `presenter/routes/chat/` |
| Resolução e eco do `X-Conversation-Id` | `presenter/routes/chat/ConversationIds` e `presenter/configuration/ConversationIdFilter` |
| Corpo de erro e mapeamento para status HTTP | `presenter/configuration/exception/GlobalExceptionHandler` |
| Validação, orquestração e classificação de falha | `application/chat/` |
| As exceções que o caso de uso lança | `application/chat/` — não em `presenter/`, senão o handler importaria a entrada |
| O LLM, atrás de uma interface | `infrastructure/data/anticorruptionLayer/llm/Assistant` e `impl/` |
| Cliente MCP | `infrastructure/data/anticorruptionLayer/mcp/` e `infrastructure/configuration/{mcp-class}Config` |
<!-- se memoria -->
| Memória de conversa | `infrastructure/configuration/ChatMemoryConfig` |
<!-- fim se memoria -->
| Span, métricas e conteúdo dos traces | `infrastructure/observability/` |
| Prompts | `src/main/resources/prompts/` |

**Nenhum tipo de `dev.langchain4j` aparece fora de `infrastructure/`.** O
handler conhece `Assistant`, que só fala `String` e `Flux<String>`. Trocar de
biblioteca de LLM é reescrever `impl/`.

`domain/` nasce vazio: o scaffold não escreve regra de negócio.

#### Como rodar

| Comando | O que faz |
|---|---|
| `make run-agent` | sobe o agente com as variáveis de `local.env` |
| `make run-agent-ollama` | sobe o agente com `local.env.ollama`, contra um Ollama local |
<!-- se do-zero -->
<!-- se web -->
| `make run` | sobe o agente (Ollama local) e o web juntos |
<!-- fim se web -->
| `make test-backend` | testes unitários |
| `make test-integration` | testes de integração (`*IT`) |
<!-- fim se do-zero -->
<!-- se existente -->
| `make test-agent` | testes unitários do agente |
| `make test-agent-integration` | testes de integração (`*IT`) do agente |
<!-- fim se existente -->
| `make langwatch-up` / `langwatch-down` / `langwatch-logs` | LangWatch local |

`local.env` e `local.env.ollama` nunca são versionados: copie do `.example` ao
lado de cada um. Sem o arquivo, o `make` falha dizendo qual `cp` fazer.

#### Identidade vem da requisição, nunca do modelo

O identificador de quem está conversando — usuário, cliente, tenant — chega na
requisição e é passado adiante **pelo código**. Ele nunca é lido da resposta do
LLM nem pedido ao usuário no prompt: um modelo pode ser convencido a trocar um
identificador, e uma tool que confia nele entrega o dado de outra pessoa.
Quando o agente ganhar autenticação, a rota resolve a identidade em
`presenter/configuration/security/` e a entrega ao caso de uso no `ChatCommand`.

#### LLM

Qualquer provedor OpenAI-compatível. `LLM_BASE_URL`, `LLM_API_TOKEN` e
`LLM_MODEL` vêm do ambiente e **não têm default**: sem eles a aplicação não
sobe. Um default no YAML é o que faz alguém gastar token de produção sem
saber. `make run-agent` usa `local.env`; `make run-agent-ollama` usa
`local.env.ollama`, que aponta para um Ollama local, sem chave e sem custo.

`LLM_TIMEOUT` vale 120 segundos por padrão (`PT120S`); o `local.env.ollama`
sobe para 300, porque inferência em CPU é lenta.

#### Servidor MCP

O servidor `{mcp-name}` é configurado em `{mcp-name}.*`
(`{mcp-env}_ENABLED`, `_BASE_URL`, `_AUTHORIZATION`, `_TIMEOUT`).

- **A conexão é preguiçosa.** O cliente nasce na primeira conversa, não na
  subida: o agente sobe e o healthcheck passa com o servidor fora do ar. Em
  qualquer falha o cliente é descartado, e a conversa seguinte reconecta — é
  o que cobre o restart do servidor.
- **Servidor fora na hora da conversa é erro, não degradação.** A requisição
  devolve `502` com `MCP_UNAVAILABLE`. O agente nunca responde "sem
  ferramentas": um modelo que perde as tools em silêncio inventa o dado.
- **`{mcp-name}.enabled=false`** desliga o cliente; o agente conversa só com o LLM.
- **`{mcp-name}.authorization`** é o valor inteiro do header `Authorization`
  mandado ao servidor. É uma credencial **do agente**, não do usuário:
  propagar a identidade de quem conversa até o servidor MCP não está decidido.

Para um segundo servidor: copie o par `{mcp-class}Config` + `{mcp-class}Properties`
com outro nome e prefixo, e troque o bean `chatToolProvider` por um
`ToolProvider` que junte os dois.

Para uma tool **local** (código deste módulo, não um servidor): escreva a
classe em `infrastructure/data/anticorruptionLayer/<vendor>/` e registre-a no
AI Service (`AssistantAiService`) — o wiring dele é explícito, nada entra
sozinho. Toda tool é uma decisão sobre que dado o modelo passa a ver: confira
campo a campo o que ela devolve.

#### Falhas da conversa

O corpo de erro é sempre `code` + `message`, com mensagem fixa: nunca
stacktrace, token, URL nem o que o LLM ou o servidor MCP respondeu. O detalhe
vai para o log.
<!-- se buildingBlocks -->
O tipo é o `ErrorMessage` do `buildingBlocks`, que serializa também
`"details": null`.
<!-- fim se buildingBlocks -->

| Situação | Status | `code` |
|---|---|---|
| `body` ausente, em branco ou com mais de 8000 caracteres | 400 | `INVALID_REQUEST` |
| JSON que não abre | 400 | `MALFORMED_JSON` |
| `Content-Type` que não é JSON | 415 | `UNSUPPORTED_MEDIA_TYPE` |
| falha do provedor de LLM | 502 | `UPSTREAM_FAILURE` |
| timeout do provedor de LLM | 504 | `UPSTREAM_TIMEOUT` |
| servidor MCP indisponível | 502 | `MCP_UNAVAILABLE` |
| timeout do servidor MCP numa tool call | 504 | `MCP_TIMEOUT` |

A validação do `body` é do handler, não da rota, para valer também para quem
chamar o caso de uso por outro caminho.

#### Memória de conversa
<!-- se memoria-jdbc -->

Janela das últimas 30 mensagens por `conversationId`, persistida na tabela
`chat_memory` (uma linha por conversa, mensagens em JSON), criada pela
migration `V1__chat_memory.sql`. O `conversationId` vem do header
`X-Conversation-Id`, senão do campo `from`, senão é gerado — e uma conversa sem
identificador estável começa do zero a cada mensagem.

O store é criado na primeira conversa, não na subida. Consequência: se a
tabela `chat_memory` não existir, o agente **sobe** e a primeira conversa
devolve `502`.
<!-- fim se memoria-jdbc -->
<!-- se memoria-processo -->

Janela das últimas 30 mensagens por `conversationId`, **em processo**: some a
cada restart e não é compartilhada entre réplicas. Serve para desenvolvimento.
Antes de rodar com mais de uma instância, troque o `ChatMemoryConfig` por um
`ChatMemoryStore` persistente. O `conversationId` vem do header
`X-Conversation-Id`, senão do campo `from`, senão é gerado — e uma conversa sem
identificador estável começa do zero a cada mensagem.
<!-- fim se memoria-processo -->
<!-- se sem-memoria -->

O agente não guarda conversa: cada chamada é independente. O `conversationId`
existe só para agrupar os traces.
<!-- fim se sem-memoria -->
<!-- se postgres -->

#### Banco

O módulo usa `spring-boot-starter-jdbc` e Flyway. Ele nasce sem entidade
nenhuma; quem escrever a primeira `@Entity` troca o starter por
`spring-boot-starter-data-jpa`.
<!-- se kotlin -->
Com a troca, aplique também o `kotlin("plugin.jpa")` no módulo.
<!-- fim se kotlin -->
<!-- se do-zero -->

`make run-agent` e `make run-agent-ollama` sobem o Postgres do
`docker-compose.yml` e esperam ele ficar saudável antes de subir o agente;
`make db-up`, `db-down` e `db-reset` existem para mexer nele à parte.
<!-- fim se do-zero -->
<!-- se existente -->

O banco do agente é `{db-name}`, na porta `{db-port}`, separado do banco do
`-core`: dois Flyway no mesmo schema disputam a mesma `flyway_schema_history`.
É o serviço `postgres-agent` do compose; `make run-agent` e
`make run-agent-ollama` o sobem e esperam ficar saudável antes de subir o
agente.
<!-- fim se existente -->
<!-- fim se postgres -->

#### Observabilidade

- **Span por conversa** (`chat` e `chatStream`) com `conversationId`,
  `user_id` e `thread_id` — os dois últimos são o que o LangWatch usa para
  agrupar por usuário e por conversa.
- **Atributos `gen_ai.*`** (modelo, tokens, finish reason) em toda chamada ao LLM.
- **Conteúdo** — prompt, resposta, argumentos e resultado de tool — só entra
  no trace com as flags `langchain4j.tracing.include-*`, **desligadas por
  padrão** e ligadas no profile `dev`. Em produção ficam desligadas: prompt e
  resposta carregam dado de usuário, e resultado de tool carrega dado de domínio.
- **O profile padrão é `dev`.** Fora do desenvolvimento, defina
  `SPRING_PROFILES_ACTIVE=prod` — senão o conteúdo das conversas vai para o
  trace.
- **Métricas** em `/actuator/prometheus`: `chat_requests_total`, com a tag
  `outcome` (`success` ou `failure`), e `chat_request_duration_seconds`.
- **LangWatch local:** `cp langwatch.env.example langwatch.env`, troque os
  quatro segredos, `make langwatch-up`, interface em `http://localhost:5560`.
  Crie a chave na interface e ponha em `LANGWATCH_API_KEY` no `local.env` (e
  no `local.env.ollama`).

#### Testes do agente

| Nível | LLM | Para quê |
|---|---|---|
| Unitário (`*Test`) | `ScriptedChatModel` — roteiro determinístico | texto exato, fluxo de tool, classificação de falha, contrato HTTP |
| Integração (`*IT`) | Ollama em Testcontainers | a aplicação inteira responde de verdade |

**Um IT nunca compara o texto da resposta.** Com modelo pequeno ele varia.
Afirme status, forma do JSON, resposta não vazia, header ecoado, linha de
memória gravada, métrica emitida. O que precisa de texto exato é unitário.

Nos ITs o servidor MCP fica desligado: é outro sistema. O fluxo de tool é
coberto no unitário, com `FakeToolProvider`.
<!-- se it-dedicado -->

Os ITs moram no módulo `{project-name}-integration-tests` e rodam com
`./gradlew integrationTest`. O LLM é ligado na base deles por
`OllamaTestContainer.registerLlm`.
<!-- fim se it-dedicado -->
<!-- se it-no-modulo -->

Os ITs moram no próprio `{agent-module}`, em `src/test`, separados dos
unitários pelo sufixo `IT`, e rodam com
`./gradlew :{agent-module}:integrationTest`.
<!-- fim se it-no-modulo -->

A primeira execução dos ITs baixa a imagem do Ollama e o modelo (~2 GB) e
grava a imagem local `tc-ollama-<modelo>`; as seguintes reaproveitam. A
inferência roda em CPU e leva minutos — por isso os ITs ficam fora do `build`.
Troque o modelo com `IT_OLLAMA_MODEL`.

#### Não está decidido

- Autenticação do endpoint de chat e propagação da identidade até o servidor MCP.
- Limite de requisições e de custo por usuário.
- Avaliação de qualidade das respostas (evals).
- Dockerfile e pipeline do agente.
