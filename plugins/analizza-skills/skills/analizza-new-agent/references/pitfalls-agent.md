# Armadilhas do agente

O que quebrou — ou quase — ao escrever e aplicar esta skill.

## LangChain4j

### `DefaultMcpClient` conecta no construtor

Como `@Bean` comum, um servidor MCP fora do ar derruba a subida do agente. Por
isso o cliente nasce dentro do `LazyMcpToolProvider`, na primeira conversa.

### `McpToolProvider` engole a falha do servidor

Sem `failIfOneServerFails(true)`, um servidor que não responde vira um aviso no
log e **zero tools**: o modelo responde sem ferramenta e inventa. A skill liga
a flag e traduz a falha em `502`.

### Versões da família precisam ser a mesma

Os starters e o cliente MCP ainda saem na linha beta. Versões misturadas
compilam e quebram em runtime. Uma variável só, `langchain4jVersion`, em
`gradle.properties`.

### O timeout do cliente HTTP não é um `java.util.concurrent.TimeoutException`

Por isso o `ChatFailures` também olha o nome da classe na cadeia de causas.

### `SQLChatMemoryStore` confere a tabela no construtor

Como `@Bean` comum ele é instanciado antes de o Flyway rodar, não acha a
`chat_memory` e derruba a subida. Por isso o `ChatMemoryConfig` cria o store de
forma preguiçosa, na primeira conversa.

O efeito colateral: uma `chat_memory` ausente — migration apagada, banco
errado, Flyway desligado — **não aparece na subida**. O agente sobe, o
healthcheck passa, e a primeira conversa devolve `502`. Diante de um `502`
logo na primeira mensagem, com o LLM no ar, olhe a `flyway_schema_history`
antes de olhar o provedor.

### Em Kotlin, o lambda final liga no último parâmetro

`LazyMcpToolProvider("nome") { ... }` passaria o lambda como
`toolProviderFactory`, não como `clientFactory`. O `{mcp-class}Config` usa o
argumento nomeado `clientFactory = { ... }`; mantenha assim ao copiar o par
para um segundo servidor.

## Spring

### `webmvc` e `webflux` no mesmo módulo

O `webflux` entra só pelo `Flux` do endpoint SSE. Com `webmvc` no classpath o
Boot continua subindo servlet. O efeito colateral é no teste: `RestTestClient`
sem fábrica explícita escolhe o transporte pelo classpath — a base de IT passa
`JdkClientHttpRequestFactory`.

### O `contextLoads` do Initializr

Ele sobe a aplicação inteira e passaria a exigir `LLM_*` em todo `build`. A
skill o remove; o teste de contexto volta como IT, com o LLM em container.

### O Spring escreve SSE sem espaço depois de `data:`

Um token `" mundo"` chega como `data: mundo`. Um parser que tira o espaço
depois dos dois-pontos — o que a especificação de SSE manda — cola as palavras.
O `parseSse` do web guarda tudo depois de `data:`.

### `{{userInput}}` não é placeholder da skill

Em `prompts/user-prompt.prompt` as chaves duplas são a variável de template do
LangChain4j, ligada ao `@V("userInput")` do AI Service. Substituir ou apagar
faz o modelo receber um prompt sem a mensagem do usuário.

## Ambiente

### O Postgres do LangWatch disputaria a 5432

O compose do LangWatch traz o próprio Postgres. No template ele não publica
porta no host: a 5432 é do banco do projeto.

### Variável de ambiente vence o profile

`LANGCHAIN4J_TRACING_INCLUDE_PROMPT=false` no `local.env` desliga a captura
mesmo no profile `dev`. Por isso essas linhas vêm comentadas no exemplo.

### `Authorization` com espaço no arquivo de variáveis

O `make run-agent` faz `source` do arquivo. `Bearer abc` sem aspas vira dois
comandos. Use `{mcp-env}_AUTHORIZATION="Bearer abc"`.

### `make run-agent` checa o arquivo antes de subir o banco

A ordem é de propósito: sem `local.env`, o `make` falha com a instrução de
`cp` **antes** de chamar o Docker. `run-agent` não depende de `db-up`; quem
sobe o Postgres é a própria receita, depois da checagem. Ao mexer no
`Makefile`, não transforme isso em pré-requisito do alvo — pré-requisito roda
antes da receita, e o Docker voltaria a subir para depois falhar por falta do
arquivo.

## Web

### Os `*.test.ts` quebram o `npm run build` enquanto não houver Vitest

O `next build` checa os tipos de todo `.ts` de `src/`, e os três testes
importam `vitest`: sem o pacote instalado, o build para em
`TS2307: Cannot find module 'vitest'`. Por isso o `SKILL.md` só copia os
testes depois de a `analizza-integration-test` instalar o Vitest.

### `npm install -D vitest` falha com `ERESOLVE` num `create-next-app` novo

O scaffold do Next fixa `@types/node` em `^20`, e o Vitest atual pede
`^22 || >=24` como peer. Resolve subindo os dois juntos:

```bash
npm install --save-dev @types/node@^24 vitest
```

`--legacy-peer-deps` **não** resolve: deixa o `vite` fora do
`package-lock.json` e o `npm ci` seguinte quebra. A
`analizza-integration-test` já confere o `@types/node` antes de instalar; a
armadilha morde quem instala o Vitest à mão.

### `crypto.randomUUID` some fora de contexto seguro

Abrir o servidor de desenvolvimento pelo IP da rede, em `http`, deixa
`crypto.randomUUID` indefinido — só existe em `https` ou `localhost`. O
`novaConversa` de `src/lib/conversation.ts` cai para `crypto.getRandomValues`,
que funciona nos dois casos. Não troque por `randomUUID` direto.

## Testes

### Primeiro IT lento não é IT travado

Baixar ~2 GB e inferir em CPU leva minutos. Só interrompa depois de olhar
`docker logs` do container do Ollama.

### Modelo pequeno e tool calling

Modelos de 3B chamam tool de forma inconsistente. Não escreva IT que dependa
de o modelo chamar a tool; isso é unitário com `ScriptedChatModel`.

### A regra ArchUnit do módulo dedicado acusa a `ChatRoute`

A `analizza-integration-test` exige um `<Nome>IT` para todo `@RestController`.
Se a verificação dela rodar antes de o `ChatRouteIT` ser copiado, falha — e o
`ApplicationContextIT` dela também, porque o contexto não sobe sem `LLM_*`.
Aplique a camada de LLM ([it-llm-layer.md](./it-llm-layer.md)) **antes** da
verificação dela.

### A `analizza-integration-test` oferece um dublê para `Assistant`

Ela cria dublê em memória para toda interface de
`infrastructure/data/anticorruptionLayer` que não tenha container. O
`Assistant` **tem**: o Ollama. Um dublê `@Primary` dele faria o `ChatRouteIT`
passar sem nunca chamar um LLM.
