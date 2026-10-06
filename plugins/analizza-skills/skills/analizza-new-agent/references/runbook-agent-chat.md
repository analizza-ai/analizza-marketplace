---
<!-- se web -->
type: screen-web
<!-- fim se web -->
<!-- se sem-web -->
type: api
<!-- fim se sem-web -->
---

# Checkpoint: conversa com o agente

Integração externa: LLM e servidor MCP.

## 1. O que precisa bater

Suba o agente contra o Ollama local:

```bash
cp local.env.ollama.example local.env.ollama   # ajuste LLM_MODEL para um modelo que voce tenha
make run-agent-ollama
```

<!-- se postgres -->
O `make` sobe o Postgres antes do agente; o Docker precisa estar rodando.

<!-- fim se postgres -->
| Passo | Comando | Esperado |
|---|---|---|
| Saúde | `curl -s localhost:{agent-port}/actuator/health` | `"status":"UP"`, mesmo com o servidor MCP fora |
| Conversa | `curl -s -D - -X POST localhost:{agent-port}/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: check-1' -d '{"body":"oi"}'` | `200`, header `X-Conversation-Id: check-1` ecoado, `{"response":"..."}` não vazio |
| Fluxo | `curl -s -N -X POST localhost:{agent-port}/api/v1/agent/stream -H 'Content-Type: application/json' -d '{"body":"conte ate 5"}'` | linhas `data:` chegando aos poucos |
| Métrica | `curl -s localhost:{agent-port}/actuator/prometheus \| grep chat_requests_total` | `outcome="success"` com a contagem das chamadas acima |
<!-- se memoria -->
| Memória | duas chamadas com o mesmo `X-Conversation-Id`: "meu nome é Ana", depois "qual é o meu nome?" | a segunda resposta usa a primeira |
<!-- fim se memoria -->
<!-- se memoria-jdbc -->
<!-- se do-zero -->
| Memória gravada | `docker compose exec postgres psql -U {db-name} -d {db-name} -c 'select memory_id, length(content) from chat_memory'` | uma linha por `X-Conversation-Id` usado |
<!-- fim se do-zero -->
<!-- se existente -->
| Memória gravada | `docker compose exec postgres-agent psql -U {db-name} -d {db-name} -c 'select memory_id, length(content) from chat_memory'` | uma linha por `X-Conversation-Id` usado |
<!-- fim se existente -->
<!-- fim se memoria-jdbc -->
<!-- se web -->
| Tela | `make run-web`, abrir `http://localhost:3000`, mandar uma mensagem | o texto aparece aos poucos |
<!-- se memoria -->
| Tela, memória | na mesma página, dizer o nome e depois perguntar por ele | a segunda resposta lembra da primeira; recarregar a página começa outra conversa |
<!-- fim se memoria -->
<!-- fim se web -->

Trace: `cp langwatch.env.example langwatch.env`, troque os segredos,
`make langwatch-up`, crie a chave em `http://localhost:5560`, ponha em
`LANGWATCH_API_KEY` no `local.env.ollama`, reinicie o agente e converse. O
trace `chat` precisa aparecer com `thread_id` igual ao `X-Conversation-Id` e,
no profile `dev`, com o prompt e a resposta.

## 2. O que tentar para ver se quebra

| Tentativa | Esperado |
|---|---|
| `{"body":"   "}` | `400`, `INVALID_REQUEST`, sem chamada ao LLM |
| corpo com mais de 8000 caracteres | `400`, `INVALID_REQUEST` |
| JSON quebrado | `400`, `MALFORMED_JSON` |
| `Content-Type: text/plain` | `415`, `UNSUPPORTED_MEDIA_TYPE` |
| Parar o Ollama e conversar | `502` ou `504`, corpo com `code` e `message` e **sem** stacktrace nem URL |
| `{mcp-env}_ENABLED=true` e `{mcp-env}_BASE_URL` apontando para um servidor MCP parado | o agente **sobe**; a conversa devolve `502` `MCP_UNAVAILABLE` |
| Subir o servidor MCP e conversar de novo, sem reiniciar o agente | a conversa volta a funcionar |
| Pedir ao agente o dado de "outro usuário" | o agente não troca de identidade a pedido |
<!-- se memoria-jdbc -->
| Subir o agente contra um banco sem a tabela `chat_memory` | o agente **sobe**; a primeira conversa devolve `502` — o store de memória só é criado na primeira conversa |
<!-- fim se memoria-jdbc -->
<!-- se web -->
| Só o web no ar (`make run-web`, agente parado), mandar mensagem | a tela avisa que o agente está indisponível, sem detalhe técnico |
<!-- fim se web -->

## 3. O que não está na lista

Olhe o que cada tool do servidor MCP **devolve ao modelo**, campo a campo.
URL assinada, e-mail, documento, dado de outra pessoa: tudo o que a tool
devolve o modelo pode repetir na resposta. Esta conferência não tem como ser
automatizada e é o motivo de este runbook existir.

Com as flags de conteúdo ligadas, olhe também o que foi parar no trace.

## 4. O que este checkpoint já pegou

_(vazio — preencha a cada conferência)_
