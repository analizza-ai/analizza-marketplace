---
type: api
---

# Checkpoint: relatório de execuções (`/diagnostics/report`)

Uma página que mostra, por conversa, o que o agente fez desde que subiu:
pergunta, resposta, tools com argumentos e retorno, tokens e duração. Quem
desenha a página é o `HtmlReportGenerator` do `langchain4j-agentic`. O chat
não passa pelo agentic: uma ponte (`ExecutionMonitor`) repassa os eventos do
AI Service. A página abre no navegador, mas não é tela do web, e por isso o
tipo é `api`.

Integração externa: LLM.

## 1. O que precisa bater

Suba o agente como no `agent-chat.md` (`make run-agent-ollama`).

| Passo | Como | Esperado |
|---|---|---|
| Página vazia | logo depois de subir, sem conversar: `curl -s -i localhost:{agent-port}/diagnostics/report` | `200`, `Content-Type: text/html;charset=UTF-8`, o texto `Nenhuma execução registrada ainda.` |
| Uma conversa | `curl -s -X POST localhost:{agent-port}/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: report-1' -d '{"body":"oi"}'` e abrir `http://localhost:{agent-port}/diagnostics/report` no navegador | uma sessão `report-1` com um *run*: a pergunta (`userInput`), `agente = {agent-module}`, a resposta, tokens e duração |
| Mesma conversa de novo | repetir o `curl` com o mesmo `X-Conversation-Id` e recarregar a página | a mesma sessão, agora com dois *runs* |
| Fluxo | `curl -s -N -X POST localhost:{agent-port}/api/v1/agent/stream -H 'Content-Type: application/json' -H 'X-Conversation-Id: report-2' -d '{"body":"conte ate 5"}'` e recarregar a página | uma sessão `report-2`, com a coluna de tokens preenchida. Os testes só provam tokens no caminho JSON, porque o modelo falso de streaming não informa uso |
| Chat igual | as respostas acima | as mesmas de antes do relatório: a ponte só observa |

### Com o servidor MCP no ar

| Passo | Como | Esperado |
|---|---|---|
| Linha de tool | uma pergunta que só uma tool do servidor responde, e recarregar a página | no *run*, uma linha por tool chamada, com os argumentos e o retorno que o modelo recebeu |

## 2. O que tentar para ver se quebra

| Tentativa | Esperado |
|---|---|
| Duas chamadas com o mesmo `X-Conversation-Id` quase ao mesmo tempo (dois `curl` com `&`) | dois *runs* com pergunta e resposta casadas; o segundo pode aparecer como `<id> (paralelo 2)`, nunca com a pergunta de um e a resposta do outro |
| Parar o Ollama e conversar | o chat falha como sempre falhou (`502`/`504`), e a página mostra o *run* como falha. Volte o Ollama: a conversa segue registrando |
| Reiniciar o agente | a página volta vazia: o monitor fica em memória |
| Conversa longa ou tool que devolve muito texto | a página continua abrindo? Anote o tamanho |

## 3. O que não está na lista

A página mostra o conteúdo cru das tools de **todas** as conversas, de todas
as pessoas. Ela nasce sem chave e, com o endpoint sem autenticação, quem
alcança a porta do agente lê tudo. Confira que a porta não está exposta fora
da rede do time. Estranhe também sessão chamada `default`, *run* sem
`agente`, `Result@` na saída, ou tokens e duração zerados num turno que foi
ao modelo.

## 4. O que este checkpoint já pegou

_(vazio — preencha a cada conferência)_
