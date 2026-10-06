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

### Cliente que fecha o SSE no meio conta como falha

`chat_requests_total{outcome="failure"}` sobe quando o cliente fecha a
conexão antes de o fluxo terminar: `curl -N … | head`, Ctrl+C, aba fechada. O
agente não sabe distinguir isso de um fluxo que quebrou. Num smoke, deixe o
`curl` ir até o fim (com `--max-time`); senão a métrica mostra uma falha que
não é defeito.

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

### `Failed to export spans` sem o LangWatch no ar

O exporter OTLP aponta, por padrão, para o LangWatch local
(`localhost:5560`). Com ele parado, cada lote de spans vira uma linha
`ERROR … HttpExporter : Failed to export spans` no log do agente, de tempos em
tempos. Não é falha do agente nem do smoke: desconte essas linhas ao procurar
erro no log. Para calar em desenvolvimento, sem subir o LangWatch, ponha
`OTEL_TRACES_SAMPLER_RATIO=0.0` no `local.env` — nenhuma requisição é
amostrada, então não há o que exportar. Tire a linha antes de querer ver um
trace.

### Matar quem segura a porta não encerra o `make run-agent`

`make run-agent-ollama &` abre uma árvore: o `make`, o `bash` da receita, o
cliente do `gradlew` e, fora dela, o daemon do Gradle, que é quem lança a JVM
do agente. `lsof -ti tcp:<porta> | xargs kill` mata só a JVM; o resto pode
ficar vivo, segurando o terminal e memória. O Passo 11 do `SKILL.md` encerra
os três: a JVM pela porta, `pkill -f '[:]<módulo>:bootRun'` para o `bash` e o
cliente, e `./gradlew --stop` para o daemon. O `[:]` no padrão é o que impede
o `pkill -f` de casar com o próprio shell que o executa.

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
`infrastructure/data/anticorruptionLayer` que não tenha container. O LLM
**tem**: o Ollama. Isso vale para tudo sob `anticorruptionLayer/llm` — o
`Assistant` e também `llm/impl/AssistantAiService`, que é interface —, então
nenhum dublê é criado ali e o `{doubles}` do `TestConfig` fica vazio neste
módulo. Um dublê `@Primary` faria o `ChatRouteIT` passar sem nunca chamar um
LLM; o IT existe para exercitar o LLM real no container.

### O Pitest da `analizza-integration-test` quebra os unitários em Boot 4

Débito da skill irmã, contornado aqui. O template de Pitest dela aplica o
plugin `info.solidsoft.pitest` com `junit5PluginVersion`, e o plugin, por
padrão, acrescenta ao classpath de teste do módulo um
`junit-platform-launcher` da linha 1.x. O BOM do Spring Boot 4 traz o JUnit 6:
engine e launcher ficam em versões diferentes, e todo
`./gradlew :<módulo>:test` — portanto todo `build` — passa a falhar com:

```
OutputDirectoryCreator not available; probably due to unaligned versions of
the junit-platform-engine and junit-platform-launcher jars on the classpath
```

`./gradlew :<módulo>:dependencyInsight --dependency junit-platform-launcher
--configuration testRuntimeClasspath` mostra a versão forçada pelo plugin.

A correção é uma linha dentro do bloco `pitest {}` do `{agent-module}`, a
mesma em `.kts` e em Groovy:

```kotlin
    // O launcher ja vem do BOM do Boot; o que o plugin adicionaria desalinha do engine.
    addJUnitPlatformLauncher = false
```

O build do módulo já declara
`testRuntimeOnly("org.junit.platform:junit-platform-launcher")`, sem versão,
então o launcher continua no classpath — na versão do BOM. O Pitest roda
normalmente depois disso. Enquanto o template dela não trouxer a linha, quem
aplica esta skill a acrescenta (Passo 10) e o diz no relatório.
