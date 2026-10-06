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
├── {base}-api/                         intocado
├── {base}-core/                        intocado
├── {base}-mcp/                         vira o servidor MCP padrão, se existir
├── {agent-module}/                     app próprio, porta própria
├── docker-compose.langwatch.yml
├── local.env*.example
└── Makefile                            + alvos do agente
```

Do zero **não existe `-core`**: `presenter/`, `application/`, `domain/` e
`infrastructure/` são pacotes do `{agent-module}`. No projeto existente o
agente é uma aplicação Spring Boot própria, que **não depende do `-core` nem do
`-api`**: o que ele sabe do domínio, sabe por MCP.

## Quando usar

- Agente conversacional novo, do zero, em Java ou Kotlin
- Acrescentar um agente a um projeto Gradle multi-módulo com Spring Boot 4.x
- **Não** use para monorepo `-api` + `-core` sem agente — essa é a `analizza-new-project`
- **Não** use para expor o domínio como tools — essa é a `analizza-add-mcp-module`; o agente **consome** o que ela cria

## Vocabulário

| Placeholder | Valor |
|---|---|
| `{project-name}` | nome da pasta raiz (do zero) ou `rootProject.name` (existente) |
| `{base}` | só no modo existente: o prefixo dos módulos que já existem (`{base}-api`, `{base}-core`), em geral o próprio `{project-name}` |
| `{agent-module}` | módulo do agente — pergunta |
| `{app-class}` | PascalCase de `{agent-module}` + `Application` (`demo-agent` → `DemoAgentApplication`) |
| `{package}` | pacote base do projeto |
| `{base-package}` | pacote raiz do agente: `{package}` do zero, `{package}.agent` no existente |
| `{bb-package}` | pacote do `buildingBlocks`: `{package}` |
| `{package-path}` | `{base-package}` com `.` trocado por `/` |
| `{group}`, `{java-version}` | perguntados (do zero) ou lidos do build (existente) |
| `{language}`, `{src-dir}` | `kotlin` ou `java` — o mesmo valor nos dois |
| `{dsl-ext}` | `.kts` ou vazio |
| `{boot-version}`, `{dependency-management-version}`, `{kotlin-version}` | só do zero: lidas do `plugins {}` que o Initializr gerou (Passo 2). `{kotlin-version}` só em Kotlin |
| `{agent-port}` | `8080` do zero; `8081` no existente, ou a seguinte se o `-api` já a usa |
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
`templates/` e também `references/agent-conventions.md` e
`references/runbook-agent-chat.md`.

| Condição | Vale quando |
|---|---|
| `kotlin` / `java` | linguagem do fonte |
| `do-zero` / `existente` | o modo |
| `postgres` / `sem-postgres` | o agente tem banco |
| `memoria` / `sem-memoria` | o usuário quis memória de conversa |
| `memoria-jdbc` | `memoria` e `postgres` |
| `memoria-processo` | `memoria` e `sem-postgres` |
| `buildingBlocks` / `sem-buildingBlocks` | o projeto tem o módulo `buildingBlocks`. Do zero vale sempre; no existente, detecte (Passo 1) |
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

Sem Docker a skill ainda gera o projeto, mas não verifica: os ITs e o banco
dependem dele. Avise antes de seguir.

**Existente** — confirme Spring Boot 4.x antes de seguir:

```bash
grep -rhoE "org\.springframework\.boot[\"')]*[[:space:]]+version[[:space:]]+[\"'][0-9]+" --include='build.gradle*' . | sort -u
find . -name 'libs.versions.toml' -not -path '*/build/*' -exec grep -nE "spring-?boot|springBoot|^[[:space:]]*boot[[:space:]]*=" {} +
```

Boot 3.x: **pare e diga** que os starters `langchain4j-*-spring-boot4-*`
exigem Boot 4. Nada detectado: pergunte a versão e só siga com 4.x confirmado.

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
| `group`, `package`, `java-version` | pergunta; `br.com.analizza`, `{group}.{project-name}`, `25` | lê do build e do pacote da aplicação |
| `agent-module` | pergunta; padrão `{project-name}-agent` | pergunta; padrão `{base}-agent` |
| `web` | pergunta; padrão sim | não oferece |
| `postgres` | pergunta; padrão sim | pergunta; padrão não |
| `chat-memory` | pergunta; padrão sim | pergunta; padrão sim |
| `mcp-name` e `mcp-url` | pergunta; pode ficar vazio | padrão: `{base}-mcp` e `http://localhost:<porta do -api>/mcp`, se o módulo existir |

Pacote não aceita `-`: se `{project-name}` tiver hífen, o padrão
`{group}.{project-name}` não serve — pergunte o pacote em vez de assumir.

**Nome do módulo.** Se `{project-name}` já termina em `-agent`, diga que o
padrão ficaria redundante (`x-agent-agent`) e ofereça
`{project-name}-assistant` — sem decidir sozinho.

**Java tem piso de versão: 17.** Os templates usam `record` e pattern matching.

**Servidor MCP no modo existente.** Procure o módulo e a porta do `-api`:

```bash
grep -E "include.*-mcp" settings.gradle*
grep -rhE "server\.port|^\s*port:" --include='application*.properties' --include='application*.y*ml' . | head
```

Um servidor criado pela `analizza-add-mcp-module` é protegido: avise que o
agente vai precisar de uma credencial em `{mcp-env}_AUTHORIZATION` e que, sem
ela, as conversas devolvem `502`.

**`buildingBlocks` no modo existente.** A condição vale se o módulo existe com
este nome exato e traz os dois contratos que os templates importam:

```bash
grep -E "include.*buildingBlocks" settings.gradle*
find buildingBlocks/src/main \( -name 'ResultCommandHandler.*' -o -name 'ErrorMessage.*' \)
```

`{bb-package}` é o pacote desses arquivos **sem** o sufixo `.application` /
`.presenter.exception`. Faltando o módulo ou um dos dois, vale
`sem-buildingBlocks` — a skill não cria `buildingBlocks` em projeto existente.

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
  módulo, não do Initializr.
- Promova o wrapper, o `settings.gradle{dsl-ext}`, o `.gitignore` e o
  `.gitattributes` à raiz; o resto fica em `{agent-module}/`.
- Leia do `plugins {}` de `{agent-module}/build.gradle{dsl-ext}` as versões
  que o Initializr resolveu — `{boot-version}`,
  `{dependency-management-version}` e, em Kotlin, `{kotlin-version}` — e grave
  [root.gradle.kts.template](./templates/build/kts/root.gradle.kts.template) ou
  [root.gradle.template](./templates/build/groovy/root.gradle.template) como
  `build.gradle{dsl-ext}` da raiz.
- Só depois **substitua** o `build.gradle{dsl-ext}` do módulo por
  [agent-module.gradle.kts.template](./templates/build/kts/agent-module.gradle.kts.template)
  ou [agent-module.gradle.template](./templates/build/groovy/agent-module.gradle.template).
- Gere o `buildingBlocks` exatamente como o Passo 5 da
  [analizza-new-project](../analizza-new-project/SKILL.md) (templates em
  `../analizza-new-project/templates/buildingBlocks/`), inclusive a
  verificação dele.
- `settings.gradle{dsl-ext}`: `rootProject.name` = `{project-name}` e os
  `include` de `buildingBlocks` e `{agent-module}` — não há `-api` nem `-core`.
- Confira que a classe de aplicação que o Initializr gerou se chama
  `{app-class}` e está em `{package}`; se o nome for outro, o `{app-class}` é
  o que está no disco.
- **Apague** `{agent-module}/src/test` e
  `{agent-module}/src/main/resources/application.properties` que vieram do
  Initializr. O `contextLoads` dele sobe a aplicação inteira e exigiria as
  variáveis do LLM em todo `build`; o teste de contexto volta como IT no
  Passo 10. E a configuração passa a ser o `application.yaml` do Passo 4.
- `git init` agora, se ainda não for repositório — os Passos 7 e 8 dependem disso.

**Existente.** Crie `{agent-module}/` com o `build.gradle{dsl-ext}` do template
da DSL do projeto, acrescente o `include` ao `settings.gradle{dsl-ext}` e
confira que a raiz declara, com versão, todo plugin que o módulo aplica sem
versão (`org.springframework.boot`, `io.spring.dependency-management` e, em
Kotlin, `kotlin("jvm")` e `kotlin("plugin.spring")`). A classe de aplicação vem
de `templates/source/{language}/main/__app-class__.*`, copiada no Passo 4 — o
arquivo só existe neste modo (`<!-- arquivo se existente -->`).

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
`:buildingBlocks:compileJava` num projeto Kotlin).

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
  é copiada). Sem compose no projeto, crie `docker-compose.yml` com as duas
  chaves. O banco é **do agente** (`{db-name}`, porta `{db-port}`), nunca o
  do `-core`. Não renomeie o serviço: o `make run-agent` o sobe pelo nome.
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
| `gitignore-extra.template` | acrescentado ao fim do `.gitignore` | sempre |

Receitas do `Makefile` são com **TAB**; copie sem converter em espaço.

O que os alvos fazem, para não descrever errado ao usuário:

- `run-agent` e `run-agent-ollama` checam **primeiro** se o arquivo de
  variáveis existe (`local.env` / `local.env.ollama`) e falham com a instrução
  de `cp` se faltar. Só então, com `postgres`, sobem o banco e esperam ele
  ficar saudável — `docker compose up -d --wait` do zero,
  `docker compose up -d --wait postgres-agent` no existente — e por fim rodam
  o `bootRun`. Nenhum dos dois depende do alvo `db-up`.
- Do zero: `build`, `build-backend`, `test-backend`, `clean`, `help`,
  `langwatch-up`, `langwatch-down`, `langwatch-logs`; com `postgres`, `db-up`,
  `db-down`, `db-reset`; com `web`, `install`, `build-web`, `test-web`,
  `run-web` e `run` (agente contra o Ollama local + web); com `it-no-modulo`,
  `test-integration`. Em `it-dedicado` quem acrescenta o `test-integration` é
  a `analizza-integration-test`, no Passo 10.
- Existente: `run-agent`, `run-agent-ollama`, `test-agent`,
  `test-agent-integration`, `langwatch-up`, `langwatch-down`, `langwatch-logs`.

No modo existente, se o `Makefile` já tiver um alvo com o mesmo nome, **não
sobrescreva**: mostre o conflito e pergunte. Sem `Makefile` no projeto, crie um
só com o trecho. Se o compose do projeto não for o arquivo padrão do
`docker compose`, acrescente o `-f <arquivo>` à linha do `postgres-agent`.

```bash
[ "$(grep -c $'^\t' Makefile)" -ge 10 ] && echo "TAB OK" || echo "TAB FALHOU"
for f in local.env local.env.ollama langwatch.env; do git check-ignore -q "$f" || echo "NAO IGNORADO: $f"; done
```

`TAB OK` e nenhuma linha `NAO IGNORADO`.

### Passo 8 — Web (só `web`)

A raiz precisa ser repositório Git **antes** — senão o `create-next-app` cria
um `.git` aninhado e o módulo entra como gitlink (ver
[armadilhas da new-project](../analizza-new-project/references/pitfalls.md)).

```bash
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || git init
npx --yes create-next-app@latest {project-name}-web \
  --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
[ -d {project-name}-web/.git ] && echo "ATENÇÃO: .git aninhado"
```

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

### Passo 9 — Convenções e runbook

Detecte o framework de SDD e o arquivo de destino por
[sdd-frameworks.md](../analizza-new-project/references/sdd-frameworks.md). O
resumo de `context:` que ela mostra para o OpenSpec descreve o monorepo da
`analizza-new-project`; aqui ele descreve os módulos deste projeto.

- **Do zero:** grave
  [architecture-conventions.md.template](./templates/architecture-conventions.md.template)
  — que abre com `## Arquitetura` — e, logo depois, a seção de
  [agent-conventions.md](./references/agent-conventions.md), que abre com
  `### Agente` e fica dentro dela.
- **Existente:** acrescente só a seção de `agent-conventions.md`, dentro de
  `## Arquitetura` se ela existir, senão no fim do arquivo. **Nunca
  sobrescreva** o que o arquivo já tem; se já houver um `### Agente`, é
  segunda execução: substitua só essa seção.

Grave [runbook-agent-chat.md](./references/runbook-agent-chat.md) como
`docs/checkpoints/agent-chat.md`. Depois de tirar os marcadores, a primeira
linha do arquivo é o `---` do frontmatter.

Os dois arquivos de `references/` levam placeholders e marcadores, como
qualquer template. Confira que nada sobrou:

```bash
grep -nE '<!-- (se|fim se|arquivo se) |\{(agent-module|project-name|base-package|mcp-name|mcp-class|mcp-env|agent-port|db-name|db-port|app-class|language|dsl-ext)\}' <arquivo do SDD> docs/checkpoints/agent-chat.md
```

Nenhuma linha.

### Passo 10 — Testes

**Unitários.** Copie `templates/source/{language}/test/`.

```bash
./gradlew :{agent-module}:test --console=plain > /tmp/agent-test.log 2>&1; echo "EXIT=$?"
grep -ho '<testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' {agent-module}/build/test-results/test/*.xml
```

Exija `EXIT=0` e leia a contagem no XML, não no `BUILD SUCCESSFUL`: cinco
suítes, `failures="0" errors="0"`, somando **36 testes com memória, 34 sem**
(`ChatHandlerTest` 10, `ChatRouteTest` 11, `ConversationIdsTest` 4,
`LazyMcpToolProviderTest` 5, `AssistantAiServiceTest` 6 — ou 4 em
`sem-memoria`).

**Integração, `it-dedicado`.** Avise o usuário antes: a primeira execução dos
ITs baixa cerca de 2 GB (imagem do Ollama e modelo) e a inferência em CPU leva
minutos. Então invoque a skill
[analizza-integration-test](../analizza-integration-test/SKILL.md):

```
escopo=ambos|backend linguagem={language} banco=postgres layout=dedicado
```

`ambos` se houver web. Três coisas mudam em relação ao que ela faria sozinha:

1. **Não crie dublê para `Assistant`** quando ela chegar ao `TestConfig`. Ela
   cria dublê para interface de saída *sem container*, e o LLM tem: o Ollama.
   Um dublê `@Primary` faria o `ChatRouteIT` passar sem chamar LLM nenhum.
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

**Integração, `it-no-modulo`.** Copie `templates/source/{language}/it/` para
dentro do `{agent-module}` — os três arquivos. A `analizza-integration-test`
**não** é invocada para o backend: ela exige um banco e um módulo dedicado
cuja aplicação é a do `-api`. Consequência a relatar: sem regra ArchUnit,
JaCoCo e Pitest para o agente. Havendo web, invoque-a com `escopo=frontend`.

**Web (só `web`).** Depois que a `analizza-integration-test` instalar o Vitest
no `{project-name}-web`, copie os três testes que ficaram de fora no Passo 8
— `app/api/chat/route.test.ts`, `lib/sse.test.ts`, `lib/conversation.test.ts` —
e rode:

```bash
cd {project-name}-web && npx vitest run; echo "EXIT=$?"
```

`EXIT=0`, com **15 testes** nesses três arquivos (4, 8 e 3), mais o
`page.test.tsx` que ela gerou. Se o `npm install` do Vitest falhar com
`ERESOLVE`, veja [armadilhas](./references/pitfalls-agent.md) — nunca
`--legacy-peer-deps`.

### Passo 11 — Verificar

Obrigatório. Sem isso não há como afirmar que o agente funciona.

```bash
# do zero: make build        existente: ./gradlew :{agent-module}:build --console=plain
make build > /tmp/agent-build.log 2>&1; echo "EXIT=$?"
# it-dedicado: ./gradlew integrationTest      it-no-modulo: ./gradlew :{agent-module}:integrationTest
./gradlew integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
find . -path '*/build/test-results/integrationTest/*.xml' -not -path '*/node_modules/*' \
  -exec grep -ho '<testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' {} \;
```

O `build` não precisa de banco, de LLM nem de Docker: os unitários usam LLM
roteirizado e os ITs ficam fora dele. Nos ITs, exija `EXIT=0`,
`failures="0" errors="0"` e o `ChatRouteIT` com `tests="3"`; em `it-dedicado`,
também `ApplicationContextIT` e `EntrypointHasIntegrationTestIT`.

Avise o usuário **antes** de rodar os ITs, se ainda não avisou: a primeira
execução baixa cerca de 2 GB e a inferência em CPU leva minutos.

Smoke com LLM de verdade. Se o usuário já tem um `local.env.ollama`, use o
dele e pule as duas primeiras linhas. Senão, suba a imagem que os ITs acabaram
de gravar e gere um arquivo de variáveis apontando para ela, com o servidor
MCP desligado — ele é outro sistema e pode não estar no ar:

```bash
docker run -d --rm --name agent-smoke-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
sed -e 's#localhost:11434#localhost:11435#' -e 's#qwen2.5:7b#qwen2.5:3b#' \
    -e 's#^{mcp-env}_ENABLED=.*#{mcp-env}_ENABLED=false#' local.env.ollama.example > local.env.ollama
make run-agent-ollama > /tmp/agent-run.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:{agent-port}/actuator/health > /dev/null 2>&1 && break; sleep 2; done
curl -s -D - -X POST http://localhost:{agent-port}/api/v1/agent/http \
  -H 'Content-Type: application/json' -H 'X-Conversation-Id: smoke-1' -d '{"body":"Diga oi."}'
curl -s -N --max-time 240 -X POST http://localhost:{agent-port}/api/v1/agent/stream \
  -H 'Content-Type: application/json' -d '{"body":"Diga tchau."}' | head -5
curl -s http://localhost:{agent-port}/actuator/prometheus | grep '^chat_requests_total'
```

Precisa vir `200` com o header `X-Conversation-Id: smoke-1` ecoado e
`response` não vazio, linhas `data:`, e
`chat_requests_total{outcome="success"}`. Se o loop estourar, leia
`/tmp/agent-run.log` e reporte — não siga adiante. Com `postgres`, o próprio
`make run-agent-ollama` sobe o banco.

Encerre na ordem, e confirme que as portas ficaram livres:

```bash
lsof -ti tcp:{agent-port} | xargs kill
docker stop agent-smoke-ollama
# so com postgres -- do zero: make db-down      existente: docker compose stop postgres-agent
rm local.env.ollama        # so se foi o smoke que criou
lsof -ti tcp:{agent-port}; echo "porta livre se nada acima"
```

### Passo 12 — Relatar

- O modo detectado, a linguagem, o conjunto de condições, e as versões reais
  (Boot, Java, LangChain4j, Next) — **lidas dos arquivos**
- Os `EXIT=` e as contagens de teste observados, unitários e de integração
- O que ficou **desligado** e como ligar: servidor MCP, memória, web
- Com `memoria-processo`: que a memória some a cada restart
- Com `memoria-jdbc`: que uma tabela `chat_memory` ausente aparece como `502`
  na primeira conversa, não na subida
- No modo existente com `{base}-mcp`: que falta a credencial em
  `{mcp-env}_AUTHORIZATION`, se o servidor for protegido
- Em `it-no-modulo`: que o agente ficou sem ArchUnit, JaCoCo e Pitest
- Que o primeiro IT baixa ~2 GB e que os ITs ficam fora do `build`
- Que o endpoint de chat nasce **sem autenticação** e que o profile padrão é
  `dev`, com o conteúdo das conversas nos traces
- Onde as convenções e o runbook foram gravados
- O que **não** foi conferido — a tela no navegador, o trace no LangWatch — em
  vez de afirmar que funciona

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
