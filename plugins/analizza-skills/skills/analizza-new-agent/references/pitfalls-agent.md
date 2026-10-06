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

### `WARNING: A restricted method in java.lang.System has been called`

Em Java 24 ou mais novo, a subida do agente (`bootRun`) imprime um grupo de
linhas `WARNING: A restricted method in java.lang.System has been called …
io.netty … NativeLibraryUtil`, seguido da sugestão de
`--enable-native-access=ALL-UNNAMED`. É o Netty — que vem com o `webflux` —
carregando a biblioteca nativa dele, e a JVM avisando que um dia vai exigir
permissão explícita. Não é erro nem falha do smoke: desconte essas linhas,
como as de `Failed to export spans`, ao filtrar o log por `WARN`.

### `docker compose down` num projeto existente derruba o que não é do agente

O banco do agente entra no compose **do projeto hospedeiro**, ao lado do banco
do `-core`. Ali, `docker compose down` para e remove todos os containers do
projeto, e `down -v` apaga também os volumes — os dados do banco de quem já
estava lá. Regra: no modo existente, todo comando de compose que a skill roda
ou sugere leva o **nome do serviço**.

```bash
docker compose stop postgres-agent            # para; os dados ficam
docker compose rm -f -v postgres-agent        # remove o container do agente
docker volume ls | grep postgres-agent-data   # o nome exato do volume do agente
docker volume rm <nome que saiu acima>        # apaga os dados do agente, e so eles
```

As duas últimas só a pedido do usuário. `docker volume prune` e os alvos
`db-down` / `db-reset` que o `Makefile` do projeto já tinha também não são do
agente.

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

### A raiz do projeto existente já registra `integrationTest`

Projetos multi-módulo costumam configurar os testes de todos os subprojetos
na raiz (`subprojects { tasks.register('integrationTest', Test) { … } }`).
Um segundo `tasks.register` com o mesmo nome não falha só no módulo: quebra a
**configuração do build inteiro**, até `./gradlew projects`, com `Cannot add
task 'integrationTest' as a task with that name already exists`. Por isso o
build do módulo pergunta `tasks.names` antes — reaproveita a tarefa se ela
existe, cria se não — e a configura do mesmo jeito nos dois casos. Não troque
por `tasks.register` nem por `tasks.named` direto: cada um quebra num dos dois
modos.

### `integrationTest` verde em dois segundos, com zero testes

A tarefa herdada costuma filtrar por tag (`useJUnitPlatform { includeTags
'integration' }`). Os `*IT` do agente não levam `@Tag`: o filtro descarta
todos, o Gradle não acha o que rodar e sai com `EXIT=0` — sem um XML sequer em
`build/test-results/integrationTest/`. Três defesas, e as três ficam:

- o build do módulo **zera** `includeTags` e `excludeTags` e **substitui** os
  padrões de nome (`setIncludePatterns('*IT')`, `setExcludePatterns()`) em vez
  de somar aos herdados, e redefine `testClassesDirs` e `classpath`;
- na `integrationTest`, `failOnNoMatchingTests = true`: sem nenhum teste a
  tarefa falha com `No tests found for given includes: [*IT]`;
- o Passo 11 confere a contagem no XML (`ChatRouteIT` com `tests="3"`), não o
  `EXIT`.

A `test` tem o mesmo cuidado no sentido inverso: descarta tags e padrões
herdados e exclui `*IT`, e o Passo 10 exige a soma exata (36, ou 34 sem
memória) e nenhum `*IT` entre os XML.

O que o template **não** alcança: configuração que a raiz aplica **depois** da
do módulo — `afterEvaluate`, ou `gradle.projectsEvaluated` — roda por último e
repõe o filtro. O sintoma é a contagem errada nos Passos 10 ou 11; aí mostre o
trecho da raiz ao usuário e pergunte, sem editar o build dele por conta
própria. Outro efeito herdado, inofensivo: se a raiz liga `jacocoTestReport`
ao `test` de todo subprojeto, o `test` do agente passa a gerar relatório de
cobertura onde ela mandar.

### `buildingBlocks` existe, mas o `ErrorMessage` é outro

Um projeto pode ter o módulo `buildingBlocks`, com `ResultCommandHandler` e
`ErrorMessage` nos pacotes esperados, e ainda assim não servir: `record
ErrorMessage(int status, String message)` não aceita `new
ErrorMessage("CODE", "mensagem")`, e o `GlobalExceptionHandler` não compila
"Arrumar" passando um número não é
saída: o corpo de erro deixaria de ser `code` + `message`, que é o contrato
HTTP do agente e o que os testes conferem. Por isso o Passo 1 confere as
**assinaturas**, e qualquer divergência leva a `sem-buildingBlocks` inteiro:
o agente declara o próprio `ErrorMessage`, e `ChatCommand` / `ChatHandler`
não implementam os contratos do projeto. Não edite o `buildingBlocks` do
hospedeiro para caber.

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
