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

### Id de conversa no render quebra o build do Next 16.4

O `create-next-app` atual liga `cacheComponents: true`. Com ele, ler valor
aleatório (`crypto.randomUUID`, `getRandomValues`) durante a renderização de um
Client Component faz o `npm run build` falhar no prerender ("unstable value").
Por isso o `page.tsx` cria o id de conversa no primeiro envio, dentro do
handler, guardado num `useRef` — não em `useState(novaConversa)`. Não envolva a
página em `<Suspense>` para contornar: o id no render continuaria impuro.

### Volume e containers do Docker derivam do nome do projeto

O projeto compose, os containers e o volume (`{project-name}_postgres-data`)
saem da pasta / de `{project-name}`. Um segundo projeto com o mesmo nome na
mesma máquina reaproveita o volume antigo: o Flyway já encontra schema e a
`chat_memory` traz linhas de conversas passadas, o que contamina uma
conferência por `X-Conversation-Id`. Antes do primeiro `make up`, confira
com `docker volume ls`.

### O Postgres do LangWatch disputaria a 5432

O compose do LangWatch traz o próprio Postgres. No template ele não publica
porta no host: a 5432 é do banco do projeto.

### Variável de ambiente vence o profile

`LANGCHAIN4J_TRACING_INCLUDE_PROMPT=false` no `local.env` desliga a captura
mesmo no profile `dev`. Por isso essas linhas vêm comentadas no exemplo.

### Sem `SPRING_PROFILES_ACTIVE` não há profile — e é de propósito

O `application.yaml` não traz default em `spring.profiles.active`. Com um
default `dev`, um deploy que esquecesse a variável exportaria prompt, resposta
e resultado de tool nos traces, com amostragem de 100%. Quem ativa o `dev` são
os `local.env*.example`. O sintoma de esquecer a variável **localmente** é o
inverso, e inofensivo: o log da subida diz `No active profile set`, o trace
vem sem o conteúdo da conversa e o log do pacote do agente fica em `INFO`.

### `Authorization` com espaço no arquivo de variáveis

O `make run-agent` faz `source` do arquivo. `Bearer abc` sem aspas vira dois
comandos. Use `{mcp-env}_AUTHORIZATION="Bearer abc"`.

### `make run-agent` checa o arquivo antes de subir o banco

A ordem é de propósito: sem `local.env`, o `make` falha com a instrução de
`cp` **antes** de chamar o Docker. `run-agent` não depende de `up`; quem
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
do projeto. Ali, `docker compose down` para e remove todos os containers do
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
`down` / `down-volumes` que o `Makefile` do projeto já tinha também não são do
agente.

### Matar quem segura a porta mata o processo errado

`lsof -ti tcp:<porta> | xargs kill` tem dois defeitos. Mata **quem estiver**
na porta: se outra aplicação já a ocupava, o `bootRun` do agente falhou, a
checagem de saúde foi respondida por ela, e é ela que morre. E não encerra o
que o `make run-agent… &` abriu: o `make`, o `bash` da receita e o cliente do
`gradlew` ficam vivos.

Por isso o smoke do Passo 11 do `SKILL.md` (i) aborta se a porta do agente ou
a `11435` já tiver dono, (ii) grava o PID do `make` que ele mesmo lançou e, no
fim, encerra **só essa árvore** — a JVM do agente não é filha dela (quem a
lança é o daemon do Gradle), mas o daemon cancela o build e a encerra quando
perde o cliente — e (iii) confere pelo log que foi este agente que subiu
(`Started <classe de aplicação>`).

`./gradlew --stop` fica de fora: derruba todo daemon daquela versão do Gradle
na máquina, o de outro projeto com build em andamento inclusive. O daemon que
sobra fica ocioso e sai sozinho.

### O smoke não toca no `local.env.ollama`

O arquivo é do usuário, é git-ignored — apagado ou sobrescrito, não volta — e
pode guardar a credencial do servidor MCP. O smoke gera o próprio
`local.env.smoke` (também ignorado pelo Git), sobe o agente com
`make run-agent-with ENV_FILE=local.env.smoke` e apaga só esse arquivo.

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
herdados e exclui `*IT`, e o Passo 10 exige a soma exata (39, ou 37 sem
memória) e nenhum `*IT` entre os XML.

O que o template **não** alcança: configuração que a raiz aplica **depois** da
do módulo — `afterEvaluate`, ou `gradle.projectsEvaluated` — roda por último e
repõe o filtro. O sintoma é a contagem errada nos Passos 10 ou 11; aí mostre o
trecho da raiz ao usuário e pergunte, sem editar o build dele por conta
própria. Outro efeito herdado, inofensivo: se a raiz liga `jacocoTestReport`
ao `test` de todo subprojeto, o `test` do agente passa a gerar relatório de
cobertura onde ela mandar.

### Um `check.dependsOn(integrationTest)` do hospedeiro leva os ITs para o `build`

O build do módulo do agente deixa a `integrationTest` **fora** do `check`. Mas
a raiz de um projeto existente pode ligar as duas para todo subprojeto
(`subprojects { tasks.named('check') { dependsOn 'integrationTest' } }`, ou o
equivalente em `.kts`). Aí `./gradlew :<módulo do agente>:build` passa a subir
o Ollama: baixa ~2 GB na primeira vez e leva minutos de inferência em CPU, em
todo build e no CI.

Como notar: o `build` do Passo 11 demora minutos em vez de segundos e o log
dele traz `> Task :<módulo do agente>:integrationTest`; ou, sem rodar nada,

```bash
./gradlew :<módulo do agente>:build --dry-run --console=plain | grep integrationTest
```

imprime uma linha (o esperado é nenhuma). O que fazer: mostre o trecho da raiz
ao usuário e pergunte — a skill não edita o build do hospedeiro, e não desfaz
a ligação por dentro do módulo sem ele saber. As saídas são dele: tirar o
agente daquele bloco da raiz, ou aceitar os ITs no `build` e garantir Docker
no CI. Diga no relatório qual ficou.

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

### Em Java, `isBlank()` e `strip()` não tratam o espaço sem quebra como branco

`"\u00A0".isBlank()` é `false` em Java; em Kotlin, `isBlank()` e `trim()`
tratam U+00A0, U+2007 e U+202F como branco. Com `isBlank()`, o agente Java
aceitaria um `body` só com esses caracteres e o mandaria ao LLM; o Kotlin
devolveria `400`. Por isso o código Java usa `application/chat/Whitespace`
(`isBlank` e `trim` com `Character.isWhitespace(c) || Character.isSpaceChar(c)`)
em `ChatInput`, `ConversationIds` e `ConversationIdFilter`, e o
`ChatHandlerTest` tem um caso com o corpo só de espaços sem quebra. Ao validar
texto novo em Java, use a mesma classe.

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
