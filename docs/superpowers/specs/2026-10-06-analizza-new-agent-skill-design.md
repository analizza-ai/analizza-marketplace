# `analizza-new-agent` — design

> Uma entrega, 1 PR, no `analizza-marketplace`: a skill, Kotlin e Java, provada
> por quatro aplicações reais antes do merge.

## Contexto

A `analizza-new-project` cria um monorepo com `-api` e `-core`. Para um agente
de IA essa divisão sobra: o `eaf-agent` nasceu dela e teve os dois módulos
fundidos à mão num só (`eaf-agent-assistant`), com `presenter/`,
`application/`, `domain/` e `infrastructure/` como pacotes. Mas o `eaf-agent`
ainda não tem código de agente nenhum — é só a forma.

O recheio existe em outros dois lugares:

- **`agent-invest-sgap`** — agente em produção na Pags. Kotlin, Boot 4.1.1,
  LangChain4j (`langchain4j-open-ai-spring-boot4-starter`, `langchain4j-mcp`),
  `ChatController` com `/api/v1/agent/http` e `/stream`, um par
  `*McpConfig`/`*McpProperties` por servidor MCP, `GenAiSpanEnricher` e
  `LangChain4jTracingProperties` exportando para o LangWatch por OTLP,
  Prometheus, `ConversationIdFilter`, `GlobalExceptionHandler`. Pacotes planos
  (`controller/service/config`) e bastante coisa que é só de lá: logger
  corporativo, URLs de intranet, o experimento multi-agente wallet/orders.
- **`ai-demos/agent-to-agent`** — POC em Java. É a referência de **teste**:
  `OllamaTestContainer` singleton com o modelo em cache por `commitToImage`,
  `BaseIntegrationTest` injetando o LLM por `@DynamicPropertySource`,
  `ScriptedChatModel` para unitário determinístico, dublê de `ToolProvider`,
  conexão MCP preguiçosa e memória de chat em Postgres.

Nenhum dos três é a skill. A forma vem do primeiro, o código genérico do
segundo realocado nas camadas, os testes do terceiro.

## Objetivo

Uma skill `analizza-new-agent` que entrega um agente conversacional
funcionando — endpoint, LLM, cliente MCP, memória, observabilidade e testes —
em dois modos: criando um projeto do zero, sem `-core`, ou acrescentando o
módulo do agente a um projeto Gradle multi-módulo que já existe.

## Fora do escopo

- **Mobile.** A skill de agente não cria Expo.
- **Multi-agente** (`langchain4j-agentic`), **A2A** e **gateway LiteLLM**.
- **Dockerfile, CI/CD e deploy** do agente.
- **Autenticação do endpoint de chat.** A forma fica nas convenções; o código
  não sai do scaffold, pela mesma fronteira da `new-project`.
- **Código de domínio.** `domain/` nasce vazio.
- **Alterar a `analizza-integration-test`.** Ela não tem opção "sem banco"
  (ver D16); a lacuna é contornada aqui e fica como débito dela.
- **Qualquer coisa da Pags:** logger `pagseguro-logger`, URLs de intranet,
  `customerId`, Jenkinsfile, repositório Artifactory.

## Decisões

**D1 — Skill própria, reaproveitando arquivos da `new-project` por caminho
relativo.** A `new-agent` tem `SKILL.md` e templates próprios para o que é de
agente. O que é idêntico — `templates/buildingBlocks/`,
`references/initializr-api.md`, `gradle-multi-module.md`, `pitfalls.md`,
`sdd-frameworks.md` — é referenciado como `../analizza-new-project/...`. Há
precedente: a `analizza-integration-test` já aponta para
`../analizza-new-project/references/sdd-frameworks.md`. Descartados: copiar
tudo (30 templates de `buildingBlocks` duplicados, divergindo no primeiro
ajuste) e estender a `new-project` com um modo "agente" (ela tem 465 linhas e
a fronteira "entrega a forma, não escreve código", que o agente quebra de
propósito).

**D2 — O modo é detectado, não perguntado.** `settings.gradle*` na raiz →
modo *existente*. Sem build Gradle → modo *do zero*. A skill diz qual detectou
e por quê antes de seguir. Pasta não vazia sem build Gradle: mostra o conteúdo
e confirma, como a `new-project`.

**D3 — Do zero, um módulo de backend só.** `{agent-module}` carrega as quatro
camadas como pacotes, e depende de `buildingBlocks`. Não existe `-core`. A
seta entre camadas (`presenter → application → domain`, `infrastructure`
implementando portas) vale por convenção de pacote, como no `eaf-agent`.

**D4 — No projeto existente, o agente é um app Spring Boot próprio.** Tem
`@SpringBootApplication` e porta próprias, processo separado do `-api`, e
**não depende do `-core`**: fala com o domínio por MCP. A skill não assume
que o projeto tem módulos `-api` e `-core`: fala do "módulo que tem a
`@SpringBootApplication`" e do "banco do projeto". Isso mantém
LangChain4j, WebFlux e OTel fora do classpath do `-api`. Descartados: módulo
de biblioteca no processo do `-api` (o `-api` herdaria todas as dependências
de LLM) e app próprio com `implementation(project(":-core"))` (exigiria
datasource e Flyway do core também no agente).

**D5 — No modo existente, o pacote raiz do agente é `{package}.agent`.** No
modo do zero é `{package}`. O sufixo evita que, em qualquer classpath onde os
dois apps coexistam, o component scan do `-api` (raiz `{package}`) e o do
agente se misturem por acidente — e dá ao agente uma raiz de scan que não
alcança o resto do projeto. Se `{package}` já termina em `.agent`, a skill
aponta a redundância (`….agent.agent`) e oferece outro sufixo, sem decidir
sozinha; `{base-package}` continua diferente de `{package}`.

**D6 — O nome do módulo é pergunta, com padrão `{project-name}-agent`.**
Quando o nome do projeto já termina em `-agent`, a skill aponta a redundância
(`eaf-agent-agent`) e sugere `{project-name}-assistant` como alternativa, sem
decidir sozinha (na prova 2 virou `suporte-agent-assistant`).

**D7 — Kotlin e Java.** Mesmo contrato das irmãs: a DSL do Gradle segue a
linguagem no modo do zero (Kotlin → `.kts`, Java → Groovy); no modo existente,
linguagem e DSL são detectadas separadamente, como na `add-mcp-module`. Todo
template de fonte existe nas duas linguagens. O lado Java não tem referência
de produção — é provado pela aplicação nº 2 (ver *Prova*).

**D8 — A skill entrega uma fatia vertical funcionando.** Uma conversa, de
ponta a ponta. É a diferença deliberada em relação à `new-project`: um agente
sem endpoint, LLM e trace não prova nada. A única proibição que sobra é a de
código de domínio. O handler só implementa os contratos do `buildingBlocks`
quando eles existem **na forma que os templates usam** (`ResultCommand`,
`ResultCommandHandler.handle`, `ErrorMessage(String code, String message)`):
do zero vale sempre; no existente a skill confere módulo e assinaturas, e se
algo diverge o agente nasce sem depender dele, com o próprio `ErrorMessage`.

**D9 — O LLM fica atrás de uma interface em `anticorruptionLayer/llm/`.**
`Assistant` (interface) e `impl/` com o `@AiService` do LangChain4j. A
interface só expõe `String` e `Flux<String>` — nenhum tipo do LangChain4j
vaza para `application/`. É o `<vendor>` que as convenções do `eaf-agent` já
previam para o provedor de LLM.

**D10 — Provedor OpenAI-compatível, sem default de modelo no código.**
`LLM_BASE_URL`, `LLM_API_TOKEN` e `LLM_MODEL` vêm do ambiente. O
`local.env.ollama.example` traz a combinação que funciona local. Um default
de URL ou modelo escondido no YAML é o que faz alguém gastar token de
produção sem saber. Ollama é o caminho local e o dos testes; qualquer gateway
OpenAI-compatível serve em produção.

**D11 — MCP preguiçoso e falha explícita.** A skill pergunta nome e URL de um
servidor MCP. No modo existente, se houver `{base}-mcp`, ele é o padrão
(`http://localhost:{api-port}/mcp`). O `ToolProvider` conecta na primeira
conversa, não na subida — o agente sobe e o healthcheck passa com o servidor
fora. Se o servidor estiver fora na hora da conversa, a requisição falha com
**502** e mensagem canônica; o agente **não** responde sem ferramentas, porque
um agente que perde as tools em silêncio inventa a resposta. Sem servidor
informado, o par Config+Properties é gerado com `enabled=false` e nenhum
cliente MCP é criado. Um servidor feito pela `analizza-add-mcp-module` é
protegido, então o cliente aceita uma credencial **do agente** em
`{mcp-name}.authorization` (o header `Authorization` inteiro). Propagar a
identidade do usuário até o servidor MCP fica fora do escopo.

**D12 — Memória de conversa é pergunta; onde ela mora depende do banco.**
Chave: `conversationId`, passado como `@MemoryId`.

| `chat-memory` | `postgres` | Resultado |
|---|---|---|
| sim | sim | `ChatMemoryStore` JDBC (`langchain4j-community-sql`), janela de 30 mensagens, tabela `chat_memory` por migration Flyway |
| sim | não | `MessageWindowChatMemory` em processo; aviso nas convenções: não sobrevive a restart nem a duas réplicas |
| não | — | cada chamada é independente |

O schema que o store espera foi lido do jar
(`langchain4j-community-sql-1.20.0-beta30`, `PostgreSQLDialect`):
`chat_memory (memory_id VARCHAR(255) PRIMARY KEY, content TEXT NOT NULL DEFAULT '')`
— uma linha por conversa, com a janela em JSON. A migration reproduz isso e o
store é criado com `autoCreateTable(false)`. O construtor do store confere a
tabela antes de o Flyway rodar, então ele é criado na primeira conversa, não
na subida; por isso uma `chat_memory` ausente aparece como 502 na primeira
conversa.

**D13 — Banco é pergunta, e no modo existente é do agente.** Padrão *sim* do
zero, *não* no existente. No existente, com `postgres=sim`, o agente ganha
banco próprio (`{db-name}_agent`) no compose do projeto: dois Flyway na mesma
`flyway_schema_history` se atropelam. Com banco o módulo leva
`spring-boot-starter-jdbc` e Flyway — não `data-jpa`: ele nasce sem entidade
nenhuma, e quem escrever a primeira troca o starter. Sem banco, nenhum dos dois. O módulo
não assume `-api`/`-core` do projeto: o banco é o "banco do projeto", e o
encerramento da verificação derruba só o serviço do agente.

**D14 — Observabilidade vem pronta e roda sem conta externa.** Código: span
`chat` por conversa com `conversationId`, `user_id` e `thread_id`;
`GenAiSpanEnricher` com atributos `gen_ai.*` sempre e conteúdo sob quatro
flags (`include-prompt`, `-completion`, `-tool-arguments`, `-tool-result`),
todas `false` por padrão e `true` só no profile `dev`; métricas
`chat.requests{outcome}` e `chat.request.duration` em Prometheus; push OTLP de
métricas desligado. Ambiente: `docker-compose.langwatch.yml` isolado,
`langwatch.env.example` e alvos `make langwatch-up/down`. Com o LangWatch fora
do ar o exporter OTLP loga falha periodicamente (esperado);
`OTEL_TRACES_SAMPLER_RATIO=0.0` silencia.

**D15 — Três níveis de teste, com LLM real só na integração.**

| Nível | LLM | MCP |
|---|---|---|
| Unitário (`*Test`) | `ScriptedChatModel`: roteiro determinístico, falha em chamada inesperada | `ToolProvider` falso |
| Integração (`*IT`) | Ollama em Testcontainers (`qwen2.5:3b`, trocável por `IT_OLLAMA_MODEL`) | dublê — MCP é outro sistema |
| Conferência manual | Ollama local | o real, se houver |

Regra gravada nas convenções: com modelo pequeno, IT nunca compara o texto da
resposta. Afirma status, forma do JSON, resposta não vazia, header ecoado,
linha de memória no Postgres, span emitido. Resposta exata é unitário.

**D16 — Onde os ITs moram depende do modo.** Do zero: a `new-agent` invoca a
`analizza-integration-test` com `layout=dedicado` e, depois dela, acrescenta
`OllamaTestContainer`, as propriedades de LLM no `BaseIntegrationTest` e o
`ChatRouteIT` — assim a regra ArchUnit "todo entrypoint tem IT" já nasce
satisfeita. Existente: ITs dentro do próprio `{agent-module}`, com
`BaseIntegrationTest` próprio; a skill não toca no `{base}-integration-tests`,
que sobe a aplicação do `-api`. Se o build do projeto já define a tarefa
`integrationTest`, o módulo a reaproveita, limpa filtros de tag herdados e
trata zero testes como falha. Em `it-dedicado` a camada de LLM é aplicada
**antes** da verificação da skill de testes de integração, porque a regra
ArchUnit dela exige o `ChatRouteIT`; nenhum dublê é criado para
`anticorruptionLayer/llm`. O módulo do agente leva
`addJUnitPlatformLauncher = false` no bloco `pitest {}`: o template da skill
irmã injeta um `junit-platform-launcher` desalinhado do JUnit do Boot 4 e
quebra `./gradlew test` (débito dela, ver *Riscos*).

Do zero **sem banco**, os ITs também ficam dentro do módulo: a
`analizza-integration-test` só oferece Postgres, Oracle, MySQL ou "outro", e o
`BaseIntegrationTest` dela nasce com um container de banco. Consequência
assumida e relatada ao usuário: nesses dois casos o agente fica sem a regra
ArchUnit, sem JaCoCo e sem Pitest. A base tem o mesmo nome e pacote nos dois
layouts, para o `ChatRouteIT` ser um arquivo só. Nos ITs o servidor MCP fica
desligado — é outro sistema; o fluxo de tool é coberto no unitário.

**D17 — O web é uma tela de chat, não um Next vazio.** Pergunta só no modo do
zero, padrão *sim*. `create-next-app` mais `src/app/page.tsx` com a conversa
e `src/app/api/chat/route.ts` repassando o stream para `AGENT_URL` — o
backend não precisa de CORS — e mantendo o `X-Conversation-Id` da sessão. O id
nasce em `lib/conversation.ts` no primeiro envio, não na renderização (o Next
16.4 com `cacheComponents` não admite gerá-lo ali). Sem biblioteca de UI. Cumpre o papel do `chat-simulator` estático do
`agent-invest-sgap`.

**D18 — Versões são lidas, não lembradas.** `langchain4jVersion` fica em
`gradle.properties`, uma só para toda a família. A skill parte da versão da
referência (`1.20.0-beta30`) e confere a existência no Maven Central na execução. A
versão do Boot vem do Initializr (do zero) ou do projeto (existente). Boot 3.x
no modo existente: para e avisa — os starters `langchain4j-*-spring-boot4-*`
exigem Boot 4.

## O que a skill gera

### Do zero

```
{project-name}/
├── settings.gradle{dsl-ext}          include de buildingBlocks e {agent-module}
├── build.gradle{dsl-ext}             versões dos plugins, apply false
├── gradle.properties                 langchain4jVersion
├── buildingBlocks/                   templates da new-project
├── {agent-module}/                   Spring Boot; as quatro camadas
├── {project-name}-web/               [pergunta] Next.js + tela de chat
├── docker-compose.yml                [se postgres]
├── docker-compose.langwatch.yml
├── local.env.example
├── local.env.ollama.example
├── langwatch.env.example
├── Makefile
├── .gitignore                        + local.env, local.env.ollama, langwatch.env
└── <arquivo do SDD>                  camadas + seção "Agente"
```

Mais `{project-name}-integration-tests`, criado pela `analizza-integration-test`.

### Existente

```
{base}/
├── settings.gradle{dsl-ext}          + include do {agent-module}
├── gradle.properties                 + langchain4jVersion
├── {agent-module}/                   pacote raiz {package}.agent
├── docker-compose.yml                + banco do agente [se postgres]
├── docker-compose.langwatch.yml      novo
├── local.env*.example, langwatch.env.example
├── Makefile                          + run-agent (checa o env antes de subir o banco), run-agent-ollama, langwatch-up/down, test-agent-integration
└── <arquivo do SDD>                  + seção "Agente" (acrescenta, nunca sobrescreve)
```

Não cria `buildingBlocks` — usa o do projeto se existir com as assinaturas
certas; se não, o agente nasce sem depender dele e o handler não
implementa o contrato. Não cria web.
Não toca no `-api` nem no `-core`.

### Entradas

| Entrada | Do zero | Existente |
|---|---|---|
| `language`, `group`, `package`, `java-version` | pergunta (defaults da `new-project`) | detecta e confirma |
| `agent-module` | pergunta, padrão `{project-name}-agent` | pergunta, padrão `{base}-agent` |
| `agent-port` | `8080` | `8081`, ou a seguinte se colidir com o `-api` |
| `web` | pergunta, padrão sim | não oferece |
| `postgres` | pergunta, padrão sim | pergunta, padrão não |
| `chat-memory` | pergunta, padrão sim | pergunta, padrão sim |
| `mcp-name`, `mcp-url` | pergunta, pode ficar vazio (vira `tools-mcp`, desligado) | padrão `{base}-mcp` se o módulo existir |

### O módulo do agente

```
__app-class__                   ponto de entrada ({app-class}); raiz do component scan
presenter/
  routes/chat/                  ChatRoute (+ ChatRequest, ChatResponse), ConversationIds
  configuration/                ConversationIdFilter
  configuration/exception/      GlobalExceptionHandler
  configuration/security/       .gitkeep
  jobs/                         .gitkeep
application/
  chat/                         ChatCommand, ChatResult, ChatHandler, ChatStreamHandler,
                                ChatInput, ChatFailures, e as exceções do caso de uso:
                                InvalidChatRequestException, UpstreamException,
                                UpstreamTimeoutException, McpUpstreamException,
                                McpUpstreamTimeoutException
domain/                         .gitkeep em rules/, repositories/, services/
infrastructure/
  data/anticorruptionLayer/llm/ Assistant; impl/LangChain4jAssistant, AssistantAiService
  data/anticorruptionLayer/mcp/ LazyMcpToolProvider, McpUnavailableException
  configuration/                {mcp-class}Config, {mcp-class}Properties, ChatMemoryConfig
  observability/                ChatTelemetry, GenAiSpanEnricher, TracingProperties
  repositories/, security/, utils/   .gitkeep
resources/
  application.yaml              profiles dev e prod; tudo por variável de ambiente
  prompts/                      system-prompt.prompt, user-prompt.prompt
  db/migration/                 V1__chat_memory.sql [se memória em Postgres]
```

As exceções moram em `application/chat/`, e não em `presenter/`, porque quem
as lança é o handler: na entrada, o caso de uso importaria `presenter`.

Contrato HTTP, igual ao da referência menos `customerId`:

- `POST /api/v1/agent/http` — `{ "from": "...", "body": "..." }` →
  `{ "response": "..." }`
- `POST /api/v1/agent/stream` — mesmo corpo, resposta `text/event-stream`
- `X-Conversation-Id` opcional; precedência header → `from` → UUID gerado;
  trim e limite de 128; ecoado na resposta
- `body` vazio ou acima de 8000 caracteres → 400; JSON inválido → 400; mídia
  errada → 415; falha do LLM ou do MCP → 502; timeout de LLM ou MCP → 504.
- Corpo de erro canônico `{"code": "...", "message": "..."}` — o `ErrorMessage`
  do `buildingBlocks` —, sem stacktrace nem conteúdo do upstream. Códigos:
  `INVALID_REQUEST`, `MALFORMED_JSON`, `UNSUPPORTED_MEDIA_TYPE`,
  `UPSTREAM_FAILURE`, `UPSTREAM_TIMEOUT`, `MCP_UNAVAILABLE`, `MCP_TIMEOUT`

### Convenções gravadas — seção "Agente"

Onde mora prompt; como acrescentar um segundo servidor MCP (copiar o par
Config+Properties); como acrescentar uma tool local; identificador de usuário
vem da requisição e **nunca** do LLM; as quatro flags de conteúdo e por que
ficam desligadas em produção; o limite da memória em processo; a regra de
asserção dos ITs (D15); o custo do primeiro IT.

## Procedimento da skill

Cada passo fecha com verificação por código de saída, não por ausência de erro.

0. Detectar o modo e os pré-requisitos — JDK, Docker, Node se houver web,
   Initializr no modo do zero, Boot 4.x no existente.
1. Coletar as entradas, uma pergunta por vez, com o detectado como padrão.
2. Backend base — do zero: Initializr com `artifactId={agent-module}`,
   promover o wrapper, `build.gradle` da raiz, `buildingBlocks`; existente:
   criar o módulo e o `include`.
3. Dependências e `gradle.properties`; `./gradlew :{agent-module}:dependencies`
   resolve.
4. Código do agente e árvore de camadas; compila, e a tarefa de compilação não
   sai `NO-SOURCE`.
5. Cliente MCP — o par ligado, ou `enabled=false`.
6. Memória e banco, conforme as respostas.
7. Observabilidade local — composes, env examples, alvos do Makefile.
8. Web, se aceito — `git init` antes; checar `.git` aninhado.
9. Convenções no arquivo do SDD e runbook `docs/checkpoints/agent-chat.md`.
10. Testes — unitários; depois a `analizza-integration-test` (do zero) ou os
    ITs no módulo (existente); por fim a camada Ollama.
11. Verificar — `make build`, `make test-integration`, e smoke real com
    `local.env.ollama`: `curl` nos dois endpoints, `/actuator/health`,
    `/actuator/prometheus` mostrando `chat_requests`.
12. Relatar — versões lidas dos arquivos, códigos de saída, o que ficou
    desligado, e que o primeiro `test-integration` baixa cerca de 2 GB de
    modelo e roda inferência em CPU. Esse alvo fica fora do `make build`.

## Arquivos da skill

```
plugins/analizza-skills/skills/analizza-new-agent/
├── SKILL.md
├── references/
│   ├── agent-conventions.md       a seção "Agente" do arquivo do SDD (inclui MCP e observabilidade)
│   ├── it-llm-layer.md            o que acrescentar ao módulo de IT dedicado
│   ├── pitfalls-agent.md
│   ├── readme-env-vars.md         a seção "Variáveis de ambiente" do README do projeto
│   └── runbook-agent-chat.md
└── templates/
    ├── architecture-conventions.md.template   camadas num módulo só
    ├── build/{groovy,kts}/        módulo do agente; raiz sem core
    ├── source/{java,kotlin}/      main, test e it, espelhando a árvore de pacotes
    │                              (`__app-class__`, `__mcp-class__Config` no nome do arquivo)
    ├── resources/                 application.yaml, prompts, migration
    ├── web/                       page.tsx, route.ts, lib/conversation.ts, parser de SSE, testes
    └── root/                      Makefile, composes, env examples
```

Também: versão `0.5.0 → 0.6.0` nos dois `plugin.json`, entrada no `README.md`,
`make validate && make check`.

## Prova

Uma skill escrita só a partir da referência quebra no projeto nº 2 — foi o que
a spec da `add-mcp-module` aprendeu com o `analizza-auction`. Quatro aplicações
reais, em pasta descartável, antes do merge. Cada uma é feita por um executor
que recebe só o `SKILL.md` e as respostas: o que ele precisar adivinhar é
defeito da skill.

1. **Do zero, Kotlin, tudo ligado** — web, Postgres, memória persistida, sem
   MCP. ITs no módulo dedicado.
2. **Do zero, Java, mínimo** — sem web, sem banco, memória em processo, num
   projeto cujo nome termina em `-agent` (exercita D6).
3. **Existente, Java** — cópia do `analizza-auction`, o único projeto local com
   `-mcp`. Prova que o agente sobe com o servidor MCP fora e que a conversa
   devolve `502`.
4. **Existente, Kotlin** — cópia do `eaf-agent`, com banco próprio do agente.

As provas 3 e 4 rodam em cópias; os repositórios originais não são tocados.
Cada uma precisa terminar com build e testes de integração em `EXIT=0` e o
smoke do passo 11 respondendo. O que cada execução ensinou voltou para a
skill antes do PR.

Resultado observado:

1. **Do zero, Kotlin, tudo ligado** — rodada final: `make build` `EXIT=0`; 36
   unitários; 5 ITs (`ChatRouteIT` 3, `ApplicationContextIT` 1,
   `EntrypointHasIntegrationTestIT` 1); web 16 (Vitest); Pitest 28/46
   mutantes mortos; smoke 200 e SSE, com
   `chat_requests_total{outcome="success"}`. Na tela: a resposta aparece, o
   foco se mantém e a memória vale entre mensagens.
2. **Do zero, Java, mínimo** — `make build` `EXIT=0`; 36 unitários; 3 ITs;
   smoke 200; a segunda mensagem lembrou da primeira. Nenhuma alteração em
   código gerado. A skill apontou a redundância do nome (D6).
3. **Existente, Java** — 36 unitários; 3 ITs; o `-api` do projeto segue
   compilando e nenhum arquivo dos módulos existentes mudou. Com o MCP ligado
   e o `-api` parado: health UP e a conversa devolve 502 `MCP_UNAVAILABLE`.
4. **Existente, Kotlin** — 36 unitários; 3 ITs; smoke 200; `chat_memory`
   gravada no banco do agente (porta 5433) com o serviço `postgres` do projeto
   intacto. Nenhuma alteração em código gerado.

Não provado:

- Trace chegando ao LangWatch local (exige criar a chave na interface).
- Tool calling e reconexão contra um servidor MCP real com credencial: só o
  502 com o servidor fora foi provado.
- Texto chegando token a token na tela: as leituras pegaram "…" e depois a
  resposta completa.
- O download de ~2 GB do modelo na primeira execução dos ITs (a imagem já
  estava em cache).
- Tabela `chat_memory` ausente (502 na primeira conversa).
- Projeto existente que já tem módulo de IT dedicado com ArchUnit próprio: a
  regra do projeto não enxerga o agente.

## Riscos

- **Starters LangChain4j em beta** (`1.20.0-beta30` na referência) — a API de
  MCP e de `@AiService` pode mudar entre versões; por isso D18.
- **Modelo pequeno em CPU** — IT lento e ocasionalmente instável em tool
  calling; por isso a regra de asserção de D15 e o dublê de MCP.
- **Débito da `analizza-integration-test`** — o template de Pitest injeta um
  `junit-platform-launcher` desalinhado do JUnit do Boot 4 e quebra
  `./gradlew test`, e ela não tem opção "sem banco" (D16). Esta skill contorna
  os dois no módulo do agente; corrigir é trabalho da skill irmã.
- **Acoplamento com a `new-project`** (D1) — uma mudança nos templates de
  `buildingBlocks` afeta as duas skills. Aceito; a alternativa é a duplicação.
