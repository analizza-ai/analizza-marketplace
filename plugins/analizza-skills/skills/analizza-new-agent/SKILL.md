---
name: analizza-new-agent
description: >-
  Cria um agente conversacional de IA em Spring Boot (Java ou Kotlin): do zero,
  como monorepo sem -core, com {project-name}-agent carregando presenter,
  application, domain e infrastructure num módulo só, mais buildingBlocks e,
  se pedido, {project-name}-web com tela de chat, Postgres e memória de
  conversa; ou acrescentando o módulo {base}-agent, como aplicação própria, a
  um projeto Gradle multi-módulo existente. Entrega endpoint de chat (JSON e
  SSE), LLM OpenAI-compatível via LangChain4j atrás de uma interface, cliente
  MCP preguiçoso, observabilidade (OpenTelemetry, LangWatch local,
  Prometheus) e testes com Ollama em Testcontainers. Use quando o usuário
  pedir "novo agente", "criar agent", "agente de IA", "adicionar módulo
  agent", "chat com LLM", "agente com MCP" ou invocar /analizza-new-agent.
  Para monorepo com -api e -core sem agente, use analizza-new-project.
argument-hint: "Sem argumentos — o modo (do zero ou projeto existente) é detectado; linguagem, módulo, web, Postgres, memória e servidor MCP são perguntados com defaults"
---

# Novo agente conversacional

A skill entrega um agente **funcionando**: uma conversa de ponta a ponta, com
endpoint, LLM, cliente MCP, observabilidade e testes. É a diferença deliberada
em relação à `analizza-new-project`, que entrega só a forma — um agente sem
endpoint, LLM e trace não prova nada. O que continua proibido é **código de
domínio**: `domain/` nasce vazio.

Dois modos, **detectados, não perguntados**:

```
Do zero
{project-name}/
├── buildingBlocks/
├── {agent-module}/                     4 camadas
├── {project-name}-web/                 [pergunta]
├── {project-name}-integration-tests/   [se Postgres]
├── docker-compose.yml                  [se Postgres]
├── docker-compose.langwatch.yml
├── local.env*.example
├── Makefile
└── <arquivo do SDD>

Projeto existente
{base}/
├── <módulos do projeto>/               intocados
├── {base}-mcp/                         vira o servidor MCP padrão, se existir
├── {agent-module}/                     app próprio, porta própria
├── docker-compose.langwatch.yml
├── local.env*.example
└── Makefile                            + alvos do agente
```

Do zero **não existe `-core`**: `presenter/`, `application/`, `domain/` e
`infrastructure/` são pacotes do `{agent-module}`. No projeto existente o
agente é uma aplicação Spring Boot própria, que **não depende de nenhum módulo
do projeto** (além do `buildingBlocks`, se houver): o que ele sabe do domínio,
sabe por MCP.

## Quando usar

- Agente conversacional novo, do zero, em Java ou Kotlin
- Acrescentar um agente a um projeto Gradle multi-módulo com Spring Boot 4.x
- **Não** use para monorepo `-api` + `-core` sem agente — essa é a `analizza-new-project`
- **Não** use para expor o domínio como tools — essa é a `analizza-add-mcp-module`; o agente **consome** o que ela cria

## Vocabulário

| Placeholder | Valor |
|---|---|
| `{project-name}` | nome da pasta raiz (do zero) ou `rootProject.name` (existente) |
| `{base}` | só no modo existente: o prefixo comum dos módulos que já existem (`{base}-api`, `{base}-core`, quando seguem essa convenção), em geral o próprio `{project-name}`; sem prefixo comum (ex.: módulos `demo-agent-assistant` e `buildingBlocks`), o `{project-name}` |
| `{agent-module}` | módulo do agente — pergunta |
| `{app-class}` | PascalCase de `{agent-module}` + `Application` (`demo-agent` → `DemoAgentApplication`) |
| `{package}` | pacote base do projeto |
| `{base-package}` | pacote raiz do agente: `{package}` do zero, `{package}.agent` no existente |
| `{bb-package}` | pacote do `buildingBlocks`: `{package}` do zero; no existente, **detectado** (o pacote onde o `buildingBlocks` do projeto declara, por exemplo, `ResultCommandHandler`, Passo 1) |
| `{package-path}` | `{base-package}` com `.` trocado por `/` |
| `{group}`, `{java-version}` | perguntados (do zero) ou lidos do build (existente) |
| `{mode}` | `do-zero` ou `existente` — o modo detectado no Passo 0 |
| `{language}`, `{src-dir}` | `kotlin` ou `java` — o mesmo valor nos dois |
| `{dsl-ext}` | `.kts` ou vazio |
| `{boot-version}`, `{dependency-management-version}`, `{kotlin-version}` | só do zero: lidas do `plugins {}` do build baixado do Initializr (Passo 2), depois do download — o pedido usa o `default` do metadata. `{kotlin-version}` só em Kotlin |
| `{agent-port}` | `8080` do zero; `8081` no existente, ou a seguinte se o módulo do host (o do `@SpringBootApplication`) já a usa |
| `{mcp-name}` | nome kebab do servidor MCP; `tools-mcp` se nenhum foi informado |
| `{mcp-class}`, `{mcp-env}` | `{mcp-name}` em PascalCase e em UPPER_SNAKE (`tools-mcp` → `ToolsMcp`, `TOOLS_MCP`) |
| `{mcp-url}`, `{mcp-enabled}` | URL e `true`, ou vazio e `false` |
| `{db-name}` | `{project-name}` com `-`→`_`; no existente, com o sufixo `_agent` |
| `{db-port}` | `5432` do zero; `5433` no existente |
| `{langchain4j-version}` | `1.20.0-beta30`, conferida no Passo 3 |
| `{it-module}` | onde moram os ITs: `{agent-module}` em `it-no-modulo`, `{project-name}-integration-tests` em `it-dedicado` |

Em **nome de arquivo** o placeholder aparece como `__nome__`
(`__mcp-class__Config.kt.template` → `ToolsMcpConfig.kt`,
`__app-class__.kt.template` → `DemoAgentApplication.kt`).

**Só o que está nesta tabela é placeholder.** Ficam como estão: `{{userInput}}`
em `prompts/user-prompt.prompt` (variável do LangChain4j), `${VAR:default}` no
`application.yaml` (do Spring — mas o placeholder **dentro** dele é
substituído: `${{mcp-env}_ENABLED:{mcp-enabled}}` vira
`${TOOLS_MCP_ENABLED:false}`), `$(VAR)` e `$$1` no `Makefile`, e as chaves de
JSX em `page.tsx`.

### Marcadores condicionais

Uma linha `<!-- se X -->` abre um bloco que só entra quando X vale; `<!-- fim
se X -->` fecha. Blocos podem estar aninhados: o de dentro só entra se todos os
de fora valerem. A primeira linha `<!-- arquivo se X -->` condiciona o arquivo
inteiro: se X não vale, o arquivo **não é criado**. **Nenhuma linha de marcador
vai para o arquivo final**, e blocos de condição que não vale somem inteiros.

Os marcadores valem para tudo o que a skill grava no projeto: os arquivos de
`templates/` e também `references/agent-conventions.md`,
`references/runbook-agent-chat.md` e `references/readme-env-vars.md`.

| Condição | Vale quando |
|---|---|
| `kotlin` / `java` | linguagem do fonte |
| `do-zero` / `existente` | o modo |
| `postgres` / `sem-postgres` | o agente tem banco |
| `memoria` / `sem-memoria` | o usuário quis memória de conversa |
| `memoria-jdbc` | `memoria` e `postgres` |
| `memoria-processo` | `memoria` e `sem-postgres` |
| `buildingBlocks` / `sem-buildingBlocks` | o projeto tem o módulo `buildingBlocks` **com os contratos na forma que os templates usam**. Do zero vale sempre; no existente, confira módulo e assinaturas (Passo 1) |
| `web` / `sem-web` | modo do zero com `-web` aceito. No existente vale sempre `sem-web` |
| `it-dedicado` | do zero **com** banco: ITs em `{project-name}-integration-tests` |
| `it-no-modulo` | existente, **ou** do zero sem banco: ITs dentro do `{agent-module}` |

De cada par vale exatamente um; de `memoria-jdbc`/`memoria-processo`, um se
houver memória e nenhum se não houver; de `it-dedicado`/`it-no-modulo`,
exatamente um.

### Espelhamento de árvore

| Template | Destino |
|---|---|
| `templates/source/{language}/main/<caminho>` | `{agent-module}/src/main/{src-dir}/{package-path}/<caminho>` |
| `templates/source/{language}/test/<caminho>` | `{agent-module}/src/test/{src-dir}/{package-path}/<caminho>` |
| `templates/source/{language}/it/<caminho>` | `{it-module}/src/test/{src-dir}/{package-path}/<caminho>` |
| `templates/resources/<caminho>` | `{agent-module}/src/main/resources/<caminho>` |
| `templates/web/src/<caminho>` | `{project-name}-web/src/<caminho>` |

O sufixo `.template` cai.

## Procedimento

### Passo 0 — Detectar o modo e os pré-requisitos

```bash
find . -maxdepth 1 -name 'settings.gradle*'
java -version; docker info > /dev/null 2>&1 && echo "docker OK"
```

- **Há `settings.gradle*`** → modo **existente**. Diga isso ao usuário e por quê.
- **Não há** → modo **do zero**. Se a pasta não estiver vazia, mostre o
  conteúdo e confirme antes de escrever qualquer coisa.

**De quem é o repositório Git** — só no modo do zero, antes de escrever (no
existente a skill não roda `git init`, `git add` nem `git commit`):

```bash
raiz=$(git rev-parse --show-toplevel 2> /dev/null)
if [ -z "$raiz" ]; then echo "SEM REPOSITORIO"
elif [ "$(cd "$raiz" && pwd -P)" = "$(pwd -P)" ]; then echo "REPOSITORIO PROPRIO"
else echo "DENTRO DE OUTRO REPOSITORIO: $raiz"
fi
```

`git rev-parse --is-inside-work-tree` **não serve** para essa pergunta: responde
`true` também numa pasta vazia que está dentro do repositório de outra coisa.
Só `REPOSITORIO PROPRIO` — a raiz do repositório é esta pasta — quer dizer que
o repositório é do projeto.

`DENTRO DE OUTRO REPOSITORIO`: **pare e pergunte**, mostrando o caminho que
saiu. Não rode `git init` (criaria um repositório aninhado em silêncio) e não
decida sozinho. Se o usuário confirmar que o projeto mora mesmo dentro daquele
repositório, siga sem `git init` e **sem commit** — o Passo 11 trata como pasta
que já tinha arquivos: um `git add -A` aqui levaria junto as mudanças que o
repositório de fora tem em andamento.

Sem Docker a skill ainda gera o projeto, mas não verifica: os ITs e o banco
dependem dele. Avise antes de seguir.

**Existente** — confirme Spring Boot 4.x antes de seguir:

```bash
grep -rhoE "org\.springframework\.boot[\"')]*[[:space:]]+version[[:space:]]+[\"'][0-9][0-9A-Za-z.-]*" --include='build.gradle*' \
  --exclude-dir=build --exclude-dir=.claude --exclude-dir=node_modules . | sort -u
find . -name 'libs.versions.toml' -not -path '*/build/*' -exec grep -nE "spring-?boot|springBoot|^[[:space:]]*boot[[:space:]]*=" {} +
```

Boot 3.x: **pare e diga** que os starters `langchain4j-*-spring-boot4-*`
exigem Boot 4. Nada detectado: pergunte a versão e só siga com 4.x confirmado.
Guarde a versão completa que saiu (`4.1.0`): o relatório do Passo 12 a cita.

**Do zero** — o Initializr precisa responder, e o Node só se houver web:

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://start.spring.io/metadata/client
node -v; npx -v
```

Sem rede, **pare e avise** — não escreva o wrapper nem as versões à mão.

### Passo 1 — Coletar as entradas

Uma pergunta por vez, com o padrão — e, no modo existente, com o detectado e
de onde veio.

| Entrada | Do zero | Existente |
|---|---|---|
| `language` | pergunta; padrão `kotlin` | detecta pelo fonte do módulo com `@SpringBootApplication` |
| `group`, `package`, `java-version` | pergunta; `br.com.analizza`, `{group}.{project-name}`, `25` | lê do build e do pacote do módulo do host com `@SpringBootApplication` (o `-api`, se houver; o único módulo com a anotação, ou pergunte qual se forem vários); a raiz pode não declarar `group` |
| `agent-module` | pergunta; padrão `{project-name}-agent` | pergunta; padrão `{base}-agent` |
| `web` | pergunta; padrão sim | não oferece |
| `postgres` | pergunta; padrão sim | pergunta; padrão não |
| `chat-memory` | pergunta; padrão sim | pergunta; padrão sim |
| `mcp-name` e `mcp-url` | pergunta; pode ficar vazio | padrão: `{base}-mcp` e `http://localhost:<porta do módulo do host>/mcp`, se o módulo existir |

Pacote não aceita `-`: se `{project-name}` tiver hífen, o padrão
`{group}.{project-name}` não serve — pergunte o pacote em vez de assumir.

**Nomes redundantes (existente).** Se `{package}` já termina em `.agent`,
`{base-package}` vira `….agent.agent` e `{db-name}` pode virar `…_agent_agent`:
aponte isso e ofereça outro sufixo para o pacote (o nome do módulo sem o prefixo
`{base}`, ex.: `.concierge`) e para o banco — sem decidir sozinho. Use o
escolhido em todo lugar, e `{base-package}` continua **diferente** de
`{package}`: é o que isola o component scan do host do pacote do agente.

**Nome do módulo.** Se `{project-name}` já termina em `-agent`, diga que o
padrão ficaria redundante (`x-agent-agent`) e ofereça
`{project-name}-assistant` — sem decidir sozinho. O `agent` que sobra nesse
nome é o do próprio projeto; diga que o usuário pode digitar qualquer outro.

**Java tem piso de versão: 17.** Os templates usam `record` e pattern matching.

**Servidor MCP no modo existente.** Procure o módulo `-mcp` e a porta do módulo do host:

```bash
grep -E "include.*-mcp" settings.gradle*
grep -rnE "server\.port|^[[:space:]]*port:" --include='application*.properties' --include='application*.y*ml' \
  --exclude-dir=.claude --exclude-dir=.git --exclude-dir=.gradle --exclude-dir=build \
  --exclude-dir=node_modules --exclude-dir=worktrees --exclude-dir=.worktrees . | head
```

Cada linha traz o arquivo de onde veio: só vale a que está em
`src/main/resources` do módulo do host; mostre-a ao usuário. As pastas excluídas
guardam cópias do projeto (worktrees, saída de build) e dariam porta de outro
lugar. **Nenhuma linha quer dizer `8080`**, o padrão do Spring Boot — então
`{agent-port}` é `8081`.

Um servidor criado pela `analizza-add-mcp-module` é protegido: avise que o
agente vai precisar de uma credencial em `{mcp-env}_AUTHORIZATION` e que, sem
ela, as conversas devolvem `502`.

**`buildingBlocks` no modo existente.** Existir o módulo não basta: a condição
só vale se os contratos têm a **forma** que os templates usam. Confira os três:

```bash
grep -E "include.*buildingBlocks" settings.gradle*
bb=buildingBlocks/src/main
grep -rnE "interface ResultCommand<" "$bb"
grep -rnE "interface ResultCommandHandler<|handle\(" --include='ResultCommandHandler.*' "$bb"
grep -rnE "ErrorMessage\((val code: String, val message: String|String code, String message\))" "$bb"
```

Os três `grep` levam o diretório como argumento, de propósito: um `grep` que
recebe a lista de arquivos de um `$(find …)` fica **sem argumento** quando o
`find` não acha nada, e passa a esperar a entrada padrão — a skill trava ali.
Nesta forma, arquivo ausente é só um `grep` sem saída. **`grep` sem saída, ou
`No such file or directory` porque o módulo não existe, quer dizer
`sem-buildingBlocks`** (para o terceiro, depois de abrir o arquivo, como dito
abaixo).

| Contrato | O que o código gerado faz com ele | Precisa ser |
|---|---|---|
| `ResultCommand` | `ChatCommand implements ResultCommand<ChatResult>` | interface com **um** parâmetro de tipo, em `<pacote>.application` — `interface ResultCommand<R>` (Java), `interface ResultCommand<out R>` (Kotlin) |
| `ResultCommandHandler` | `ChatHandler implements ResultCommandHandler<ChatCommand, ChatResult>` e sobrescreve `handle` | interface com dois parâmetros de tipo, comando primeiro, e um método `handle` que recebe o comando e devolve o resultado — `R handle(C command)` / `fun handle(command: C): R` |
| `ErrorMessage` | `new ErrorMessage("CODE", "mensagem")`, serializado como `code` + `message` | em `<pacote>.presenter.exception`, com construtor `(String code, String message)` e esses dois nomes — em Java, record de dois componentes ou com esse construtor a mais; em Kotlin, `data class ErrorMessage(val code: String, val message: String, …)` com o resto opcional |

O terceiro `grep` só casa com declaração numa linha: sem resultado, abra o
arquivo antes de concluir. `{bb-package}` é o pacote desses arquivos **sem** o
sufixo `.application` / `.presenter.exception`.

Faltando o módulo, um contrato ou uma assinatura — um `ErrorMessage(int
status, String message)`, por exemplo —, vale **`sem-buildingBlocks`**, para os
três de uma vez: não há meio-termo. Diga ao usuário qual contrato divergiu e o
que isso significa: o agente declara o próprio `ErrorMessage` (`code` +
`message`), o `ChatCommand` e o `ChatHandler` **não implementam** os contratos
do projeto, e o módulo não depende de `buildingBlocks`. A skill não cria nem
altera `buildingBlocks` em projeto existente
(ver [armadilhas](./references/pitfalls-agent.md)).

**DSL do Gradle.** Do zero segue a linguagem (Kotlin → `.kts`, Java → Groovy).
No existente vale a do `settings.gradle*` que já existe.

Com as respostas, fixe as condições da tabela de marcadores e diga ao usuário
o conjunto resultante antes de escrever.

### Passo 2 — Backend base

**Do zero.** Siga a [referência do Initializr](../analizza-new-project/references/initializr-api.md)
e o [multi-módulo](../analizza-new-project/references/gradle-multi-module.md)
da `analizza-new-project`, lendo `{agent-module}` onde elas dizem
`{project-name}-api`, e com estas diferenças:

- `artifactId` e `name` = `{agent-module}`; `packageName={package}`;
  `dependencies=web,actuator`. O resto das dependências vem do template do
  módulo, não do Initializr. Para `bootVersion` peça o `default` do metadata
  do Initializr (a referência acima descreve onde ele está); as versões que
  entram nos templates só se leem depois, do arquivo baixado (abaixo).
- Promova o wrapper, o `settings.gradle{dsl-ext}`, o `.gitignore` e o
  `.gitattributes` à raiz; o resto fica em `{agent-module}/`.
- Reescreva já o `settings.gradle{dsl-ext}`: `rootProject.name` =
  `{project-name}` e os `include` de `buildingBlocks` e `{agent-module}` — não
  há `-api` nem `-core`.
- Leia do `plugins {}` de `{agent-module}/build.gradle{dsl-ext}` as versões
  que o Initializr resolveu — `{boot-version}`,
  `{dependency-management-version}` e, em Kotlin, `{kotlin-version}` — e grave
  [root.gradle.kts.template](./templates/build/kts/root.gradle.kts.template) ou
  [root.gradle.template](./templates/build/groovy/root.gradle.template) como
  `build.gradle{dsl-ext}` da raiz.
- Só depois **substitua** o `build.gradle{dsl-ext}` do módulo por
  [agent-module.gradle.kts.template](./templates/build/kts/agent-module.gradle.kts.template)
  ou [agent-module.gradle.template](./templates/build/groovy/agent-module.gradle.template),
  e grave o `gradle.properties` do fim deste passo: o build do módulo lê a
  versão do LangChain4j de lá.
- Gere o `buildingBlocks` exatamente como o Passo 5 da
  [analizza-new-project](../analizza-new-project/SKILL.md) (templates em
  `../analizza-new-project/templates/buildingBlocks/`), inclusive a
  verificação dele. Ela vem depois dos quatro itens acima de propósito: o
  Gradle configura todos os módulos, e sem o `settings`, o build da raiz, o
  do módulo e o `gradle.properties` no lugar ela falha por outro motivo.
- Confira que a classe de aplicação que o Initializr gerou se chama
  `{app-class}` e está em `{package}`; se o nome for outro, o `{app-class}` é
  o que está no disco.
- **Apague** `{agent-module}/src/test` e
  `{agent-module}/src/main/resources/application.properties` que vieram do
  Initializr. O `contextLoads` dele sobe a aplicação inteira e exigiria as
  variáveis do LLM em todo `build`; o teste de contexto volta como IT no
  Passo 10. E a configuração passa a ser o `application.yaml` do Passo 4.
- Apague também o que o Initializr deixa e este projeto não usa:
  `{agent-module}/HELP.md` e os diretórios vazios `static` e `templates` de
  `{agent-module}/src/main/resources/` (`rmdir`, que só remove se estiver
  vazio). Ficando, o `find -empty` do Passo 4 os conservaria com `.gitkeep` —
  e um `templates/` na raiz do classpath é o que as convenções mandam evitar.
- `git init` agora, **só** se o Passo 0 respondeu `SEM REPOSITORIO` — os
  Passos 7 e 8 dependem de haver um. Com `REPOSITORIO PROPRIO` ele já existe;
  com `DENTRO DE OUTRO REPOSITORIO` vale o que o usuário respondeu lá, e nunca
  um `git init`.

**Existente.** Crie `{agent-module}/` com o `build.gradle{dsl-ext}` do template
da DSL do projeto, acrescente o `include` ao `settings.gradle{dsl-ext}` (depois dos
`include` que já existem, na mesma sintaxe deles) e
confira que a raiz declara, com versão, todo plugin que o módulo aplica sem
versão (`org.springframework.boot`, `io.spring.dependency-management` e, em
Kotlin, `kotlin("jvm")` e `kotlin("plugin.spring")`). Se faltar algum, acrescente
a declaração (`apply false`, com versão) **só** ao build da raiz, depois de
mostrar a mudança ao usuário; nunca edite o build dos módulos do projeto. Se o
projeto gerencia as versões de plugin de um jeito que a skill não sabe seguir
(catálogo de versões, `pluginManagement`), pare e pergunte. A classe de aplicação vem
de `templates/source/{language}/main/__app-class__.*`, copiada no Passo 4 — o
arquivo só existe neste modo (`<!-- arquivo se existente -->`).

A raiz do projeto pode já configurar `test` e registrar `integrationTest` em
todo subprojeto (`subprojects {}`, `allprojects {}`). O template conta com
isso — reaproveita a tarefa e descarta os filtros herdados — e **não deve ser
editado para contornar**; o que ainda escapa está nas
[armadilhas](./references/pitfalls-agent.md).

Nos dois modos, acrescente a `gradle.properties` da raiz (criando o arquivo se
faltar):

```properties
langchain4jVersion={langchain4j-version}
```

### Passo 3 — Conferir as dependências

A versão do LangChain4j não é a de memória desta skill: confira que existe.

```bash
curl -s https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-mcp/maven-metadata.xml | grep -c '<version>{langchain4j-version}</version>'
./gradlew projects --console=plain > /tmp/agent-projects.log 2>&1; echo "EXIT=$?"
./gradlew :{agent-module}:dependencies --configuration runtimeClasspath --console=plain > /tmp/agent-deps.log 2>&1; echo "EXIT=$?"
grep -c 'FAILED' /tmp/agent-deps.log
```

Precisam sair `1`, dois `EXIT=0` e `0`. Se a versão não existir, use a mais
recente da mesma linha, **a mesma para toda a família**, e diga ao usuário.

### Passo 4 — O código do agente

Copie `templates/source/{language}/main/` e `templates/resources/` pela regra
de espelhamento, resolvendo placeholders e marcadores. Depois crie as pastas
das camadas que ficaram vazias, com `.gitkeep`:

```bash
src={agent-module}/src/main/{src-dir}/{package-path}
mkdir -p "$src/domain/rules" "$src/domain/repositories" "$src/domain/services" \
         "$src/infrastructure/repositories" "$src/infrastructure/security" "$src/infrastructure/utils" \
         "$src/presenter/jobs" "$src/presenter/configuration/security"
find {agent-module}/src/main -type d -empty -exec touch {}/.gitkeep \;
```

Com `postgres` e sem `memoria-jdbc`, crie também
`{agent-module}/src/main/resources/db/migration/.gitkeep`: é onde a primeira
migration vai morar.

**Não escreva nada em `domain/`.** E reescreva o
`resources/prompts/system-prompt.prompt` só se o usuário disser o papel do
agente; o que vem do template é neutro de propósito.

O que cada condição muda aqui: `ChatMemoryConfig` só existe com `memoria`;
`V1__chat_memory.sql` só com `memoria-jdbc`; em Java, `ErrorMessage.java` só
com `sem-buildingBlocks` (em Kotlin o tipo fica dentro do
`GlobalExceptionHandler.kt`).

```bash
compile=$([ "{language}" = kotlin ] && echo compileKotlin || echo compileJava)
./gradlew :{agent-module}:$compile --console=plain > /tmp/agent-compile.log 2>&1; echo "EXIT=$?"
grep -c ":{agent-module}:$compile NO-SOURCE" /tmp/agent-compile.log
```

`EXIT=0` e `0`. Outras linhas `NO-SOURCE` no log são normais (por exemplo
`:buildingBlocks:compileJava` num projeto Kotlin). O `grep -c` que conta `0`
sai com status 1: não o encadeie com `&&`.

### Passo 5 — O servidor MCP

O par `{mcp-class}Config` + `{mcp-class}Properties` já veio no Passo 4. O que
muda com a resposta do usuário é só `{mcp-enabled}` e `{mcp-url}` no
`application.yaml` e nos arquivos de ambiente.

Não há o que conectar agora, e isso é intencional: o cliente nasce na primeira
conversa. Sem servidor informado, diga no relatório que o agente conversa só
com o LLM e como ligar depois (`{mcp-env}_ENABLED=true` e `{mcp-env}_BASE_URL`).

### Passo 6 — Banco e memória

- **`postgres`, do zero:** grave
  [o compose da new-project](../analizza-new-project/templates/docker-compose.template)
  como `docker-compose.yml`.
- **`postgres`, existente:** acrescente ao compose do projeto o que está em
  [docker-compose.agent-postgres.template](./templates/root/docker-compose.agent-postgres.template):
  o serviço `postgres-agent` sob `services:` e o volume `postgres-agent-data`
  sob `volumes:` (a linha `# sob volumes:` do template é só a indicação e não
  é copiada). É inserção de texto, na indentação do arquivo, sem reordenar
  o que já está lá; confira com `docker compose config -q`. Sem compose no
  projeto, crie `docker-compose.yml` com as duas chaves. O banco é **do agente** (`{db-name}`, porta `{db-port}`), nunca o
  do projeto hospedeiro. Não renomeie o serviço: o `make run-agent` o sobe pelo nome.
- **`memoria-jdbc`:** a migration `V1__chat_memory.sql` e o `ChatMemoryConfig`
  já vieram no Passo 4. Não mude nome nem tipo de coluna: é o schema que o
  store do LangChain4j espera. O store é criado na **primeira conversa**, não
  na subida — uma tabela ausente aparece como `502` na primeira conversa, com
  o agente de pé (ver [armadilhas](./references/pitfalls-agent.md)).
- **`memoria-processo`:** nada a fazer além do aviso no relatório — a memória
  some a cada restart e não é compartilhada entre réplicas.

### Passo 7 — Ambiente local e observabilidade

De `templates/root/`, para a raiz do projeto:

| Template | Destino | Quando |
|---|---|---|
| `Makefile.template` | `Makefile` | do zero |
| `Makefile.agent-targets.template` | acrescentado ao fim do `Makefile` | existente |
| `local.env.example.template` | `local.env.example` | sempre |
| `local.env.ollama.example.template` | `local.env.ollama.example` | sempre |
| `langwatch.env.example.template` | `langwatch.env.example` | sempre |
| `docker-compose.langwatch.yml.template` | `docker-compose.langwatch.yml` | sempre |
| `gitignore-extra.template` | acrescentado ao fim do `.gitignore` (no existente, pule as linhas que o arquivo já tem, como o bloco do macOS) | sempre |

Receitas do `Makefile` são com **TAB**; copie sem converter em espaço.

O que os alvos fazem, para não descrever errado ao usuário:

- `run-agent` e `run-agent-ollama` checam **primeiro** se o arquivo de
  variáveis existe (`local.env` / `local.env.ollama`) e falham com a instrução
  de `cp` se faltar. Só então, com `postgres`, sobem o banco e esperam ele
  ficar saudável — `docker compose up -d --wait` do zero,
  `docker compose up -d --wait postgres-agent` no existente — e por fim rodam
  o `bootRun`. Nenhum dos dois depende do alvo `db-up`.
- `run-agent-with ENV_FILE=<arquivo>` é a mesma receita com um arquivo de
  variáveis avulso. É o que o smoke do Passo 11 usa, com `local.env.smoke`,
  para nunca escrever no `local.env.ollama` do usuário.
- Do zero: `run-agent`, `run-agent-ollama`, `run-agent-with`, `build`,
  `build-backend`, `test-backend`, `clean`, `help`, `langwatch-up`,
  `langwatch-down`, `langwatch-logs`; com `postgres`, `db-up`, `db-down`,
  `db-reset`; com `web`, `install`, `build-web`, `test-web`,
  `run-web` e `run` (agente contra o Ollama local + web); com `it-no-modulo`,
  `test-integration`. Em `it-dedicado` quem acrescenta o `test-integration` é
  a `analizza-integration-test`, no Passo 10.
- Existente: `run-agent`, `run-agent-ollama`, `run-agent-with`, `test-agent`,
  `test-agent-integration`, `langwatch-up`, `langwatch-down`, `langwatch-logs`.

No modo existente, se o `Makefile` já tiver um alvo com o mesmo nome, **não
sobrescreva**: mostre o conflito e pergunte. Sem `Makefile` no projeto, crie um
só com o trecho. Se o compose do projeto não for o arquivo padrão do
`docker compose`, acrescente o `-f <arquivo>` à linha do `postgres-agent`.

```bash
# no existente so o trecho acrescentado conta: as receitas que ja eram do projeto nao provam nada
inicio=$([ "{mode}" = existente ] && echo '/^##@ Agente/' || echo 1)
[ "$(sed -n "$inicio,\$p" Makefile | grep -c $'^\t')" -ge 10 ] && echo "TAB OK" || echo "TAB FALHOU"
for f in local.env local.env.ollama local.env.smoke langwatch.env; do git check-ignore -q "$f" || echo "NAO IGNORADO: $f"; done
```

`TAB OK` e nenhuma linha `NAO IGNORADO`.

### Passo 8 — Web (só `web`)

A pasta precisa estar num repositório Git **antes** — senão o
`create-next-app` cria um `.git` aninhado e o módulo entra como gitlink (ver
[armadilhas da new-project](../analizza-new-project/references/pitfalls.md)).
O `git init` é o do Passo 2, decidido pelo Passo 0; a primeira linha abaixo só
confere, e não cria nada:

```bash
git rev-parse --show-toplevel > /dev/null 2>&1 || echo "SEM REPOSITORIO: volte ao Passo 0"
npx --yes create-next-app@latest {project-name}-web \
  --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
[ -d {project-name}-web/.git ] && echo "ATENÇÃO: .git aninhado"
```

O `create-next-app` atual gera também `AGENTS.md` e `CLAUDE.md` dentro de
`{project-name}-web/` (em algumas versões só o `AGENTS.md`): são dele, valem só
para aquela pasta e ficam como vieram.

Copie `templates/web/src/` sobre `{project-name}-web/src/`, substituindo o
`page.tsx` — **menos os três `*.test.ts`**, que entram no Passo 10. Eles
importam `vitest`, que ainda não está instalado, e o `next build` checa os
tipos de todo `.ts` de `src/`: copiados agora, quebram o build abaixo.

São quatro arquivos neste passo: `app/page.tsx`, `app/api/chat/route.ts`,
`lib/sse.ts` e `lib/conversation.ts`. Em `page.tsx` o **único** placeholder é
`{project-name}`: o resto entre chaves é JSX e fica como está. Em `route.ts` é
`{agent-port}`.

```bash
cd {project-name}-web && npm run lint && npm run build; echo "EXIT=$?"
```

### Passo 9 — Convenções, runbook e README

Detecte o framework de SDD e o arquivo de destino por
[sdd-frameworks.md](../analizza-new-project/references/sdd-frameworks.md). O
resumo de `context:` que ela mostra para o OpenSpec descreve o monorepo da
`analizza-new-project`; aqui ele descreve os módulos deste projeto.

- **Do zero:** grave
  [architecture-conventions.md.template](./templates/architecture-conventions.md.template)
  — que abre com `## Arquitetura` — e, logo depois, a seção de
  [agent-conventions.md](./references/agent-conventions.md), que abre com
  `### Agente` e fica dentro dela. Sem framework detectado, **pergunte** o
  destino, como a referência manda, sugerindo `docs/INSTRUCTIONS.md`; aceito
  o sugerido, crie-o com o título `# Instruções do projeto`.
- **Existente:** acrescente só a seção de `agent-conventions.md`, no **fim**
  de `## Arquitetura` se ela existir — imediatamente antes da próxima `##`,
  ou no fim do arquivo se não houver outra —, senão no fim do arquivo. **Nunca
  sobrescreva** o que o arquivo já tem; se já houver um `### Agente`, é
  segunda execução: substitua só essa seção.

**`### Agente` é sempre a última seção de `## Arquitetura`.** Toda seção
`###` que entrar depois dela no tempo — as três que a
`analizza-integration-test` acrescenta no Passo 10 (`### Variáveis de
ambiente`, `### Checkpoints de conferência`, `### Débitos técnicos`) — é
inserida imediatamente **antes** de `### Agente`, nunca no fim do arquivo,
onde ficaria pendurada depois das subseções `####` do agente.

Grave [runbook-agent-chat.md](./references/runbook-agent-chat.md) como
`docs/checkpoints/agent-chat.md`. Depois de tirar os marcadores, a primeira
linha do arquivo é o `---` do frontmatter.

Grave a seção de [readme-env-vars.md](./references/readme-env-vars.md) — abre
com `## Variáveis de ambiente` — no `README.md` da raiz, criando-o com o
título `# {project-name}` se não existir. Ela lista, **sem valor**, toda
variável que o `application.yaml` lê. Nos dois modos e em todo layout: as
regras de projeto que a `analizza-integration-test` grava exigem essa seção,
e nem ela nem outra skill a escrevem. No modo existente a seção entra no README do
hospedeiro (criada se não houver, e listada no Passo 12); se ele já tiver
uma seção com esse título, não a substitua: a tabela entra dentro dela, sob
um subtítulo `### {agent-module}`. Confira que nenhuma variável ficou de fora:

```bash
for v in $(grep -oE '\$\{[A-Z][A-Z0-9_]*' {agent-module}/src/main/resources/application.yaml | tr -d '${' | sort -u); do
  grep -q "\`$v=\`" README.md || echo "FALTA NO README: $v"
done
```

Nenhuma linha `FALTA NO README`.

Os três arquivos de `references/` levam placeholders e marcadores, como
qualquer template. **Conferência de sobras** — sobre tudo o que a skill
gravou, não só sobre eles:

```bash
nomes='project-name|base|agent-module|app-class|package|base-package|bb-package|package-path|group|java-version|mode|language|src-dir|dsl-ext|boot-version|dependency-management-version|kotlin-version|agent-port|mcp-name|mcp-class|mcp-env|mcp-url|mcp-enabled|db-name|db-port|langchain4j-version|it-module'
grep -rnE "<!-- (se|fim se|arquivo se) |(^|[^\$\{]|\$\{)\{($nomes)\}" \
  --exclude-dir=node_modules --exclude-dir=build --exclude-dir=.next \
  --exclude-dir=.git --exclude-dir=.gradle <onde>
```

`<onde>` é `.` do zero; no modo existente, só o que a skill escreveu:
`{agent-module} <arquivo do SDD> docs/checkpoints/agent-chat.md README.md
Makefile local.env.example local.env.ollama.example langwatch.env.example
docker-compose.langwatch.yml gradle.properties .gitignore` e, com `postgres`,
o compose do projeto (`docker-compose.yml`) — ali, linha em trecho que já era
do projeto hospedeiro não é sobra. Nenhuma linha. A lista em `nomes` é a tabela
do Vocabulário, nome a nome, e fica **sem** substituição: é ela que deixa
passar as chaves legítimas (JSX, `${VAR}`, `{{userInput}}`, o `{}` de log) e
ainda pega placeholder de uma palavra só, como `{package}` ou `{group}`. A
alternativa `\$\{` do padrão existe para o placeholder **dentro** de um
`${…}` do Spring: sem ela, um `${{mcp-env}_ENABLED:…}` que sobrasse no
`application.yaml` passaria despercebido.

### Passo 10 — Testes

**Unitários.** Copie `templates/source/{language}/test/`.

```bash
./gradlew :{agent-module}:test --console=plain > /tmp/agent-test.log 2>&1; echo "EXIT=$?"
grep -ho '<testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' {agent-module}/build/test-results/test/*.xml
grep -ho '<testsuite [^>]*' {agent-module}/build/test-results/test/*.xml | grep -oE ' tests="[0-9]+"' | grep -oE '[0-9]+' | paste -sd+ - | bc
ls {agent-module}/build/test-results/test/ | grep -c 'IT\.xml$'
```

Exija `EXIT=0` e leia a contagem no XML, não no `BUILD SUCCESSFUL`: cinco
suítes, `failures="0" errors="0"`, somando **39 testes com memória, 37 sem**
(`ChatHandlerTest` 13, `ChatRouteTest` 11, `ConversationIdsTest` 4,
`LazyMcpToolProviderTest` 5, `AssistantAiServiceTest` 6 — ou 4 em
`sem-memoria`), e `0` suítes `*IT`. **`EXIT=0` com soma diferente é falha**:
menos testes (ou nenhum XML) é filtro herdado do projeto hospedeiro
escondendo classes; um `*IT` aqui é o `test` subindo container.

**Integração, `it-dedicado`.** Avise o usuário antes: a primeira execução dos
ITs baixa cerca de 2 GB (imagem do Ollama e modelo) e a inferência em CPU leva
minutos. Então invoque a skill
[analizza-integration-test](../analizza-integration-test/SKILL.md):

```
escopo=ambos|backend linguagem={language} banco=postgres layout=dedicado
```

`ambos` se houver web. Quatro coisas mudam em relação ao que ela faria sozinha:

1. **Não crie dublê para nada sob `anticorruptionLayer/llm`** (`Assistant` e
   `llm/impl/AssistantAiService`) quando ela chegar ao `TestConfig`: o
   `{doubles}` dele fica vazio neste módulo. Ela cria dublê para interface de
   saída *sem container*, e o LLM tem: o Ollama. O IT existe para exercitar o
   LLM de verdade; um dublê `@Primary` faria o `ChatRouteIT` passar sem chamar
   LLM nenhum.
2. **Antes da verificação dela** (o passo "Verificar", que roda
   `./gradlew integrationTest`), aplique
   [it-llm-layer.md](./references/it-llm-layer.md), trocando `{mcp-name}` nos
   dois trechos de código pelo nome do servidor MCP do projeto. Sem a camada,
   a verificação dela falha duas vezes: o contexto do `ApplicationContextIT`
   não sobe sem `LLM_*`, e a regra ArchUnit acusa a `ChatRoute` sem
   `ChatRouteIT`.
3. Do `templates/source/{language}/it/` só entram `support/OllamaTestContainer`
   e `presenter/routes/chat/ChatRouteIT`; a base é a que ela gerou (o
   `BaseIntegrationTest` do template é `<!-- arquivo se it-no-modulo -->`).
4. **O Pitest dela precisa de uma linha a mais.** Ela instala o Pitest no
   módulo de produção que tem a lógica — o `{mutation-module}` dela, que aqui
   é o `{agent-module}`: sem `-core`, é o único com `application/` e
   `domain/`. Em Boot 4 o plugin injeta um `junit-platform-launcher` mais
   velho que o JUnit do BOM, e `./gradlew :{agent-module}:test` passa a
   falhar com `OutputDirectoryCreator not available; probably due to
   unaligned versions`. Logo depois de ela mesclar o bloco `pitest {}` no
   build do `{agent-module}`, acrescente dentro dele
   `addJUnitPlatformLauncher = false` (a linha é a mesma em `.kts` e em
   Groovy; o módulo já declara o launcher como `testRuntimeOnly`) e rode de
   novo os unitários acima, **antes** da verificação dela. É débito da skill
   irmã, não deste scaffold — ver [armadilhas](./references/pitfalls-agent.md).

**Integração, `it-no-modulo`.** Copie `templates/source/{language}/it/` para
dentro do `{agent-module}` — os três arquivos (`ChatRouteIT`,
`support/BaseIntegrationTest`, `support/OllamaTestContainer`). A `analizza-integration-test`
**não** é invocada para o backend: a base de teste dela exige um container de
banco (não serve a um módulo sem Postgres) e, no modo existente, invocá-la
reescreveria a configuração de teste do projeto hospedeiro, que esta skill não
pode tocar. Consequência a relatar: sem regra ArchUnit,
JaCoCo e Pitest para o agente. Havendo web, invoque-a com `escopo=frontend`.

Se o host já tem módulo dedicado de ITs com regra ArchUnit própria ("todo
entrypoint tem IT"), os ITs do agente ainda ficam no `{agent-module}`
(`it-no-modulo`) e o módulo do host não é tocado: a regra dele não enxerga o
agente (que não está no classpath daquele módulo), então nem falha nem protege.
Relate isso no Passo 12.

**Web (só `web`).** Depois que a `analizza-integration-test` instalar o Vitest
no `{project-name}-web`, copie os três testes que ficaram de fora no Passo 8
— `app/api/chat/route.test.ts`, `lib/sse.test.ts`, `lib/conversation.test.ts` —
e rode:

```bash
cd {project-name}-web && npx vitest run; echo "EXIT=$?"
```

`EXIT=0`, com **16 testes** nesses três arquivos (5, 8 e 3), mais o
`page.test.tsx` que ela gerou. Se o `npm install` do Vitest falhar com
`ERESOLVE`, veja [armadilhas](./references/pitfalls-agent.md) — nunca
`--legacy-peer-deps`.

**O que a `analizza-integration-test` grava além dos testes.** Toda invocação
dela, inclusive a de `escopo=frontend`, também mexe na raiz. É esperado —
aceite, com estas regras:

- **`Makefile`.** Os alvos dela substituem os nossos de mesmo nome
  (`test-backend`; `test-web`, que deixa de ser só lint e passa a rodar lint,
  typecheck e Vitest) e entram `test`, `test-integration` e `test-mutation`.
  Mantenha a nossa `GRADLEW := ./gradlew`, o nosso `WEB_DIR` e a nossa regra
  `$(WEB_DIR)/node_modules` (a que depende do `package-lock.json`). Nada de
  mobile: sem `MOBILE_DIR`, sem `test-mobile`, nem no `test`. O
  `test-mutation` roda `$(GRADLEW) :{agent-module}:pitest`. Com
  `escopo=frontend` os alvos de backend continuam os nossos: o
  `test-integration` dela rodaria `integrationTest` sem o prefixo do módulo,
  e não há Pitest para um `test-mutation`.
- **`CLAUDE.md`** da raiz (o bloco *O que "pronto" inclui*), a seção *Testes*
  do **`README.md`** — a *Variáveis de ambiente* do Passo 9 fica como está —,
  **`docs/checkpoints/README.md`** e a skill local
  **`.claude/skills/test-runbook/`**.
- **Arquivo do SDD.** Com backend no escopo, ela troca o corpo de
  `### Testes` pelo dela; o parágrafo final, que aponta para *Testes do
  agente*, continua depois do corpo novo. Nada próprio de agente se perde: o
  que é de agente mora em `### Agente`, que ela não toca. Em todo escopo ela
  acrescenta as três seções de regras de projeto — **antes** de `### Agente`
  (Passo 9).

### Passo 11 — Verificar

Obrigatório. Sem isso não há como afirmar que o agente funciona.

```bash
if [ "{mode}" = existente ]; then
  ./gradlew :{agent-module}:build --console=plain > /tmp/agent-build.log 2>&1; echo "EXIT=$?"
else
  make build > /tmp/agent-build.log 2>&1; echo "EXIT=$?"
fi
# em todo layout (it-dedicado ou it-no-modulo), só o módulo dos ITs:
./gradlew :{it-module}:integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
grep -ho '<testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' \
  {it-module}/build/test-results/integrationTest/*.xml
find {it-module}/build/test-results/integrationTest -name '*.xml' 2>/dev/null | wc -l
# unitários (já lidos no Passo 10): {agent-module}/build/test-results/test/*.xml
```

No modo existente o `make build` não serve (pode não existir ou construir os
módulos do host e o web), por isso o bloco o evita. Nunca rode `integrationTest` sem o
prefixo do módulo, que executaria também os ITs do projeto hospedeiro.

O `build` não precisa de banco, de LLM nem de Docker: os unitários usam LLM
roteirizado e os ITs ficam fora dele. Nos ITs, exija `EXIT=0`,
`failures="0" errors="0"` e o `ChatRouteIT` com `tests="3"`; em `it-dedicado`,
também `ApplicationContextIT` e `EntrypointHasIntegrationTestIT`.

**Zero testes de integração executados é FALHA, mesmo com `EXIT=0`.** Sem a
linha do `ChatRouteIT` com `tests="3"` — nenhum XML, o `wc -l` em `0`, a tarefa
terminando em segundos — nada foi testado: alguma configuração herdada
filtrou as classes (ver [armadilhas](./references/pitfalls-agent.md)). Não
siga para o smoke nem relate verde.

Avise o usuário **antes** de rodar os ITs, se ainda não avisou: a primeira
execução baixa cerca de 2 GB e a inferência em CPU leva minutos.

Smoke com LLM de verdade. O smoke **nunca lê, escreve nem apaga
`local.env.ollama`**: o arquivo é do usuário, é git-ignored (apagado, não
volta) e pode guardar a credencial de `{mcp-env}_AUTHORIZATION`. Ele usa um
arquivo só dele, `local.env.smoke` — gerado do `.example`, apontando para a
imagem que os ITs acabaram de gravar e com o servidor MCP desligado (é outro
sistema e pode não estar no ar) — e o alvo `run-agent-with`.

Antes de subir, as portas precisam estar **livres**. Com outra aplicação na
`{agent-port}`, o `bootRun` falharia e o `curl` de saúde seria respondido por
ela: o smoke passaria a medir, e depois a encerrar, o processo errado.

```bash
rm -f /tmp/agent-smoke.pid
ocupadas=""
for p in {agent-port} 11435; do
  lsof -nP -iTCP:$p -sTCP:LISTEN > /dev/null 2>&1 && ocupadas="$ocupadas $p"
done
if [ -n "$ocupadas" ]; then
  echo "SMOKE ABORTADO: porta em uso:$ocupadas"
else
  docker run -d --rm --name agent-smoke-ollama -p 127.0.0.1:11435:11434 tc-ollama-qwen2.5-3b
  sed -e 's#localhost:11434#localhost:11435#' -e 's#qwen2.5:7b#qwen2.5:3b#' \
      -e 's#^{mcp-env}_ENABLED=.*#{mcp-env}_ENABLED=false#' local.env.ollama.example > local.env.smoke
  make run-agent-with ENV_FILE=local.env.smoke > /tmp/agent-run.log 2>&1 &
  echo $! > /tmp/agent-smoke.pid
  for i in $(seq 90); do curl -sf http://localhost:{agent-port}/actuator/health > /dev/null 2>&1 && break; sleep 2; done
  if kill -0 "$(cat /tmp/agent-smoke.pid)" 2> /dev/null && grep -q 'Started {app-class}' /tmp/agent-run.log; then
    echo "SMOKE PRONTO"
  else
    echo "SMOKE FALHOU: leia /tmp/agent-run.log"
  fi
fi
```

- **`SMOKE ABORTADO`** — nada foi iniciado. Mostre ao usuário quem segura a
  porta (`lsof -nP -iTCP:<porta> -sTCP:LISTEN`) e pergunte; **não mate** o
  processo. O smoke fica por fazer e o relatório diz isso.
- **`SMOKE FALHOU`** — o `make` morreu ou o log não traz a linha de subida
  deste agente: leia `/tmp/agent-run.log`, rode o encerramento abaixo e
  reporte. Não siga para as conversas.
- **`SMOKE PRONTO`** — o `make` que o smoke abriu está vivo e foi **este**
  agente que subiu. Só então converse:

```bash
curl -s -D - --max-time 300 -X POST http://localhost:{agent-port}/api/v1/agent/http \
  -H 'Content-Type: application/json' -H 'X-Conversation-Id: smoke-1' -d '{"body":"Diga oi."}'
curl -s -N --max-time 300 -X POST http://localhost:{agent-port}/api/v1/agent/stream \
  -H 'Content-Type: application/json' -d '{"body":"Diga tchau."}'
curl -s http://localhost:{agent-port}/actuator/prometheus | grep '^chat_requests_total'
```

Precisa vir `200` com o header `X-Conversation-Id: smoke-1` ecoado e
`response` não vazio, linhas `data:` até o fluxo acabar sozinho, e
`chat_requests_total{outcome="success"}` valendo `2.0` — as duas conversas.
O header só é ecoado quando o cliente o manda: o `curl` do `/stream` acima
não manda, e a resposta dele vem sem `X-Conversation-Id`.
**Não corte o SSE** (`| head`, Ctrl+C): fechar a conexão no meio do fluxo é
contado como `outcome="failure"`, e a métrica passa a parecer defeito. Uma
série `failure` aqui é isso ou uma conversa que falhou de verdade — nos dois
casos, leia `/tmp/agent-run.log`. Com `postgres`, o próprio
`make run-agent-with` sobe o banco.

O `local.env.smoke` herda `SPRING_PROFILES_ACTIVE=dev` do `.example`: o smoke
roda no profile `dev` porque o arquivo manda, não porque seja o padrão — sem a
variável não há profile ativo (ver as convenções).

Sem o LangWatch no ar, o log traz `ERROR … Failed to export spans` de tempos
em tempos (o exporter OTLP não alcança `localhost:5560`). É esperado e não é
falha do agente: ao procurar erro no log, desconte essas linhas. Em Java 24+
também são esperadas as linhas `WARNING: A restricted method in
java.lang.System has been called`, do Netty (ver
[armadilhas](./references/pitfalls-agent.md)).

Encerre **só o que o smoke abriu** — a árvore do `make` cujo PID ficou em
`/tmp/agent-smoke.pid`, o container `agent-smoke-ollama` e o `local.env.smoke`
— e confirme que nada sobrou. O bloco serve também depois de `SMOKE ABORTADO`
ou `SMOKE FALHOU`: sem o arquivo de PID ele não mata nada.

```bash
arvore() { for f in $(pgrep -P "$1"); do arvore "$f"; done; echo "$1"; }
if [ -s /tmp/agent-smoke.pid ]; then
  kill $(arvore "$(cat /tmp/agent-smoke.pid)") 2> /dev/null
  rm -f /tmp/agent-smoke.pid
fi
docker stop agent-smoke-ollama
rm -f local.env.smoke
# so com postgres -- do zero: make db-down
#                    existente: docker compose stop postgres-agent   (so o servico do agente)
for i in $(seq 15); do lsof -nP -iTCP:{agent-port} -sTCP:LISTEN > /dev/null 2>&1 || break; sleep 2; done
lsof -nP -iTCP:{agent-port} -sTCP:LISTEN; pgrep -fl '[:]{agent-module}:bootRun'; echo "encerrado se nada acima"
```

A árvore é o `make`, o `bash` da receita e o cliente do `gradlew`. A JVM do
agente não é filha deles — quem a lança é o daemon do Gradle —, mas morre
junto: sem o cliente, o daemon cancela o build e encerra o que ele abriu. O
laço espera isso (o desligamento é gracioso e leva alguns segundos).

**Nunca `lsof -ti tcp:{agent-port} | xargs kill`, nem `pkill` por nome:**
matam quem estiver na porta, seja ou não o que o smoke abriu. Se depois do
laço ainda houver alguém escutando na `{agent-port}`, mostre a linha do `lsof`
ao usuário e pergunte, em vez de matar.

O daemon do Gradle continua vivo, ocioso, e sai sozinho depois de umas horas
sem uso. `./gradlew --stop` o encerra, mas **não faz parte do encerramento**:
derruba todo daemon dessa versão do Gradle na máquina, inclusive o de outro
projeto que o usuário tenha aberto, com o build dele no meio. Só a pedido, e
dizendo isso. Com `postgres`, confira também a porta `{db-port}`
(`lsof -nP -iTCP:{db-port} -sTCP:LISTEN`; uma porta por comando).

**No modo existente, só o que é do agente é encerrado — sempre pelo nome do
serviço.** `docker compose stop postgres-agent` para o banco e conserva os
dados: o container parado e o volume **ficam em disco por desenho**, e o
relatório diz isso. Para apagar só eles, se o usuário pedir:
`docker compose rm -sf postgres-agent` e `docker volume rm <projeto>_postgres-agent-data`
(`<projeto>` é o nome do projeto do compose, em geral a pasta; o nome exato sai
de `docker volume ls | grep postgres-agent-data`). **Nunca** rode nem sugira
`docker compose down`, `down -v`, `stop` ou `rm` sem o nome do serviço, nem
`docker volume prune`: derrubam os containers e apagam os volumes do projeto
hospedeiro, o banco dele inclusive. Os alvos `db-down` e `db-reset` que o
`Makefile` do projeto já tinha são dele, não do agente.

**Auditoria e commit.** Só com tudo acima verde. Repita antes a conferência
de sobras do Passo 9: os testes entraram depois dela.

*Do zero, em pasta que estava vazia e com `REPOSITORIO PROPRIO` no Passo 0* —
audite o que vai entrar e faça **um** commit para o scaffold. São dois blocos,
de propósito: o primeiro só mostra, o segundo só commita se a auditoria passar.

```bash
raiz=$(git rev-parse --show-toplevel 2> /dev/null)
if [ -n "$raiz" ] && [ "$(cd "$raiz" && pwd -P)" = "$(pwd -P)" ]; then
  git add -A
  git diff --cached --name-only | grep -cE '(^|/)(node_modules|\.next|build)/'
  git ls-files --stage | grep -c '^160000'
  git diff --cached --name-only | grep -cE '(^|/)(local\.env|local\.env\.ollama|local\.env\.smoke|langwatch\.env)$'
else
  echo "NAO E A RAIZ DE UM REPOSITORIO PROPRIO: nada foi adicionado"
fi
```

Os três `grep` precisam devolver `0`. O primeiro pega saída de build e
dependência instalada. O segundo pega gitlink: se o `{project-name}-web`
aparecer assim, o `.git` aninhado do Passo 8 passou — remova-o, rode
`git rm -r --cached {project-name}-web` e o bloco de novo. O terceiro pega
arquivo de ambiente com valor real. `NAO E A RAIZ…` é o caso do Passo 0 que
não commita: pare aqui e siga pelo parágrafo seguinte.

O commit refaz a auditoria em vez de confiar na leitura acima — copiado
sozinho, ou depois de um `grep` que não deu `0`, ele recusa:

```bash
raiz=$(git rev-parse --show-toplevel 2> /dev/null)
sobras=$( { git diff --cached --name-only | grep -E '(^|/)(node_modules|\.next|build)/|(^|/)(local\.env|local\.env\.ollama|local\.env\.smoke|langwatch\.env)$'
            git ls-files --stage | grep '^160000'; } | wc -l | tr -d ' ')
if [ -n "$raiz" ] && [ "$(cd "$raiz" && pwd -P)" = "$(pwd -P)" ] && [ "$sobras" = 0 ]; then
  git commit -q -m "Scaffold do agente {project-name}" && git log --oneline -1
else
  echo "COMMIT RECUSADO: auditoria com $sobras linha(s), ou a pasta nao e a raiz de um repositorio proprio"
fi
```

*Modo existente, do zero em pasta que já tinha arquivos, ou do zero dentro de
outro repositório (Passo 0)* — antes, confirme
`grep -c '^## Variáveis de ambiente' README.md` (deve dar `1` ou mais). **Não commite**
nem rode `git add`: mostre o `git status --short` ao usuário e deixe o commit
com ele. O repositório é dele, e a skill não sabe o que mais está em
andamento ali.

### Passo 12 — Relatar

- O modo detectado, a linguagem, o conjunto de condições, e as versões reais
  (Boot, Java, LangChain4j e, com `web`, Next) — **lidas dos arquivos**
- No modo existente com `sem-buildingBlocks`: o motivo (módulo ausente ou
  qual contrato divergiu) e que o agente tem o próprio `ErrorMessage` e não
  implementa os contratos do projeto
- Os `EXIT=` e as contagens de teste observados, unitários e de integração
- Quando a `analizza-integration-test` rodou: o que ela criou (módulo de
  ITs, `CLAUDE.md`, `README.md`, `docs/checkpoints/README.md`,
  `.claude/skills/test-runbook/`, alvos do `Makefile`) e, com backend no
  escopo, o mutation score do `{agent-module}` com as classes de mutantes
  sobreviventes, e que foi preciso `addJUnitPlatformLauncher = false` no
  bloco `pitest {}` — débito da skill irmã
- O que ficou **desligado** e como ligar: servidor MCP, memória, web
- Com `memoria-processo`: que a memória some a cada restart
- Com `memoria-jdbc`: que uma tabela `chat_memory` ausente aparece como `502`
  na primeira conversa, não na subida
- No modo existente com `{base}-mcp`: que falta a credencial em
  `{mcp-env}_AUTHORIZATION`, se o servidor for protegido
- Em `it-no-modulo`: que o agente ficou sem ArchUnit, JaCoCo e Pitest; no
  existente com módulo de ITs próprio, que a regra ArchUnit do host não vê o agente
- No modo existente: que o container e o volume do `postgres-agent` ficam em disco
- Quando a `analizza-integration-test` não rodou para o backend (todo
  `it-no-modulo` sem web e todo o modo existente, salvo projeto que já os tenha):
  que `docs/checkpoints/README.md` e a skill `test-runbook` não foram
  instalados, então o runbook `docs/checkpoints/agent-chat.md` ficou sem quem o
  conduza; o usuário instala com a skill `test-runbook`
- Que o primeiro IT baixa ~2 GB e que os ITs ficam fora do `build`
- Que o endpoint de chat nasce **sem autenticação** — e, com o id da conversa
  escolhido pelo cliente, quem souber um id lê a memória daquela conversa
- Que **nenhum profile é ativo por padrão**: o conteúdo das conversas só vai
  para os traces com `SPRING_PROFILES_ACTIVE=dev`, que os `local.env*.example`
  definem; um deploy que não define a variável sobe sem conteúdo nos traces,
  e o `prod` ainda baixa a amostragem e o log
- Onde as convenções e o runbook foram gravados, e que o `README.md` (no
  existente, o do hospedeiro) ganhou a seção `## Variáveis de ambiente`; o resto
  do README dele (como subir, tabela de testes) não cita o agente
- O commit do scaffold (do zero) ou, no modo existente, que **nada foi
  commitado** e o `git status` ficou para o usuário
- O que **não** foi conferido — a tela no navegador, o trace no LangWatch — em
  vez de afirmar que funciona. Entre o que não foi conferido, sempre: **o
  caminho feliz do MCP**. Este scaffold não foi exercitado contra um servidor
  MCP de verdade pela própria skill — nem aqui (o smoke e os ITs rodam com o
  servidor desligado), nem quando a skill foi escrita: o que tem teste é o
  `502` com o servidor fora e o fluxo de tool com um provedor de mentira. Tool
  chamada com o servidor no ar, o header `Authorization` aceito e a reconexão
  depois de um restart ficam para o runbook (`docs/checkpoints/agent-chat.md`)
- Se o smoke foi abortado por porta em uso: qual porta, e que ele ficou por fazer

## Fora de escopo

Mobile, multi-agente, A2A, gateway de LLM, Dockerfile e CI/CD do agente.

Autenticação do endpoint de chat e propagação da identidade do usuário até o
servidor MCP: a forma está nas convenções, o código não sai do scaffold.

Tools: a skill entrega o **cliente** MCP. Quais tools existem e o que cada uma
devolve ao modelo é decisão de quem conhece o domínio — na
`analizza-add-mcp-module` e no runbook.

## Notas

- Ver [armadilhas do agente](./references/pitfalls-agent.md) antes de depurar
  qualquer coisa de LangChain4j, SSE, Vitest ou Testcontainers.
- O `{agent-module}` leva `spring-boot-starter-jdbc`, não `data-jpa`: nasce sem
  entidade. Quem escrever a primeira troca o starter.
- O web fala com o agente por route handler (`/api/chat`), então o agente não
  precisa de CORS. O id da conversa é gerado no navegador, um por carregamento
  de página.
