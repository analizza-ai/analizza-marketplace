## Variáveis de ambiente

O que o `{agent-module}` lê do ambiente, em
`{agent-module}/src/main/resources/application.yaml`. Aqui ficam só os nomes:
o padrão de cada variável mora no `application.yaml`, e os valores de
desenvolvimento em `local.env` e `local.env.ollama`, na raiz — copiados de
`local.env.example` e `local.env.ollama.example`, nunca versionados. Variável
nova entra no `application.yaml`, nesta tabela e nos dois `.example`, no mesmo
commit.

"Obrigatória" quer dizer sem padrão: faltando, a aplicação não sobe.

| Variável | Obrigatória | Para quê |
|---|---|---|
| `LLM_BASE_URL=` | sim | URL base do provedor de LLM (OpenAI-compatível) |
| `LLM_API_TOKEN=` | sim | chave do provedor de LLM; no Ollama, qualquer texto |
| `LLM_MODEL=` | sim | nome do modelo |
| `LLM_TIMEOUT=` | não | tempo máximo de uma chamada ao LLM, como duração ISO-8601 |
| `SPRING_PROFILES_ACTIVE=` | não | profile do Spring (lida pelo próprio Spring; o `application.yaml` não lhe dá padrão); sem ela, nenhum profile fica ativo. `dev` grava o conteúdo das conversas nos traces (é o que os `local.env*.example` definem); fora do desenvolvimento use `prod` |
| `PORT=` | não | porta HTTP do agente |
| `LOG_LEVEL=` | não | nível de log do agente e do LangChain4j |
| `TERMINATION_GRACE_PERIOD_SECONDS=` | não | segundos de espera pelas requisições em curso ao desligar |
<!-- se postgres -->
| `DB_URL=` | não | URL JDBC do Postgres do agente |
| `DB_USER=` | não | usuário do banco |
| `DB_PASSWORD=` | não | senha do banco |
<!-- fim se postgres -->
| `{mcp-env}_ENABLED=` | não | liga o cliente do servidor MCP `{mcp-name}`; desligado, o agente conversa só com o LLM |
| `{mcp-env}_BASE_URL=` | não | URL do servidor MCP; precisa de valor quando o cliente está ligado |
| `{mcp-env}_AUTHORIZATION=` | não | valor inteiro do header `Authorization` mandado ao servidor MCP; vazio, sem header |
| `{mcp-env}_TIMEOUT=` | não | tempo máximo de uma chamada ao servidor MCP, como duração ISO-8601 |
| `{mcp-env}_LOG_REQUESTS=` | não | loga o que o agente manda ao servidor MCP; só para depuração local (ver abaixo) |
| `{mcp-env}_LOG_RESPONSES=` | não | loga o que o servidor MCP devolve; só para depuração local (ver abaixo) |
| `OTEL_EXPORTER_OTLP_ENDPOINT=` | não | para onde os traces são exportados (OTLP/HTTP) |
| `LANGWATCH_API_KEY=` | não | chave do LangWatch, mandada como `Bearer` na exportação dos traces |
| `OTEL_TRACES_SAMPLER_RATIO=` | não | fração das requisições que vira trace, de `0.0` a `1.0` |
| `OTEL_SERVICE_NAME=` | não | nome do serviço nos traces e em `spring.application.name` |
| `APP_VERSION=` | não | versão do serviço nos traces |
| `DEPLOYMENT_ENVIRONMENT=` | não | nome do ambiente nos traces |
| `LANGCHAIN4J_TRACING_INCLUDE_PROMPT=` | não | grava o prompt no trace; carrega dado de usuário |
| `LANGCHAIN4J_TRACING_INCLUDE_COMPLETION=` | não | grava a resposta do LLM no trace; carrega dado de usuário |
| `LANGCHAIN4J_TRACING_INCLUDE_TOOL_ARGUMENTS=` | não | grava os argumentos das tool calls no trace |
| `LANGCHAIN4J_TRACING_INCLUDE_TOOL_RESULT=` | não | grava o resultado das tools no trace; carrega dado de domínio |
| `LANGCHAIN4J_LOG_REQUESTS=` | não | loga as requisições ao provedor de LLM; só para depuração local (ver abaixo) |
| `LANGCHAIN4J_LOG_RESPONSES=` | não | loga as respostas do provedor de LLM; só para depuração local (ver abaixo) |

As quatro `LANGCHAIN4J_TRACING_INCLUDE_*` vencem o profile: definidas como
`false`, desligam a captura também em `dev`.

**As quatro `*_LOG_REQUESTS` / `*_LOG_RESPONSES` ficam desligadas fora da
depuração local.** Ligadas, podem escrever no log o conteúdo das requisições
e das respostas — a conversa do usuário, o resultado das tools — e os
cabeçalhos, o `Authorization` (a chave do LLM, a credencial do servidor MCP)
entre eles. Log costuma ir para mais gente, e ficar guardado por mais tempo,
do que um trace.

Fora do `application.yaml`:

<!-- se web -->
- `AGENT_URL=` — lida pelo `{project-name}-web` (`src/app/api/chat/route.ts`):
  a URL do agente vista do servidor do Next. O `make run-web` a define.
<!-- fim se web -->
- `IT_OLLAMA_MODEL=` — só nos testes de integração: troca o modelo que o
  container do Ollama carrega.
