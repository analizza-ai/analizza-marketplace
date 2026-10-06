# `analizza-new-agent` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `analizza-new-agent`, que entrega um agente conversacional funcionando (endpoint, LLM, cliente MCP, memória, observabilidade e testes) do zero ou como módulo novo num projeto Gradle existente, em Kotlin e Java.

**Architecture:** A skill é irmã da `analizza-new-project`: `SKILL.md` com vocabulário e procedimento, `templates/` espelhando a árvore de pacotes do módulo gerado, `references/` para o que entra na documentação do projeto alvo. Reaproveita por caminho relativo o `buildingBlocks` e as referências da `new-project`. Os templates Kotlin são escritos primeiro e **verificados a cada tarefa** num projeto descartável em `/tmp/new-agent-proof`, renderizado por um script de apoio; depois vêm os templates Java, o `SKILL.md` completo e quatro aplicações de prova.

**Tech Stack:** Markdown (skill e templates), Python 3 (script de apoio descartável e validadores do repositório), `claude plugin validate`, pytest. Os templates alvejam Spring Boot 4.x, LangChain4j `1.20.0-beta30` (`langchain4j-open-ai-spring-boot4-starter`, `langchain4j-spring-boot4-starter`, `langchain4j-mcp`, `langchain4j-community-sql`), OpenTelemetry, Micrometer/Prometheus, Testcontainers (Postgres e Ollama), Next.js.

**Spec:** [`docs/superpowers/specs/2026-10-06-analizza-new-agent-skill-design.md`](../specs/2026-10-06-analizza-new-agent-skill-design.md)

## Global Constraints

- **Modo detectado, não perguntado (D2):** `settings.gradle*` na raiz → *existente*; sem build Gradle → *do zero*.
- **Do zero não existe `-core` (D3).** Um módulo de backend, quatro camadas como pacotes.
- **Existente: app Spring Boot próprio, sem depender do `-core` nem do `-api` (D4).** Pacote raiz `{package}.agent` (D5).
- **Nenhum código de domínio.** `domain/` nasce só com `.gitkeep` (D8).
- **Nenhum tipo do LangChain4j em `application/` ou `presenter/` (D9).** Só `infrastructure/` importa `dev.langchain4j`.
- **`application/` não importa nada de `presenter/`.** As exceções lançadas pelo handler moram em `application/chat/`.
- **Sem default de URL ou modelo de LLM no código (D10).** `LLM_BASE_URL`, `LLM_API_TOKEN`, `LLM_MODEL` vêm do ambiente.
- **MCP preguiçoso; servidor fora na conversa → 502, nunca resposta sem tools (D11).** `failIfOneServerFails(true)` no `McpToolProvider`.
- **Nada da Pags:** sem `pagseguro-logger`, sem URL de intranet, sem `customerId`, sem `langchain4j-agentic`.
- **Boot 3.x no modo existente: a skill para e avisa (D18).**
- **IT nunca compara o texto da resposta do LLM (D15).**
- Schema da memória (lido do jar `langchain4j-community-sql-1.20.0-beta30`): `chat_memory (memory_id VARCHAR(255) PRIMARY KEY, content TEXT NOT NULL DEFAULT '')` — uma linha por conversa.
- Comentários de código nos templates: português, sem acento, explicando o **porquê**. Arquivos copiados das referências mantêm os comentários originais.
- Indentação dos templates: 4 espaços em Kotlin/Java, TAB nas receitas de Makefile.
- Todo passo de verificação do repositório roda a partir da raiz e exige `EXIT=0`.
- Versão do plugin: `0.5.0 → 0.6.0`, idêntica nos dois `plugin.json`.

## Convenções de template (valem para todas as tarefas)

Raiz da skill: `S=plugins/analizza-skills/skills/analizza-new-agent`.

**Placeholders** — `{nome}` no conteúdo, `__nome__` em nome de arquivo:

| Placeholder | Valor | Prova 1 |
|---|---|---|
| `{project-name}` | nome da pasta raiz / `rootProject.name` | `demo` |
| `{agent-module}` | módulo do agente | `demo-agent` |
| `{app-class}` | PascalCase de `{agent-module}` + `Application` | `DemoAgentApplication` |
| `{base-package}` | pacote raiz do agente: `{package}` do zero, `{package}.agent` no existente | `br.com.analizza.demo` |
| `{bb-package}` | pacote do `buildingBlocks` (sempre `{package}`) | `br.com.analizza.demo` |
| `{group}` | group Gradle | `br.com.analizza` |
| `{java-version}` | versão do Java | `25` |
| `{agent-port}` | porta HTTP do agente | `8080` |
| `{mcp-name}` | nome kebab do servidor MCP; `tools-mcp` se nenhum foi informado | `tools-mcp` |
| `{mcp-class}` | PascalCase de `{mcp-name}` | `ToolsMcp` |
| `{mcp-env}` | UPPER_SNAKE de `{mcp-name}` | `TOOLS_MCP` |
| `{mcp-url}` | URL do servidor; vazio se nenhum | *(vazio)* |
| `{mcp-enabled}` | `true` se o usuário informou servidor, senão `false` | `false` |
| `{db-name}` | `{project-name}` com `-`→`_` (do zero); `{base}` com `-`→`_` + `_agent` (existente) | `demo` |
| `{db-port}` | `5432` do zero, `5433` no existente | `5432` |
| `{langchain4j-version}` | conferida no Maven Central | `1.20.0-beta30` |

**Marcadores condicionais** — cada um numa linha própria; a linha do marcador nunca vai para o arquivo final:

```
<!-- se X -->
...linhas que só entram quando X vale...
<!-- fim se X -->
```

Primeira linha `<!-- arquivo se X -->`: o arquivo inteiro só é gerado quando X vale.

| Condição | Vale quando |
|---|---|
| `kotlin` / `java` | linguagem do fonte |
| `do-zero` / `existente` | o modo |
| `postgres` / `sem-postgres` | o agente tem (ou não) banco |
| `memoria` | `chat-memory=sim` |
| `sem-memoria` | `chat-memory=não` |
| `memoria-jdbc` | `memoria` e `postgres` |
| `memoria-processo` | `memoria` e `sem-postgres` |
| `buildingBlocks` / `sem-buildingBlocks` | o projeto tem (ou não) o módulo `buildingBlocks` |
| `web` / `sem-web` | modo do zero com `-web` aceito (ou não) |
| `it-no-modulo` | ITs dentro do `{agent-module}`: modo existente, **ou** do zero sem banco |
| `it-dedicado` | ITs em `{project-name}-integration-tests`: do zero com banco |

**Espelhamento de árvore** — o caminho do template dá o destino:

| Template | Destino |
|---|---|
| `templates/source/{lang}/main/<caminho>` | `{agent-module}/src/main/{lang}/{package-path}/<caminho>` |
| `templates/source/{lang}/test/<caminho>` | `{agent-module}/src/test/{lang}/{package-path}/<caminho>` |
| `templates/source/{lang}/it/<caminho>` | `{it-module}/src/test/{lang}/{package-path}/<caminho>` |
| `templates/resources/<caminho>` | `{agent-module}/src/main/resources/<caminho>` |

`{package-path}` é `{base-package}` com `.` trocado por `/`. `{it-module}` é `{agent-module}` em `it-no-modulo` e `{project-name}-integration-tests` em `it-dedicado`. O sufixo `.template` cai.

## File Structure

```
plugins/analizza-skills/skills/analizza-new-agent/
├── SKILL.md                                         T1 esqueleto, T8 completo
├── references/
│   ├── agent-conventions.md                         T8  seção "Agente" do arquivo do SDD
│   ├── it-llm-layer.md                              T5  o que acrescentar ao BaseIntegrationTest dedicado
│   ├── pitfalls-agent.md                            T8
│   └── runbook-agent-chat.md                        T8
└── templates/
    ├── architecture-conventions.md.template         T8  camadas num módulo só
    ├── build/kts/{root,agent-module}.gradle.kts.template      T1
    ├── build/groovy/{root,agent-module}.gradle.template       T1
    ├── resources/
    │   ├── application.yaml.template                T2
    │   ├── prompts/{system,user}-prompt.prompt.template       T2
    │   └── db/migration/V1__chat_memory.sql.template          T2
    ├── source/kotlin/main/                          T2
    │   ├── presenter/routes/chat/{ChatRoute,ConversationIds}.kt.template
    │   ├── presenter/configuration/ConversationIdFilter.kt.template
    │   ├── presenter/configuration/exception/GlobalExceptionHandler.kt.template
    │   ├── application/chat/{ChatCommand,ChatResult,ChatInput,ChatExceptions,ChatFailures,ChatHandler,ChatStreamHandler}.kt.template
    │   ├── infrastructure/data/anticorruptionLayer/llm/Assistant.kt.template
    │   ├── infrastructure/data/anticorruptionLayer/llm/impl/{AssistantAiService,LangChain4jAssistant}.kt.template
    │   ├── infrastructure/data/anticorruptionLayer/mcp/{LazyMcpToolProvider,McpUnavailableException}.kt.template
    │   ├── infrastructure/configuration/{__mcp-class__Config,__mcp-class__Properties,ChatMemoryConfig}.kt.template
    │   └── infrastructure/observability/{ChatTelemetry,GenAiSpanEnricher,TracingProperties}.kt.template
    ├── source/kotlin/test/                          T3
    │   ├── support/{ScriptedChatModel,FakeToolProvider}.kt.template
    │   ├── presenter/routes/chat/{ConversationIdsTest,ChatRouteTest}.kt.template
    │   ├── application/chat/ChatHandlerTest.kt.template
    │   ├── infrastructure/data/anticorruptionLayer/llm/impl/AssistantAiServiceTest.kt.template
    │   └── infrastructure/data/anticorruptionLayer/mcp/LazyMcpToolProviderTest.kt.template
    ├── source/kotlin/it/                            T5
    │   ├── support/{OllamaTestContainer,BaseIntegrationTest}.kt.template
    │   └── presenter/routes/chat/ChatRouteIT.kt.template
    ├── source/java/{main,test,it}/                  T7  mesmos caminhos, .java.template
    ├── web/src/{lib/sse.ts,lib/sse.test.ts,app/api/chat/route.ts,app/api/chat/route.test.ts,app/page.tsx}.template   T6
    └── root/                                        T4
        ├── Makefile.template
        ├── Makefile.agent-targets.template
        ├── docker-compose.agent-postgres.template
        ├── docker-compose.langwatch.yml.template
        ├── gitignore-extra.template
        ├── local.env.example.template
        ├── local.env.ollama.example.template
        └── langwatch.env.example.template
plugins/analizza-skills/.claude-plugin/plugin.json   T10 versão
plugins/analizza-skills/.codex-plugin/plugin.json    T10 versão e longDescription
README.md                                            T10 linha da skill
docs/superpowers/specs/2026-10-06-...-design.md      T10 o que as provas mudarem
```

Fora do repositório, descartável: `/tmp/new-agent-proof/` (script `render.py`, `vars.env`, projetos de prova).

---

### Task 1: Esqueleto da skill, templates de build e o projeto de prova

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-new-agent/SKILL.md`
- Create: `plugins/analizza-skills/skills/analizza-new-agent/templates/build/kts/root.gradle.kts.template`
- Create: `plugins/analizza-skills/skills/analizza-new-agent/templates/build/kts/agent-module.gradle.kts.template`
- Create: `plugins/analizza-skills/skills/analizza-new-agent/templates/build/groovy/root.gradle.template`
- Create: `plugins/analizza-skills/skills/analizza-new-agent/templates/build/groovy/agent-module.gradle.template`
- Create (descartável): `/tmp/new-agent-proof/render.py`, `/tmp/new-agent-proof/vars.env`, `/tmp/new-agent-proof/demo/`

**Interfaces:**
- Consumes: `../analizza-new-project/templates/buildingBlocks/`.
- Produces: `render.py` com dois comandos — `render.py file <template> <destino>` e `render.py tree <dir-de-templates> <dir-destino>` — lendo `VARS` (arquivo `chave=valor`) e `ON` (condições separadas por vírgula) do ambiente; o projeto `/tmp/new-agent-proof/demo` com `buildingBlocks` e `demo-agent` resolvendo no Gradle. Todas as tarefas até a T6 verificam contra esse projeto.

- [ ] **Step 1: Criar a branch de trabalho**

A spec está em `docs/analizza-new-agent-design`. O trabalho segue nela:

```bash
git checkout docs/analizza-new-agent-design
git checkout -b feat/analizza-new-agent
```

- [ ] **Step 2: Escrever o script de apoio**

Não entra no repositório. Crie `/tmp/new-agent-proof/render.py`:

```python
#!/usr/bin/env python3
"""Renderiza templates da analizza-new-agent num projeto de prova.

Uso: VARS=vars.env ON=kotlin,postgres render.py file <template> <destino>
     VARS=vars.env ON=kotlin,postgres render.py tree <dir-templates> <dir-destino>
"""
import os
import re
import sys
from pathlib import Path

ABRE = re.compile(r"^\s*<!-- se ([\w-]+) -->\s*$")
FECHA = re.compile(r"^\s*<!-- fim se ([\w-]+) -->\s*$")
ARQUIVO = re.compile(r"^\s*<!-- arquivo se ([\w-]+) -->\s*$")
SOBRA = re.compile(r"(?<![{$])\{[a-z][a-z0-9]*(?:-[a-z0-9]+)*\}(?!\})")


def carregar():
    variaveis = {}
    for linha in Path(os.environ["VARS"]).read_text().splitlines():
        if "=" in linha and not linha.startswith("#"):
            chave, valor = linha.split("=", 1)
            variaveis[chave.strip()] = valor
    return variaveis, set(filter(None, os.environ.get("ON", "").split(",")))


def renderizar(texto, variaveis, ligadas, origem):
    linhas = texto.split("\n")
    if linhas and (m := ARQUIVO.match(linhas[0])):
        if m.group(1) not in ligadas:
            return None
        linhas = linhas[1:]
    saida, pilha = [], []
    for linha in linhas:
        if m := ABRE.match(linha):
            pilha.append(m.group(1))
        elif m := FECHA.match(linha):
            if not pilha or pilha[-1] != m.group(1):
                sys.exit(f"{origem}: 'fim se {m.group(1)}' sem abertura correspondente")
            pilha.pop()
        elif all(c in ligadas for c in pilha):
            saida.append(linha)
    if pilha:
        sys.exit(f"{origem}: marcador 'se {pilha[-1]}' sem fechamento")
    resultado = "\n".join(saida)
    for chave, valor in variaveis.items():
        resultado = resultado.replace("{" + chave + "}", valor)
    # Em TSX, {identificador} e JSX legitimo: a conferencia de sobra nao vale.
    if not origem.endswith(".tsx.template") and (sobra := SOBRA.search(resultado)):
        sys.exit(f"{origem}: placeholder sem valor: {sobra.group(0)}")
    return resultado


def nome_final(nome, variaveis):
    for chave, valor in variaveis.items():
        nome = nome.replace(f"__{chave}__", valor)
    return nome.removesuffix(".template")


def gravar(template, destino, variaveis, ligadas):
    texto = renderizar(template.read_text(), variaveis, ligadas, str(template))
    if texto is None:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto)
    print(destino)


def main():
    modo, origem, destino = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    variaveis, ligadas = carregar()
    if modo == "file":
        gravar(origem, destino, variaveis, ligadas)
    else:
        for template in sorted(origem.rglob("*.template")):
            relativo = template.relative_to(origem)
            alvo = destino / relativo.parent / nome_final(relativo.name, variaveis)
            gravar(template, alvo, variaveis, ligadas)


if __name__ == "__main__":
    main()
```

O `SOBRA` ignora `{{userInput}}` (prompt do LangChain4j), `${...}` (YAML e Kotlin) e `{ it }` (lambda): só acusa `{kebab-case}` que ficou sem valor. Arquivos `.tsx.template` ficam fora dessa conferência, porque `{erro}` e `{indice}` são JSX.

- [ ] **Step 3: Conferir o script com um caso que deve falhar e um que deve passar**

```bash
cd /tmp/new-agent-proof
printf 'nome=demo\n' > t.env
printf '<!-- se a -->\nfica {nome}\n<!-- fim se a -->\n<!-- se b -->\nsome\n<!-- fim se b -->\nprompt {{userInput}} ${X}\n' > t.template
VARS=t.env ON=a python3 render.py file t.template t.out && cat t.out
printf 'falta {outro-nome}\n' > t2.template
VARS=t.env ON=a python3 render.py file t2.template t2.out; echo "EXIT=$?"
```

Expected: `t.out` contém `fica demo` e `prompt {{userInput}} ${X}`, sem `some` nem marcadores; a segunda chamada imprime `placeholder sem valor: {outro-nome}` e `EXIT=1`.

- [ ] **Step 4: Escrever os templates de build da raiz**

`$S/templates/build/kts/root.gradle.kts.template`:

```kotlin
// Versoes dos plugins declaradas uma vez so, na raiz. Os subprojetos aplicam
// sem versao: o Kotlin Gradle Plugin nao suporta ser carregado com versao
// explicita em mais de um subprojeto, e um subprojeto so aplica um plugin sem
// versao se ele ja estiver no classpath do buildscript herdado da raiz.
plugins {
<!-- se kotlin -->
    kotlin("jvm") version "{kotlin-version}" apply false
    kotlin("plugin.spring") version "{kotlin-version}" apply false
    kotlin("plugin.jpa") version "{kotlin-version}" apply false
<!-- fim se kotlin -->
    id("org.springframework.boot") version "{boot-version}" apply false
    id("io.spring.dependency-management") version "{dependency-management-version}" apply false
}
```

`$S/templates/build/groovy/root.gradle.template`:

```groovy
// Versoes dos plugins declaradas uma vez so, na raiz. Um subprojeto so aplica
// um plugin sem versao se ele ja estiver no classpath do buildscript herdado
// da raiz.
plugins {
<!-- se kotlin -->
    id 'org.jetbrains.kotlin.jvm' version '{kotlin-version}' apply false
    id 'org.jetbrains.kotlin.plugin.spring' version '{kotlin-version}' apply false
    id 'org.jetbrains.kotlin.plugin.jpa' version '{kotlin-version}' apply false
<!-- fim se kotlin -->
    id 'org.springframework.boot' version '{boot-version}' apply false
    id 'io.spring.dependency-management' version '{dependency-management-version}' apply false
}
```

`{kotlin-version}`, `{boot-version}` e `{dependency-management-version}` são lidos do `build.gradle*` que o Initializr gera, nunca escritos de memória.

- [ ] **Step 5: Escrever o template do módulo do agente em Kotlin DSL**

`$S/templates/build/kts/agent-module.gradle.kts.template`:

```kotlin
plugins {
<!-- se kotlin -->
    kotlin("jvm")
    kotlin("plugin.spring")
<!-- fim se kotlin -->
<!-- se java -->
    java
<!-- fim se java -->
    id("org.springframework.boot")
    id("io.spring.dependency-management")
}

group = "{group}"
version = "0.0.1-SNAPSHOT"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of({java-version})
    }
}

repositories {
    mavenCentral()
}

// Uma versao so para toda a familia LangChain4j, em gradle.properties: os
// starters e o cliente MCP ainda saem na linha beta, e versoes misturadas
// quebram em runtime, nao na compilacao.
val langchain4jVersion: String by project

dependencies {
<!-- se buildingBlocks -->
    implementation(project(":buildingBlocks"))
<!-- fim se buildingBlocks -->
    implementation("org.springframework.boot:spring-boot-starter-webmvc")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    // So pelo Flux do endpoint SSE. Com webmvc no classpath o Boot continua
    // subindo servlet, nao Netty.
    implementation("org.springframework.boot:spring-boot-starter-webflux")
<!-- se kotlin -->
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("tools.jackson.module:jackson-module-kotlin")
<!-- fim se kotlin -->

    implementation("org.springframework.boot:spring-boot-starter-opentelemetry")
    implementation("io.micrometer:micrometer-registry-prometheus")

    implementation("dev.langchain4j:langchain4j-open-ai-spring-boot4-starter:$langchain4jVersion")
    implementation("dev.langchain4j:langchain4j-spring-boot4-starter:$langchain4jVersion")
    implementation("dev.langchain4j:langchain4j-mcp:$langchain4jVersion")
<!-- se memoria-jdbc -->
    implementation("dev.langchain4j:langchain4j-community-sql:$langchain4jVersion")
<!-- fim se memoria-jdbc -->
<!-- se postgres -->

    implementation("org.springframework.boot:spring-boot-starter-jdbc")
    implementation("org.springframework.boot:spring-boot-starter-flyway")
    implementation("org.flywaydb:flyway-database-postgresql")
    runtimeOnly("org.postgresql:postgresql")
<!-- fim se postgres -->

<!-- se kotlin -->
    // MockK no lugar do Mockito: mock de classe final e de funcao de extensao
    // sem configuracao extra.
    testImplementation("org.springframework.boot:spring-boot-starter-test") {
        exclude(group = "org.mockito")
    }
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testImplementation("io.mockk:mockk:1.13.12")
    testImplementation("com.ninja-squad:springmockk:5.0.1")
<!-- fim se kotlin -->
<!-- se java -->
    testImplementation("org.springframework.boot:spring-boot-starter-test")
<!-- fim se java -->
    testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
    testImplementation("io.opentelemetry:opentelemetry-sdk-testing")
<!-- se it-no-modulo -->
    testImplementation("org.springframework.boot:spring-boot-testcontainers")
    testImplementation("org.testcontainers:testcontainers-junit-jupiter")
    testImplementation("org.testcontainers:testcontainers-ollama")
<!-- fim se it-no-modulo -->
<!-- se it-no-modulo -->
<!-- se postgres -->
    testImplementation("org.testcontainers:testcontainers-postgresql")
<!-- fim se postgres -->
<!-- fim se it-no-modulo -->
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
<!-- se kotlin -->

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict", "-Xannotation-default-target=param-property")
    }
}
<!-- fim se kotlin -->

// Unitarios: nunca sobem container nem falam com LLM.
tasks.named<Test>("test") {
    useJUnitPlatform()
    filter {
        excludeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
}
<!-- se it-no-modulo -->

// Fora do `build` de proposito: sobe o Ollama em container e roda inferencia
// em CPU, o que leva minutos.
tasks.register<Test>("integrationTest") {
    description = "Testes de integracao (classes *IT) com LLM real em Testcontainers."
    group = "verification"
    testClassesDirs = sourceSets.test.get().output.classesDirs
    classpath = sourceSets.test.get().runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
    shouldRunAfter(tasks.named("test"))
    testLogging {
        events("failed")
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
<!-- fim se it-no-modulo -->
```

`spring-boot-starter-jdbc` em vez de `data-jpa`: o agente nasce sem entidade nenhuma, e a memória de chat usa JDBC puro. Quem escrever a primeira `@Entity` troca o starter e acrescenta `plugin.jpa` — isso entra nas convenções (T8).

- [ ] **Step 6: Escrever o template do módulo do agente em Groovy**

`$S/templates/build/groovy/agent-module.gradle.template`:

```groovy
plugins {
<!-- se kotlin -->
    id 'org.jetbrains.kotlin.jvm'
    id 'org.jetbrains.kotlin.plugin.spring'
<!-- fim se kotlin -->
<!-- se java -->
    id 'java'
<!-- fim se java -->
    id 'org.springframework.boot'
    id 'io.spring.dependency-management'
}

group = '{group}'
version = '0.0.1-SNAPSHOT'

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of({java-version})
    }
}

repositories {
    mavenCentral()
}

// Uma versao so para toda a familia LangChain4j, em gradle.properties: os
// starters e o cliente MCP ainda saem na linha beta, e versoes misturadas
// quebram em runtime, nao na compilacao.
def langchain4jVersion = property('langchain4jVersion')

dependencies {
<!-- se buildingBlocks -->
    implementation project(':buildingBlocks')
<!-- fim se buildingBlocks -->
    implementation 'org.springframework.boot:spring-boot-starter-webmvc'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    // So pelo Flux do endpoint SSE. Com webmvc no classpath o Boot continua
    // subindo servlet, nao Netty.
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
<!-- se kotlin -->
    implementation 'org.jetbrains.kotlin:kotlin-reflect'
    implementation 'tools.jackson.module:jackson-module-kotlin'
<!-- fim se kotlin -->

    implementation 'org.springframework.boot:spring-boot-starter-opentelemetry'
    implementation 'io.micrometer:micrometer-registry-prometheus'

    implementation "dev.langchain4j:langchain4j-open-ai-spring-boot4-starter:${langchain4jVersion}"
    implementation "dev.langchain4j:langchain4j-spring-boot4-starter:${langchain4jVersion}"
    implementation "dev.langchain4j:langchain4j-mcp:${langchain4jVersion}"
<!-- se memoria-jdbc -->
    implementation "dev.langchain4j:langchain4j-community-sql:${langchain4jVersion}"
<!-- fim se memoria-jdbc -->
<!-- se postgres -->

    implementation 'org.springframework.boot:spring-boot-starter-jdbc'
    implementation 'org.springframework.boot:spring-boot-starter-flyway'
    implementation 'org.flywaydb:flyway-database-postgresql'
    runtimeOnly 'org.postgresql:postgresql'
<!-- fim se postgres -->

<!-- se kotlin -->
    // MockK no lugar do Mockito: mock de classe final e de funcao de extensao
    // sem configuracao extra.
    testImplementation('org.springframework.boot:spring-boot-starter-test') {
        exclude group: 'org.mockito'
    }
    testImplementation 'org.jetbrains.kotlin:kotlin-test-junit5'
    testImplementation 'io.mockk:mockk:1.13.12'
    testImplementation 'com.ninja-squad:springmockk:5.0.1'
<!-- fim se kotlin -->
<!-- se java -->
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
<!-- fim se java -->
    testImplementation 'org.springframework.boot:spring-boot-starter-webmvc-test'
    testImplementation 'io.opentelemetry:opentelemetry-sdk-testing'
<!-- se it-no-modulo -->
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation 'org.testcontainers:testcontainers-ollama'
<!-- fim se it-no-modulo -->
<!-- se it-no-modulo -->
<!-- se postgres -->
    testImplementation 'org.testcontainers:testcontainers-postgresql'
<!-- fim se postgres -->
<!-- fim se it-no-modulo -->
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}
<!-- se kotlin -->

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll('-Xjsr305=strict', '-Xannotation-default-target=param-property')
    }
}
<!-- fim se kotlin -->

// Unitarios: nunca sobem container nem falam com LLM.
tasks.named('test') {
    useJUnitPlatform()
    filter {
        excludeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
}
<!-- se it-no-modulo -->

// Fora do `build` de proposito: sobe o Ollama em container e roda inferencia
// em CPU, o que leva minutos.
tasks.register('integrationTest', Test) {
    description = 'Testes de integracao (classes *IT) com LLM real em Testcontainers.'
    group = 'verification'
    testClassesDirs = sourceSets.test.output.classesDirs
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
    shouldRunAfter tasks.named('test')
    testLogging {
        events 'failed'
        exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
    }
}
<!-- fim se it-no-modulo -->
```

- [ ] **Step 7: Escrever o esqueleto do `SKILL.md`**

O validador exige um `SKILL.md` por pasta de skill. O procedimento completo entra na T8, quando todos os templates existirem; até lá o arquivo declara a skill e as convenções de template. `$S/SKILL.md`:

```markdown
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

Procedimento em construção — ver o plano
`docs/superpowers/plans/2026-10-06-analizza-new-agent-skill.md`.
```

- [ ] **Step 8: Gerar o backend base do projeto de prova**

```bash
cd /tmp/new-agent-proof && rm -rf demo starter.zip && mkdir demo && cd demo
curl -sS --max-time 90 -o ../starter.zip -G https://start.spring.io/starter.zip \
  --data-urlencode 'type=gradle-project-kotlin' \
  --data-urlencode 'language=kotlin' \
  --data-urlencode 'groupId=br.com.analizza' \
  --data-urlencode 'artifactId=demo-agent' \
  --data-urlencode 'name=demo-agent' \
  --data-urlencode 'packageName=br.com.analizza.demo' \
  --data-urlencode 'packaging=jar' \
  --data-urlencode 'javaVersion=25' \
  --data-urlencode 'dependencies=web,actuator'
unzip -l ../starter.zip | head -30
mkdir demo-agent && unzip -q ../starter.zip -d demo-agent
mv demo-agent/gradlew demo-agent/gradlew.bat demo-agent/gradle demo-agent/.gitignore demo-agent/.gitattributes .
rm -f demo-agent/settings.gradle.kts demo-agent/HELP.md
grep -nE 'version "' demo-agent/build.gradle.kts
git init -q
```

Expected: o `grep` mostra as versões do Kotlin, do Boot e do `dependency-management`. Anote as três — entram no `vars.env` do próximo passo. Se o `unzip -l` mostrar um diretório-base (`demo-agent/` antes de cada arquivo), extraia em `.` em vez de em `demo-agent`.

- [ ] **Step 9: Escrever o `vars.env` e renderizar o build**

`/tmp/new-agent-proof/vars.env`, trocando as três versões pelas lidas no passo anterior:

```
project-name=demo
agent-module=demo-agent
app-class=DemoAgentApplication
base-package=br.com.analizza.demo
bb-package=br.com.analizza.demo
package=br.com.analizza.demo
group=br.com.analizza
java-version=25
agent-port=8080
mcp-name=tools-mcp
mcp-class=ToolsMcp
mcp-env=TOOLS_MCP
mcp-url=
mcp-enabled=false
db-name=demo
db-port=5432
langchain4j-version=1.20.0-beta30
kotlin-version=2.3.21
boot-version=4.1.1
dependency-management-version=1.1.7
```

```bash
cd /tmp/new-agent-proof
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills
export VARS=$PWD/vars.env ON=kotlin,postgres,memoria,memoria-jdbc,buildingBlocks,web,it-dedicado
python3 render.py file $R/analizza-new-agent/templates/build/kts/root.gradle.kts.template demo/build.gradle.kts
python3 render.py file $R/analizza-new-agent/templates/build/kts/agent-module.gradle.kts.template demo/demo-agent/build.gradle.kts
python3 render.py file $R/analizza-new-project/templates/buildingBlocks/build.gradle.kts.template demo/buildingBlocks/build.gradle.kts
python3 render.py tree $R/analizza-new-project/templates/buildingBlocks/kotlin demo/buildingBlocks/src/main/kotlin/br/com/analizza/demo
printf 'rootProject.name = "demo"\ninclude(":buildingBlocks")\ninclude(":demo-agent")\n' > demo/settings.gradle.kts
printf 'langchain4jVersion=1.20.0-beta30\n' > demo/gradle.properties
rm -rf demo/demo-agent/src/test
```

O `src/test` do Initializr sai porque o `contextLoads` dele sobe a aplicação inteira e passaria a exigir as variáveis do LLM em todo `./gradlew build`; o teste de contexto volta como IT na T5.

- [ ] **Step 10: Verificar que o Gradle enxerga os dois módulos e resolve as dependências**

```bash
cd /tmp/new-agent-proof/demo
./gradlew projects --console=plain > /tmp/agent-projects.log 2>&1; echo "EXIT=$?"
grep -E "Project ':(buildingBlocks|demo-agent)'" /tmp/agent-projects.log
./gradlew :buildingBlocks:compileKotlin :demo-agent:dependencies --configuration runtimeClasspath --console=plain > /tmp/agent-deps.log 2>&1; echo "EXIT=$?"
grep -cE 'FAILED' /tmp/agent-deps.log
grep -E 'langchain4j-(mcp|community-sql|open-ai-spring-boot4-starter)' /tmp/agent-deps.log | head -5
```

Expected: `EXIT=0` nas duas; os dois projetos listados; `0` linhas `FAILED`; as três dependências LangChain4j resolvidas em `1.20.0-beta30`. Se alguma sair `FAILED`, a versão não existe no Maven Central — confira com `curl -s https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-mcp/maven-metadata.xml` e ajuste `langchain4j-version` no `vars.env`, no `gradle.properties` e na tabela de placeholders deste plano.

- [ ] **Step 11: Validar o repositório e commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
make check > /tmp/check.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent
git commit -m "Esqueleto da analizza-new-agent e templates de build

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Expected: `EXIT=0` nos dois.

---

### Task 2: Código de produção do agente em Kotlin

**Files** (todos sob `$S/templates/`):
- Create: `resources/application.yaml.template`
- Create: `resources/prompts/system-prompt.prompt.template`, `resources/prompts/user-prompt.prompt.template`
- Create: `resources/db/migration/V1__chat_memory.sql.template`
- Create: `source/kotlin/main/presenter/routes/chat/ChatRoute.kt.template`, `ConversationIds.kt.template`
- Create: `source/kotlin/main/presenter/configuration/ConversationIdFilter.kt.template`
- Create: `source/kotlin/main/presenter/configuration/exception/GlobalExceptionHandler.kt.template`
- Create: `source/kotlin/main/application/chat/{ChatCommand,ChatResult,ChatInput,ChatExceptions,ChatFailures,ChatHandler,ChatStreamHandler}.kt.template`
- Create: `source/kotlin/main/infrastructure/data/anticorruptionLayer/llm/Assistant.kt.template`
- Create: `source/kotlin/main/infrastructure/data/anticorruptionLayer/llm/impl/{AssistantAiService,LangChain4jAssistant}.kt.template`
- Create: `source/kotlin/main/infrastructure/data/anticorruptionLayer/mcp/{LazyMcpToolProvider,McpUnavailableException}.kt.template`
- Create: `source/kotlin/main/infrastructure/configuration/{__mcp-class__Config,__mcp-class__Properties,ChatMemoryConfig}.kt.template`
- Create: `source/kotlin/main/infrastructure/observability/{ChatTelemetry,GenAiSpanEnricher,TracingProperties}.kt.template`

**Interfaces:**
- Consumes: `render.py` e `/tmp/new-agent-proof/demo` da T1; contratos `ResultCommand<Result>` e `ResultCommandHandler<TCommand, TResult>` (`fun handle(command: TCommand): TResult`) de `{bb-package}.application`; `ErrorMessage(code: String, message: String, details: String? = null)` de `{bb-package}.presenter.exception`.
- Produces (nomes que a T3, a T5 e a T7 usam):
  - `ChatRequest(from: String?, body: String?)`, `ChatResponse(response: String)`
  - `ConversationIds.HEADER = "X-Conversation-Id"`, `ConversationIds.resolve(header: String?, from: String?): String`
  - `ChatCommand(conversationId: String, body: String?)`, `ChatResult(response: String)`
  - `ChatHandler(assistant: Assistant, telemetry: ChatTelemetry).handle(command: ChatCommand): ChatResult`
  - `ChatStreamHandler(assistant: Assistant, telemetry: ChatTelemetry).handle(command: ChatCommand): Flux<String>`
  - `InvalidChatRequestException(message)`, `UpstreamException(cause)`, `UpstreamTimeoutException(cause)`, `McpUpstreamException(cause)`, `McpUpstreamTimeoutException(cause)`
  - `Assistant.chat(conversationId: String, userInput: String): String`, `Assistant.chatStream(conversationId: String, userInput: String): Flux<String>`
  - `AssistantAiService.chat(conversationId, userInput): String`, `.chatStream(conversationId, userInput): TokenStream`
  - `LazyMcpToolProvider(serverName: String, clientFactory: () -> McpClient, toolProviderFactory: (McpClient) -> ToolProvider = <McpToolProvider estrito>) : ToolProvider, AutoCloseable`
  - `McpUnavailableException(serverName: String, cause: Throwable)`
  - `ChatTelemetry(tracer: Tracer, meterRegistry: MeterRegistry)` com `observe(spanName, conversationId, block)`, `start(spanName, conversationId): ChatSpan`, `succeed(ChatSpan)`, `fail(ChatSpan, Throwable)`
  - `TracingProperties` com `includePrompt`, `includeCompletion`, `includeToolArguments`, `includeToolResult`
  - bean `chatToolProvider: ToolProvider` (sempre existe), bean `chatMemoryProvider: ChatMemoryProvider` (só com `memoria`)
  - Corpo de erro HTTP: `{"code": "...", "message": "..."}` com os códigos `INVALID_REQUEST`, `MALFORMED_JSON`, `UNSUPPORTED_MEDIA_TYPE`, `UPSTREAM_FAILURE`, `UPSTREAM_TIMEOUT`, `MCP_UNAVAILABLE`, `MCP_TIMEOUT`

Esta tarefa escreve produção sem teste junto porque os templates de teste são a T3; o gate daqui é **compilar e subir**. A T3 fecha o ciclo.

- [ ] **Step 1: `application.yaml`**

`resources/application.yaml.template`:

```yaml
spring:
  application:
    name: ${OTEL_SERVICE_NAME:{agent-module}}
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}
  lifecycle:
    timeout-per-shutdown-phase: ${TERMINATION_GRACE_PERIOD_SECONDS:30}s
<!-- se postgres -->
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:{db-port}/{db-name}}
    username: ${DB_USER:{db-name}}
    password: ${DB_PASSWORD:{db-name}}
<!-- fim se postgres -->

server:
  port: ${PORT:{agent-port}}
  shutdown: graceful

management:
  endpoints:
    web:
      exposure:
        include: health,prometheus,info
  endpoint:
    health:
      probes:
        enabled: true
      show-details: when-authorized
  # Metricas saem so por Prometheus (pull). O push OTLP vem ligado junto com o
  # starter de OpenTelemetry e falha a cada ciclo sem coletor local.
  otlp:
    metrics:
      export:
        enabled: false
  opentelemetry:
    resource-attributes:
      service.name: ${OTEL_SERVICE_NAME:{agent-module}}
      service.version: ${APP_VERSION:0.0.1}
      deployment.environment.name: ${DEPLOYMENT_ENVIRONMENT:local}
    tracing:
      export:
        otlp:
          # Default aponta para o LangWatch local do docker-compose.langwatch.yml.
          endpoint: ${OTEL_EXPORTER_OTLP_ENDPOINT:http://localhost:5560/api/otel/v1/traces}
          headers:
            Authorization: "Bearer ${LANGWATCH_API_KEY:}"
  tracing:
    sampling:
      probability: ${OTEL_TRACES_SAMPLER_RATIO:1.0}

# Sem default de URL, token ou modelo: um default escondido aqui e o que faz
# alguem gastar token de producao sem saber. Rode com local.env ou
# local.env.ollama (make run-agent / make run-agent-ollama).
langchain4j:
  # Conteudo de conversa nos traces: desligado por padrao, ligado so no
  # profile dev. Prompt e resposta carregam dado de usuario.
  tracing:
    include-prompt: ${LANGCHAIN4J_TRACING_INCLUDE_PROMPT:false}
    include-completion: ${LANGCHAIN4J_TRACING_INCLUDE_COMPLETION:false}
    include-tool-arguments: ${LANGCHAIN4J_TRACING_INCLUDE_TOOL_ARGUMENTS:false}
    include-tool-result: ${LANGCHAIN4J_TRACING_INCLUDE_TOOL_RESULT:false}
  open-ai:
    chat-model:
      api-key: ${LLM_API_TOKEN}
      base-url: ${LLM_BASE_URL}
      model-name: ${LLM_MODEL}
      timeout: ${LLM_TIMEOUT:PT120S}
      max-retries: 3
      log-requests: ${LANGCHAIN4J_LOG_REQUESTS:false}
      log-responses: ${LANGCHAIN4J_LOG_RESPONSES:false}
    streaming-chat-model:
      api-key: ${LLM_API_TOKEN}
      base-url: ${LLM_BASE_URL}
      model-name: ${LLM_MODEL}
      timeout: ${LLM_TIMEOUT:PT120S}
      log-requests: ${LANGCHAIN4J_LOG_REQUESTS:false}
      log-responses: ${LANGCHAIN4J_LOG_RESPONSES:false}

# Servidor MCP consumido pelo agente. Com enabled=false nenhum cliente e
# criado e o agente conversa so com o LLM.
{mcp-name}:
  enabled: ${{mcp-env}_ENABLED:{mcp-enabled}}
  base-url: ${{mcp-env}_BASE_URL:{mcp-url}}
  # Valor inteiro do header Authorization (ex.: "Bearer <token>"). Vazio = sem header.
  authorization: ${{mcp-env}_AUTHORIZATION:}
  timeout: ${{mcp-env}_TIMEOUT:PT10S}
  log-requests: ${{mcp-env}_LOG_REQUESTS:false}
  log-responses: ${{mcp-env}_LOG_RESPONSES:false}

logging:
  pattern:
    correlation: "[${spring.application.name:},%X{traceId:-},%X{spanId:-}] "
  level:
    {base-package}: ${LOG_LEVEL:INFO}
    dev.langchain4j: ${LOG_LEVEL:INFO}

---
spring:
  config:
    activate:
      on-profile: dev

langchain4j:
  tracing:
    include-prompt: true
    include-completion: true
    include-tool-arguments: true
    include-tool-result: true

logging:
  level:
    {base-package}: DEBUG

---
spring:
  config:
    activate:
      on-profile: prod

management:
  tracing:
    sampling:
      probability: ${OTEL_TRACES_SAMPLER_RATIO:0.1}

logging:
  level:
    {base-package}: WARN
    dev.langchain4j: WARN
```

Atenção ao `${{mcp-env}_ENABLED:...}`: depois de renderizado vira `${TOOLS_MCP_ENABLED:false}`. O `SOBRA` do `render.py` não acusa `${...}`, então confira o resultado à mão no Step 9.

- [ ] **Step 2: Prompts e migration**

`resources/prompts/system-prompt.prompt.template`:

```
Você é o assistente do {project-name}. Responda no idioma do usuário, com clareza e objetividade.

- Use as ferramentas disponíveis sempre que forem relevantes ao pedido; não invente dados que uma ferramenta deveria fornecer.
- Se uma ferramenta falhar ou não devolver dados, diga isso de forma transparente, sem expor detalhes técnicos.
- Se não souber, ou o pedido estiver fora do seu escopo, diga isso.
- Nunca peça ao usuário um identificador que o sistema já deveria conhecer.
```

`resources/prompts/user-prompt.prompt.template`:

```
{{userInput}}
```

`resources/db/migration/V1__chat_memory.sql.template`:

```sql
<!-- arquivo se memoria-jdbc -->
-- Memoria de conversa do agente: uma linha por conversa, com a janela de
-- mensagens serializada em JSON. O schema e o que o SQLChatMemoryStore do
-- LangChain4j espera (PostgreSQLDialect); mudar nome ou tipo de coluna aqui
-- exige mudar a configuracao do store em ChatMemoryConfig.
CREATE TABLE chat_memory (
    memory_id VARCHAR(255) PRIMARY KEY,
    content   TEXT NOT NULL DEFAULT ''
);
```

- [ ] **Step 3: Entrada — rota, resolução de conversa, filtro e handler de erro**

`source/kotlin/main/presenter/routes/chat/ConversationIds.kt.template`:

```kotlin
package {base-package}.presenter.routes.chat

import java.util.UUID

/**
 * Resolve o identificador da conversa. Precedencia: header, depois o campo
 * `from` do corpo, depois um UUID novo. O limite de tamanho existe porque o
 * valor vira chave de memoria e atributo de span.
 */
object ConversationIds {

    const val HEADER = "X-Conversation-Id"
    private const val MAX_LENGTH = 128

    fun resolve(header: String?, from: String?): String {
        val candidate = when {
            !header.isNullOrBlank() -> header.trim()
            !from.isNullOrBlank() -> from.trim()
            else -> null
        }
        return candidate?.take(MAX_LENGTH) ?: UUID.randomUUID().toString()
    }
}
```

`source/kotlin/main/presenter/routes/chat/ChatRoute.kt.template`:

```kotlin
package {base-package}.presenter.routes.chat

import {base-package}.application.chat.ChatCommand
import {base-package}.application.chat.ChatHandler
import {base-package}.application.chat.ChatStreamHandler
import org.springframework.http.MediaType
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestHeader
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import reactor.core.publisher.Flux

data class ChatRequest(val from: String? = null, val body: String? = null)

data class ChatResponse(val response: String)

/**
 * Entrada do agente. Sem regra de negocio: resolve a conversa, monta o Command
 * e traduz o resultado. A validacao do corpo e do handler, para valer tambem
 * para quem chamar o caso de uso por outro caminho.
 */
@RestController
@RequestMapping("/api/v1/agent")
class ChatRoute(
    private val chatHandler: ChatHandler,
    private val chatStreamHandler: ChatStreamHandler,
) {

    @PostMapping(
        "/http",
        consumes = [MediaType.APPLICATION_JSON_VALUE],
        produces = [MediaType.APPLICATION_JSON_VALUE],
    )
    fun chat(
        @RequestBody request: ChatRequest,
        @RequestHeader(ConversationIds.HEADER, required = false) header: String?,
    ): ChatResponse {
        val command = ChatCommand(ConversationIds.resolve(header, request.from), request.body)
        return ChatResponse(chatHandler.handle(command).response)
    }

    @PostMapping(
        "/stream",
        consumes = [MediaType.APPLICATION_JSON_VALUE],
        produces = [MediaType.TEXT_EVENT_STREAM_VALUE],
    )
    fun stream(
        @RequestBody request: ChatRequest,
        @RequestHeader(ConversationIds.HEADER, required = false) header: String?,
    ): Flux<String> =
        chatStreamHandler.handle(ChatCommand(ConversationIds.resolve(header, request.from), request.body))
}
```

`source/kotlin/main/presenter/configuration/ConversationIdFilter.kt.template`:

```kotlin
package {base-package}.presenter.configuration

import {base-package}.presenter.routes.chat.ConversationIds
import jakarta.servlet.Filter
import jakarta.servlet.FilterChain
import jakarta.servlet.ServletRequest
import jakarta.servlet.ServletResponse
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.core.annotation.Order
import org.springframework.stereotype.Component

/**
 * Ecoa o X-Conversation-Id na resposta, para o cliente correlacionar o que
 * recebeu com o trace da conversa.
 */
@Component
@Order(1)
class ConversationIdFilter : Filter {

    override fun doFilter(request: ServletRequest, response: ServletResponse, chain: FilterChain) {
        if (request is HttpServletRequest && response is HttpServletResponse) {
            val conversationId = request.getHeader(ConversationIds.HEADER)
            if (!conversationId.isNullOrBlank()) {
                response.setHeader(ConversationIds.HEADER, conversationId)
            }
        }
        chain.doFilter(request, response)
    }
}
```

`source/kotlin/main/presenter/configuration/exception/GlobalExceptionHandler.kt.template`:

```kotlin
package {base-package}.presenter.configuration.exception

import {base-package}.application.chat.InvalidChatRequestException
import {base-package}.application.chat.McpUpstreamException
import {base-package}.application.chat.McpUpstreamTimeoutException
import {base-package}.application.chat.UpstreamException
import {base-package}.application.chat.UpstreamTimeoutException
<!-- se buildingBlocks -->
import {bb-package}.presenter.exception.ErrorMessage
<!-- fim se buildingBlocks -->
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.HttpMediaTypeNotSupportedException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.ResponseStatus
import org.springframework.web.bind.annotation.RestControllerAdvice
<!-- se sem-buildingBlocks -->

data class ErrorMessage(val code: String, val message: String)
<!-- fim se sem-buildingBlocks -->

/**
 * Corpo de erro canonico. Nunca devolve stacktrace, token nem o corpo que o
 * LLM ou o servidor MCP respondeu: o detalhe fica no log, a mensagem para o
 * cliente e fixa.
 */
@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(InvalidChatRequestException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun invalidRequest(e: InvalidChatRequestException) =
        ErrorMessage("INVALID_REQUEST", e.message ?: "requisicao invalida")

    @ExceptionHandler(HttpMessageNotReadableException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun malformedJson(e: HttpMessageNotReadableException) =
        ErrorMessage("MALFORMED_JSON", "requisicao JSON invalida")

    @ExceptionHandler(HttpMediaTypeNotSupportedException::class)
    @ResponseStatus(HttpStatus.UNSUPPORTED_MEDIA_TYPE)
    fun unsupportedMediaType(e: HttpMediaTypeNotSupportedException) =
        ErrorMessage("UNSUPPORTED_MEDIA_TYPE", "tipo de midia nao suportado")

    @ExceptionHandler(UpstreamException::class)
    @ResponseStatus(HttpStatus.BAD_GATEWAY)
    fun upstream(e: UpstreamException): ErrorMessage {
        log.error("falha do provedor de LLM", e)
        return ErrorMessage("UPSTREAM_FAILURE", "falha de comunicacao com o provedor")
    }

    @ExceptionHandler(UpstreamTimeoutException::class)
    @ResponseStatus(HttpStatus.GATEWAY_TIMEOUT)
    fun upstreamTimeout(e: UpstreamTimeoutException): ErrorMessage {
        log.error("timeout do provedor de LLM", e)
        return ErrorMessage("UPSTREAM_TIMEOUT", "tempo limite da requisicao excedido")
    }

    @ExceptionHandler(McpUpstreamException::class)
    @ResponseStatus(HttpStatus.BAD_GATEWAY)
    fun mcpUnavailable(e: McpUpstreamException): ErrorMessage {
        log.error("servidor MCP indisponivel", e)
        return ErrorMessage("MCP_UNAVAILABLE", "ferramenta externa indisponivel")
    }

    @ExceptionHandler(McpUpstreamTimeoutException::class)
    @ResponseStatus(HttpStatus.GATEWAY_TIMEOUT)
    fun mcpTimeout(e: McpUpstreamTimeoutException): ErrorMessage {
        log.error("timeout do servidor MCP", e)
        return ErrorMessage("MCP_TIMEOUT", "tempo limite ao consultar ferramenta externa")
    }

    private companion object {
        val log = LoggerFactory.getLogger(GlobalExceptionHandler::class.java)
    }
}
```

- [ ] **Step 4: Caso de uso — command, validação, exceções e classificação de falha**

`source/kotlin/main/application/chat/ChatCommand.kt.template`:

```kotlin
package {base-package}.application.chat

<!-- se buildingBlocks -->
import {bb-package}.application.ResultCommand

data class ChatCommand(val conversationId: String, val body: String?) : ResultCommand<ChatResult>
<!-- fim se buildingBlocks -->
<!-- se sem-buildingBlocks -->
data class ChatCommand(val conversationId: String, val body: String?)
<!-- fim se sem-buildingBlocks -->
```

`source/kotlin/main/application/chat/ChatResult.kt.template`:

```kotlin
package {base-package}.application.chat

data class ChatResult(val response: String)
```

`source/kotlin/main/application/chat/ChatExceptions.kt.template`:

```kotlin
package {base-package}.application.chat

// Moram em application/, e nao em presenter/, porque quem as lanca e o
// handler: se morassem na entrada, o caso de uso importaria presenter.

/** Corpo ausente, vazio ou longo demais. A mensagem vai para o cliente. */
class InvalidChatRequestException(message: String) : RuntimeException(message)

/** Falha de comunicacao com o provedor de LLM. */
class UpstreamException(cause: Throwable) : RuntimeException("falha de comunicacao com o provedor", cause)

/** Timeout na chamada ao provedor de LLM. */
class UpstreamTimeoutException(cause: Throwable) : RuntimeException("tempo limite da requisicao excedido", cause)

/** O servidor MCP nao respondeu ou recusou a conexao. */
class McpUpstreamException(cause: Throwable) : RuntimeException("ferramenta externa indisponivel", cause)

/** O servidor MCP nao respondeu a tempo durante uma tool call. */
class McpUpstreamTimeoutException(cause: Throwable) :
    RuntimeException("tempo limite ao consultar ferramenta externa", cause)
```

`source/kotlin/main/application/chat/ChatInput.kt.template`:

```kotlin
package {base-package}.application.chat

/** Validacao do corpo, compartilhada pelo handler sincrono e pelo de stream. */
internal object ChatInput {

    const val MAX_BODY_LENGTH = 8000

    fun validate(body: String?): String {
        if (body.isNullOrBlank()) {
            throw InvalidChatRequestException("campo body vazio")
        }
        if (body.trim().length > MAX_BODY_LENGTH) {
            throw InvalidChatRequestException("campo body excede $MAX_BODY_LENGTH caracteres")
        }
        return body
    }
}
```

`source/kotlin/main/application/chat/ChatFailures.kt.template`:

```kotlin
package {base-package}.application.chat

import {base-package}.infrastructure.data.anticorruptionLayer.mcp.McpUnavailableException
import java.net.SocketTimeoutException
import java.util.concurrent.TimeoutException

/**
 * Traduz qualquer falha da conversa numa das excecoes do caso de uso. Olha a
 * cadeia de causas inteira porque o LangChain4j embrulha a excecao original, e
 * pelo nome da classe porque o timeout do cliente HTTP dele nao estende
 * java.util.concurrent.TimeoutException.
 */
internal object ChatFailures {

    private const val MAX_DEPTH = 20

    fun classify(error: Throwable): RuntimeException {
        if (error is InvalidChatRequestException) return error
        val chain = generateSequence(error) { it.cause }.take(MAX_DEPTH).toList()
        return when {
            chain.any(::isMcpTimeout) -> McpUpstreamTimeoutException(error)
            chain.any { it is McpUnavailableException } -> McpUpstreamException(error)
            chain.any(::isTimeout) -> UpstreamTimeoutException(error)
            else -> UpstreamException(error)
        }
    }

    private fun isTimeout(e: Throwable): Boolean =
        e is SocketTimeoutException || e is TimeoutException || e.javaClass.simpleName.endsWith("TimeoutException")

    private fun isMcpTimeout(e: Throwable): Boolean =
        isTimeout(e) && e.javaClass.name.startsWith("dev.langchain4j.mcp")
}
```

- [ ] **Step 5: Caso de uso — os dois handlers**

`source/kotlin/main/application/chat/ChatHandler.kt.template`:

```kotlin
package {base-package}.application.chat

<!-- se buildingBlocks -->
import {bb-package}.application.ResultCommandHandler
<!-- fim se buildingBlocks -->
import {base-package}.infrastructure.data.anticorruptionLayer.llm.Assistant
import {base-package}.infrastructure.observability.ChatTelemetry
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component

/** Uma rodada de conversa, sincrona: valida, chama o assistente, classifica a falha. */
@Component
class ChatHandler(
    private val assistant: Assistant,
    private val telemetry: ChatTelemetry,
<!-- se buildingBlocks -->
) : ResultCommandHandler<ChatCommand, ChatResult> {

    override fun handle(command: ChatCommand): ChatResult {
<!-- fim se buildingBlocks -->
<!-- se sem-buildingBlocks -->
) {

    fun handle(command: ChatCommand): ChatResult {
<!-- fim se sem-buildingBlocks -->
        val body = ChatInput.validate(command.body)
        return telemetry.observe("chat", command.conversationId) {
            try {
                ChatResult(assistant.chat(command.conversationId, body))
            } catch (e: Exception) {
                val failure = ChatFailures.classify(e)
                log.warn(
                    "conversa falhou conversationId={} tipo={}",
                    command.conversationId,
                    failure.javaClass.simpleName,
                )
                throw failure
            }
        }
    }

    private companion object {
        val log = LoggerFactory.getLogger(ChatHandler::class.java)
    }
}
```

`source/kotlin/main/application/chat/ChatStreamHandler.kt.template`:

```kotlin
package {base-package}.application.chat

import {base-package}.infrastructure.data.anticorruptionLayer.llm.Assistant
import {base-package}.infrastructure.observability.ChatTelemetry
import org.springframework.stereotype.Component
import reactor.core.publisher.Flux

/**
 * Uma rodada de conversa em stream. Nao implementa o contrato de handler do
 * buildingBlocks porque devolve um fluxo, nao um resultado: o span e as
 * metricas fecham quando o fluxo termina, nao quando este metodo retorna.
 */
@Component
class ChatStreamHandler(
    private val assistant: Assistant,
    private val telemetry: ChatTelemetry,
) {

    fun handle(command: ChatCommand): Flux<String> {
        val body = ChatInput.validate(command.body)
        val chatSpan = telemetry.start("chatStream", command.conversationId)
        val tokens = try {
            // O span precisa estar corrente quando o assistente dispara a
            // chamada ao modelo, para o enricher de GenAI anexar os atributos nele.
            chatSpan.span.makeCurrent().use { assistant.chatStream(command.conversationId, body) }
        } catch (e: Exception) {
            val failure = ChatFailures.classify(e)
            telemetry.fail(chatSpan, failure)
            throw failure
        }
        return tokens
            .onErrorMap { ChatFailures.classify(it) }
            .doOnComplete { telemetry.succeed(chatSpan) }
            .doOnError { telemetry.fail(chatSpan, it) }
            .doOnCancel { telemetry.fail(chatSpan, IllegalStateException("stream cancelado pelo cliente")) }
    }
}
```

- [ ] **Step 6: Saída — o assistente atrás da interface**

`source/kotlin/main/infrastructure/data/anticorruptionLayer/llm/Assistant.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.llm

import reactor.core.publisher.Flux

/**
 * O provedor de LLM visto pelo caso de uso. Nenhum tipo do LangChain4j
 * aparece aqui de proposito: trocar de biblioteca e reescrever o impl/, nao
 * os handlers.
 */
interface Assistant {

    fun chat(conversationId: String, userInput: String): String

    fun chatStream(conversationId: String, userInput: String): Flux<String>
}
```

`source/kotlin/main/infrastructure/data/anticorruptionLayer/llm/impl/AssistantAiService.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.llm.impl

<!-- se memoria -->
import dev.langchain4j.service.MemoryId
<!-- fim se memoria -->
import dev.langchain4j.service.SystemMessage
import dev.langchain4j.service.TokenStream
import dev.langchain4j.service.UserMessage
import dev.langchain4j.service.V
import dev.langchain4j.service.spring.AiService
import dev.langchain4j.service.spring.AiServiceWiringMode

/**
 * AI Service do LangChain4j: o starter gera a implementacao em runtime.
 * Wiring explicito para que acrescentar um segundo ChatModel ou ToolProvider
 * ao contexto nao mude em silencio o que este assistente usa.
 */
@AiService(
    wiringMode = AiServiceWiringMode.EXPLICIT,
    chatModel = "openAiChatModel",
    streamingChatModel = "openAiStreamingChatModel",
    toolProvider = "chatToolProvider",
<!-- se memoria -->
    chatMemoryProvider = "chatMemoryProvider",
<!-- fim se memoria -->
)
interface AssistantAiService {

    @SystemMessage(fromResource = "prompts/system-prompt.prompt")
    @UserMessage(fromResource = "prompts/user-prompt.prompt")
<!-- se memoria -->
    fun chat(@MemoryId conversationId: String, @V("userInput") userInput: String): String
<!-- fim se memoria -->
<!-- se sem-memoria -->
    fun chat(@V("conversationId") conversationId: String, @V("userInput") userInput: String): String
<!-- fim se sem-memoria -->

    @SystemMessage(fromResource = "prompts/system-prompt.prompt")
    @UserMessage(fromResource = "prompts/user-prompt.prompt")
<!-- se memoria -->
    fun chatStream(@MemoryId conversationId: String, @V("userInput") userInput: String): TokenStream
<!-- fim se memoria -->
<!-- se sem-memoria -->
    fun chatStream(@V("conversationId") conversationId: String, @V("userInput") userInput: String): TokenStream
<!-- fim se sem-memoria -->
}
```

`source/kotlin/main/infrastructure/data/anticorruptionLayer/llm/impl/LangChain4jAssistant.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.llm.impl

import {base-package}.infrastructure.data.anticorruptionLayer.llm.Assistant
import org.springframework.stereotype.Component
import reactor.core.publisher.Flux
import reactor.core.publisher.Sinks

/** Adapta o AI Service a porta Assistant: e aqui que o TokenStream vira Flux. */
@Component
class LangChain4jAssistant(private val aiService: AssistantAiService) : Assistant {

    override fun chat(conversationId: String, userInput: String): String =
        aiService.chat(conversationId, userInput)

    override fun chatStream(conversationId: String, userInput: String): Flux<String> {
        val sink = Sinks.many().unicast().onBackpressureBuffer<String>()
        aiService.chatStream(conversationId, userInput)
            .onPartialResponse { sink.tryEmitNext(it) }
            .onCompleteResponse { sink.tryEmitComplete() }
            .onError { sink.tryEmitError(it) }
            .start()
        return sink.asFlux()
    }
}
```

- [ ] **Step 7: Saída — cliente MCP preguiçoso e sua configuração**

`source/kotlin/main/infrastructure/data/anticorruptionLayer/mcp/McpUnavailableException.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.mcp

/** O servidor MCP nao aceitou a conexao ou nao listou as tools. */
class McpUnavailableException(serverName: String, cause: Throwable) :
    RuntimeException("servidor MCP '$serverName' indisponivel", cause)
```

`source/kotlin/main/infrastructure/data/anticorruptionLayer/mcp/LazyMcpToolProvider.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.mcp

import dev.langchain4j.mcp.McpToolProvider
import dev.langchain4j.mcp.client.McpClient
import dev.langchain4j.service.tool.ToolProvider
import dev.langchain4j.service.tool.ToolProviderRequest
import dev.langchain4j.service.tool.ToolProviderResult
import org.slf4j.LoggerFactory

/**
 * Tools de um servidor MCP, com conexao na primeira conversa.
 *
 * O DefaultMcpClient conecta no construtor: como bean comum, um servidor MCP
 * fora do ar impediria o agente de subir. Aqui o cliente so nasce quando uma
 * conversa pede as tools, e e descartado em qualquer falha -- a conversa
 * seguinte reconecta, o que cobre o restart do servidor, que invalida a sessao.
 *
 * Falha vira McpUnavailableException em vez de "nenhuma tool": um agente que
 * perde as ferramentas em silencio inventa a resposta.
 */
class LazyMcpToolProvider(
    private val serverName: String,
    private val clientFactory: () -> McpClient,
    // Costura de teste: o padrao e o McpToolProvider de verdade.
    private val toolProviderFactory: (McpClient) -> ToolProvider = ::strictMcpToolProvider,
) : ToolProvider, AutoCloseable {

    private val lock = Any()
    private var client: McpClient? = null
    private var delegate: ToolProvider? = null

    override fun provideTools(request: ToolProviderRequest): ToolProviderResult {
        val provider = connect()
        try {
            return provider.provideTools(request)
        } catch (e: RuntimeException) {
            discard()
            throw McpUnavailableException(serverName, e)
        }
    }

    private fun connect(): ToolProvider = synchronized(lock) {
        delegate ?: try {
            val created = clientFactory()
            client = created
            toolProviderFactory(created).also { delegate = it }
        } catch (e: RuntimeException) {
            throw McpUnavailableException(serverName, e)
        }
    }

    private fun discard() {
        val stale = synchronized(lock) {
            val current = client
            client = null
            delegate = null
            current
        }
        closeQuietly(stale)
    }

    override fun close() = discard()

    private fun closeQuietly(target: McpClient?) {
        try {
            target?.close()
        } catch (e: Exception) {
            log.debug("falha ao fechar o cliente MCP '{}': {}", serverName, e.toString())
        }
    }

    private companion object {
        val log = LoggerFactory.getLogger(LazyMcpToolProvider::class.java)
    }
}

// Sem failIfOneServerFails o provider registra um aviso e devolve zero tools
// quando o servidor falha -- exatamente o silencio que nao queremos.
private fun strictMcpToolProvider(client: McpClient): ToolProvider =
    McpToolProvider.builder()
        .mcpClients(client)
        .failIfOneServerFails(true)
        .build()
```

`source/kotlin/main/infrastructure/configuration/__mcp-class__Properties.kt.template`:

```kotlin
package {base-package}.infrastructure.configuration

import org.springframework.boot.context.properties.ConfigurationProperties
import org.springframework.stereotype.Component
import java.time.Duration

/** Conexao com o servidor MCP `{mcp-name}`. */
@Component
@ConfigurationProperties(prefix = "{mcp-name}")
class {mcp-class}Properties {
    var enabled: Boolean = false
    var baseUrl: String = ""

    /** Valor inteiro do header Authorization. Vazio = nenhum header. */
    var authorization: String = ""
    var timeout: Duration = Duration.ofSeconds(10)
    var logRequests: Boolean = false
    var logResponses: Boolean = false
}
```

`source/kotlin/main/infrastructure/configuration/__mcp-class__Config.kt.template`:

```kotlin
package {base-package}.infrastructure.configuration

import {base-package}.infrastructure.data.anticorruptionLayer.mcp.LazyMcpToolProvider
import dev.langchain4j.mcp.client.DefaultMcpClient
import dev.langchain4j.mcp.client.transport.http.StreamableHttpMcpTransport
import dev.langchain4j.service.tool.ToolProvider
import dev.langchain4j.service.tool.ToolProviderResult
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * Tools do assistente. O bean `chatToolProvider` existe sempre -- o AI Service
 * o referencia pelo nome --, e o que muda com `{mcp-name}.enabled` e o que ele
 * entrega: as tools do servidor MCP, ou nenhuma.
 *
 * Para um segundo servidor MCP: copie este par Config + Properties com outro
 * nome e troque o `chatToolProvider` por um ToolProvider que junte os dois.
 */
@Configuration(proxyBeanMethods = false)
class {mcp-class}Config {

    @Bean("chatToolProvider", destroyMethod = "close")
    @ConditionalOnProperty(prefix = "{mcp-name}", name = ["enabled"], havingValue = "true")
    fun mcpToolProvider(properties: {mcp-class}Properties): LazyMcpToolProvider =
        LazyMcpToolProvider("{mcp-name}") {
            val headers = if (properties.authorization.isBlank()) {
                emptyMap()
            } else {
                mapOf("Authorization" to properties.authorization)
            }
            DefaultMcpClient.builder()
                .key("{mcp-name}")
                .clientName("{agent-module}")
                .transport(
                    StreamableHttpMcpTransport.builder()
                        .url(properties.baseUrl)
                        .timeout(properties.timeout)
                        .customHeaders(headers)
                        .logRequests(properties.logRequests)
                        .logResponses(properties.logResponses)
                        .build(),
                )
                .initializationTimeout(properties.timeout)
                .toolExecutionTimeout(properties.timeout)
                .build()
        }

    @Bean("chatToolProvider")
    @ConditionalOnProperty(prefix = "{mcp-name}", name = ["enabled"], havingValue = "false", matchIfMissing = true)
    fun noToolProvider(): ToolProvider = ToolProvider { ToolProviderResult.builder().build() }
}
```

- [ ] **Step 8: Saída — memória e observabilidade**

`source/kotlin/main/infrastructure/configuration/ChatMemoryConfig.kt.template`:

```kotlin
<!-- arquivo se memoria -->
package {base-package}.infrastructure.configuration

<!-- se memoria-jdbc -->
import dev.langchain4j.community.store.memory.chat.sql.PostgreSQLDialect
import dev.langchain4j.community.store.memory.chat.sql.SQLChatMemoryStore
<!-- fim se memoria-jdbc -->
import dev.langchain4j.memory.chat.ChatMemoryProvider
import dev.langchain4j.memory.chat.MessageWindowChatMemory
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
<!-- se memoria-jdbc -->
import javax.sql.DataSource
<!-- fim se memoria-jdbc -->

/** Memoria de conversa: janela das ultimas mensagens, uma por conversationId. */
@Configuration(proxyBeanMethods = false)
class ChatMemoryConfig {

<!-- se memoria-jdbc -->
    // autoCreateTable(false): a tabela e da migration V1__chat_memory.sql. Com
    // Flyway no projeto, schema criado por biblioteca em runtime e schema que
    // ninguem versionou.
    @Bean
    fun chatMemoryProvider(dataSource: DataSource): ChatMemoryProvider {
        val store = SQLChatMemoryStore.builder()
            .dataSource(dataSource)
            .sqlDialect(PostgreSQLDialect())
            .tableName("chat_memory")
            .autoCreateTable(false)
            .build()
        return ChatMemoryProvider { memoryId ->
            MessageWindowChatMemory.builder()
                .id(memoryId)
                .maxMessages(MAX_MESSAGES)
                .chatMemoryStore(store)
                .build()
        }
    }
<!-- fim se memoria-jdbc -->
<!-- se memoria-processo -->
    // Memoria em processo: some a cada restart e nao e compartilhada entre
    // replicas. Serve para desenvolvimento; em producao com mais de uma
    // instancia, troque por um ChatMemoryStore persistente.
    @Bean
    fun chatMemoryProvider(): ChatMemoryProvider = ChatMemoryProvider { memoryId ->
        MessageWindowChatMemory.builder()
            .id(memoryId)
            .maxMessages(MAX_MESSAGES)
            .build()
    }
<!-- fim se memoria-processo -->

    private companion object {
        const val MAX_MESSAGES = 30
    }
}
```

`source/kotlin/main/infrastructure/observability/ChatTelemetry.kt.template`:

```kotlin
package {base-package}.infrastructure.observability

import io.micrometer.core.instrument.Counter
import io.micrometer.core.instrument.MeterRegistry
import io.micrometer.core.instrument.Timer
import io.opentelemetry.api.trace.Span
import io.opentelemetry.api.trace.StatusCode
import io.opentelemetry.api.trace.Tracer
import org.springframework.stereotype.Component

/** Um span em andamento e o cronometro da mesma conversa. */
class ChatSpan(val span: Span, internal val sample: Timer.Sample)

/**
 * Span e metricas de uma rodada de conversa. Os handlers chamam isto em vez
 * de montar span na mao, para que o sincrono e o de stream emitam os mesmos
 * atributos e as mesmas metricas.
 *
 * user_id e thread_id sao os atributos que o LangWatch usa para agrupar
 * traces por usuario e por conversa.
 */
@Component
class ChatTelemetry(
    private val tracer: Tracer,
    private val meterRegistry: MeterRegistry,
) {

    fun <T> observe(spanName: String, conversationId: String, block: () -> T): T {
        val chatSpan = start(spanName, conversationId)
        try {
            val result = chatSpan.span.makeCurrent().use { block() }
            succeed(chatSpan)
            return result
        } catch (e: Exception) {
            fail(chatSpan, e)
            throw e
        }
    }

    fun start(spanName: String, conversationId: String): ChatSpan {
        val span = tracer.spanBuilder(spanName).startSpan()
        span.setAttribute("conversationId", conversationId)
        span.setAttribute("user_id", conversationId)
        span.setAttribute("thread_id", conversationId)
        return ChatSpan(span, Timer.start(meterRegistry))
    }

    fun succeed(chatSpan: ChatSpan) = finish(chatSpan, "success")

    fun fail(chatSpan: ChatSpan, error: Throwable) {
        chatSpan.span.setStatus(StatusCode.ERROR, error.message ?: "erro desconhecido")
        chatSpan.span.recordException(error)
        finish(chatSpan, "failure")
    }

    private fun finish(chatSpan: ChatSpan, outcome: String) {
        Counter.builder("chat.requests").tag("outcome", outcome).register(meterRegistry).increment()
        chatSpan.sample.stop(Timer.builder("chat.request.duration").register(meterRegistry))
        chatSpan.span.end()
    }
}
```

`TracingProperties` e `GenAiSpanEnricher` vêm do `agent-invest-sgap`, onde já rodam em produção. Copie e adapte com estes comandos (a partir da raiz do repositório):

```bash
REF=/Users/diegolirio/Documents/Github/agent-invest-sgap/src/main/kotlin/pags/platform/investmentsaiagents/investmentsadvisoragent/config
OBS=plugins/analizza-skills/skills/analizza-new-agent/templates/source/kotlin/main/infrastructure/observability
PKG='package {base-package}.infrastructure.observability'

expand -t 4 $REF/LangChain4jTracingProperties.kt \
  | sed -e "1s/.*/$PKG/" -e 's/LangChain4jTracingProperties/TracingProperties/g' \
  > $OBS/TracingProperties.kt.template

expand -t 4 $REF/GenAiSpanEnricher.kt \
  | sed -e "1s/.*/$PKG/" -e 's/LangChain4jTracingProperties/TracingProperties/g' \
  > $OBS/GenAiSpanEnricher.kt.template

head -3 $OBS/GenAiSpanEnricher.kt.template
grep -c 'pags\|Pags' $OBS/GenAiSpanEnricher.kt.template $OBS/TracingProperties.kt.template
```

Expected: a primeira linha dos dois arquivos é `package {base-package}.infrastructure.observability`; o `grep -c` devolve `0` para os dois. No `GenAiSpanEnricher.kt.template`, troque à mão o comentário do `onError` — ele cita `ChatService`, que não existe aqui:

```kotlin
    override fun onError(context: ChatModelErrorContext) {
        // O erro e registrado no span da conversa por ChatTelemetry.fail().
    }
```

- [ ] **Step 9: Renderizar no projeto de prova e compilar**

```bash
cd /tmp/new-agent-proof
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates
export VARS=$PWD/vars.env ON=kotlin,postgres,memoria,memoria-jdbc,buildingBlocks,web,it-dedicado
python3 render.py tree $R/source/kotlin/main demo/demo-agent/src/main/kotlin/br/com/analizza/demo
rm -f demo/demo-agent/src/main/resources/application.properties
python3 render.py tree $R/resources demo/demo-agent/src/main/resources
grep -n 'TOOLS_MCP' demo/demo-agent/src/main/resources/application.yaml
cd demo && ./gradlew :demo-agent:compileKotlin --console=plain > /tmp/agent-compile.log 2>&1; echo "EXIT=$?"
grep -E 'NO-SOURCE|^e: ' /tmp/agent-compile.log | head -20
find demo-agent/build/classes -name '*.class' | wc -l
```

Expected: o `grep` do YAML mostra seis linhas no formato `${TOOLS_MCP_ENABLED:false}`, sem `{` sobrando; `EXIT=0`; nenhuma linha `NO-SOURCE` nem `e: `; mais de 25 classes.

Se a compilação falhar numa API do LangChain4j (`failIfOneServerFails`, `customHeaders`, `initializationTimeout`, `onPartialResponse`, `chatMemoryProvider` no `@AiService`), a assinatura real está no jar: `find ~/.gradle -name 'langchain4j-mcp-1.20.0-beta30.jar' | head -1 | xargs -I{} javap -cp {} dev.langchain4j.mcp.McpToolProvider\$Builder`. Corrija o **template** e renderize de novo — nunca conserte só o projeto de prova.

- [ ] **Step 10: Subir a aplicação e conferir que ela responde sem MCP e sem LLM de verdade**

O contexto precisa subir com o MCP desligado e com um LLM inalcançável: é a prova de D11 (nada conecta na subida).

```bash
cd /tmp/new-agent-proof/demo
docker run -d --rm --name agent-proof-pg -e POSTGRES_DB=demo -e POSTGRES_USER=demo -e POSTGRES_PASSWORD=demo -p 5432:5432 postgres:17-alpine
sleep 5
LLM_BASE_URL=http://localhost:9/v1 LLM_API_TOKEN=x LLM_MODEL=x ./gradlew :demo-agent:bootRun --console=plain > /tmp/agent-run.log 2>&1 &
for i in $(seq 60); do curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1 && break; sleep 2; done
curl -s http://localhost:8080/actuator/health
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8080/api/v1/agent/http -H 'Content-Type: application/json' -d '{"body":"   "}'
curl -s -w '\n%{http_code}\n' -X POST http://localhost:8080/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: prova-1' -d '{"body":"oi"}'
grep -iE 'flyway.*chat_memory|Successfully applied' /tmp/agent-run.log | head -3
pkill -f 'demo-agent' ; docker stop agent-proof-pg
```

Expected: health `{"status":"UP"...}`; `400` para o corpo em branco; para `"oi"`, corpo `{"code":"UPSTREAM_FAILURE",...}` ou `UPSTREAM_TIMEOUT` com `502`/`504` (o LLM em `localhost:9` não existe); o log mostra o Flyway aplicando 1 migration. Se a porta 5432 já estiver ocupada na máquina, use `-p 5544:5432` e acrescente `DB_URL=jdbc:postgresql://localhost:5544/demo` às variáveis do `bootRun`.

- [ ] **Step 11: Validar e commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent/templates
git commit -m "Templates Kotlin de producao da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Testes unitários em Kotlin

**Files** (todos sob `$S/templates/source/kotlin/test/`):
- Create: `support/ScriptedChatModel.kt.template`, `support/FakeToolProvider.kt.template`
- Create: `presenter/routes/chat/ConversationIdsTest.kt.template`, `presenter/routes/chat/ChatRouteTest.kt.template`
- Create: `application/chat/ChatHandlerTest.kt.template`
- Create: `infrastructure/data/anticorruptionLayer/llm/impl/AssistantAiServiceTest.kt.template`
- Create: `infrastructure/data/anticorruptionLayer/mcp/LazyMcpToolProviderTest.kt.template`

**Interfaces:**
- Consumes: tudo o que a T2 produz (ver o bloco *Produces* dela).
- Produces: `ScriptedChatModel(steps: List<(ChatRequest) -> AiMessage>, listeners: List<ChatModelListener> = emptyList())` com `requests: List<ChatRequest>`, `ScriptedChatModel.callTool(name, argumentsJson)`, `ScriptedChatModel.answer(text)`; `FakeToolProvider.TOOL`, `FakeToolProvider.create(result: (String) -> String): ToolProvider`. A T7 traduz os dois para Java com os mesmos nomes.

A produção já existe (T2), então aqui o ciclo é invertido de propósito: escreva o teste, veja passar, e **quebre a produção para ver o teste falhar** (Step 7). Um teste que nunca foi visto falhando não prova nada.

- [ ] **Step 1: Os dublês de apoio**

`support/ScriptedChatModel.kt.template`:

```kotlin
package {base-package}.support

import dev.langchain4j.agent.tool.ToolExecutionRequest
import dev.langchain4j.data.message.AiMessage
import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.model.chat.listener.ChatModelListener
import dev.langchain4j.model.chat.request.ChatRequest
import dev.langchain4j.model.chat.response.ChatResponse

/**
 * LLM falso e deterministico: cada chamada ao modelo consome o proximo passo
 * do roteiro, e uma chamada alem do roteiro falha o teste. E o que permite
 * afirmar o texto exato da resposta -- coisa que um modelo real nao permite.
 */
class ScriptedChatModel(
    private val steps: List<(ChatRequest) -> AiMessage>,
    private val listeners: List<ChatModelListener> = emptyList(),
) : ChatModel {

    val requests = mutableListOf<ChatRequest>()

    override fun listeners(): List<ChatModelListener> = listeners

    override fun doChat(request: ChatRequest): ChatResponse {
        val call = requests.size
        requests += request
        check(call < steps.size) { "chamada inesperada ao modelo #${call + 1}" }
        return ChatResponse.builder().aiMessage(steps[call](request)).build()
    }

    companion object {
        fun callTool(name: String, argumentsJson: String): (ChatRequest) -> AiMessage = {
            AiMessage.from(
                ToolExecutionRequest.builder().id("call-$name").name(name).arguments(argumentsJson).build(),
            )
        }

        fun answer(text: String): (ChatRequest) -> AiMessage = { AiMessage.from(text) }
    }
}
```

`support/FakeToolProvider.kt.template`:

```kotlin
package {base-package}.support

import dev.langchain4j.agent.tool.ToolSpecification
import dev.langchain4j.model.chat.request.json.JsonObjectSchema
import dev.langchain4j.service.tool.ToolExecutor
import dev.langchain4j.service.tool.ToolProvider
import dev.langchain4j.service.tool.ToolProviderResult

/**
 * Duble de um servidor MCP: uma tool com nome, descricao e parametro, e a
 * resposta que o teste escolher. O servidor MCP de verdade e outro sistema e
 * nao entra em teste unitario.
 */
object FakeToolProvider {

    const val TOOL = "consultar_exemplo"

    fun create(result: (String) -> String): ToolProvider {
        val specification = ToolSpecification.builder()
            .name(TOOL)
            .description("Consulta um registro de exemplo pelo identificador.")
            .parameters(
                JsonObjectSchema.builder()
                    .addStringProperty("id", "Identificador do registro")
                    .required("id")
                    .build(),
            )
            .build()
        val executor = ToolExecutor { request, _ -> result(request.arguments()) }
        val provided = ToolProviderResult.builder().add(specification, executor).build()
        return ToolProvider { provided }
    }
}
```

- [ ] **Step 2: `ConversationIdsTest`**

`presenter/routes/chat/ConversationIdsTest.kt.template`:

```kotlin
package {base-package}.presenter.routes.chat

import org.junit.jupiter.api.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals

class ConversationIdsTest {

    @Test
    fun `header vence o campo from`() {
        assertEquals("do-header", ConversationIds.resolve(" do-header ", "do-corpo"))
    }

    @Test
    fun `sem header usa o campo from`() {
        assertEquals("do-corpo", ConversationIds.resolve("   ", " do-corpo "))
    }

    @Test
    fun `sem header e sem from gera um id novo a cada chamada`() {
        val primeiro = ConversationIds.resolve(null, null)
        val segundo = ConversationIds.resolve(null, null)
        assertEquals(36, primeiro.length)
        assertNotEquals(primeiro, segundo)
    }

    @Test
    fun `corta em 128 caracteres`() {
        assertEquals(128, ConversationIds.resolve("x".repeat(300), null).length)
    }
}
```

- [ ] **Step 3: `ChatHandlerTest`**

`application/chat/ChatHandlerTest.kt.template`:

```kotlin
package {base-package}.application.chat

import {base-package}.infrastructure.data.anticorruptionLayer.llm.Assistant
import {base-package}.infrastructure.data.anticorruptionLayer.mcp.McpUnavailableException
import {base-package}.infrastructure.observability.ChatTelemetry
import io.micrometer.core.instrument.simple.SimpleMeterRegistry
import io.opentelemetry.api.OpenTelemetry
import org.junit.jupiter.api.Test
import reactor.core.publisher.Flux
import java.util.concurrent.TimeoutException
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class ChatHandlerTest {

    private val registry = SimpleMeterRegistry()
    private val telemetry = ChatTelemetry(OpenTelemetry.noop().getTracer("test"), registry)

    /** Assistente de mentira: conta as chamadas e devolve (ou lanca) o que o teste mandar. */
    private class StubAssistant(private val reply: () -> String) : Assistant {
        var calls = 0

        override fun chat(conversationId: String, userInput: String): String {
            calls++
            return reply()
        }

        override fun chatStream(conversationId: String, userInput: String): Flux<String> {
            calls++
            return Flux.just(reply())
        }
    }

    private fun counter(outcome: String): Double =
        registry.find("chat.requests").tag("outcome", outcome).counter()?.count() ?: 0.0

    @Test
    fun `corpo valido devolve a resposta do assistente e conta sucesso`() {
        val assistant = StubAssistant { "Ola!" }

        val result = ChatHandler(assistant, telemetry).handle(ChatCommand("conv-1", "oi"))

        assertEquals("Ola!", result.response)
        assertEquals(1.0, counter("success"))
        assertEquals(1, registry.find("chat.request.duration").timer()!!.count())
    }

    @Test
    fun `corpo em branco e recusado sem chamar o assistente`() {
        val assistant = StubAssistant { "nao deveria" }

        val error = assertFailsWith<InvalidChatRequestException> {
            ChatHandler(assistant, telemetry).handle(ChatCommand("conv-1", "   "))
        }

        assertEquals("campo body vazio", error.message)
        assertEquals(0, assistant.calls)
    }

    @Test
    fun `corpo nulo e recusado`() {
        assertFailsWith<InvalidChatRequestException> {
            ChatHandler(StubAssistant { "x" }, telemetry).handle(ChatCommand("conv-1", null))
        }
    }

    @Test
    fun `corpo acima de 8000 caracteres e recusado`() {
        val error = assertFailsWith<InvalidChatRequestException> {
            ChatHandler(StubAssistant { "x" }, telemetry).handle(ChatCommand("conv-1", "x".repeat(8001)))
        }

        assertEquals("campo body excede 8000 caracteres", error.message)
    }

    @Test
    fun `timeout embrulhado vira UpstreamTimeoutException e conta falha`() {
        val assistant = StubAssistant { throw RuntimeException(TimeoutException("demorou")) }

        assertFailsWith<UpstreamTimeoutException> {
            ChatHandler(assistant, telemetry).handle(ChatCommand("conv-1", "oi"))
        }
        assertEquals(1.0, counter("failure"))
    }

    @Test
    fun `servidor MCP fora vira McpUpstreamException`() {
        val assistant = StubAssistant {
            throw RuntimeException(McpUnavailableException("tools-mcp", IllegalStateException("recusada")))
        }

        assertFailsWith<McpUpstreamException> {
            ChatHandler(assistant, telemetry).handle(ChatCommand("conv-1", "oi"))
        }
    }

    @Test
    fun `qualquer outra falha vira UpstreamException`() {
        val assistant = StubAssistant { throw IllegalStateException("500 do provedor") }

        assertFailsWith<UpstreamException> {
            ChatHandler(assistant, telemetry).handle(ChatCommand("conv-1", "oi"))
        }
    }

    @Test
    fun `stream emite os tokens e conta sucesso ao terminar`() {
        val tokens = ChatStreamHandler(StubAssistant { "Ola!" }, telemetry)
            .handle(ChatCommand("conv-1", "oi"))
            .collectList()
            .block()

        assertEquals(listOf("Ola!"), tokens)
        assertEquals(1.0, counter("success"))
    }

    @Test
    fun `stream com corpo em branco falha antes de abrir o fluxo`() {
        assertFailsWith<InvalidChatRequestException> {
            ChatStreamHandler(StubAssistant { "x" }, telemetry).handle(ChatCommand("conv-1", ""))
        }
    }

    @Test
    fun `falha ao abrir o stream e classificada e conta falha`() {
        val assistant = StubAssistant {
            throw McpUnavailableException("tools-mcp", IllegalStateException("recusada"))
        }

        assertFailsWith<McpUpstreamException> {
            ChatStreamHandler(assistant, telemetry).handle(ChatCommand("conv-1", "oi"))
        }
        assertEquals(1.0, counter("failure"))
    }
}
```

- [ ] **Step 4: `ChatRouteTest`**

`presenter/routes/chat/ChatRouteTest.kt.template`:

```kotlin
package {base-package}.presenter.routes.chat

import {base-package}.application.chat.ChatCommand
import {base-package}.application.chat.ChatHandler
import {base-package}.application.chat.ChatResult
import {base-package}.application.chat.ChatStreamHandler
import {base-package}.application.chat.InvalidChatRequestException
import {base-package}.application.chat.McpUpstreamException
import {base-package}.application.chat.UpstreamException
import {base-package}.application.chat.UpstreamTimeoutException
import {base-package}.presenter.configuration.ConversationIdFilter
import {base-package}.presenter.configuration.exception.GlobalExceptionHandler
import com.ninjasquad.springmockk.MockkBean
import io.mockk.every
import io.mockk.slot
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.context.annotation.Import
import org.springframework.http.MediaType
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.header
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.status
import java.util.concurrent.TimeoutException
import kotlin.test.assertEquals

/**
 * A rota com os handlers mockados: prova o contrato HTTP -- status, corpo de
 * erro, resolucao da conversa. O fluxo SSE de verdade e do ChatRouteIT, que
 * fala HTTP com a aplicacao inteira.
 */
@WebMvcTest(ChatRoute::class)
@Import(GlobalExceptionHandler::class, ConversationIdFilter::class)
class ChatRouteTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockkBean
    private lateinit var chatHandler: ChatHandler

    @MockkBean
    private lateinit var chatStreamHandler: ChatStreamHandler

    private fun postChat(json: String, conversationId: String? = null) = mockMvc.perform(
        post("/api/v1/agent/http")
            .contentType(MediaType.APPLICATION_JSON)
            .content(json)
            .apply { if (conversationId != null) header(ConversationIds.HEADER, conversationId) },
    )

    @Test
    fun `devolve 200 com a resposta do handler`() {
        every { chatHandler.handle(any()) } returns ChatResult("Ola! Como posso ajudar?")

        postChat("""{"from":"u1","body":"oi"}""")
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.response").value("Ola! Como posso ajudar?"))
    }

    @Test
    fun `usa o header como conversa e o ecoa na resposta`() {
        val command = slot<ChatCommand>()
        every { chatHandler.handle(capture(command)) } returns ChatResult("ok")

        postChat("""{"from":"u1","body":"oi"}""", conversationId = "conv-9")
            .andExpect(status().isOk)
            .andExpect(header().string(ConversationIds.HEADER, "conv-9"))

        assertEquals("conv-9", command.captured.conversationId)
        assertEquals("oi", command.captured.body)
    }

    @Test
    fun `sem header usa o campo from como conversa`() {
        val command = slot<ChatCommand>()
        every { chatHandler.handle(capture(command)) } returns ChatResult("ok")

        postChat("""{"from":"u1","body":"oi"}""").andExpect(status().isOk)

        assertEquals("u1", command.captured.conversationId)
    }

    @Test
    fun `campo desconhecido no JSON e ignorado`() {
        every { chatHandler.handle(any()) } returns ChatResult("ok")

        postChat("""{"body":"oi","outro":"ignorado"}""").andExpect(status().isOk)
    }

    @Test
    fun `corpo invalido devolve 400 com a mensagem do caso de uso`() {
        every { chatHandler.handle(any()) } throws InvalidChatRequestException("campo body vazio")

        postChat("""{"body":"  "}""")
            .andExpect(status().isBadRequest)
            .andExpect(jsonPath("$.code").value("INVALID_REQUEST"))
            .andExpect(jsonPath("$.message").value("campo body vazio"))
    }

    @Test
    fun `JSON malformado devolve 400`() {
        postChat("""{"body":""")
            .andExpect(status().isBadRequest)
            .andExpect(jsonPath("$.code").value("MALFORMED_JSON"))
    }

    @Test
    fun `midia errada devolve 415`() {
        mockMvc.perform(post("/api/v1/agent/http").contentType(MediaType.TEXT_PLAIN).content("oi"))
            .andExpect(status().isUnsupportedMediaType)
            .andExpect(jsonPath("$.code").value("UNSUPPORTED_MEDIA_TYPE"))
    }

    @Test
    fun `falha do provedor devolve 502 sem vazar a causa`() {
        every { chatHandler.handle(any()) } throws UpstreamException(RuntimeException("sk-segredo no corpo"))

        postChat("""{"body":"oi"}""")
            .andExpect(status().isBadGateway)
            .andExpect(jsonPath("$.code").value("UPSTREAM_FAILURE"))
            .andExpect(jsonPath("$.message").value("falha de comunicacao com o provedor"))
    }

    @Test
    fun `timeout do provedor devolve 504`() {
        every { chatHandler.handle(any()) } throws UpstreamTimeoutException(TimeoutException())

        postChat("""{"body":"oi"}""")
            .andExpect(status().isGatewayTimeout)
            .andExpect(jsonPath("$.code").value("UPSTREAM_TIMEOUT"))
    }

    @Test
    fun `servidor MCP fora devolve 502 com codigo proprio`() {
        every { chatHandler.handle(any()) } throws McpUpstreamException(RuntimeException("recusada"))

        postChat("""{"body":"oi"}""")
            .andExpect(status().isBadGateway)
            .andExpect(jsonPath("$.code").value("MCP_UNAVAILABLE"))
    }

    @Test
    fun `stream com corpo invalido devolve 400 antes de abrir o fluxo`() {
        every { chatStreamHandler.handle(any()) } throws InvalidChatRequestException("campo body vazio")

        mockMvc.perform(
            post("/api/v1/agent/stream").contentType(MediaType.APPLICATION_JSON).content("""{"body":""}"""),
        )
            .andExpect(status().isBadRequest)
            .andExpect(jsonPath("$.code").value("INVALID_REQUEST"))
    }
}
```

- [ ] **Step 5: `LazyMcpToolProviderTest`**

`infrastructure/data/anticorruptionLayer/mcp/LazyMcpToolProviderTest.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.mcp

import dev.langchain4j.mcp.client.McpClient
import dev.langchain4j.service.tool.ToolProvider
import dev.langchain4j.service.tool.ToolProviderRequest
import dev.langchain4j.service.tool.ToolProviderResult
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class LazyMcpToolProviderTest {

    private val request = mockk<ToolProviderRequest>(relaxed = true)
    private val noTools = ToolProvider { ToolProviderResult.builder().build() }

    @Test
    fun `nao conecta enquanto nenhuma conversa pede as tools`() {
        var connections = 0

        LazyMcpToolProvider("tools-mcp", { connections++; mockk(relaxed = true) }, { noTools })

        assertEquals(0, connections)
    }

    @Test
    fun `servidor fora vira McpUnavailableException e a conversa seguinte tenta de novo`() {
        var connections = 0
        val provider = LazyMcpToolProvider(
            "tools-mcp",
            { connections++; throw IllegalStateException("connection refused") },
            { noTools },
        )

        val error = assertFailsWith<McpUnavailableException> { provider.provideTools(request) }
        assertFailsWith<McpUnavailableException> { provider.provideTools(request) }

        assertTrue(error.message!!.contains("tools-mcp"))
        assertEquals(2, connections)
    }

    @Test
    fun `reaproveita a conexao enquanto o servidor responde`() {
        var connections = 0
        val provider = LazyMcpToolProvider("tools-mcp", { connections++; mockk(relaxed = true) }, { noTools })

        provider.provideTools(request)
        provider.provideTools(request)

        assertEquals(1, connections)
    }

    @Test
    fun `falha ao listar as tools fecha o cliente e reconecta na proxima`() {
        val clients = mutableListOf<McpClient>()
        var failing = true
        val provider = LazyMcpToolProvider(
            "tools-mcp",
            { mockk<McpClient>(relaxed = true).also { clients += it } },
            { ToolProvider { if (failing) throw IllegalStateException("sessao invalida") else noTools.provideTools(it) } },
        )

        assertFailsWith<McpUnavailableException> { provider.provideTools(request) }
        failing = false
        provider.provideTools(request)

        assertEquals(2, clients.size)
        verify(exactly = 1) { clients[0].close() }
    }

    @Test
    fun `close fecha o cliente conectado`() {
        val client = mockk<McpClient>(relaxed = true)
        val provider = LazyMcpToolProvider("tools-mcp", { client }, { noTools })
        provider.provideTools(request)

        provider.close()

        verify(exactly = 1) { client.close() }
    }
}
```

- [ ] **Step 6: `AssistantAiServiceTest`**

`infrastructure/data/anticorruptionLayer/llm/impl/AssistantAiServiceTest.kt.template`:

```kotlin
package {base-package}.infrastructure.data.anticorruptionLayer.llm.impl

import {base-package}.infrastructure.observability.GenAiSpanEnricher
import {base-package}.infrastructure.observability.TracingProperties
import {base-package}.support.FakeToolProvider
import {base-package}.support.ScriptedChatModel
import {base-package}.support.ScriptedChatModel.Companion.answer
import {base-package}.support.ScriptedChatModel.Companion.callTool
import dev.langchain4j.data.message.SystemMessage
import dev.langchain4j.data.message.ToolExecutionResultMessage
<!-- se memoria -->
import dev.langchain4j.memory.chat.MessageWindowChatMemory
<!-- fim se memoria -->
import dev.langchain4j.model.chat.ChatModel
import dev.langchain4j.service.AiServices
import dev.langchain4j.service.tool.ToolProvider
import io.opentelemetry.api.common.AttributeKey
import io.opentelemetry.sdk.testing.junit5.OpenTelemetryExtension
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.RegisterExtension
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * O AI Service montado a mao, com modelo roteirizado e tool de mentira: prova
 * que os prompts carregam do classpath, que a tool e chamada e o resultado
 * volta ao modelo, e que o enricher anota o span. Nenhuma rede.
 */
class AssistantAiServiceTest {

    private fun assistant(model: ChatModel, tools: ToolProvider): AssistantAiService =
        AiServices.builder(AssistantAiService::class.java)
            .chatModel(model)
            .toolProvider(tools)
<!-- se memoria -->
            .chatMemoryProvider { memoryId -> MessageWindowChatMemory.builder().id(memoryId).maxMessages(10).build() }
<!-- fim se memoria -->
            .build()

    @Test
    fun `chama a tool e devolve ao usuario a resposta final do modelo`() {
        val toolArguments = mutableListOf<String>()
        val model = ScriptedChatModel(
            listOf(callTool(FakeToolProvider.TOOL, """{"id":"r-1"}"""), answer("Registro r-1 encontrado.")),
        )
        val tools = FakeToolProvider.create { toolArguments += it; """{"status":"ATIVO"}""" }

        val response = assistant(model, tools).chat("conv-1", "cade o registro r-1?")

        assertEquals("Registro r-1 encontrado.", response)
        assertEquals(1, toolArguments.size)
        assertTrue(toolArguments[0].contains("r-1"))
        assertTrue(model.requests[1].messages().any { it is ToolExecutionResultMessage })
    }

    @Test
    fun `manda o prompt de sistema carregado do classpath`() {
        val model = ScriptedChatModel(listOf(answer("ok")))

        assistant(model, FakeToolProvider.create { "" }).chat("conv-1", "oi")

        val system = model.requests[0].messages().filterIsInstance<SystemMessage>().single()
        assertTrue(system.text().isNotBlank())
    }
<!-- se memoria -->

    @Test
    fun `a segunda rodada da mesma conversa leva a primeira junto`() {
        val model = ScriptedChatModel(listOf(answer("primeira"), answer("segunda")))
        val service = assistant(model, FakeToolProvider.create { "" })

        service.chat("conv-1", "oi")
        service.chat("conv-1", "e agora?")

        assertTrue(model.requests[1].messages().size > model.requests[0].messages().size)
    }

    @Test
    fun `conversas diferentes nao compartilham memoria`() {
        val model = ScriptedChatModel(listOf(answer("primeira"), answer("segunda")))
        val service = assistant(model, FakeToolProvider.create { "" })

        service.chat("conv-1", "oi")
        service.chat("conv-2", "oi")

        assertEquals(model.requests[0].messages().size, model.requests[1].messages().size)
    }
<!-- fim se memoria -->

    @Test
    fun `o enricher anota o span corrente com atributos e conteudo GenAI`() {
        val properties = TracingProperties().apply {
            includePrompt = true
            includeCompletion = true
        }
        val model = ScriptedChatModel(listOf(answer("ok")), listOf(GenAiSpanEnricher(properties)))
        val span = otel.openTelemetry.getTracer("test").spanBuilder("chat").startSpan()

        span.makeCurrent().use { assistant(model, FakeToolProvider.create { "" }).chat("conv-1", "oi") }
        span.end()

        val recorded = otel.spans.single()
        assertEquals("chat", recorded.attributes.get(AttributeKey.stringKey("gen_ai.operation.name")))
        assertTrue(recorded.events.any { it.name == "gen_ai.content.prompt" })
        assertTrue(recorded.events.any { it.name == "gen_ai.content.completion" })
    }

    @Test
    fun `com as flags desligadas o enricher nao grava conteudo`() {
        val model = ScriptedChatModel(listOf(answer("ok")), listOf(GenAiSpanEnricher(TracingProperties())))
        val span = otel.openTelemetry.getTracer("test").spanBuilder("chat").startSpan()

        span.makeCurrent().use { assistant(model, FakeToolProvider.create { "" }).chat("conv-1", "oi") }
        span.end()

        assertTrue(otel.spans.single().events.isEmpty())
    }

    companion object {
        @JvmField
        @RegisterExtension
        val otel: OpenTelemetryExtension = OpenTelemetryExtension.create()
    }
}
```

- [ ] **Step 7: Renderizar, rodar e ver passar**

```bash
cd /tmp/new-agent-proof
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates
export VARS=$PWD/vars.env ON=kotlin,postgres,memoria,memoria-jdbc,buildingBlocks,web,it-dedicado
python3 render.py tree $R/source/kotlin/test demo/demo-agent/src/test/kotlin/br/com/analizza/demo
cd demo && ./gradlew :demo-agent:test --console=plain > /tmp/agent-test.log 2>&1; echo "EXIT=$?"
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
t = f = e = 0
for x in glob.glob('demo-agent/build/test-results/test/*.xml'):
    r = ET.parse(x).getroot(); t += int(r.get('tests')); f += int(r.get('failures')); e += int(r.get('errors'))
print(f"tests={t} failures={f} errors={e}")
PY
```

Expected: `EXIT=0` e `tests=36 failures=0 errors=0` (4 + 10 + 11 + 5 + 6). Leia o resultado do XML, não do `BUILD SUCCESSFUL`: um filtro errado deixa a task verde com zero testes.

Falha esperada mais provável: uma API do LangChain4j com outro nome (`ChatModel.listeners()`, `ToolExecutor` como SAM, `OpenTelemetryExtension`). Corrija o **template**, renderize de novo. Se o `ChatModel.chat()` padrão não invocar `listeners()`, os dois últimos testes do `AssistantAiServiceTest` falham por span sem atributo — nesse caso registre o achado e substitua os dois testes por um `GenAiSpanEnricherTest` que chame `onRequest`/`onResponse` direto, com `ChatModelRequestContext` e `ChatModelResponseContext` construídos à mão (o `Expected` cai para a nova contagem).

- [ ] **Step 8: Quebrar a produção e ver os testes falharem**

Cada mutação abaixo é no projeto de prova, uma por vez, desfeita em seguida (`git -C /tmp/new-agent-proof/demo stash` não serve — o projeto ainda não tem commit; refaça com o `render.py tree` do Step 9 da T2).

| Mutação em `demo-agent/src/main/kotlin/.../` | Teste que precisa falhar |
|---|---|
| `ChatInput.kt`: trocar `8000` por `80000` | `corpo acima de 8000 caracteres e recusado` |
| `ChatFailures.kt`: remover a linha do `McpUnavailableException` | `servidor MCP fora vira McpUpstreamException` |
| `ConversationIds.kt`: inverter a ordem dos dois primeiros ramos do `when` | `header vence o campo from` |
| `LazyMcpToolProvider.kt`: remover a chamada `discard()` do `catch` de `provideTools` | `falha ao listar as tools fecha o cliente e reconecta na proxima` |
| `GlobalExceptionHandler.kt`: em `upstream`, devolver `e.cause?.message` como mensagem | `falha do provedor devolve 502 sem vazar a causa` |

```bash
cd /tmp/new-agent-proof/demo && ./gradlew :demo-agent:test --console=plain > /tmp/agent-mut.log 2>&1; echo "EXIT=$?"
grep -E 'FAILED' /tmp/agent-mut.log
```

Expected, para cada mutação: `EXIT=1` e a linha `FAILED` do teste da tabela. Uma mutação que não derruba nenhum teste é um buraco: escreva o teste que falta no template antes de seguir. Ao final, renderize a produção de novo e confirme `EXIT=0`.

- [ ] **Step 9: Commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent/templates/source/kotlin/test
git commit -m "Templates Kotlin de teste unitario da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Arquivos da raiz — Makefile, ambiente local e LangWatch

**Files** (todos sob `$S/templates/root/`):
- Create: `Makefile.template` (modo do zero)
- Create: `Makefile.agent-targets.template` (modo existente: alvos a acrescentar)
- Create: `docker-compose.agent-postgres.template` (modo existente com banco)
- Create: `docker-compose.langwatch.yml.template`, `langwatch.env.example.template`
- Create: `local.env.example.template`, `local.env.ollama.example.template`
- Create: `gitignore-extra.template`

**Interfaces:**
- Consumes: `../analizza-new-project/templates/docker-compose.template` (Postgres do modo do zero); a porta e as variáveis `LLM_*`, `{mcp-env}_*`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGWATCH_API_KEY` do `application.yaml` (T2).
- Produces: alvos `run-agent`, `run-agent-ollama`, `langwatch-up`, `langwatch-down`, `langwatch-logs`, `test-backend`, e (com `it-no-modulo`) `test-integration` / (existente) `test-agent-integration`. A T8 cita esses nomes no `SKILL.md` e no runbook.

Nos blocos de Makefile abaixo, `@@TAB@@` marca o caractere TAB que inicia cada linha de receita. Ao gravar o template, troque cada `@@TAB@@` por um TAB de verdade (Step 6 faz isso com `sed`).

- [ ] **Step 1: `Makefile.template`**

```make
AGENT_DIR := {agent-module}
<!-- se web -->
WEB_DIR   := {project-name}-web
<!-- fim se web -->
GRADLEW   := ./gradlew

AGENT_PORT ?= {agent-port}
<!-- se web -->
WEB_PORT ?= 3000
<!-- fim se web -->

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Carrega um arquivo de variaveis e sobe o agente. O arquivo nunca e
# versionado; o .example ao lado dele e.
define run_agent_with
@@TAB@@@test -f $(1) || { echo "Erro: $(1) nao existe. Copie com: cp $(1).example $(1)"; exit 1; }
@@TAB@@set -a && . ./$(1) && set +a && $(GRADLEW) :$(AGENT_DIR):bootRun --console=plain
endef

##@ Geral

.PHONY: help
help: ## Mostra esta ajuda
@@TAB@@@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make \033[36m<alvo>\033[0m\n"} \
@@TAB@@@@TAB@@/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
@@TAB@@@@TAB@@/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
@@TAB@@@echo ""
<!-- se web -->

##@ Dependências

$(WEB_DIR)/node_modules: $(WEB_DIR)/package-lock.json
@@TAB@@cd $(WEB_DIR) && npm ci
@@TAB@@@touch $@

.PHONY: install
install: $(WEB_DIR)/node_modules ## Instala dependências do web
<!-- fim se web -->
<!-- se postgres -->

##@ Banco

.PHONY: db-up
db-up: ## Sobe o Postgres e espera ficar saudável
@@TAB@@docker compose up -d --wait

.PHONY: db-down
db-down: ## Derruba o Postgres (mantém o volume)
@@TAB@@docker compose down

.PHONY: db-reset
db-reset: ## Derruba o Postgres e apaga o volume de dados
@@TAB@@docker compose down -v
<!-- fim se postgres -->

##@ Build

.PHONY: build
<!-- se web -->
build: build-backend build-web ## Builda backend e web
<!-- fim se web -->
<!-- se sem-web -->
build: build-backend ## Builda o backend
<!-- fim se sem-web -->

.PHONY: build-backend
build-backend: ## Compila e roda os testes unitários (não precisa de banco nem de LLM)
@@TAB@@$(GRADLEW) build
<!-- se web -->

.PHONY: build-web
build-web: $(WEB_DIR)/node_modules ## Builda o web (produção)
@@TAB@@cd $(WEB_DIR) && npm run build
<!-- fim se web -->

##@ Testes

.PHONY: test-backend
test-backend: ## Testes unitários do backend (LLM roteirizado, sem rede)
@@TAB@@$(GRADLEW) test
<!-- se it-no-modulo -->

.PHONY: test-integration
test-integration: ## Testes de integração (*IT) com Ollama em Testcontainers; a 1ª execução baixa ~2 GB
@@TAB@@$(GRADLEW) :$(AGENT_DIR):integrationTest
<!-- fim se it-no-modulo -->
<!-- se web -->

.PHONY: test-web
test-web: $(WEB_DIR)/node_modules ## Lint do web
@@TAB@@cd $(WEB_DIR) && npm run lint
<!-- fim se web -->

##@ Execução

.PHONY: run-agent
<!-- se postgres -->
run-agent: db-up ## Sobe o agente com as variáveis de local.env
<!-- fim se postgres -->
<!-- se sem-postgres -->
run-agent: ## Sobe o agente com as variáveis de local.env
<!-- fim se sem-postgres -->
@@TAB@@$(call run_agent_with,local.env)

.PHONY: run-agent-ollama
<!-- se postgres -->
run-agent-ollama: db-up ## Sobe o agente contra o Ollama local (local.env.ollama)
<!-- fim se postgres -->
<!-- se sem-postgres -->
run-agent-ollama: ## Sobe o agente contra o Ollama local (local.env.ollama)
<!-- fim se sem-postgres -->
@@TAB@@$(call run_agent_with,local.env.ollama)
<!-- se web -->

.PHONY: run-web
run-web: $(WEB_DIR)/node_modules ## Roda o web (dev) em http://localhost:$(WEB_PORT)
@@TAB@@cd $(WEB_DIR) && AGENT_URL=http://localhost:$(AGENT_PORT) npm run dev

.PHONY: run
run: $(WEB_DIR)/node_modules ## Sobe agente (Ollama local) e web juntos; Ctrl+C encerra os dois
@@TAB@@@echo "agente -> http://localhost:$(AGENT_PORT)"
@@TAB@@@echo "web    -> http://localhost:$(WEB_PORT)"
@@TAB@@@trap 'kill 0' INT TERM; \
@@TAB@@@@TAB@@( $(MAKE) --no-print-directory run-agent-ollama 2>&1 | awk '{ print "[agente] " $$0; fflush() }' ) & \
@@TAB@@@@TAB@@( $(MAKE) --no-print-directory run-web 2>&1 | awk '{ print "[web] " $$0; fflush() }' ) & \
@@TAB@@@@TAB@@wait
<!-- fim se web -->

##@ Observabilidade

.PHONY: langwatch-up
langwatch-up: ## Sobe o LangWatch local em http://localhost:5560
@@TAB@@@test -f langwatch.env || { echo "Erro: langwatch.env nao existe. Copie com: cp langwatch.env.example langwatch.env"; exit 1; }
@@TAB@@docker compose -f docker-compose.langwatch.yml --env-file langwatch.env up -d

.PHONY: langwatch-down
langwatch-down: ## Derruba o LangWatch local
@@TAB@@docker compose -f docker-compose.langwatch.yml --env-file langwatch.env down

.PHONY: langwatch-logs
langwatch-logs: ## Acompanha os logs do LangWatch local
@@TAB@@docker compose -f docker-compose.langwatch.yml --env-file langwatch.env logs -f

##@ Limpeza

.PHONY: clean
clean: ## Remove artefatos de build
@@TAB@@$(GRADLEW) clean
<!-- se web -->
@@TAB@@rm -rf $(WEB_DIR)/.next
<!-- fim se web -->
```

As condições negativas (`sem-web`, `sem-postgres`) precisam estar no `ON` do `render.py` quando `web`/`postgres` não valerem: o script não deduz o complemento.

- [ ] **Step 2: `Makefile.agent-targets.template`**

Acrescentado ao fim do `Makefile` de um projeto existente. Se o projeto não tiver `Makefile`, este arquivo vira o `Makefile` inteiro, precedido de `GRADLEW := ./gradlew` e `SHELL := /bin/bash`.

```make

##@ Agente

AGENT_DIR  := {agent-module}
AGENT_PORT ?= {agent-port}

# Carrega um arquivo de variaveis e sobe o agente. O arquivo nunca e
# versionado; o .example ao lado dele e.
define run_agent_with
@@TAB@@@test -f $(1) || { echo "Erro: $(1) nao existe. Copie com: cp $(1).example $(1)"; exit 1; }
@@TAB@@set -a && . ./$(1) && set +a && ./gradlew :$(AGENT_DIR):bootRun --console=plain
endef

.PHONY: run-agent
run-agent: ## Sobe o agente com as variáveis de local.env
@@TAB@@$(call run_agent_with,local.env)

.PHONY: run-agent-ollama
run-agent-ollama: ## Sobe o agente contra o Ollama local (local.env.ollama)
@@TAB@@$(call run_agent_with,local.env.ollama)

.PHONY: test-agent
test-agent: ## Testes unitários do agente (LLM roteirizado, sem rede)
@@TAB@@./gradlew :$(AGENT_DIR):test

.PHONY: test-agent-integration
test-agent-integration: ## Testes de integração do agente com Ollama em Testcontainers; a 1ª execução baixa ~2 GB
@@TAB@@./gradlew :$(AGENT_DIR):integrationTest

.PHONY: langwatch-up
langwatch-up: ## Sobe o LangWatch local em http://localhost:5560
@@TAB@@@test -f langwatch.env || { echo "Erro: langwatch.env nao existe. Copie com: cp langwatch.env.example langwatch.env"; exit 1; }
@@TAB@@docker compose -f docker-compose.langwatch.yml --env-file langwatch.env up -d

.PHONY: langwatch-down
langwatch-down: ## Derruba o LangWatch local
@@TAB@@docker compose -f docker-compose.langwatch.yml --env-file langwatch.env down
```

- [ ] **Step 3: Arquivos de ambiente**

`local.env.example.template`:

```
################################################################################
# Ambiente local do {agent-module}
#
#   cp local.env.example local.env     (local.env e git-ignored)
#   make run-agent
#
# Nunca versione este arquivo com valores reais.
# Para rodar 100% local, sem chave, use local.env.ollama.example.
################################################################################

# --- LLM (obrigatorio): qualquer provedor OpenAI-compativel -------------------
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_TOKEN=change-it
LLM_MODEL=gpt-4o-mini

# --- Aplicacao ----------------------------------------------------------------
SPRING_PROFILES_ACTIVE=dev
PORT={agent-port}
LOG_LEVEL=INFO

# --- Servidor MCP {mcp-name} --------------------------------------------------
{mcp-env}_ENABLED={mcp-enabled}
{mcp-env}_BASE_URL={mcp-url}
# Valor inteiro do header Authorization, entre aspas se tiver espaco:
#   {mcp-env}_AUTHORIZATION="Bearer <token>"
{mcp-env}_AUTHORIZATION=

# --- Traces -> LangWatch local (make langwatch-up) ----------------------------
# A chave e criada na interface do LangWatch (http://localhost:5560), em
# Settings > API Key, depois do primeiro login.
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:5560/api/otel/v1/traces
LANGWATCH_API_KEY=change-it

# O profile dev ja liga a captura de prompt, resposta e tool calls nos traces.
# MANTENHA COMENTADO: variavel de ambiente vence o profile e desligaria a
# captura em dev.
#LANGCHAIN4J_TRACING_INCLUDE_PROMPT=false
#LANGCHAIN4J_TRACING_INCLUDE_COMPLETION=false
#LANGCHAIN4J_TRACING_INCLUDE_TOOL_ARGUMENTS=false
#LANGCHAIN4J_TRACING_INCLUDE_TOOL_RESULT=false
```

`local.env.ollama.example.template`:

```
################################################################################
# Ambiente local do {agent-module} com Ollama (sem chave, sem custo)
#
#   1. Instale o Ollama: https://ollama.com/download
#   2. Baixe um modelo:  ollama pull qwen2.5:7b
#   3. Copie:            cp local.env.ollama.example local.env.ollama
#   4. Rode:             make run-agent-ollama
#
# Modelo pequeno erra mais em tool calling. Se o agente nao chamar as tools do
# servidor MCP, tente um modelo maior antes de mexer no prompt.
################################################################################

LLM_BASE_URL=http://localhost:11434/v1
LLM_API_TOKEN=ollama
LLM_MODEL=qwen2.5:7b
# Inferencia em CPU e lenta: o default de 120s nao basta para modelo local.
LLM_TIMEOUT=PT300S

SPRING_PROFILES_ACTIVE=dev
PORT={agent-port}
LOG_LEVEL=DEBUG

{mcp-env}_ENABLED={mcp-enabled}
{mcp-env}_BASE_URL={mcp-url}
{mcp-env}_AUTHORIZATION=

OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:5560/api/otel/v1/traces
LANGWATCH_API_KEY=change-it
```

`gitignore-extra.template`:

```

# --- Ambiente do agente (nunca versionar) ---
local.env
local.env.ollama
langwatch.env
<!-- se web -->

# --- Frontend ---
node_modules/
.next/
out/
*.tsbuildinfo
.env
.env.local
.env.*.local
<!-- fim se web -->

# --- macOS ---
.DS_Store
```

- [ ] **Step 4: Banco do agente no modo existente**

`docker-compose.agent-postgres.template` — o serviço entra sob `services:` e o volume sob `volumes:` do `docker-compose.yml` que o projeto já tem (ou vira o arquivo inteiro, se não houver):

```yaml
  # Banco do agente, separado do banco do -core: dois Flyway no mesmo schema
  # disputam a mesma flyway_schema_history.
  postgres-agent:
    image: postgres:17-alpine
    container_name: {project-name}-agent-postgres
    environment:
      POSTGRES_DB: {db-name}
      POSTGRES_USER: {db-name}
      POSTGRES_PASSWORD: {db-name}
    ports:
      - "{db-port}:5432"
    volumes:
      - postgres-agent-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {db-name} -d {db-name}"]
      interval: 5s
      timeout: 3s
      retries: 10

# sob volumes:
  postgres-agent-data:
```

- [ ] **Step 5: LangWatch local**

Vem do `agent-invest-sgap`, com uma mudança: o Postgres **dele** não publica a porta 5432 no host, que é a do banco do projeto.

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
REF=/Users/diegolirio/Documents/Github/agent-invest-sgap
ROOT=plugins/analizza-skills/skills/analizza-new-agent/templates/root
python3 - "$REF/docker-compose.langwatch.yml" "$ROOT/docker-compose.langwatch.yml.template" <<'PY'
import sys
texto = open(sys.argv[1]).read()
publicada = '    ports:\n      - "5432:5432"\n'
assert texto.count(publicada) == 1, "esperava exatamente um mapeamento 5432:5432"
texto = texto.replace(publicada, "    # Sem porta publicada: 5432 no host e do banco do projeto.\n")
open(sys.argv[2], "w").write(texto)
PY
cp "$REF/langwatch.env.example" "$ROOT/langwatch.env.example.template"
grep -n 'local.env.example\|Seldon\|corporativo' "$ROOT/langwatch.env.example.template"
```

O `grep` aponta as linhas que falam do LangWatch corporativo da Pags. Substitua aquele parágrafo do cabeçalho por:

```
# Este LangWatch e so local: serve para ver os traces do agente durante o
# desenvolvimento. Nao e o ambiente de observabilidade de producao.
```

Verifique que o compose é válido:

```bash
cd /tmp && mkdir -p lw-check && cp /Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates/root/docker-compose.langwatch.yml.template lw-check/docker-compose.langwatch.yml
printf 'LANGWATCH_API_TOKEN_JWT_SECRET=a\nLANGWATCH_CREDENTIALS_SECRET=b\nLANGWATCH_NEXTAUTH_SECRET=c\nLANGWATCH_CRON_API_KEY=d\n' > lw-check/langwatch.env
docker compose -f lw-check/docker-compose.langwatch.yml --env-file lw-check/langwatch.env config -q; echo "EXIT=$?"
grep -c '5432:5432' lw-check/docker-compose.langwatch.yml
```

Expected: `EXIT=0` e `0`.

- [ ] **Step 6: Gravar os Makefiles com TAB e renderizar no projeto de prova**

Depois de criar os dois templates de Makefile com `@@TAB@@` literal:

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates/root
for f in Makefile.template Makefile.agent-targets.template; do
  python3 -c "import sys,pathlib; p=pathlib.Path(sys.argv[1]); p.write_text(p.read_text().replace('@@TAB@@','\t'))" $f
  grep -c '@@TAB@@' $f; grep -c $'^\t' $f
done

cd /tmp/new-agent-proof
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills
export VARS=$PWD/vars.env ON=kotlin,postgres,memoria,memoria-jdbc,buildingBlocks,web,it-dedicado
python3 render.py file $R/analizza-new-agent/templates/root/Makefile.template demo/Makefile
python3 render.py file $R/analizza-new-agent/templates/root/local.env.example.template demo/local.env.example
python3 render.py file $R/analizza-new-agent/templates/root/local.env.ollama.example.template demo/local.env.ollama.example
python3 render.py file $R/analizza-new-agent/templates/root/langwatch.env.example.template demo/langwatch.env.example
python3 render.py file $R/analizza-new-agent/templates/root/docker-compose.langwatch.yml.template demo/docker-compose.langwatch.yml
python3 render.py file $R/analizza-new-project/templates/docker-compose.template demo/docker-compose.yml
python3 render.py file $R/analizza-new-agent/templates/root/gitignore-extra.template /tmp/new-agent-proof/gitignore-extra && cat /tmp/new-agent-proof/gitignore-extra >> demo/.gitignore
cd demo && make help; echo "EXIT=$?"
make run-agent; echo "EXIT=$?"
make -n run-agent-ollama | head -5
```

Expected: para cada Makefile, `0` sentinelas restantes e mais de 10 linhas com TAB; `make help` lista os grupos Geral, Dependências, Banco, Build, Testes, Execução, Observabilidade e Limpeza com `EXIT=0`; `make run-agent` falha com `Erro: local.env nao existe. Copie com: cp local.env.example local.env` e `EXIT=2`; o `make -n` mostra `docker compose up -d --wait` seguido do `bootRun`.

- [ ] **Step 7: Commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent/templates/root
git commit -m "Makefile, ambiente local e LangWatch da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Camada de integração com LLM real (Kotlin)

**Files:**
- Create: `$S/templates/source/kotlin/it/support/OllamaTestContainer.kt.template`
- Create: `$S/templates/source/kotlin/it/support/BaseIntegrationTest.kt.template` (só `it-no-modulo`)
- Create: `$S/templates/source/kotlin/it/presenter/routes/chat/ChatRouteIT.kt.template`
- Create: `$S/references/it-llm-layer.md`

**Interfaces:**
- Consumes: `POST /api/v1/agent/http`, `/stream`, o header `X-Conversation-Id`, o corpo de erro `{code, message}` e as métricas `chat.requests` (T2); a tabela `chat_memory(memory_id, content)`.
- Produces: `OllamaTestContainer.model: String`, `OllamaTestContainer.openAiBaseUrl(): String`, `OllamaTestContainer.registerLlm(registry: DynamicPropertyRegistry, mcpName: String)`; classe abstrata `{base-package}.support.BaseIntegrationTest` com o campo protegido `http: RestTestClient` — o **mesmo nome e pacote** da base que a `analizza-integration-test` gera, para o `ChatRouteIT` ser um arquivo só nos dois layouts.

A base se chama `BaseIntegrationTest` nos dois layouts, justamente para o `ChatRouteIT` não ter variante.

- [ ] **Step 1: `OllamaTestContainer`**

```kotlin
package {base-package}.support

import org.springframework.test.context.DynamicPropertyRegistry
import org.testcontainers.DockerClientFactory
import org.testcontainers.ollama.OllamaContainer
import org.testcontainers.utility.DockerImageName
import java.util.Locale

/**
 * LLM real dos testes de integracao: Ollama em container, um por JVM, iniciado
 * de forma eager -- o mesmo estilo do container de banco da base.
 *
 * Para nao baixar o modelo (~2 GB) a cada execucao: na primeira vez sobe a
 * imagem base, faz `ollama pull` e grava o container como a imagem local
 * `tc-ollama-<modelo>`; nas seguintes sobe direto dela. Para refazer o cache:
 * `docker rmi tc-ollama-<modelo>`.
 *
 * Modelo padrao qwen2.5:3b: faz tool calling e nao emite tags de "thinking".
 * Troque com a system property ou variavel de ambiente IT_OLLAMA_MODEL.
 */
object OllamaTestContainer {

    private const val BASE_IMAGE = "ollama/ollama:0.34.3"
    private const val DEFAULT_MODEL = "qwen2.5:3b"

    val model: String = (System.getProperty("IT_OLLAMA_MODEL") ?: System.getenv("IT_OLLAMA_MODEL"))
        ?.trim()
        ?.takeIf { it.isNotEmpty() }
        ?: DEFAULT_MODEL

    val container: OllamaContainer = start()

    /** URL OpenAI-compativel do container. */
    fun openAiBaseUrl(): String = container.endpoint + "/v1"

    /**
     * Aponta os dois modelos do LangChain4j para o container e desliga o que
     * nao e deste teste: o servidor MCP (outro sistema) e a exportacao de traces.
     */
    fun registerLlm(registry: DynamicPropertyRegistry, mcpName: String) {
        for (prefix in listOf("langchain4j.open-ai.chat-model", "langchain4j.open-ai.streaming-chat-model")) {
            registry.add("$prefix.base-url") { openAiBaseUrl() }
            registry.add("$prefix.api-key") { "ollama" }
            registry.add("$prefix.model-name") { model }
            // Inferencia em CPU: uma chamada pode levar minutos.
            registry.add("$prefix.timeout") { "PT300S" }
        }
        registry.add("$mcpName.enabled") { "false" }
        registry.add("management.tracing.sampling.probability") { "0.0" }
    }

    private fun start(): OllamaContainer {
        val cachedImage = "tc-ollama-" + model.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9._-]"), "-")
        val cached = DockerClientFactory.instance().client()
            .listImagesCmd()
            .withReferenceFilter(cachedImage)
            .exec()
            .isNotEmpty()

        val started = if (cached) {
            OllamaContainer(DockerImageName.parse(cachedImage).asCompatibleSubstituteFor("ollama/ollama"))
        } else {
            OllamaContainer(BASE_IMAGE)
        }
        started.start()
        if (!cached) {
            val pull = started.execInContainer("ollama", "pull", model)
            check(pull.exitCode == 0) { "ollama pull $model falhou: ${pull.stderr}" }
            started.commitToImage(cachedImage)
        }
        return started
    }
}
```

- [ ] **Step 2: `BaseIntegrationTest` para os ITs dentro do módulo**

```kotlin
<!-- arquivo se it-no-modulo -->
package {base-package}.support

import {base-package}.{app-class}
import org.junit.jupiter.api.BeforeEach
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.boot.test.web.server.LocalServerPort
<!-- se postgres -->
import org.springframework.boot.testcontainers.service.connection.ServiceConnection
<!-- fim se postgres -->
import org.springframework.http.client.JdkClientHttpRequestFactory
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.springframework.test.web.servlet.client.RestTestClient
<!-- se postgres -->
import org.testcontainers.postgresql.PostgreSQLContainer
<!-- fim se postgres -->

/**
 * Base de todo teste de integracao do agente: toda classe terminada em IT a
 * estende. Aplicacao inteira em porta aleatoria, LLM real em container.
 *
 * Os containers sao um por suite, iniciados na mao e sem @Container: o ciclo
 * do @Container e por classe e reiniciaria tudo a cada IT.
 */
@SpringBootTest(
    classes = [{app-class}::class],
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
)
abstract class BaseIntegrationTest {

    @LocalServerPort
    private var port: Int = 0

    protected lateinit var http: RestTestClient

    @BeforeEach
    fun prepararCliente() {
        // O JdkClientHttpRequestFactory vai explicito porque bindToServer() sem
        // argumento escolhe o cliente HTTP pelo classpath, e o webflux deste
        // modulo traria outro transporte para o teste.
        http = RestTestClient.bindToServer(JdkClientHttpRequestFactory())
            .baseUrl("http://localhost:$port")
            .build()
    }

    companion object {
<!-- se postgres -->
        @JvmStatic
        @field:ServiceConnection
        val database: PostgreSQLContainer = PostgreSQLContainer("postgres:17-alpine").also { it.start() }

<!-- fim se postgres -->
        @JvmStatic
        @DynamicPropertySource
        fun llm(registry: DynamicPropertyRegistry) {
            OllamaTestContainer.registerLlm(registry, "{mcp-name}")
        }
    }
}
```

- [ ] **Step 3: `ChatRouteIT`**

```kotlin
package {base-package}.presenter.routes.chat

import {base-package}.support.BaseIntegrationTest
import org.junit.jupiter.api.Test
<!-- se memoria-jdbc -->
import org.springframework.beans.factory.annotation.Autowired
<!-- fim se memoria-jdbc -->
import org.springframework.http.MediaType
import java.util.UUID
<!-- se memoria-jdbc -->
import javax.sql.DataSource
<!-- fim se memoria-jdbc -->
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/**
 * A conversa de ponta a ponta: HTTP de verdade, aplicacao inteira, LLM real
 * (Ollama em container). As assercoes toleram um modelo pequeno -- afirmam
 * status, forma e efeitos colaterais, nunca o texto da resposta. O que precisa
 * de texto exato e teste unitario com ScriptedChatModel.
 */
class ChatRouteIT : BaseIntegrationTest() {
<!-- se memoria-jdbc -->

    @Autowired
    private lateinit var dataSource: DataSource

    private fun memoryRows(conversationId: String): Int =
        dataSource.connection.use { connection ->
            connection.prepareStatement("SELECT count(*) FROM chat_memory WHERE memory_id = ?").use { statement ->
                statement.setString(1, conversationId)
                statement.executeQuery().use { it.next(); it.getInt(1) }
            }
        }
<!-- fim se memoria-jdbc -->

    private fun post(path: String, json: String, conversationId: String) =
        http.post().uri(path)
            .contentType(MediaType.APPLICATION_JSON)
            .header(ConversationIds.HEADER, conversationId)
            .body(json)
            .exchange()

    @Test
    fun `http responde com o LLM real, ecoa a conversa e registra a metrica`() {
        val conversationId = "it-${UUID.randomUUID()}"

        val body = post("/api/v1/agent/http", """{"body":"Responda com uma unica palavra: ok"}""", conversationId)
            .expectStatus().isOk
            .expectHeader().valueEquals(ConversationIds.HEADER, conversationId)
            .expectBody(String::class.java)
            .returnResult()
            .responseBody

        assertNotNull(body)
        assertTrue(Regex("\"response\"\\s*:\\s*\"[^\"]").containsMatchIn(body), "resposta vazia: $body")
<!-- se memoria-jdbc -->
        // Uma linha por conversa: a janela de mensagens e um JSON so.
        assertEquals(1, memoryRows(conversationId))
<!-- fim se memoria-jdbc -->

        val metrics = http.get().uri("/actuator/prometheus").exchange()
            .expectStatus().isOk
            .expectBody(String::class.java)
            .returnResult()
            .responseBody
        assertNotNull(metrics)
        assertTrue(metrics.contains("chat_requests_total"), "metrica chat_requests_total ausente")
    }

    @Test
    fun `stream devolve eventos SSE`() {
        val body = post("/api/v1/agent/stream", """{"body":"Responda com uma unica palavra: ok"}""", "it-${UUID.randomUUID()}")
            .expectStatus().isOk
            .expectBody(String::class.java)
            .returnResult()
            .responseBody

        assertNotNull(body)
        assertTrue(body.contains("data:"), "nenhum evento SSE: $body")
    }

    @Test
    fun `corpo em branco devolve 400 sem chamar o LLM`() {
        val conversationId = "it-${UUID.randomUUID()}"

        val body = post("/api/v1/agent/http", """{"body":"   "}""", conversationId)
            .expectStatus().isBadRequest
            .expectBody(String::class.java)
            .returnResult()
            .responseBody

        assertNotNull(body)
        assertTrue(body.contains("INVALID_REQUEST"))
<!-- se memoria-jdbc -->
        assertEquals(0, memoryRows(conversationId))
<!-- fim se memoria-jdbc -->
    }
}
```

Sem `memoria-jdbc` o `import kotlin.test.assertEquals` fica sem uso. Envolva essa linha de import no mesmo marcador `<!-- se memoria-jdbc -->` ao gravar o template.

- [ ] **Step 4: `references/it-llm-layer.md`**

É o que a skill aplica **depois** que a `analizza-integration-test` criou o módulo dedicado (layout `it-dedicado`).

````markdown
# A camada de LLM sobre o módulo de testes de integração

A `analizza-integration-test` entrega `{project-name}-integration-tests` com
`BaseIntegrationTest`, banco em container e a regra ArchUnit. Ela não sabe que
a aplicação depende de um LLM. Sem esta camada, o contexto do
`ApplicationContextIT` nem sobe: `LLM_BASE_URL`, `LLM_API_TOKEN` e `LLM_MODEL`
não têm default (de propósito).

## 1. Dependência do módulo de IT

No `build.gradle{dsl-ext}` de `{project-name}-integration-tests`, junto dos
outros módulos do Testcontainers:

```kotlin
    testImplementation("org.testcontainers:testcontainers-ollama")   // kts
```

```groovy
    testImplementation 'org.testcontainers:testcontainers-ollama'    // groovy
```

## 2. `OllamaTestContainer` e `ChatRouteIT`

Copie de `templates/source/{language}/it/` para o módulo de IT, pela regra de
espelhamento: `support/OllamaTestContainer` e
`presenter/routes/chat/ChatRouteIT`. **Não** copie o `support/BaseIntegrationTest`
do template — ele é do layout `it-no-modulo`; aqui a base é a que a
`analizza-integration-test` gerou.

## 3. Ligar o LLM na base que já existe

Em `support/BaseIntegrationTest`, acrescente o método abaixo ao lado do
container de banco, e os dois imports.

Kotlin — dentro do `companion object`:

```kotlin
        @JvmStatic
        @DynamicPropertySource
        fun llm(registry: DynamicPropertyRegistry) {
            OllamaTestContainer.registerLlm(registry, "{mcp-name}")
        }
```

Java — método estático da classe:

```java
    @DynamicPropertySource
    static void llm(DynamicPropertyRegistry registry) {
        OllamaTestContainer.registerLlm(registry, "{mcp-name}");
    }
```

Imports: `org.springframework.test.context.DynamicPropertyRegistry` e
`org.springframework.test.context.DynamicPropertySource`.

## 4. Conferir

```bash
./gradlew integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
```

`EXIT=0`, com `ChatRouteIT`, `ApplicationContextIT` e
`EntrypointHasIntegrationTestIT` no XML de resultado. A regra ArchUnit passa
porque a `ChatRoute` — o único `@RestController` — tem o `ChatRouteIT`.

A primeira execução baixa a imagem do Ollama e o modelo (~2 GB) e grava a
imagem local `tc-ollama-<modelo>`; as seguintes sobem direto dela.
````

- [ ] **Step 5: Verificar no projeto de prova, com os ITs dentro do módulo**

O layout dedicado depende da `analizza-integration-test` e é provado na T9. Aqui o projeto de prova troca para `it-no-modulo`, que exercita os mesmos três arquivos:

```bash
cd /tmp/new-agent-proof
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates
export VARS=$PWD/vars.env ON=kotlin,postgres,memoria,memoria-jdbc,buildingBlocks,web,it-no-modulo
python3 render.py file $R/build/kts/agent-module.gradle.kts.template demo/demo-agent/build.gradle.kts
python3 render.py tree $R/source/kotlin/it demo/demo-agent/src/test/kotlin/br/com/analizza/demo
cd demo && ./gradlew :demo-agent:test --console=plain > /tmp/agent-test.log 2>&1; echo "EXIT=$?"
./gradlew :demo-agent:integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
for x in sorted(glob.glob('demo-agent/build/test-results/integrationTest/*.xml')):
    r = ET.parse(x).getroot()
    print(r.get('name'), 'tests=' + r.get('tests'), 'failures=' + r.get('failures'), 'errors=' + r.get('errors'), 'time=' + r.get('time'))
PY
docker images --format '{{.Repository}}' | grep -c '^tc-ollama-qwen2.5-3b$'
```

Expected: `test` com `EXIT=0` (os 36 unitários continuam passando e nenhum `*IT` roda nele); `integrationTest` com `EXIT=0` e `ChatRouteIT tests=3 failures=0 errors=0`; a imagem `tc-ollama-qwen2.5-3b` existe (`1`). Sem a imagem em cache a primeira execução leva vários minutos — não interrompa.

Falhas prováveis e onde corrigir (sempre no template):
- `testcontainers-ollama` não resolve → o BOM do Boot em uso ainda é Testcontainers 1.x; o artefato lá é `org.testcontainers:ollama`. Registre qual vale e ajuste os dois templates de build e o `it-llm-layer.md`.
- `expectHeader().valueEquals` não existe no `RestTestClient` → use `.returnResult()` e leia `responseHeaders.getFirst(...)`.
- O IT de stream estoura o timeout do cliente → o `JdkClientHttpRequestFactory` não tem timeout de leitura por padrão; se tiver, configure `setReadTimeout(Duration.ofMinutes(5))`.

- [ ] **Step 6: Ver um IT falhar por motivo real**

No projeto de prova, em `ChatTelemetry.kt`, troque `"chat.requests"` por `"chat.pedidos"` e rode só o IT:

```bash
cd /tmp/new-agent-proof/demo && ./gradlew :demo-agent:integrationTest --console=plain > /tmp/agent-it-mut.log 2>&1; echo "EXIT=$?"
grep -E 'metrica chat_requests_total ausente' -r demo-agent/build/test-results/integrationTest | head -2
```

Expected: `EXIT=1` com a mensagem da asserção. Desfaça a mutação (renderize a produção de novo) e confirme `EXIT=0`.

- [ ] **Step 7: Smoke com LLM de verdade pelo Makefile**

```bash
cd /tmp/new-agent-proof/demo
docker run -d --rm --name agent-proof-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
sed -e 's#http://localhost:11434/v1#http://localhost:11435/v1#' -e 's#qwen2.5:7b#qwen2.5:3b#' local.env.ollama.example > local.env.ollama
make run-agent-ollama > /tmp/agent-run.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1 && break; sleep 2; done
curl -s -D - -X POST http://localhost:8080/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: smoke-1' -d '{"body":"Diga oi em uma palavra."}'
curl -s -N --max-time 240 -X POST http://localhost:8080/api/v1/agent/stream -H 'Content-Type: application/json' -H 'X-Conversation-Id: smoke-1' -d '{"body":"E agora diga tchau."}' | head -5
curl -s http://localhost:8080/actuator/prometheus | grep '^chat_requests_total'
docker exec demo-postgres psql -U demo -d demo -tc "select memory_id, length(content) from chat_memory"
pkill -f 'demo-agent'; make db-down; docker stop agent-proof-ollama
```

Expected: `200` com `X-Conversation-Id: smoke-1` e `{"response":"..."}` não vazio; linhas `data:` no stream; `chat_requests_total{outcome="success"} 2.0`; uma linha `smoke-1` em `chat_memory`. Confirme que 8080 ficou livre (`lsof -i :8080` vazio) antes de seguir.

- [ ] **Step 8: Commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent
git commit -m "Camada de integracao com Ollama da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Tela de chat no web

**Files** (todos sob `$S/templates/web/src/`):
- Create: `lib/sse.ts.template`, `lib/sse.test.ts.template`
- Create: `app/api/chat/route.ts.template`, `app/api/chat/route.test.ts.template`
- Create: `app/page.tsx.template`

**Interfaces:**
- Consumes: `POST {AGENT_URL}/api/v1/agent/stream` com corpo `{"body": string}` e header `X-Conversation-Id`; resposta `text/event-stream` em que cada evento é `data:<token>` seguido de linha em branco; erro como `{code, message}` (T2).
- Produces: `parseSse(buffer: string): { data: string[]; rest: string }`; rota `POST /api/chat` no Next, que repassa o stream. O destino de cada template é `{project-name}-web/src/<caminho>`, substituindo o `page.tsx` do `create-next-app`.

O `create-next-app` não traz framework de teste. Quem instala o Vitest no projeto gerado é a `analizza-integration-test` (escopo frontend), depois desta etapa; os dois `*.test.ts` daqui já ficam prontos para ela. Na verificação desta tarefa o Vitest entra à mão.

- [ ] **Step 1: Escrever o teste do parser de SSE**

`lib/sse.test.ts.template`:

```ts
import { describe, expect, it } from "vitest";
import { parseSse } from "./sse";

describe("parseSse", () => {
  it("extrai o dado de cada evento completo", () => {
    expect(parseSse("data:Ol\n\ndata:á\n\n")).toEqual({ data: ["Ol", "á"], rest: "" });
  });

  it("devolve como resto o evento que ainda não terminou", () => {
    expect(parseSse("data:Ol\n\ndata:á")).toEqual({ data: ["Ol"], rest: "data:á" });
  });

  it("preserva o espaço no início do token", () => {
    // O Spring escreve "data:" + token, sem espaço separador. Um token " mundo"
    // chega como "data: mundo"; tirar esse espaço cola as palavras.
    expect(parseSse("data:Olá\n\ndata: mundo\n\n").data.join("")).toBe("Olá mundo");
  });

  it("junta com quebra de linha um evento de várias linhas data", () => {
    expect(parseSse("data:linha 1\ndata:linha 2\n\n").data).toEqual(["linha 1\nlinha 2"]);
  });

  it("ignora linhas que não são data", () => {
    expect(parseSse(":comentario\nevent:x\ndata:ok\n\n").data).toEqual(["ok"]);
  });

  it("aceita CRLF", () => {
    expect(parseSse("data:ok\r\n\r\n").data).toEqual(["ok"]);
  });
});
```

- [ ] **Step 2: Criar o web no projeto de prova e ver o teste falhar**

```bash
cd /tmp/new-agent-proof/demo
npx --yes create-next-app@latest demo-web --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
[ -d demo-web/.git ] && echo "ATENCAO: .git aninhado em demo-web"
cd demo-web && npm i -D vitest
R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates
VARS=/tmp/new-agent-proof/vars.env ON=web python3 /tmp/new-agent-proof/render.py file $R/web/src/lib/sse.test.ts.template src/lib/sse.test.ts
npx vitest run src/lib; echo "EXIT=$?"
```

Expected: nenhum aviso de `.git` aninhado (o `git init` da T1 já existe na raiz); `EXIT=1` com `Failed to resolve import "./sse"`.

- [ ] **Step 3: Implementar o parser**

`lib/sse.ts.template`:

```ts
/**
 * Separa de `buffer` os eventos SSE completos e devolve o que sobrou (um
 * evento ainda pela metade) para ser prefixado ao próximo pedaço da resposta.
 *
 * O dado de cada linha é tudo depois de "data:", sem tirar espaço: o agente
 * escreve "data:" + token, e o espaço inicial de um token faz parte do texto.
 */
export function parseSse(buffer: string): { data: string[]; rest: string } {
  const events = buffer.replace(/\r\n/g, "\n").split("\n\n");
  const rest = events.pop() ?? "";
  const data: string[] = [];
  for (const event of events) {
    const lines = event
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice("data:".length));
    if (lines.length > 0) {
      data.push(lines.join("\n"));
    }
  }
  return { data, rest };
}
```

```bash
cd /tmp/new-agent-proof/demo/demo-web
VARS=/tmp/new-agent-proof/vars.env ON=web python3 /tmp/new-agent-proof/render.py file $R/web/src/lib/sse.ts.template src/lib/sse.ts
npx vitest run src/lib; echo "EXIT=$?"
```

Expected: `EXIT=0`, 6 testes passando.

- [ ] **Step 4: Escrever o teste da rota**

`app/api/chat/route.test.ts.template`:

```ts
// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "./route";

function requisicao(conversationId?: string) {
  return new Request("http://localhost:3000/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(conversationId ? { "X-Conversation-Id": conversationId } : {}),
    },
    body: JSON.stringify({ body: "oi" }),
  });
}

describe("POST /api/chat", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("AGENT_URL", "http://agente:8080");
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("repassa corpo e conversa para o stream do agente e devolve o fluxo", async () => {
    fetchMock.mockResolvedValue(
      new Response("data:Ol\n\ndata:á\n\n", { headers: { "Content-Type": "text/event-stream" } }),
    );

    const resposta = await POST(requisicao("conv-1"));

    expect(resposta.status).toBe(200);
    expect(resposta.headers.get("Content-Type")).toBe("text/event-stream");
    expect(await resposta.text()).toBe("data:Ol\n\ndata:á\n\n");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://agente:8080/api/v1/agent/stream");
    expect(init.headers["X-Conversation-Id"]).toBe("conv-1");
    expect(JSON.parse(init.body)).toEqual({ body: "oi" });
  });

  it("devolve 400 com a mensagem do agente quando o corpo é recusado", async () => {
    fetchMock.mockResolvedValue(
      Response.json({ code: "INVALID_REQUEST", message: "campo body vazio" }, { status: 400 }),
    );

    const resposta = await POST(requisicao());

    expect(resposta.status).toBe(400);
    expect(await resposta.json()).toEqual({ message: "campo body vazio" });
  });

  it("devolve 502 com mensagem genérica quando o agente responde erro", async () => {
    fetchMock.mockResolvedValue(
      Response.json({ code: "MCP_UNAVAILABLE", message: "ferramenta externa indisponivel" }, { status: 502 }),
    );

    const resposta = await POST(requisicao());

    expect(resposta.status).toBe(502);
    expect(await resposta.json()).toEqual({ message: "O agente está indisponível. Tente de novo em instantes." });
  });

  it("devolve 502 quando o agente está fora do ar", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));

    const resposta = await POST(requisicao());

    expect(resposta.status).toBe(502);
    expect(await resposta.json()).toEqual({ message: "O agente está indisponível. Tente de novo em instantes." });
  });
});
```

```bash
cd /tmp/new-agent-proof/demo/demo-web
VARS=/tmp/new-agent-proof/vars.env ON=web python3 /tmp/new-agent-proof/render.py file $R/web/src/app/api/chat/route.test.ts.template src/app/api/chat/route.test.ts
npx vitest run src/app; echo "EXIT=$?"
```

Expected: `EXIT=1` com `Failed to resolve import "./route"`.

- [ ] **Step 5: Implementar a rota**

`app/api/chat/route.ts.template`:

```ts
const INDISPONIVEL = "O agente está indisponível. Tente de novo em instantes.";
const REQUISICAO_INVALIDA = "Não foi possível enviar a mensagem.";

// Cobre a inferência de um modelo local em CPU, que leva minutos.
const TIMEOUT_MS = 300_000;

/**
 * BFF do chat: o navegador nunca fala direto com o agente. Assim o backend não
 * precisa de CORS e a URL do agente fica fora do bundle.
 */
export async function POST(request: Request) {
  const agentUrl = process.env.AGENT_URL ?? "http://localhost:{agent-port}";
  const conversationId = request.headers.get("x-conversation-id");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (conversationId) {
    headers["X-Conversation-Id"] = conversationId;
  }

  let resposta: Response;
  try {
    resposta = await fetch(`${agentUrl}/api/v1/agent/stream`, {
      method: "POST",
      headers,
      body: await request.text(),
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (erro) {
    console.error("chat: falha ao chamar o agente", erro);
    return Response.json({ message: INDISPONIVEL }, { status: 502 });
  }

  if (resposta.status === 400) {
    return Response.json({ message: await motivo(resposta) }, { status: 400 });
  }
  if (!resposta.ok || !resposta.body) {
    return Response.json({ message: INDISPONIVEL }, { status: 502 });
  }

  return new Response(resposta.body, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
  });
}

/** O agente explica um 400 em `message`; sem motivo legível, vai a mensagem genérica. */
async function motivo(resposta: Response): Promise<string> {
  try {
    const corpo = (await resposta.json()) as { message?: unknown };
    return typeof corpo.message === "string" && corpo.message.trim() ? corpo.message : REQUISICAO_INVALIDA;
  } catch {
    return REQUISICAO_INVALIDA;
  }
}
```

```bash
cd /tmp/new-agent-proof/demo/demo-web
VARS=/tmp/new-agent-proof/vars.env ON=web python3 /tmp/new-agent-proof/render.py file $R/web/src/app/api/chat/route.ts.template src/app/api/chat/route.ts
grep -n 'localhost:8080' src/app/api/chat/route.ts
npx vitest run; echo "EXIT=$?"
```

Expected: o `grep` mostra a porta renderizada; `EXIT=0`, 10 testes passando.

- [ ] **Step 6: A página de chat**

`app/page.tsx.template`:

```tsx
"use client";

import { type FormEvent, useState } from "react";
import { parseSse } from "@/lib/sse";

type Mensagem = { autor: "usuario" | "agente"; texto: string };

const FALHA = "Não foi possível falar com o agente.";

export default function Home() {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [rascunho, setRascunho] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  // Uma conversa por carregamento da página: é a chave da memória no agente.
  const [conversationId] = useState(() => crypto.randomUUID());

  function acrescentarAoAgente(pedaco: string) {
    setMensagens((atuais) => {
      const ultima = atuais[atuais.length - 1];
      return [...atuais.slice(0, -1), { ...ultima, texto: ultima.texto + pedaco }];
    });
  }

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const texto = rascunho.trim();
    if (!texto || enviando) return;

    setRascunho("");
    setErro(null);
    setEnviando(true);
    setMensagens((atuais) => [...atuais, { autor: "usuario", texto }, { autor: "agente", texto: "" }]);

    try {
      const resposta = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Conversation-Id": conversationId },
        body: JSON.stringify({ body: texto }),
      });
      if (!resposta.ok || !resposta.body) {
        const corpo = (await resposta.json().catch(() => ({}))) as { message?: string };
        throw new Error(corpo.message ?? FALHA);
      }

      const leitor = resposta.body.getReader();
      const decodificador = new TextDecoder();
      let pendente = "";
      for (;;) {
        const { done, value } = await leitor.read();
        if (done) break;
        const { data, rest } = parseSse(pendente + decodificador.decode(value, { stream: true }));
        pendente = rest;
        if (data.length > 0) acrescentarAoAgente(data.join(""));
      }
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : FALHA);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-4 p-6">
      <h1 className="text-xl font-semibold">{project-name}</h1>

      <ol className="flex flex-1 flex-col gap-3" aria-live="polite">
        {mensagens.map((mensagem, indice) => (
          <li
            key={indice}
            className={
              mensagem.autor === "usuario"
                ? "self-end rounded-lg bg-zinc-900 px-3 py-2 text-white"
                : "self-start whitespace-pre-wrap rounded-lg bg-zinc-100 px-3 py-2 text-zinc-900"
            }
          >
            {mensagem.texto || "…"}
          </li>
        ))}
      </ol>

      {erro && (
        <p role="alert" className="text-sm text-red-700">
          {erro}
        </p>
      )}

      <form onSubmit={enviar} className="flex gap-2">
        <input
          className="flex-1 rounded border border-zinc-300 px-3 py-2"
          value={rascunho}
          onChange={(evento) => setRascunho(evento.target.value)}
          placeholder="Escreva sua mensagem"
          aria-label="Mensagem"
          disabled={enviando}
        />
        <button
          type="submit"
          className="rounded bg-zinc-900 px-4 py-2 text-white disabled:opacity-50"
          disabled={enviando || !rascunho.trim()}
        >
          Enviar
        </button>
      </form>
    </main>
  );
}
```

`{project-name}` é o **único** placeholder do arquivo. Todo o resto entre chaves — `{erro}`, `{indice}`, `{enviar}` — é JSX e fica como está; o `SKILL.md` (T8) diz isso a quem aplica a skill à mão.

- [ ] **Step 7: Renderizar a página, buildar e lintar**

```bash
cd /tmp/new-agent-proof/demo/demo-web
VARS=/tmp/new-agent-proof/vars.env ON=web python3 /tmp/new-agent-proof/render.py file $R/web/src/app/page.tsx.template src/app/page.tsx
grep -n '<h1' src/app/page.tsx
npm run lint; echo "EXIT=$?"
npm run build > /tmp/agent-web-build.log 2>&1; echo "EXIT=$?"
npx vitest run; echo "EXIT=$?"
```

Expected: o `<h1>` mostra `demo`; lint, build e testes com `EXIT=0`. Se o lint acusar a regra de pureza do React em `crypto.randomUUID()`, o inicializador preguiçoso do `useState` já é a forma aceita — confira que a chamada está **dentro** da arrow function.

- [ ] **Step 8: Smoke da tela contra o agente de verdade**

```bash
cd /tmp/new-agent-proof/demo
docker run -d --rm --name agent-proof-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
make run > /tmp/agent-run-all.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1 && curl -sf http://localhost:3000 >/dev/null 2>&1 && break; sleep 2; done
curl -s -N --max-time 240 -X POST http://localhost:3000/api/chat -H 'Content-Type: application/json' -H 'X-Conversation-Id: web-1' -d '{"body":"Diga oi."}' | head -5
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:3000/api/chat -H 'Content-Type: application/json' -d '{"body":"  "}'
```

Expected: linhas `data:` vindas do agente através do Next; `400` para o corpo em branco. Encerre: `pkill -f 'demo-agent'; pkill -f 'next dev'; make db-down; docker stop agent-proof-ollama`, e confirme 8080 e 3000 livres.

Abra `http://localhost:3000` no navegador antes de encerrar e mande uma mensagem: o texto precisa aparecer aos poucos, e a segunda mensagem precisa mostrar que o agente lembra da primeira. Se não der para abrir um navegador nesta sessão, diga isso no relato da tarefa em vez de afirmar que a tela funciona.

- [ ] **Step 9: Commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent/templates/web
git commit -m "Tela de chat da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Templates Java

**Files** (sob `$S/templates/source/java/`): os mesmos caminhos de `source/kotlin/{main,test,it}`, com `.java.template`, mais os arquivos que o Java obriga a separar (um tipo público por arquivo):

| Kotlin | Java |
|---|---|
| `ChatRoute.kt` (rota + `ChatRequest` + `ChatResponse`) | `ChatRoute.java`, `ChatRequest.java`, `ChatResponse.java` |
| `ChatExceptions.kt` (5 classes) | `InvalidChatRequestException.java`, `UpstreamException.java`, `UpstreamTimeoutException.java`, `McpUpstreamException.java`, `McpUpstreamTimeoutException.java` |
| `ChatTelemetry.kt` (classe + `ChatSpan`) | `ChatTelemetry.java`, `ChatSpan.java` |
| `GlobalExceptionHandler.kt` (handler + `ErrorMessage` local) | `GlobalExceptionHandler.java`, e `ErrorMessage.java` com `<!-- arquivo se sem-buildingBlocks -->` |
| `LazyMcpToolProvider.kt` (classe + função `strictMcpToolProvider`) | `LazyMcpToolProvider.java` (método estático privado) |

**Interfaces:**
- Consumes: os templates Kotlin das T2, T3 e T5 — são a especificação. Contratos Java do `buildingBlocks`: `ResultCommand<Result>`, `ResultCommandHandler<TCommand extends ResultCommand<TResult>, TResult>` com `TResult handle(TCommand command)`, `record ErrorMessage(String code, String message, String details)` com construtor de dois argumentos.
- Produces: os mesmos nomes de classe, método e bean do Kotlin. O contrato HTTP, as mensagens de erro, os nomes de métrica e de atributo de span são **idênticos** — o runbook e o web não sabem em que linguagem o agente foi gerado.

**Esta tarefa é a única do plano que não traz o código de cada arquivo.** São 40 arquivos, a maioria de tradução mecânica de código que este plano já mostra inteiro em Kotlin; repeti-los dobraria o plano sem acrescentar decisão. Em troca, a tarefa traz as regras de tradução, o código dos três arquivos em que a tradução **não** é mecânica, e um gate objetivo: o projeto Java de prova compila, passa nos mesmos 36 testes unitários e nos mesmos 3 ITs. Um revisor rejeita a tarefa se qualquer comportamento divergir do Kotlin.

- [ ] **Step 1: Regras de tradução**

| Kotlin | Java |
|---|---|
| `data class X(val a: A)` | `public record X(A a) {}` |
| `object X { fun f() }` | `public final class X { private X() {} public static ... f() }` |
| `class X(private val a: A)` com `@Component` | classe com campo `private final` e construtor explícito (sem Lombok) |
| `String?` | `String`, anotado `@Nullable` (`org.jspecify.annotations.Nullable`) em parâmetro e campo de record |
| `class E(cause: Throwable) : RuntimeException("msg", cause)` | `public class E extends RuntimeException { public E(Throwable cause) { super("msg", cause); } }` |
| `() -> McpClient` | `java.util.function.Supplier<McpClient>` |
| `(McpClient) -> ToolProvider` | `java.util.function.Function<McpClient, ToolProvider>` |
| `fun <T> observe(..., block: () -> T): T` | `<T> T observe(String spanName, String conversationId, Supplier<T> block)` |
| `span.makeCurrent().use { ... }` | `try (Scope ignored = span.makeCurrent()) { ... }` (`io.opentelemetry.context.Scope`) |
| `synchronized(lock) { ... }` | `synchronized (lock) { ... }` |
| `generateSequence(error) { it.cause }.take(20)` | laço `for (Throwable t = error; t != null && depth < 20; t = t.getCause())` |
| `LoggerFactory.getLogger(X::class.java)` em `companion` | `private static final Logger log = LoggerFactory.getLogger(X.class);` |
| `@MockkBean`, `every { } returns`, `slot<T>()`, `verify { }` | `@MockitoBean` (`org.springframework.test.context.bean.override.mockito.MockitoBean`), `when(...).thenReturn(...)`, `ArgumentCaptor<T>`, `verify(...)` |
| `mockk<T>(relaxed = true)` | `Mockito.mock(T.class)` |
| `assertFailsWith<E> { }` / `assertEquals` do `kotlin.test` | `assertThatThrownBy(() -> ...).isInstanceOf(E.class)` / `assertThat(...)` do AssertJ |
| nome de teste entre crases | método `camelCase` com a mesma frase: `` `header vence o campo from` `` → `headerVenceOCampoFrom` |
| `"""{"body":"oi"}"""` | text block `"""` do Java |
| `companion object { @JvmStatic @DynamicPropertySource fun llm(...) }` | `@DynamicPropertySource static void llm(DynamicPropertyRegistry registry)` |
| `@JvmStatic @field:ServiceConnection val database = ...also { it.start() }` | `@ServiceConnection static final PostgreSQLContainer DATABASE = start();` com `start()` privado |
| `@JvmField @RegisterExtension val otel` em `companion` | `@RegisterExtension static final OpenTelemetryExtension otel = OpenTelemetryExtension.create();` |
| `ChatResult(assistant.chat(...))` em `ResultCommandHandler` | `record ChatCommand(String conversationId, @Nullable String body) implements ResultCommand<ChatResult>` e `class ChatHandler implements ResultCommandHandler<ChatCommand, ChatResult>` |

Mensagens, códigos de erro e comentários: copie o texto do Kotlin, sem reescrever. Marcadores condicionais: os mesmos, nas mesmas posições lógicas.

- [ ] **Step 2: `LazyMcpToolProvider.java.template`**

`source/java/main/infrastructure/data/anticorruptionLayer/mcp/LazyMcpToolProvider.java.template`:

```java
package {base-package}.infrastructure.data.anticorruptionLayer.mcp;

import dev.langchain4j.mcp.McpToolProvider;
import dev.langchain4j.mcp.client.McpClient;
import dev.langchain4j.service.tool.ToolProvider;
import dev.langchain4j.service.tool.ToolProviderRequest;
import dev.langchain4j.service.tool.ToolProviderResult;
import java.util.function.Function;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Tools de um servidor MCP, com conexao na primeira conversa.
 *
 * <p>O DefaultMcpClient conecta no construtor: como bean comum, um servidor MCP
 * fora do ar impediria o agente de subir. Aqui o cliente so nasce quando uma
 * conversa pede as tools, e e descartado em qualquer falha -- a conversa
 * seguinte reconecta, o que cobre o restart do servidor, que invalida a sessao.
 *
 * <p>Falha vira McpUnavailableException em vez de "nenhuma tool": um agente que
 * perde as ferramentas em silencio inventa a resposta.
 */
public class LazyMcpToolProvider implements ToolProvider, AutoCloseable {

    private static final Logger log = LoggerFactory.getLogger(LazyMcpToolProvider.class);

    private final String serverName;
    private final Supplier<McpClient> clientFactory;
    private final Function<McpClient, ToolProvider> toolProviderFactory;
    private final Object lock = new Object();
    private McpClient client;
    private ToolProvider delegate;

    public LazyMcpToolProvider(String serverName, Supplier<McpClient> clientFactory) {
        this(serverName, clientFactory, LazyMcpToolProvider::strictMcpToolProvider);
    }

    /** Costura de teste: o padrao e o McpToolProvider de verdade. */
    public LazyMcpToolProvider(
            String serverName,
            Supplier<McpClient> clientFactory,
            Function<McpClient, ToolProvider> toolProviderFactory) {
        this.serverName = serverName;
        this.clientFactory = clientFactory;
        this.toolProviderFactory = toolProviderFactory;
    }

    @Override
    public ToolProviderResult provideTools(ToolProviderRequest request) {
        ToolProvider provider = connect();
        try {
            return provider.provideTools(request);
        } catch (RuntimeException e) {
            discard();
            throw new McpUnavailableException(serverName, e);
        }
    }

    private ToolProvider connect() {
        synchronized (lock) {
            if (delegate == null) {
                try {
                    client = clientFactory.get();
                    delegate = toolProviderFactory.apply(client);
                } catch (RuntimeException e) {
                    throw new McpUnavailableException(serverName, e);
                }
            }
            return delegate;
        }
    }

    private void discard() {
        McpClient stale;
        synchronized (lock) {
            stale = client;
            client = null;
            delegate = null;
        }
        closeQuietly(stale);
    }

    @Override
    public void close() {
        discard();
    }

    private void closeQuietly(McpClient target) {
        if (target == null) {
            return;
        }
        try {
            target.close();
        } catch (Exception e) {
            log.debug("falha ao fechar o cliente MCP '{}': {}", serverName, e.toString());
        }
    }

    // Sem failIfOneServerFails o provider registra um aviso e devolve zero tools
    // quando o servidor falha -- exatamente o silencio que nao queremos.
    private static ToolProvider strictMcpToolProvider(McpClient client) {
        return McpToolProvider.builder()
                .mcpClients(client)
                .failIfOneServerFails(true)
                .build();
    }
}
```

Atenção ao `log.debug("... '{}': {}", ...)`: `{}` vazio não casa com o padrão de placeholder, então o template fica como está.

- [ ] **Step 3: `ScriptedChatModel.java.template` e `OllamaTestContainer.java.template`**

Os dois existem em Java na POC `agent-to-agent`. O `ScriptedChatModel` ganha a lista de listeners e os nomes em inglês; `source/java/test/support/ScriptedChatModel.java.template`:

```java
package {base-package}.support;

import dev.langchain4j.agent.tool.ToolExecutionRequest;
import dev.langchain4j.data.message.AiMessage;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.chat.listener.ChatModelListener;
import dev.langchain4j.model.chat.request.ChatRequest;
import dev.langchain4j.model.chat.response.ChatResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * LLM falso e deterministico: cada chamada ao modelo consome o proximo passo
 * do roteiro, e uma chamada alem do roteiro falha o teste. E o que permite
 * afirmar o texto exato da resposta -- coisa que um modelo real nao permite.
 */
public class ScriptedChatModel implements ChatModel {

    private final List<Function<ChatRequest, AiMessage>> steps;
    private final List<ChatModelListener> listeners;
    private final List<ChatRequest> requests = new ArrayList<>();

    public ScriptedChatModel(List<Function<ChatRequest, AiMessage>> steps) {
        this(steps, List.of());
    }

    public ScriptedChatModel(List<Function<ChatRequest, AiMessage>> steps, List<ChatModelListener> listeners) {
        this.steps = List.copyOf(steps);
        this.listeners = List.copyOf(listeners);
    }

    @Override
    public List<ChatModelListener> listeners() {
        return listeners;
    }

    @Override
    public ChatResponse doChat(ChatRequest request) {
        int call = requests.size();
        requests.add(request);
        if (call >= steps.size()) {
            throw new IllegalStateException("chamada inesperada ao modelo #" + (call + 1));
        }
        return ChatResponse.builder().aiMessage(steps.get(call).apply(request)).build();
    }

    public List<ChatRequest> requests() {
        return requests;
    }

    public static Function<ChatRequest, AiMessage> callTool(String name, String argumentsJson) {
        return request -> AiMessage.from(ToolExecutionRequest.builder()
                .id("call-" + name).name(name).arguments(argumentsJson).build());
    }

    public static Function<ChatRequest, AiMessage> answer(String text) {
        return request -> AiMessage.from(text);
    }
}
```

`source/java/it/support/OllamaTestContainer.java.template`:

```java
package {base-package}.support;

import com.github.dockerjava.api.model.Image;
import java.io.IOException;
import java.util.List;
import java.util.Locale;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.testcontainers.DockerClientFactory;
import org.testcontainers.containers.Container.ExecResult;
import org.testcontainers.ollama.OllamaContainer;
import org.testcontainers.utility.DockerImageName;

/**
 * LLM real dos testes de integracao: Ollama em container, um por JVM, iniciado
 * de forma eager -- o mesmo estilo do container de banco da base.
 *
 * <p>Para nao baixar o modelo (~2 GB) a cada execucao: na primeira vez sobe a
 * imagem base, faz {@code ollama pull} e grava o container como a imagem local
 * {@code tc-ollama-<modelo>}; nas seguintes sobe direto dela. Para refazer o
 * cache: {@code docker rmi tc-ollama-<modelo>}.
 *
 * <p>Modelo padrao qwen2.5:3b: faz tool calling e nao emite tags de "thinking".
 * Troque com a system property ou variavel de ambiente IT_OLLAMA_MODEL.
 */
public final class OllamaTestContainer {

    private static final String BASE_IMAGE = "ollama/ollama:0.34.3";
    private static final String DEFAULT_MODEL = "qwen2.5:3b";

    public static final String MODEL = model();
    public static final OllamaContainer CONTAINER = start();

    private OllamaTestContainer() {
    }

    /** URL OpenAI-compativel do container. */
    public static String openAiBaseUrl() {
        return CONTAINER.getEndpoint() + "/v1";
    }

    /**
     * Aponta os dois modelos do LangChain4j para o container e desliga o que
     * nao e deste teste: o servidor MCP (outro sistema) e a exportacao de traces.
     */
    public static void registerLlm(DynamicPropertyRegistry registry, String mcpName) {
        for (String prefix : List.of("langchain4j.open-ai.chat-model", "langchain4j.open-ai.streaming-chat-model")) {
            registry.add(prefix + ".base-url", OllamaTestContainer::openAiBaseUrl);
            registry.add(prefix + ".api-key", () -> "ollama");
            registry.add(prefix + ".model-name", () -> MODEL);
            // Inferencia em CPU: uma chamada pode levar minutos.
            registry.add(prefix + ".timeout", () -> "PT300S");
        }
        registry.add(mcpName + ".enabled", () -> "false");
        registry.add("management.tracing.sampling.probability", () -> "0.0");
    }

    private static String model() {
        String model = System.getProperty("IT_OLLAMA_MODEL", System.getenv("IT_OLLAMA_MODEL"));
        return model == null || model.isBlank() ? DEFAULT_MODEL : model.trim();
    }

    private static OllamaContainer start() {
        String cachedImage = "tc-ollama-" + MODEL.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9._-]", "-");
        List<Image> cache = DockerClientFactory.instance().client()
                .listImagesCmd()
                .withReferenceFilter(cachedImage)
                .exec();
        boolean cached = !cache.isEmpty();

        OllamaContainer container = cached
                ? new OllamaContainer(DockerImageName.parse(cachedImage).asCompatibleSubstituteFor("ollama/ollama"))
                : new OllamaContainer(BASE_IMAGE);
        container.start();
        if (!cached) {
            pull(container);
            container.commitToImage(cachedImage);
        }
        return container;
    }

    private static void pull(OllamaContainer container) {
        try {
            ExecResult pull = container.execInContainer("ollama", "pull", MODEL);
            if (pull.getExitCode() != 0) {
                throw new IllegalStateException("ollama pull " + MODEL + " falhou: " + pull.getStderr());
            }
        } catch (IOException e) {
            throw new IllegalStateException("ollama pull " + MODEL + " falhou", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("ollama pull " + MODEL + " interrompido", e);
        }
    }
}
```

O padrão `[^a-z0-9._-]` e `tc-ollama-<modelo>` não casam com placeholder (têm caracteres fora de `{kebab}`).

- [ ] **Step 4: Traduzir os demais arquivos**

Para cada template Kotlin de `source/kotlin/{main,test,it}`, na ordem abaixo, escreva o equivalente Java pela tabela do Step 1 e pela tabela de arquivos no topo da tarefa. Compile depois de cada grupo (Step 5 mostra como) em vez de traduzir tudo e compilar no fim.

1. `application/chat/` — exceções, `ChatInput`, `ChatFailures`, `ChatCommand`, `ChatResult`.
2. `infrastructure/data/anticorruptionLayer/` — `Assistant`, `McpUnavailableException`, `AssistantAiService`, `LangChain4jAssistant`.
3. `infrastructure/observability/` — `ChatSpan`, `ChatTelemetry`, `TracingProperties`, `GenAiSpanEnricher`.
4. `infrastructure/configuration/` — `__mcp-class__Properties`, `__mcp-class__Config`, `ChatMemoryConfig`.
5. `application/chat/` — `ChatHandler`, `ChatStreamHandler`.
6. `presenter/` — `ConversationIds`, `ChatRequest`, `ChatResponse`, `ChatRoute`, `ConversationIdFilter`, `ErrorMessage`, `GlobalExceptionHandler`.
7. `test/` — `FakeToolProvider`, depois os cinco testes.
8. `it/` — `BaseIntegrationTest`, `ChatRouteIT`.

Três pontos em que o Java difere de verdade:
- `TracingProperties` e `__mcp-class__Properties` são classes com getters e setters (o binder do Spring precisa deles), não records.
- `GenAiSpanEnricher`: o `when (message)` do Kotlin vira cadeia de `instanceof` com pattern matching; `context.attributes()[KEY] = span` vira `context.attributes().put(KEY, span)`.
- `__mcp-class__Config`: os dois métodos `@Bean("chatToolProvider")` têm nomes diferentes (`mcpToolProvider` e `noToolProvider`) e condições opostas, como no Kotlin; o `noToolProvider` devolve `request -> ToolProviderResult.builder().build()`.

- [ ] **Step 5: Projeto Java de prova, mínimo**

Sem web, sem banco, memória em processo, Groovy DSL, ITs dentro do módulo — o canto oposto da prova Kotlin.

```bash
cd /tmp/new-agent-proof && rm -rf demoj starterj.zip && mkdir demoj && cd demoj
curl -sS --max-time 90 -o ../starterj.zip -G https://start.spring.io/starter.zip \
  --data-urlencode 'type=gradle-project' --data-urlencode 'language=java' \
  --data-urlencode 'groupId=br.com.analizza' --data-urlencode 'artifactId=demoj-agent' \
  --data-urlencode 'name=demoj-agent' --data-urlencode 'packageName=br.com.analizza.demoj' \
  --data-urlencode 'packaging=jar' --data-urlencode 'javaVersion=25' \
  --data-urlencode 'dependencies=web,actuator'
mkdir demoj-agent && unzip -q ../starterj.zip -d demoj-agent
mv demoj-agent/gradlew demoj-agent/gradlew.bat demoj-agent/gradle demoj-agent/.gitignore demoj-agent/.gitattributes .
rm -rf demoj-agent/settings.gradle demoj-agent/HELP.md demoj-agent/src/test demoj-agent/src/main/resources/application.properties
grep -nE "version '" demoj-agent/build.gradle
git init -q
sed -e 's/=demo$/=demoj/' -e 's/demo-agent/demoj-agent/' -e 's/DemoAgentApplication/DemojAgentApplication/' \
    -e 's/analizza\.demo$/analizza.demoj/' ../vars.env > ../varsj.env
grep -nE 'demoj|boot-version' ../varsj.env

R=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills
export VARS=/tmp/new-agent-proof/varsj.env ON=java,memoria,memoria-processo,buildingBlocks,sem-web,sem-postgres,it-no-modulo
P=br/com/analizza/demoj
python3 ../render.py file $R/analizza-new-agent/templates/build/groovy/root.gradle.template build.gradle
python3 ../render.py file $R/analizza-new-agent/templates/build/groovy/agent-module.gradle.template demoj-agent/build.gradle
python3 ../render.py file $R/analizza-new-project/templates/buildingBlocks/build.gradle.template buildingBlocks/build.gradle
python3 ../render.py tree $R/analizza-new-project/templates/buildingBlocks/java buildingBlocks/src/main/java/$P
printf "rootProject.name = 'demoj'\ninclude ':buildingBlocks'\ninclude ':demoj-agent'\n" > settings.gradle
printf 'langchain4jVersion=1.20.0-beta30\n' > gradle.properties
python3 ../render.py tree $R/analizza-new-agent/templates/source/java/main demoj-agent/src/main/java/$P
python3 ../render.py tree $R/analizza-new-agent/templates/source/java/test demoj-agent/src/test/java/$P
python3 ../render.py tree $R/analizza-new-agent/templates/source/java/it demoj-agent/src/test/java/$P
python3 ../render.py tree $R/analizza-new-agent/templates/resources demoj-agent/src/main/resources
ls demoj-agent/src/main/resources/db/migration 2>/dev/null | wc -l
```

Expected: `varsj.env` com `project-name=demoj`, `agent-module=demoj-agent`, `app-class=DemojAgentApplication`, `base-package=br.com.analizza.demoj`; confira a `boot-version` contra o `grep` do `build.gradle` e corrija se o Initializr tiver mudado. Nenhuma migration gerada (`0`) — `memoria-jdbc` não vale aqui.

- [ ] **Step 6: Compilar, testar e integrar em Java**

```bash
cd /tmp/new-agent-proof/demoj
./gradlew :demoj-agent:compileJava --console=plain > /tmp/agentj-compile.log 2>&1; echo "EXIT=$?"
./gradlew :demoj-agent:test --console=plain > /tmp/agentj-test.log 2>&1; echo "EXIT=$?"
./gradlew :demoj-agent:integrationTest --console=plain > /tmp/agentj-it.log 2>&1; echo "EXIT=$?"
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
for task in ('test', 'integrationTest'):
    t = f = e = 0
    for x in glob.glob(f'demoj-agent/build/test-results/{task}/*.xml'):
        r = ET.parse(x).getroot(); t += int(r.get('tests')); f += int(r.get('failures')); e += int(r.get('errors'))
    print(f"{task}: tests={t} failures={f} errors={e}")
PY
```

Expected: três `EXIT=0`; `test: tests=36 failures=0 errors=0`; `integrationTest: tests=3 failures=0 errors=0`. Um número de testes diferente de 36 significa que um caso do Kotlin ficou sem tradução — ache qual e escreva.

- [ ] **Step 7: As mesmas mutações da T3, em Java**

Aplique no `demoj` as cinco mutações da tabela do Step 8 da T3 (nos arquivos `.java` correspondentes), uma por vez. Expected para cada: `EXIT=1` no `./gradlew :demoj-agent:test` com o teste equivalente em `FAILED`. Desfaça renderizando a produção de novo.

- [ ] **Step 8: Smoke Java, sem banco**

```bash
cd /tmp/new-agent-proof/demoj
python3 ../render.py file $R/analizza-new-agent/templates/root/Makefile.template Makefile
python3 ../render.py file $R/analizza-new-agent/templates/root/local.env.ollama.example.template local.env.ollama.example
docker run -d --rm --name agent-proof-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
sed -e 's#localhost:11434#localhost:11435#' -e 's#qwen2.5:7b#qwen2.5:3b#' local.env.ollama.example > local.env.ollama
make help | grep -cE 'db-up|run-web'
make run-agent-ollama > /tmp/agentj-run.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1 && break; sleep 2; done
curl -s -X POST http://localhost:8080/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: j-1' -d '{"body":"Meu nome e Ana. Guarde isso."}'
curl -s -X POST http://localhost:8080/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: j-1' -d '{"body":"Qual e o meu nome?"}'
pkill -f 'demoj-agent'; docker stop agent-proof-ollama
```

Expected: `0` alvos de banco ou web no `make help`; duas respostas `{"response":"..."}`. A segunda **deveria** citar "Ana" (memória em processo) — com modelo de 3B isso não é garantido; relate o que veio em vez de afirmar que a memória funciona se a resposta não mostrar.

- [ ] **Step 9: Commitar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
find plugins/analizza-skills/skills/analizza-new-agent/templates/source/java -name '*.template' | wc -l
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent/templates/source/java
git commit -m "Templates Java da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Expected: 40 templates Java (30 de produção, 7 de teste, 3 de IT).

---

### Task 8: `SKILL.md` completo, convenções e runbook

**Files:**
- Modify: `$S/SKILL.md` (substitui o esqueleto da T1)
- Create: `$S/templates/source/kotlin/main/__app-class__.kt.template`, `$S/templates/source/java/main/__app-class__.java.template`
- Create: `$S/templates/architecture-conventions.md.template`
- Create: `$S/references/agent-conventions.md`, `$S/references/pitfalls-agent.md`, `$S/references/runbook-agent-chat.md`

**Interfaces:**
- Consumes: todos os templates das T1–T7, com os caminhos e nomes de alvo exatos; `references/it-llm-layer.md` (T5); as referências e o `buildingBlocks` da `analizza-new-project`.
- Produces: o procedimento que a T9 executa **sem ler este plano**. Tudo o que um executor precisa para aplicar a skill tem de estar no `SKILL.md` e nos arquivos que ele cita.

- [ ] **Step 1: A classe de aplicação do modo existente**

Do zero, quem gera a classe `@SpringBootApplication` é o Initializr. No projeto existente a skill escreve.

`source/kotlin/main/__app-class__.kt.template`:

```kotlin
<!-- arquivo se existente -->
package {base-package}

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

// Na raiz do pacote do agente de proposito: e daqui que o component scan
// comeca, e ele nao pode alcancar o pacote do -api nem o do -core.
@SpringBootApplication
class {app-class}

fun main(args: Array<String>) {
    runApplication<{app-class}>(*args)
}
```

`source/java/main/__app-class__.java.template`:

```java
<!-- arquivo se existente -->
package {base-package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

// Na raiz do pacote do agente de proposito: e daqui que o component scan
// comeca, e ele nao pode alcancar o pacote do -api nem o do -core.
@SpringBootApplication
public class {app-class} {

    public static void main(String[] args) {
        SpringApplication.run({app-class}.class, args);
    }
}
```

No projeto de prova `demo`, que é do modo do zero, o arquivo não é gerado: `existente` não está no `ON`.

- [ ] **Step 2: `references/agent-conventions.md`**

É a seção que a skill acrescenta ao arquivo do SDD do projeto, com placeholders e marcadores resolvidos.

````markdown
### Agente

O `{agent-module}` é um agente conversacional: recebe uma mensagem por HTTP,
chama um LLM que pode usar ferramentas de um servidor MCP, e devolve a resposta
inteira (`POST /api/v1/agent/http`) ou em fluxo (`POST /api/v1/agent/stream`,
SSE).
<!-- se existente -->

É uma aplicação Spring Boot própria, com processo e porta (`{agent-port}`)
separados do `-api`, e **não depende do `-core`**: o que ele sabe do domínio,
sabe pelas tools do servidor MCP. O pacote raiz é `{base-package}`, para o
component scan dele não alcançar o resto do projeto. As quatro camadas —
`presenter/`, `application/`, `domain/`, `infrastructure/` — são pacotes do
mesmo módulo, e a seta entre elas é convenção, não regra de build.
<!-- fim se existente -->

#### Onde cada coisa mora

| O quê | Onde |
|---|---|
| Rota, request e response | `presenter/routes/chat/` |
| Corpo de erro e mapeamento para status HTTP | `presenter/configuration/exception/GlobalExceptionHandler` |
| Validação, orquestração e classificação de falha | `application/chat/` |
| As exceções que o caso de uso lança | `application/chat/` — não em `presenter/`, senão o handler importaria a entrada |
| O LLM, atrás de uma interface | `infrastructure/data/anticorruptionLayer/llm/Assistant` e `impl/` |
| Cliente MCP | `infrastructure/data/anticorruptionLayer/mcp/` e `infrastructure/configuration/{mcp-class}Config` |
| Span, métricas e conteúdo dos traces | `infrastructure/observability/` |
| Prompts | `src/main/resources/prompts/` |

**Nenhum tipo de `dev.langchain4j` aparece fora de `infrastructure/`.** O
handler conhece `Assistant`, que só fala `String` e `Flux<String>`. Trocar de
biblioteca de LLM é reescrever `impl/`.

#### Identidade vem da requisição, nunca do modelo

O identificador de quem está conversando — usuário, cliente, tenant — chega na
requisição e é passado adiante **pelo código**. Ele nunca é lido da resposta do
LLM nem pedido ao usuário no prompt: um modelo pode ser convencido a trocar um
identificador, e uma tool que confia nele entrega o dado de outra pessoa.
Quando o agente ganhar autenticação, a rota resolve a identidade em
`presenter/configuration/security/` e a entrega ao caso de uso no `ChatCommand`.

#### LLM

Qualquer provedor OpenAI-compatível. `LLM_BASE_URL`, `LLM_API_TOKEN` e
`LLM_MODEL` vêm do ambiente e **não têm default**: sem eles a aplicação não
sobe. Um default no YAML é o que faz alguém gastar token de produção sem
saber. `make run-agent` usa `local.env`; `make run-agent-ollama` usa
`local.env.ollama`, que aponta para um Ollama local, sem chave e sem custo.

#### Servidor MCP

O servidor `{mcp-name}` é configurado em `{mcp-name}.*`
(`{mcp-env}_ENABLED`, `_BASE_URL`, `_AUTHORIZATION`, `_TIMEOUT`).

- **A conexão é preguiçosa.** O cliente nasce na primeira conversa, não na
  subida: o agente sobe e o healthcheck passa com o servidor fora do ar.
- **Servidor fora na hora da conversa é erro, não degradação.** A requisição
  devolve `502` com `MCP_UNAVAILABLE`. O agente nunca responde "sem
  ferramentas": um modelo que perde as tools em silêncio inventa o dado.
- **`{mcp-name}.enabled=false`** desliga o cliente; o agente conversa só com o LLM.
- **`{mcp-name}.authorization`** é o valor inteiro do header `Authorization`
  mandado ao servidor. É uma credencial **do agente**, não do usuário:
  propagar a identidade de quem conversa até o servidor MCP não está decidido.

Para um segundo servidor: copie o par `{mcp-class}Config` + `{mcp-class}Properties`
com outro nome e prefixo, e troque o bean `chatToolProvider` por um
`ToolProvider` que junte os dois.

Para uma tool **local** (código deste módulo, não um servidor): escreva a
classe em `infrastructure/data/anticorruptionLayer/<vendor>/` e registre-a no
AI Service. Toda tool é uma decisão de exposição de dado: confira campo a campo
o que ela devolve ao modelo.

#### Memória de conversa
<!-- se memoria-jdbc -->

Janela das últimas 30 mensagens por `conversationId`, persistida na tabela
`chat_memory` (uma linha por conversa, mensagens em JSON), criada pela
migration `V1__chat_memory.sql`. O `conversationId` vem do header
`X-Conversation-Id`, senão do campo `from`, senão é gerado — e uma conversa sem
identificador estável começa do zero a cada mensagem.
<!-- fim se memoria-jdbc -->
<!-- se memoria-processo -->

Janela das últimas 30 mensagens por `conversationId`, **em processo**: some a
cada restart e não é compartilhada entre réplicas. Serve para desenvolvimento.
Antes de rodar com mais de uma instância, troque o `ChatMemoryConfig` por um
`ChatMemoryStore` persistente.
<!-- fim se memoria-processo -->
<!-- se sem-memoria -->

O agente não guarda conversa: cada chamada é independente. O `conversationId`
existe só para agrupar os traces.
<!-- fim se sem-memoria -->
<!-- se postgres -->

#### Banco

O módulo usa `spring-boot-starter-jdbc` e Flyway. Ele nasce sem entidade
nenhuma; quem escrever a primeira `@Entity` troca o starter por
`spring-boot-starter-data-jpa` e aplica o plugin de JPA da linguagem.
<!-- fim se postgres -->
<!-- se existente -->
<!-- se postgres -->
O banco do agente é `{db-name}`, na porta `{db-port}`, separado do banco do
`-core`: dois Flyway no mesmo schema disputam a mesma `flyway_schema_history`.
<!-- fim se postgres -->
<!-- fim se existente -->

#### Observabilidade

- **Span por conversa** (`chat` e `chatStream`) com `conversationId`,
  `user_id` e `thread_id` — os dois últimos são o que o LangWatch usa para
  agrupar por usuário e por conversa.
- **Atributos `gen_ai.*`** (modelo, tokens, finish reason) em toda chamada ao LLM.
- **Conteúdo** — prompt, resposta, argumentos e resultado de tool — só entra
  no trace com as flags `langchain4j.tracing.include-*`, **desligadas por
  padrão** e ligadas no profile `dev`. Em produção ficam desligadas: prompt e
  resposta carregam dado de usuário, e resultado de tool carrega dado de domínio.
- **Métricas** em `/actuator/prometheus`: `chat_requests_total{outcome}` e
  `chat_request_duration_seconds`.
- **LangWatch local:** `make langwatch-up`, interface em
  `http://localhost:5560`. Crie a chave na interface e ponha em
  `LANGWATCH_API_KEY` no `local.env`.

#### Testes do agente

| Nível | LLM | Para quê |
|---|---|---|
| Unitário (`*Test`) | `ScriptedChatModel` — roteiro determinístico | texto exato, fluxo de tool, classificação de falha, contrato HTTP |
| Integração (`*IT`) | Ollama em Testcontainers | a aplicação inteira responde de verdade |

**Um IT nunca compara o texto da resposta.** Com modelo pequeno ele varia.
Afirme status, forma do JSON, resposta não vazia, header ecoado, linha de
memória gravada, métrica emitida. O que precisa de texto exato é unitário.

Nos ITs o servidor MCP fica desligado: é outro sistema. O fluxo de tool é
coberto no unitário, com `FakeToolProvider`.

A primeira execução dos ITs baixa a imagem do Ollama e o modelo (~2 GB) e
grava a imagem local `tc-ollama-<modelo>`; as seguintes reaproveitam. A
inferência roda em CPU e leva minutos — por isso os ITs ficam fora do `build`.
Troque o modelo com `IT_OLLAMA_MODEL`.

#### Não está decidido

- Autenticação do endpoint de chat e propagação da identidade até o servidor MCP.
- Limite de requisições e de custo por usuário.
- Avaliação de qualidade das respostas (evals).
- Dockerfile e pipeline do agente.
````

- [ ] **Step 3: `references/pitfalls-agent.md`**

````markdown
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

## Testes

### Primeiro IT lento não é IT travado

Baixar ~2 GB e inferir em CPU leva minutos. Só interrompa depois de olhar
`docker logs` do container do Ollama.

### Modelo pequeno e tool calling

Modelos de 3B chamam tool de forma inconsistente. Não escreva IT que dependa
de o modelo chamar a tool; isso é unitário com `ScriptedChatModel`.
````

- [ ] **Step 4: `references/runbook-agent-chat.md`**

Vai para `docs/checkpoints/agent-chat.md` do projeto gerado.

````markdown
# Checkpoint: conversa com o agente

**Tipo:** API + integração externa (LLM, servidor MCP)

## 1. O que precisa bater

Suba o agente contra o Ollama local:

```bash
cp local.env.ollama.example local.env.ollama   # ajuste LLM_MODEL para um modelo que voce tenha
make run-agent-ollama
```

| Passo | Comando | Esperado |
|---|---|---|
| Saúde | `curl -s localhost:{agent-port}/actuator/health` | `"status":"UP"`, mesmo com o servidor MCP fora |
| Conversa | `curl -s -D - -X POST localhost:{agent-port}/api/v1/agent/http -H 'Content-Type: application/json' -H 'X-Conversation-Id: check-1' -d '{"body":"oi"}'` | `200`, header `X-Conversation-Id: check-1` ecoado, `{"response":"..."}` não vazio |
| Fluxo | `curl -s -N -X POST localhost:{agent-port}/api/v1/agent/stream -H 'Content-Type: application/json' -d '{"body":"conte ate 5"}'` | linhas `data:` chegando aos poucos |
| Métrica | `curl -s localhost:{agent-port}/actuator/prometheus \| grep chat_requests_total` | `outcome="success"` com a contagem das chamadas acima |
<!-- se memoria -->
| Memória | duas chamadas com o mesmo `X-Conversation-Id`: "meu nome é Ana", depois "qual é o meu nome?" | a segunda resposta usa a primeira |
<!-- fim se memoria -->
<!-- se web -->
| Tela | `make run`, abrir `http://localhost:3000`, mandar uma mensagem | o texto aparece aos poucos; a segunda mensagem lembra da primeira |
<!-- fim se web -->

Trace: `make langwatch-up`, crie a chave em `http://localhost:5560`, ponha em
`LANGWATCH_API_KEY`, reinicie o agente e converse. O trace `chat` precisa
aparecer com `thread_id` igual ao `X-Conversation-Id` e, no profile `dev`, com
o prompt e a resposta.

## 2. O que tentar para ver se quebra

| Tentativa | Esperado |
|---|---|
| `{"body":"   "}` | `400`, `INVALID_REQUEST`, sem chamada ao LLM |
| corpo com mais de 8000 caracteres | `400`, `INVALID_REQUEST` |
| JSON quebrado | `400`, `MALFORMED_JSON` |
| `Content-Type: text/plain` | `415` |
| Parar o Ollama e conversar | `502` ou `504`, corpo `{code, message}` **sem** stacktrace nem URL |
| `{mcp-env}_ENABLED=true` com o servidor MCP parado | o agente **sobe**; a conversa devolve `502` `MCP_UNAVAILABLE` |
| Subir o servidor MCP e conversar de novo, sem reiniciar o agente | a conversa volta a funcionar |
| Pedir ao agente o dado de "outro usuário" | o agente não troca de identidade a pedido |

## 3. O que não está na lista

Olhe o que cada tool do servidor MCP **devolve ao modelo**, campo a campo.
URL assinada, e-mail, documento, dado de outra pessoa: tudo o que a tool
devolve o modelo pode repetir na resposta. Esta conferência não tem como ser
automatizada e é o motivo de este runbook existir.

Com as flags de conteúdo ligadas, olhe também o que foi parar no trace.

## 4. O que este checkpoint já pegou

_(vazio — preencha a cada conferência)_
````

- [ ] **Step 5: `templates/architecture-conventions.md.template`**

As convenções de camadas do modo do zero. A `analizza-new-project` tem esse documento para `-api` + `-core`; aqui as quatro camadas vivem num módulo só. O `eaf-agent` já fez essa adaptação à mão, em Kotlin, e é a referência de **redação**.

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills
cp analizza-new-project/templates/architecture-conventions.md.template analizza-new-agent/templates/architecture-conventions.md.template
sed -n '1,330p' /Users/diegolirio/Documents/Github/eaf-agent/docs/superpowers/INSTRUCTIONS.md > /tmp/eaf-conventions.md
```

Edite a cópia, seção por seção, usando `/tmp/eaf-conventions.md` como modelo de texto e mantendo os blocos `<!-- se kotlin -->` / `<!-- se java -->` do original:

| Seção do original | O que fazer |
|---|---|
| `### Módulos` | Tabela com `buildingBlocks`, `{agent-module}` ("Spring Boot. `presenter/`, `application/`, `domain/` e `infrastructure/` no mesmo módulo") e, sob `<!-- se web -->`, `{project-name}-web`. Sem `-api`, `-core`, mobile. Texto da seta como no `eaf-agent`: `{agent-module} → buildingBlocks`, a separação é de pacote, e a regra "nada de `application/`, `domain/` ou `infrastructure/` importa `presenter`" é o que mantém barato extrair um `-core` depois |
| `### O que mora onde` | Fundir as duas subseções `-api` e `-core` numa só, `#### {agent-module} — entrada, casos de uso, domínio e saída`, com a árvore única do `eaf-agent` |
| `### -core pode usar Spring` | Renomear para `### Spring e a separação de camadas` e trocar o texto pelo do `eaf-agent` (não há regra de build separando as camadas; quem garante é revisão) |
| `### A fatia vertical` | "tudo dentro do `{agent-module}`", cinco passos como no `eaf-agent` |
| `### CORS e como -web e -mobile alcançam o -api` | Sob `<!-- se web -->`: o web alcança o agente por route handler do Next (`/api/chat`), então o agente não precisa de CORS. Sem web, a seção sai |
| `### Migrations` | Sob `<!-- se postgres -->`: moram em `{agent-module}/src/main/resources/db/migration` |
| `### Testes` | Manter a parte genérica; a parte de agente está em `agent-conventions.md` |
| Placeholders | `{project-name}-api` e `{project-name}-core` → `{agent-module}`; `{package}` → `{base-package}`; nomes do `eaf-agent` (`eaf-agent-assistant`, `br.com.eaf.agent`, `EafAgentAssistantApplication`) nunca aparecem |

Verifique que o resultado renderiza nas duas linguagens e não cita o que não existe:

```bash
cd /tmp/new-agent-proof
T=/Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/templates/architecture-conventions.md.template
printf 'language=kotlin\ndsl-ext=.kts\nsrc-dir=kotlin\n' >> vars.env
printf 'language=java\ndsl-ext=\nsrc-dir=java\n' >> varsj.env
VARS=$PWD/vars.env ON=kotlin,postgres,web,buildingBlocks,do-zero python3 render.py file $T /tmp/conv-kt.md; echo "EXIT=$?"
VARS=$PWD/varsj.env ON=java,sem-postgres,sem-web,buildingBlocks,do-zero python3 render.py file $T /tmp/conv-java.md; echo "EXIT=$?"
grep -nciE 'mobile|expo|eaf' /tmp/conv-kt.md /tmp/conv-java.md
grep -nE '\-core|\-api' /tmp/conv-kt.md
grep -ciE 'migration|next' /tmp/conv-java.md
```

Expected: dois `EXIT=0`; `0` ocorrências de `mobile`, `expo` e `eaf` nos dois; `-core`/`-api` só na frase sobre extração futura; `0` menções a migration e a Next na versão Java sem banco e sem web.

- [ ] **Step 6: O `SKILL.md` completo**

Substitua todo o corpo do `SKILL.md` (o frontmatter da T1 fica) por:

````markdown
# Novo agente conversacional

A skill entrega um agente **funcionando**: uma conversa de ponta a ponta, com
endpoint, LLM, cliente MCP, observabilidade e testes. É a diferença deliberada
em relação à `analizza-new-project`, que entrega só a forma — um agente sem
endpoint, LLM e trace não prova nada. O que continua proibido é **código de
domínio**: `domain/` nasce vazio.

Dois modos, **detectados, não perguntados**:

```
Do zero                                   Projeto existente
{project-name}/                           {base}/
├── buildingBlocks/                       ├── {base}-api/          intocado
├── {agent-module}/   4 camadas           ├── {base}-core/         intocado
├── {project-name}-web/   [pergunta]      ├── {base}-mcp/          vira o servidor MCP padrão, se existir
├── docker-compose.yml    [se Postgres]   ├── {agent-module}/      app próprio, porta própria
├── docker-compose.langwatch.yml          ├── docker-compose.langwatch.yml
├── local.env*.example                    ├── local.env*.example
├── Makefile                              └── Makefile             + alvos do agente
└── <arquivo do SDD>
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
| `{agent-module}` | módulo do agente — pergunta |
| `{app-class}` | PascalCase de `{agent-module}` + `Application` |
| `{package}` | pacote base do projeto |
| `{base-package}` | pacote raiz do agente: `{package}` do zero, `{package}.agent` no existente |
| `{bb-package}` | pacote do `buildingBlocks`: `{package}` |
| `{package-path}` | `{base-package}` com `.` trocado por `/` |
| `{group}`, `{java-version}` | perguntados (do zero) ou lidos do build (existente) |
| `{language}`, `{src-dir}` | `kotlin` ou `java` |
| `{dsl-ext}` | `.kts` ou vazio |
| `{agent-port}` | `8080` do zero; `8081` no existente, ou a seguinte se o `-api` já a usa |
| `{mcp-name}` | nome kebab do servidor MCP; `tools-mcp` se nenhum foi informado |
| `{mcp-class}`, `{mcp-env}` | `{mcp-name}` em PascalCase e em UPPER_SNAKE |
| `{mcp-url}`, `{mcp-enabled}` | URL e `true`, ou vazio e `false` |
| `{db-name}` | `{project-name}` com `-`→`_`; no existente, com o sufixo `_agent` |
| `{db-port}` | `5432` do zero; `5433` no existente |
| `{langchain4j-version}` | `1.20.0-beta30`, conferida no Passo 3 |

Em **nome de arquivo** o placeholder aparece como `__nome__`
(`__mcp-class__Config.kt.template` → `ToolsMcpConfig.kt`).

### Marcadores condicionais

Uma linha `<!-- se X -->` abre um bloco que só entra quando X vale; `<!-- fim
se X -->` fecha. A primeira linha `<!-- arquivo se X -->` condiciona o arquivo
inteiro. **Nenhuma linha de marcador vai para o arquivo final**, e blocos de
condição que não vale somem inteiros.

| Condição | Vale quando |
|---|---|
| `kotlin` / `java` | linguagem do fonte |
| `do-zero` / `existente` | o modo |
| `postgres` / `sem-postgres` | o agente tem banco |
| `memoria` / `sem-memoria` | o usuário quis memória de conversa |
| `memoria-jdbc` | `memoria` e `postgres` |
| `memoria-processo` | `memoria` e `sem-postgres` |
| `buildingBlocks` / `sem-buildingBlocks` | o projeto tem o módulo `buildingBlocks` |
| `web` / `sem-web` | modo do zero com `-web` aceito |
| `it-dedicado` | do zero **com** banco: ITs em `{project-name}-integration-tests` |
| `it-no-modulo` | existente, **ou** do zero sem banco: ITs dentro do `{agent-module}` |

### Espelhamento de árvore

| Template | Destino |
|---|---|
| `templates/source/{language}/main/<caminho>` | `{agent-module}/src/main/{src-dir}/{package-path}/<caminho>` |
| `templates/source/{language}/test/<caminho>` | `{agent-module}/src/test/{src-dir}/{package-path}/<caminho>` |
| `templates/source/{language}/it/<caminho>` | `{it-module}/src/test/{src-dir}/{package-path}/<caminho>` |
| `templates/resources/<caminho>` | `{agent-module}/src/main/resources/<caminho>` |
| `templates/web/src/<caminho>` | `{project-name}-web/src/<caminho>` |

O sufixo `.template` cai. `{it-module}` é `{agent-module}` em `it-no-modulo` e
`{project-name}-integration-tests` em `it-dedicado`.

## Procedimento

### Passo 0 — Detectar o modo e os pré-requisitos

```bash
find . -maxdepth 1 -name 'settings.gradle*'
java -version; docker info > /dev/null 2>&1 && echo "docker OK"
```

- **Há `settings.gradle*`** → modo **existente**. Diga isso ao usuário e por quê.
- **Não há** → modo **do zero**. Se a pasta não estiver vazia, mostre o
  conteúdo e confirme antes de escrever qualquer coisa.

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
| `mcp-name` e `mcp-url` | pergunta; pode ficar vazio | padrão: `{base}-mcp` e `http://localhost:{api-port}/mcp`, se o módulo existir |

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

**DSL do Gradle.** Do zero segue a linguagem (Kotlin → `.kts`, Java → Groovy).
No existente vale a do `settings.gradle*` que já existe.

Com as respostas, fixe as condições da tabela de marcadores e diga ao usuário
o conjunto resultante antes de escrever.

### Passo 2 — Backend base

**Do zero.** Siga a [referência do Initializr](../analizza-new-project/references/initializr-api.md)
e o [multi-módulo](../analizza-new-project/references/gradle-multi-module.md)
da `analizza-new-project`, com estas diferenças:

- `artifactId` e `name` = `{agent-module}`; `dependencies=web,actuator`. O
  resto das dependências vem do template do módulo, não do Initializr.
- Promova o wrapper, o `.gitignore` e o `.gitattributes` à raiz; o resto fica
  em `{agent-module}/`.
- Leia as versões do `plugins {}` que o Initializr gerou e grave
  [root.gradle.kts.template](./templates/build/kts/root.gradle.kts.template) ou
  [root.gradle.template](./templates/build/groovy/root.gradle.template) como
  `build.gradle{dsl-ext}` da raiz.
- **Substitua** o `build.gradle{dsl-ext}` do módulo por
  [agent-module.gradle.kts.template](./templates/build/kts/agent-module.gradle.kts.template)
  ou [agent-module.gradle.template](./templates/build/groovy/agent-module.gradle.template).
- Gere o `buildingBlocks` exatamente como o Passo 5 da `analizza-new-project`
  (templates em `../analizza-new-project/templates/buildingBlocks/`).
- `settings.gradle{dsl-ext}`: `rootProject.name` e os `include` de
  `buildingBlocks` e `{agent-module}`.
- **Apague** `{agent-module}/src/test` e
  `{agent-module}/src/main/resources/application.properties` que vieram do
  Initializr. O `contextLoads` dele sobe a aplicação inteira e exigiria as
  variáveis do LLM em todo `build`; o teste de contexto volta como IT no Passo 10.
- `git init` agora, se ainda não for repositório — o Passo 8 depende disso.

**Existente.** Crie `{agent-module}/` com o `build.gradle{dsl-ext}` do template
da DSL do projeto, acrescente o `include` ao `settings.gradle{dsl-ext}` e
confira que a raiz declara, com versão, todo plugin que o módulo aplica sem
versão. A classe de aplicação vem de `templates/source/{language}/main/__app-class__.*`.

Nos dois modos, acrescente a `gradle.properties` (criando o arquivo se faltar):

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

**Não escreva nada em `domain/`.** E reescreva o
`resources/prompts/system-prompt.prompt` só se o usuário disser o papel do
agente; o que vem do template é neutro de propósito.

```bash
compile=$([ "{language}" = kotlin ] && echo compileKotlin || echo compileJava)
./gradlew :{agent-module}:$compile --console=plain > /tmp/agent-compile.log 2>&1; echo "EXIT=$?"
grep -c "NO-SOURCE" /tmp/agent-compile.log
```

`EXIT=0` e `0`.

### Passo 5 — O servidor MCP

O par `{mcp-class}Config` + `{mcp-class}Properties` já veio no Passo 4. O que
muda com a resposta do usuário é só `{mcp-enabled}` e `{mcp-url}` no
`application.yaml` e nos arquivos de ambiente.

Não há o que conectar agora, e isso é intencional: o cliente nasce na primeira
conversa. Sem servidor informado, diga no relatório que o agente conversa só
com o LLM e como ligar depois (`{mcp-env}_ENABLED=true` e `_BASE_URL`).

### Passo 6 — Banco e memória

- **`postgres`, do zero:** grave
  [o compose da new-project](../analizza-new-project/templates/docker-compose.template)
  como `docker-compose.yml`.
- **`postgres`, existente:** acrescente o serviço e o volume de
  [docker-compose.agent-postgres.template](./templates/root/docker-compose.agent-postgres.template)
  ao compose do projeto. O banco é **do agente** (`{db-name}`, porta
  `{db-port}`), nunca o do `-core`.
- **`memoria-jdbc`:** a migration `V1__chat_memory.sql` e o `ChatMemoryConfig`
  já vieram no Passo 4. Não mude nome nem tipo de coluna: é o schema que o
  store do LangChain4j espera.
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

No modo existente, se o `Makefile` já tiver um alvo com o mesmo nome, **não
sobrescreva**: mostre o conflito e pergunte.

```bash
[ "$(grep -c $'^\t' Makefile)" -gt 10 ] && echo "TAB OK" || echo "TAB FALHOU"
git check-ignore -q local.env local.env.ollama langwatch.env && echo "IGNORE OK"
```

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
`page.tsx`. Em `page.tsx` o **único** placeholder é `{project-name}`: o resto
entre chaves é JSX e fica como está.

```bash
cd {project-name}-web && npm run lint && npm run build; echo "EXIT=$?"
```

Os dois `*.test.ts` copiados só rodam depois do Passo 10, que instala o Vitest.

### Passo 9 — Convenções e runbook

Detecte o framework de SDD e o arquivo de destino por
[sdd-frameworks.md](../analizza-new-project/references/sdd-frameworks.md).

- **Do zero:** grave
  [architecture-conventions.md.template](./templates/architecture-conventions.md.template)
  e, logo depois, a seção de
  [agent-conventions.md](./references/agent-conventions.md).
- **Existente:** acrescente só a seção de `agent-conventions.md`. **Nunca
  sobrescreva** o que o arquivo já tem.

Grave [runbook-agent-chat.md](./references/runbook-agent-chat.md) como
`docs/checkpoints/agent-chat.md`.

### Passo 10 — Testes

**Unitários.** Copie `templates/source/{language}/test/`.

```bash
./gradlew :{agent-module}:test --console=plain > /tmp/agent-test.log 2>&1; echo "EXIT=$?"
```

Exija `EXIT=0` e leia a contagem no XML de `build/test-results/test/`, não no
`BUILD SUCCESSFUL`: 36 testes com memória, 34 sem.

**Integração, `it-dedicado`.** Invoque a skill `analizza-integration-test`:

```
escopo=ambos|backend linguagem={language} banco=postgres layout=dedicado
```

`ambos` se houver web. **Antes de invocar**, exporte um LLM de mentira — a
verificação dela sobe o contexto da aplicação, que não sobe sem estas três:

```bash
export LLM_BASE_URL=http://localhost:9/v1 LLM_API_TOKEN=x LLM_MODEL=x
```

Nada conecta nessa hora (nem LLM nem MCP conectam na subida), então o contexto
sobe. Depois que ela terminar, aplique
[it-llm-layer.md](./references/it-llm-layer.md) e desfaça o `export`.

**Integração, `it-no-modulo`.** Copie `templates/source/{language}/it/` para
dentro do `{agent-module}`. A `analizza-integration-test` **não** é invocada
para o backend: ela exige um banco e um módulo dedicado cuja aplicação é a do
`-api`. Consequência a relatar: sem regra ArchUnit, JaCoCo e Pitest para o
agente. Havendo web, invoque-a com `escopo=frontend`.

### Passo 11 — Verificar

Obrigatório. Sem isso não há como afirmar que o agente funciona.

```bash
make build > /tmp/agent-build.log 2>&1; echo "EXIT=$?"
# it-dedicado: ./gradlew integrationTest      it-no-modulo: ./gradlew :{agent-module}:integrationTest
./gradlew integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
```

Avise o usuário **antes** de rodar os ITs: a primeira execução baixa cerca de
2 GB (imagem do Ollama e modelo) e a inferência em CPU leva minutos.

Smoke com LLM de verdade. Use o Ollama do usuário se houver (`ollama list`);
senão, a imagem que os ITs acabaram de gravar:

```bash
docker run -d --rm --name agent-smoke-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
sed -e 's#localhost:11434#localhost:11435#' -e 's#qwen2.5:7b#qwen2.5:3b#' local.env.ollama.example > local.env.ollama
make run-agent-ollama > /tmp/agent-run.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:{agent-port}/actuator/health > /dev/null 2>&1 && break; sleep 2; done
curl -s -D - -X POST http://localhost:{agent-port}/api/v1/agent/http \
  -H 'Content-Type: application/json' -H 'X-Conversation-Id: smoke-1' -d '{"body":"Diga oi."}'
curl -s -N --max-time 240 -X POST http://localhost:{agent-port}/api/v1/agent/stream \
  -H 'Content-Type: application/json' -d '{"body":"Diga tchau."}' | head -5
curl -s http://localhost:{agent-port}/actuator/prometheus | grep '^chat_requests_total'
```

Precisa vir `200` com o header ecoado e `response` não vazio, linhas `data:`,
e `chat_requests_total{outcome="success"}`. Se o loop estourar, leia
`/tmp/agent-run.log` e reporte — não siga adiante.

Encerre o agente e o container, e confirme que a porta ficou livre. Com
`postgres`, derrube o banco por último.

### Passo 12 — Relatar

- O modo detectado, a linguagem, e as versões reais (Boot, Java, LangChain4j,
  Next) — **lidas dos arquivos**
- Os `EXIT=` e as contagens de teste observados, unitários e de integração
- O que ficou **desligado** e como ligar: servidor MCP, memória, web
- Com `memoria-processo`: que a memória some a cada restart
- No modo existente com `{base}-mcp`: que falta a credencial em
  `{mcp-env}_AUTHORIZATION`, se o servidor for protegido
- Em `it-no-modulo`: que o agente ficou sem ArchUnit, JaCoCo e Pitest
- Que o primeiro IT baixa ~2 GB e que os ITs ficam fora do `build`
- Onde as convenções e o runbook foram gravados
- O que **não** foi conferido — a tela no navegador, o trace no LangWatch — em
  vez de afirmar que funciona

## Fora de escopo

Mobile, multi-agente, A2A, gateway de LLM, Dockerfile e CI/CD do agente.

Autenticação do endpoint de chat e propagação da identidade do usuário até o
servidor MCP: a forma está nas convenções, o código não sai do scaffold.

Tools: a skill entrega o **cliente** MCP. Quais tools existem e o que cada uma
devolve ao modelo é decisão de exposição de dado, tomada por quem conhece o
domínio — na `analizza-add-mcp-module` e no runbook.

## Notas

- Ver [armadilhas do agente](./references/pitfalls-agent.md) antes de depurar
  qualquer coisa de LangChain4j, SSE ou Testcontainers.
- O `{agent-module}` leva `spring-boot-starter-jdbc`, não `data-jpa`: nasce sem
  entidade. Quem escrever a primeira troca o starter.
- O web fala com o agente por route handler (`/api/chat`), então o agente não
  precisa de CORS.
````

- [ ] **Step 7: Conferir que todo caminho citado no `SKILL.md` existe**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent
grep -oE '\]\(\.{1,2}/[^)]+\)' SKILL.md references/*.md | sed -E 's/^([^:]+):\]\((.*)\)$/\1 \2/' | while read origem alvo; do
  base=$(dirname "$origem"); [ -e "$base/$alvo" ] || echo "QUEBRADO em $origem: $alvo"
done; echo "conferido"
grep -c '<!-- se\|<!-- fim se\|<!-- arquivo se' SKILL.md
cd ../../../.. && make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
```

Expected: nenhuma linha `QUEBRADO`; `EXIT=0`. (O `grep -c` de marcadores no `SKILL.md` é maior que zero só por causa da explicação do vocabulário — confira que não há bloco condicional de verdade perdido no texto.)

- [ ] **Step 8: Commitar**

```bash
git add plugins/analizza-skills/skills/analizza-new-agent
git commit -m "SKILL.md, convencoes e runbook da analizza-new-agent

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: As quatro aplicações de prova

**Files:**
- Modify: o que cada prova mostrar que está errado em `$S/` (templates, `SKILL.md`, referências)
- Create (descartável): `/tmp/new-agent-proof/p1` … `p4`

**Interfaces:**
- Consumes: a skill inteira, como um usuário a receberia — `SKILL.md` e os arquivos que ele cita. **Nada deste plano.**
- Produces: para cada prova, os `EXIT=` e contagens observados, e a lista do que precisou mudar na skill. A T10 leva isso para a spec e para o PR.

Até aqui os templates foram verificados renderizando-os com um script. Isso prova o **código**; não prova que o `SKILL.md` basta para alguém chegar nesse código. Cada prova é feita por um subagente novo, que recebe o caminho da skill, a pasta alvo e as respostas — e mais nada. Tudo o que ele precisar perguntar, adivinhar ou consertar é defeito do `SKILL.md`.

| # | Modo | Linguagem | Alvo | Respostas |
|---|---|---|---|---|
| 1 | do zero | Kotlin | `/tmp/new-agent-proof/p1/loja` (vazia) | módulo `loja-agent`; web sim; Postgres sim; memória sim; MCP vazio |
| 2 | do zero | Java | `/tmp/new-agent-proof/p2/suporte-agent` (vazia) | módulo `suporte-agent-assistant` (o nome do projeto termina em `-agent`: a skill tem de apontar a redundância); web não; Postgres não; memória sim; MCP vazio |
| 3 | existente | Java, Groovy | cópia do `analizza-auction` | módulo `analizza-auction-agent`; Postgres não; memória sim; MCP = o `analizza-auction-mcp` detectado |
| 4 | existente | Kotlin, `.kts` | cópia do `eaf-agent` | módulo `eaf-agent-concierge`; Postgres sim; memória sim; MCP vazio |

Juntas cobrem: os dois modos × as duas linguagens × as duas DSLs; `it-dedicado` (1) e `it-no-modulo` (2, 3, 4); `memoria-jdbc` (1, 4) e `memoria-processo` (2, 3); com e sem web; com e sem `buildingBlocks` próprio; MCP ligado (3) e desligado.

- [ ] **Step 1: Preparar os alvos**

As provas 3 e 4 rodam em **cópias**. Os repositórios originais não são tocados.

```bash
cd /tmp/new-agent-proof && rm -rf p1 p2 p3 p4 && mkdir -p p1/loja p2/suporte-agent p3 p4
rsync -a --exclude node_modules --exclude build --exclude .gradle --exclude .next \
  /Users/diegolirio/Documents/Github/analizza-auction/ p3/analizza-auction/
rsync -a --exclude node_modules --exclude build --exclude .gradle --exclude .next --exclude .expo \
  /Users/diegolirio/Documents/Github/eaf-agent/ p4/eaf-agent/
for d in p3/analizza-auction p4/eaf-agent; do
  git -C $d remote remove origin 2>/dev/null; git -C $d checkout -q -b prova-new-agent; git -C $d status --short | wc -l
done
git -C /Users/diegolirio/Documents/Github/analizza-auction status --short | wc -l
git -C /Users/diegolirio/Documents/Github/eaf-agent status --short | wc -l
```

Anote as duas últimas contagens: precisam ser as mesmas no fim da tarefa (Step 7). O `remote remove` existe para que nenhum `git push` de dentro de uma cópia chegue ao repositório de verdade.

- [ ] **Step 2: Prova 1 — do zero, Kotlin, tudo ligado**

Despache um subagente com exatamente este pedido:

```
Aplique a skill em /Users/diegolirio/Documents/Github/analizza-marketplace/plugins/analizza-skills/skills/analizza-new-agent/SKILL.md
na pasta /tmp/new-agent-proof/p1/loja (trabalhe só dentro dela). Siga o SKILL.md passo a passo; não leia
nenhum outro documento de planejamento. Respostas às perguntas da skill: linguagem kotlin; group br.com.analizza;
pacote br.com.analizza.loja; Java 25; módulo loja-agent; web sim; Postgres sim; memória de conversa sim; servidor
MCP: nenhum. Quando a skill mandar invocar a analizza-integration-test, siga o SKILL.md dela em
../analizza-integration-test/SKILL.md com os padrões indicados, aceitando cada padrão.
No fim, relate: (a) cada EXIT= e contagem de teste observados; (b) cada ponto em que o SKILL.md foi ambíguo,
incompleto ou errado, e o que você fez; (c) o que você não conseguiu verificar.
```

Gate, conferido por você e não pelo relato do subagente:

```bash
cd /tmp/new-agent-proof/p1/loja
ls; cat settings.gradle.kts
grep -rn 'dev.langchain4j' loja-agent/src/main/kotlin --include='*.kt' -l | grep -v '/infrastructure/' | wc -l
find loja-agent/src/main/kotlin -path '*/domain/*' -name '*.kt' | wc -l
grep -rnE '<!-- (fim )?se |<!-- arquivo se |\{[a-z]+(-[a-z]+)+\}' --include='*.kt' --include='*.yaml' --include='*.kts' --include='Makefile' --include='*.md' --include='*.ts' . | grep -v node_modules | head
make build > /tmp/p1-build.log 2>&1; echo "EXIT=$?"
./gradlew integrationTest --console=plain > /tmp/p1-it.log 2>&1; echo "EXIT=$?"
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
for pat in ('loja-agent/build/test-results/test/*.xml', '*-integration-tests/build/test-results/integrationTest/*.xml'):
    t = f = e = 0
    for x in glob.glob(pat):
        r = ET.parse(x).getroot(); t += int(r.get('tests')); f += int(r.get('failures')); e += int(r.get('errors'))
    print(pat.split('/')[0], f"tests={t} failures={f} errors={e}")
PY
ls *-integration-tests/build/test-results/integrationTest/ | grep -cE 'ChatRouteIT|EntrypointHasIntegrationTestIT|ApplicationContextIT'
(cd loja-web && npm test; echo "EXIT=$?")
git ls-files --stage | grep -c '^160000'
```

Expected: módulos `buildingBlocks`, `loja-agent`, `loja-integration-tests`, `loja-web`, **sem** `-core`; `0` arquivos fora de `infrastructure/` importando LangChain4j; `0` arquivos Kotlin em `domain/`; nenhum marcador ou placeholder sobrando; `make build` e `integrationTest` com `EXIT=0`; `loja-agent tests=36 failures=0 errors=0`; os três ITs presentes, com `failures=0 errors=0`; testes do web com `EXIT=0`; `0` gitlinks.

Depois, o smoke do Passo 11 do `SKILL.md`, mais a tela:

```bash
make langwatch-up 2>&1 | tail -2; echo "EXIT=$?"
```

`make langwatch-up` falha sem `langwatch.env` — copie do exemplo, gere os quatro segredos com `openssl rand -hex 32` e rode de novo. Expected: `http://localhost:5560` responde. Trace com conteúdo exige criar a chave na interface: se não der para fazer nesta sessão, registre como **não conferido**. `make langwatch-down` ao terminar.

- [ ] **Step 3: Corrigir a skill com o que a prova 1 mostrou**

Para cada item (b) do relato e cada gate vermelho: corrija o **template ou o `SKILL.md`**, nunca só a pasta de prova. Depois de corrigir, apague `p1/loja` e repita o Step 2 inteiro com um subagente novo, até o gate passar sem intervenção. Commit por rodada:

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
git add plugins/analizza-skills/skills/analizza-new-agent
git commit -m "Corrige a analizza-new-agent com o que a prova 1 ensinou

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Se a prova não mostrar nada a corrigir, não há commit — diga isso no relato.

- [ ] **Step 4: Prova 2 — do zero, Java, mínimo**

Mesmo pedido do Step 2, trocando: pasta `/tmp/new-agent-proof/p2/suporte-agent`; linguagem java; pacote `br.com.analizza.suporte`; módulo: "aceite a alternativa que a skill oferecer para o nome redundante"; web não; Postgres não; memória sim; MCP nenhum.

Gate:

```bash
cd /tmp/new-agent-proof/p2/suporte-agent
cat settings.gradle; ls
ls | grep -cE 'web|integration-tests|docker-compose.yml'
find . -path ./build -prune -o -name '*.sql' -print | wc -l
make build > /tmp/p2-build.log 2>&1; echo "EXIT=$?"
make test-integration > /tmp/p2-it.log 2>&1; echo "EXIT=$?"
python3 - <<'PY'
import glob, xml.etree.ElementTree as ET
for task in ('test', 'integrationTest'):
    t = f = e = 0
    for x in glob.glob(f'*/build/test-results/{task}/*.xml'):
        r = ET.parse(x).getroot(); t += int(r.get('tests')); f += int(r.get('failures')); e += int(r.get('errors'))
    print(task, f"tests={t} failures={f} errors={e}")
PY
```

Expected: módulo `suporte-agent-assistant` (o subagente relata que a skill apontou a redundância); `0` para web, módulo de IT dedicado e `docker-compose.yml`; `0` migrations; dois `EXIT=0`; `test tests=36`, `integrationTest tests=3`, sem falha. O relato precisa dizer que o agente ficou **sem ArchUnit, JaCoCo e Pitest** — se a skill não levou o subagente a dizer isso, o Passo 12 do `SKILL.md` está fraco.

Corrija e repita como no Step 3 (commit "…com o que a prova 2 ensinou").

- [ ] **Step 5: Prova 3 — existente, Java, com o `-mcp` de verdade**

Pedido ao subagente: aplicar a skill em `/tmp/new-agent-proof/p3/analizza-auction`; módulo `analizza-auction-agent`; Postgres não; memória sim; servidor MCP: aceitar o padrão detectado.

Gate:

```bash
cd /tmp/new-agent-proof/p3/analizza-auction
git status --short | grep -vE 'analizza-auction-agent/|settings.gradle|gradle.properties|Makefile|\.gitignore|local\.env|langwatch|docs/|AGENTS.md|CLAUDE.md|GEMINI.md' | head
grep -n 'analizza-auction-agent' settings.gradle
grep -rn '^package ' analizza-auction-agent/src/main/java | head -3
grep -rnE "project\(':analizza-auction-(core|api)'\)" analizza-auction-agent/build.gradle | wc -l
grep -nE 'enabled|base-url' analizza-auction-agent/src/main/resources/application.yaml | head -4
./gradlew :analizza-auction-agent:build --console=plain > /tmp/p3-build.log 2>&1; echo "EXIT=$?"
./gradlew :analizza-auction-agent:integrationTest --console=plain > /tmp/p3-it.log 2>&1; echo "EXIT=$?"
./gradlew :analizza-auction-api:compileJava --console=plain > /tmp/p3-api.log 2>&1; echo "EXIT=$?"
```

Expected: o primeiro comando não imprime nada — **nenhum arquivo do `-api`, do `-core` ou do `-mcp` mudou**; o pacote do agente termina em `.agent`; `0` dependências sobre `-core`/`-api`; MCP `enabled` verdadeiro apontando para `/mcp`; três `EXIT=0` (o `-api` continua compilando).

O smoke que só este cenário permite — D11, o servidor MCP fora:

```bash
docker run -d --rm --name agent-smoke-ollama -p 11435:11434 tc-ollama-qwen2.5-3b
sed -e 's#localhost:11434#localhost:11435#' -e 's#qwen2.5:7b#qwen2.5:3b#' local.env.ollama.example > local.env.ollama
make run-agent-ollama > /tmp/p3-run.log 2>&1 &
for i in $(seq 90); do curl -sf http://localhost:8081/actuator/health >/dev/null 2>&1 && break; sleep 2; done
curl -s http://localhost:8081/actuator/health
curl -s -w '\n%{http_code}\n' -X POST http://localhost:8081/api/v1/agent/http -H 'Content-Type: application/json' -d '{"body":"oi"}'
```

Expected, com o `-api` do auction **parado**: health `UP` (o agente subiu sem o servidor MCP) e a conversa devolvendo `502` com `"code":"MCP_UNAVAILABLE"`. É a prova de que o agente não responde sem ferramentas.

Em seguida tente o caminho feliz: suba o `-api` do auction (`make run` ou equivalente do projeto), obtenha uma credencial do jeito que o runbook de MCP dele descreve (`docs/checkpoints/`), ponha em `ANALIZZA_AUCTION_MCP_AUTHORIZATION` e converse de novo **sem reiniciar o agente** — precisa reconectar e responder `200`. Se não for possível obter a credencial nesta sessão, **registre como não provado**: "reconexão e tool calling contra o `-mcp` real não foram conferidos; o `502` com servidor fora foi".

Encerre tudo, confirme 8080 e 8081 livres. Corrija e repita como no Step 3 (commit "…com o que a prova 3 ensinou").

- [ ] **Step 6: Prova 4 — existente, Kotlin, com banco próprio**

Pedido ao subagente: aplicar a skill em `/tmp/new-agent-proof/p4/eaf-agent`; módulo `eaf-agent-concierge`; Postgres sim; memória sim; servidor MCP nenhum.

Gate:

```bash
cd /tmp/new-agent-proof/p4/eaf-agent
git status --short | grep -E 'eaf-agent-assistant/|eaf-agent-integration-tests/|buildingBlocks/' | head
grep -n 'postgres-agent\|5433' docker-compose.yml
grep -n 'eaf_agent_agent\|5433' eaf-agent-concierge/src/main/resources/application.yaml
ls eaf-agent-concierge/src/main/resources/db/migration
grep -n 'buildingBlocks' eaf-agent-concierge/build.gradle.kts
./gradlew :eaf-agent-concierge:build --console=plain > /tmp/p4-build.log 2>&1; echo "EXIT=$?"
./gradlew :eaf-agent-concierge:integrationTest --console=plain > /tmp/p4-it.log 2>&1; echo "EXIT=$?"
./gradlew build --console=plain > /tmp/p4-all.log 2>&1; echo "EXIT=$?"
```

Expected: nenhum arquivo dos módulos que já existiam mudou; o compose ganhou `postgres-agent` na 5433, sem mexer no `postgres` original; o YAML aponta para o banco `eaf_agent_agent` na 5433; `V1__chat_memory.sql` presente; o módulo depende de `:buildingBlocks` (o do projeto); três `EXIT=0` — o último prova que o build **inteiro** do projeto continua de pé com o módulo novo. O `ChatRouteIT` passa com a asserção da linha em `chat_memory`.

Corrija e repita como no Step 3 (commit "…com o que a prova 4 ensinou").

- [ ] **Step 7: Conferir que nada vazou e limpar**

```bash
git -C /Users/diegolirio/Documents/Github/analizza-auction status --short | wc -l
git -C /Users/diegolirio/Documents/Github/eaf-agent status --short | wc -l
docker ps --format '{{.Names}}' | grep -E 'agent-(proof|smoke)|langwatch|loja|suporte' ; echo "containers conferidos"
lsof -i :8080 -i :8081 -i :3000 -i :11435 | head -3
```

Expected: as mesmas duas contagens do Step 1; nenhum container de prova de pé; nenhuma das portas ocupada por processo desta tarefa. Derrube o que sobrar com `docker stop <nome>`. **Não** apague `/tmp/new-agent-proof` ainda: a T10 cita os logs.

---

### Task 10: Release, spec e PR

**Files:**
- Modify: `plugins/analizza-skills/.claude-plugin/plugin.json` (`version`)
- Modify: `plugins/analizza-skills/.codex-plugin/plugin.json` (`version`, `longDescription`)
- Modify: `README.md` (tabela de skills)
- Modify: `docs/superpowers/specs/2026-10-06-analizza-new-agent-skill-design.md` (o que as provas mudaram)

**Interfaces:**
- Consumes: os relatos e commits da T9.
- Produces: a branch `feat/analizza-new-agent` pronta para PR, com `make validate` e `make check` verdes.

- [ ] **Step 1: Subir a versão nos dois manifestos**

Em `plugins/analizza-skills/.claude-plugin/plugin.json` e em `plugins/analizza-skills/.codex-plugin/plugin.json`: `"version": "0.5.0"` → `"version": "0.6.0"`.

No manifesto do Codex, troque a `longDescription` por:

```json
"longDescription": "Cria monorepos do zero (api, core, web, mobile), cria agentes conversacionais de IA com LangChain4j e cliente MCP, acrescenta servidor MCP a projetos existentes e configura infraestrutura de testes de integração em projetos Kotlin ou Java com Spring Boot.",
```

- [ ] **Step 2: A linha da skill no `README.md`**

Na tabela `## Skills do plugin analizza-skills`, entre `analizza-integration-test` e `analizza-new-project` (a tabela está em ordem alfabética):

```markdown
| `analizza-new-agent` | Cria um agente conversacional de IA em Spring Boot, em Java ou Kotlin. Do zero: monorepo sem `-core`, com `{project}-agent` carregando as quatro camadas num módulo só, `buildingBlocks` e, se pedido, `{project}-web` com tela de chat, Postgres e memória de conversa. Em projeto existente: acrescenta `{base}-agent` como aplicação própria, que fala com o domínio por MCP. Entrega endpoint de chat (JSON e SSE), LLM OpenAI-compatível via LangChain4j atrás de uma interface, cliente MCP preguiçoso que falha em vez de responder sem ferramentas, observabilidade (OpenTelemetry, LangWatch local, Prometheus) e testes com LLM roteirizado e com Ollama em Testcontainers. |
```

- [ ] **Step 3: Levar à spec o que mudou**

A spec foi escrita antes do código. Atualize-a com o que as provas ensinaram, para ela descrever o que existe: cada decisão (D1–D18) que a T9 contrariou ou refinou ganha a correção **no texto da decisão**, e a seção *Prova* ganha, por prova, os `EXIT=` e contagens observados e a lista do que **não** foi provado (trace no LangWatch, tela no navegador, tool calling contra o `-mcp` real — os que se aplicarem). Não acrescente seção de "histórico": a spec descreve o desenho vigente.

- [ ] **Step 4: Validar tudo**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace
make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"
make check > /tmp/check.log 2>&1; echo "EXIT=$?"
find plugins/analizza-skills/skills/analizza-new-agent -name '*.template' | wc -l
grep -rnE 'pags|Pags|intranet|pagseguro|eaf-agent|agentic' plugins/analizza-skills/skills/analizza-new-agent | head
grep -rn '@@TAB@@' plugins/analizza-skills/skills/analizza-new-agent | head
git status --short
```

Expected: dois `EXIT=0`; cerca de 100 templates; os dois `grep` não imprimem nada — nenhum resto da Pags, do `eaf-agent` ou do sentinela de TAB; `git status` só com o que esta tarefa mudou.

- [ ] **Step 5: Commitar**

```bash
git add plugins/analizza-skills/.claude-plugin/plugin.json plugins/analizza-skills/.codex-plugin/plugin.json README.md docs/superpowers/specs/2026-10-06-analizza-new-agent-skill-design.md
git commit -m "Publica a analizza-new-agent na versao 0.6.0

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Abrir o PR — só com o aval do usuário**

Push e PR saem do repositório: **pergunte antes**. Com o sim:

```bash
git push -u origin feat/analizza-new-agent
gh pr create --base main --title "Nova skill: analizza-new-agent" --body "$(cat <<'EOF'
## O que é

Skill `analizza-new-agent`: cria um agente conversacional de IA em Spring Boot (Kotlin ou Java), do zero — sem `-core` — ou como módulo novo num projeto Gradle existente.

Spec: `docs/superpowers/specs/2026-10-06-analizza-new-agent-skill-design.md`
Plano: `docs/superpowers/plans/2026-10-06-analizza-new-agent-skill.md`

## Como foi provada

| Prova | Modo | Resultado |
|---|---|---|
| 1 | do zero, Kotlin, web + Postgres + memória | <EXIT e contagens da T9> |
| 2 | do zero, Java, mínimo | <EXIT e contagens da T9> |
| 3 | existente, Java (cópia do analizza-auction) | <EXIT e contagens da T9> |
| 4 | existente, Kotlin (cópia do eaf-agent) | <EXIT e contagens da T9> |

## O que não foi provado

<lista da T9, ou "nada ficou sem conferir">

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Preencha os `<...>` com os números reais da T9 antes de rodar — são dados da execução, não deste plano. Um PR com o texto entre `<>` no corpo não está pronto.

---

## Self-Review

**Cobertura da spec**

| Decisão | Onde |
|---|---|
| D1 reuso por caminho relativo | T1 Step 9 (`buildingBlocks`), T8 Step 6 (referências da `new-project`) |
| D2 modo detectado | T8 `SKILL.md` Passo 0; T9 provas 1–2 vs 3–4 |
| D3 um módulo, sem `-core` | T1 (settings), T9 gate da prova 1 |
| D4 app próprio, sem `-core` | T8 Step 1; T9 gate da prova 3 |
| D5 pacote `.agent` | tabela de placeholders; T9 gate da prova 3 |
| D6 nome do módulo | `SKILL.md` Passo 1; T9 prova 2 |
| D7 Kotlin e Java | T2/T3/T5 e T7 |
| D8 fatia vertical, sem domínio | T2; gate `domain/` vazio na prova 1 |
| D9 LLM atrás de interface | T2 Step 6; gate de import do LangChain4j na prova 1 |
| D10 sem default de LLM | T2 Step 1; T4 Step 3 |
| D11 MCP preguiçoso e 502 | T2 Step 7, Step 10; T3 Step 5; T9 prova 3 |
| D12 memória | T2 Step 2 e 8; T3 Step 6; T5 Step 3 |
| D13 banco do agente | T4 Step 4; T9 prova 4 |
| D14 observabilidade | T2 Step 8; T3 Step 6; T4 Step 5; T9 prova 1 |
| D15 três níveis de teste | T3, T5, runbook da T8 |
| D16 onde os ITs moram | T5; `SKILL.md` Passo 10; provas 1 (dedicado) e 2–4 (no módulo) |
| D17 web com chat | T6 |
| D18 versões lidas | T1 Step 8–10; `SKILL.md` Passo 3 |

**Onde o plano refinou a spec** (já refletido na spec, no mesmo commit deste plano):

- As exceções do caso de uso moram em `application/chat/`, não em `presenter/` — senão o handler importaria a entrada. Há uma a mais: `McpUpstreamTimeoutException`.
- O corpo de erro é `{code, message}` (o `ErrorMessage` do `buildingBlocks`), não `{error}`.
- `spring-boot-starter-jdbc` no lugar de `data-jpa`; `otelInstrumentationVersion` saiu (nada usa `@WithSpan`).
- A base de IT se chama `BaseIntegrationTest` nos dois layouts.
- Do zero **sem banco**, os ITs ficam dentro do módulo: a `analizza-integration-test` não tem opção "sem banco".
- O cliente MCP ganhou `authorization`: um servidor criado pela `add-mcp-module` é protegido.
- As provas são quatro, e a de projeto existente com `-mcp` real é em Java (o único projeto local com `-mcp` é o `analizza-auction`).
- Referências da skill: `agent-conventions`, `it-llm-layer`, `pitfalls-agent`, `runbook-agent-chat` — `mcp-client` e `observability` viraram seções de `agent-conventions`.

**Exceção declarada à regra de "todo passo com código":** a T7 (Java) traz regras de tradução, três arquivos inteiros e um gate numérico, em vez de 40 arquivos repetidos. A redação de `architecture-conventions.md.template` (T8 Step 5) é uma adaptação guiada de um documento existente, com gate por `grep`.

**Riscos que só a execução fecha:** APIs do LangChain4j beta citadas de memória das referências (`failIfOneServerFails`, `ChatModel.listeners()`, `chatMemoryProvider` no `@AiService`); o artefato `testcontainers-ollama` no BOM do Boot 4.1; `expectHeader()` no `RestTestClient`; `springmockk 5.0.1` com Boot 4.1. Cada um tem, na tarefa em que aparece, o que fazer se falhar.
