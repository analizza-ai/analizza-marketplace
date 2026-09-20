# `analizza-add-mcp-module` — Entregas 1 e 3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estreitar a convenção de autenticação das skills (Entrega 1) e criar a skill `analizza-add-mcp-module`, que acrescenta um servidor MCP como módulo Gradle de biblioteca a um projeto Spring Boot em camadas já existente (Entrega 3).

**Architecture:** A skill nasce irmã da `analizza-integration-test`: `SKILL.md` com *Vocabulário* e *Procedimento* em passos, `templates/` separados por linguagem (`java`/`kotlin`) e por DSL (`groovy`/`kts`), `references/` para os blocos que entram na documentação do projeto alvo. Cada tarefa deste plano acrescenta templates **e** a seção do `SKILL.md` que os usa, para que o repositório nunca fique com referência pendurada e `make validate` fique verde do começo ao fim.

**Tech Stack:** Markdown (skills e templates), Python 3 (validadores em `tools/`), `claude plugin validate`, pytest. Os templates gerados alvejam Spring Boot 4.x, Spring AI 2.0.1 (`spring-ai-starter-mcp-server-webmvc`), `io.modelcontextprotocol.sdk:mcp-core` e Gradle (Groovy ou Kotlin DSL).

**Spec:** [`docs/superpowers/specs/2026-09-20-add-mcp-module-e-resource-server-design.md`](../specs/2026-09-20-add-mcp-module-e-resource-server-design.md)

## Global Constraints

- **Escopo deste plano:** Entregas 1 e 3, ambas em `analizza-marketplace`. As entregas 4 (aplicar no `analizza-auction`) e 2 (migrar o auction para resource server) rodam em outro repositório e ganham plano próprio. A ordem da spec é 1 → 3 → 4 → 2.
- `{base}-mcp` **nunca** depende do `-api` (D2). A dependência é só com o `-core`, e o pacote do módulo fica sob o pacote base da aplicação.
- A ponte de autenticação usa `Authentication.getName()` e `getAuthorities()` — **nunca** `principal as Jwt` (D4).
- Nunca gerar checagem de papel num projeto sem modelo de papel: ela negaria tudo (D5).
- A skill não decide exposição de dado; ela obriga a decisão no runbook (D6).
- A regra ArchUnit passa a cobrir `org.springframework.ai.mcp.annotation.McpTool` além de `org.springframework.ai.tool.annotation.Tool`, comparando **pelo nome**, para compilar sem `spring-ai` no classpath (D9).
- Comentários em código de template seguem a casa: português, sem acento, explicando o **porquê**.
- Todo passo de verificação roda a partir da raiz do repositório e exige `EXIT=0`.

---

### Task 1: Destravar `make validate` na main

**Files:**
- Modify: `plugins/analizza-skills/.codex-plugin/plugin.json:3`

**Interfaces:**
- Consumes: nada.
- Produces: `make validate` verde — precondição de toda tarefa seguinte, que verifica por ele.

O commit que acrescentou `@Tool` à regra ArchUnit subiu a versão só no manifesto do Claude. O validador compara os dois manifestos, então a `main` está com a validação vermelha hoje. Isto não é parte da feature; é o que destrava a verificação das outras tarefas.

- [ ] **Step 1: Reproduzir a falha**

Run: `python3 tools/validate_plugin_manifests.py; echo "EXIT=$?"`
Expected: imprime `version diverge entre os manifestos` e `EXIT=1`.

- [ ] **Step 2: Alinhar a versão do manifesto do Codex**

Em `plugins/analizza-skills/.codex-plugin/plugin.json`, trocar:

```json
  "version": "0.3.2",
```

por:

```json
  "version": "0.3.3",
```

- [ ] **Step 3: Verificar**

Run: `python3 tools/validate_plugin_manifests.py; echo "EXIT=$?"`
Expected: sem saída e `EXIT=0`.

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

- [ ] **Step 4: Commit**

```bash
git add plugins/analizza-skills/.codex-plugin/plugin.json
git commit -m "Alinha a versao do manifesto do Codex com a do Claude

O commit que acrescentou @Tool a regra ArchUnit subiu 0.3.2 -> 0.3.3 so
no .claude-plugin. O validador compara os dois manifestos, entao make
validate estava vermelho na main."
```

---

### Task 2: Entrega 1 — estreitar o mecanismo de autenticação na convenção

**Files:**
- Modify: `plugins/analizza-skills/skills/analizza-new-project/templates/architecture-conventions.md.template:332-347`

**Interfaces:**
- Consumes: nada.
- Produces: a convenção que a Entrega 2 (outro plano) implementa no `analizza-auction`.

D10: fixar o mecanismo do lado da **validação** (resource server OAuth2 do Spring Security, com `JwtDecoder`), mantendo aberto qual credencial o usuário apresenta no login. A `analizza-new-project` continua **não** escrevendo código de segurança — só muda o que a forma diz.

- [ ] **Step 1: Substituir o corpo da seção**

Em `architecture-conventions.md.template`, trocar o texto entre o título `### Autenticação e autorização` e o título `### CORS e como `-web` e `-mobile` alcançam o `-api``, hoje:

```markdown
Decidido na forma, não no mecanismo: o `-api` é um resource server stateless
— recebe uma credencial em cada requisição autenticada e a valida antes de
deixar a requisição entrar. **Emitir** a credencial é saída
(`infrastructure/security/` no `-core`, com o par interface + `impl/`
descrito acima); **validar** a credencial de uma requisição que chega é
guarda de entrada (`presenter/configuration/security/` no `-api`) — mesmo
critério de "o que é `infrastructure/`" aplicado à autenticação.

Qual credencial o usuário apresenta (senha, código, OAuth, certificado), o
formato da credencial emitida e sua validade são decisão de produto —
implemente e registre aqui quando a primeira fatia de autenticação for
escrita. Falha de autenticação que precisar ser opaca por segurança (não
revelar, por exemplo, se um identificador de login existe) segue o padrão da
seção anterior.
```

por:

```markdown
O `-api` é um resource server stateless — recebe uma credencial em cada
requisição autenticada e a valida antes de deixar a requisição entrar.
**Emitir** a credencial é saída (`infrastructure/security/` no `-core`, com o
par interface + `impl/` descrito acima); **validar** a credencial de uma
requisição que chega é guarda de entrada
(`presenter/configuration/security/` no `-api`) — mesmo critério de "o que é
`infrastructure/`" aplicado à autenticação.

Decidido também o mecanismo da validação: `spring-boot-starter-oauth2-resource-server`
com um `JwtDecoder`, não um filtro de autenticação escrito à mão. Validar
credencial é onde bug de segurança mora, e o Spring Security já entrega
decodificação, conferência de assinatura, expiração e emissor. O filtro
próprio também deixa de fora, sem ninguém perceber, o que o resto do
ecossistema assume: papéis em `GrantedAuthority`, `@PreAuthorize`, e um
`Authentication` que outras camadas conseguem ler sem conhecer o formato do
token.

Continua **aberto**, porque é decisão de produto: qual credencial o usuário
apresenta no login (senha, código, OAuth, certificado), o formato da
credencial emitida e sua validade — implemente e registre aqui quando a
primeira fatia de autenticação for escrita. Falha de autenticação que
precisar ser opaca por segurança (não revelar, por exemplo, se um
identificador de login existe) segue o padrão da seção anterior.

Qualquer código que precise saber **quem** chamou lê `Authentication.getName()`
e `getAuthorities()`, nunca o objeto do token. É o que mantém uma tool MCP, um
job ou um interceptor funcionando se o mecanismo mudar.
```

- [ ] **Step 2: Verificar que nada mais no template contradiz a mudança**

Run: `grep -n "filtro\|jjwt\|mecanismo" plugins/analizza-skills/skills/analizza-new-project/templates/architecture-conventions.md.template`
Expected: as únicas ocorrências de "mecanismo" são as duas da seção reescrita; nenhuma menção a `jjwt`.

- [ ] **Step 3: Verificar a suíte**

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `make check > /tmp/check.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

- [ ] **Step 4: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-new-project/templates/architecture-conventions.md.template
git commit -m "Fixa o resource server OAuth2 como mecanismo de validacao

A convencao ja dizia a forma (resource server stateless) e deixava o
mecanismo aberto. Validar credencial e onde bug de seguranca mora, e um
filtro escrito a mao deixa de fora papeis em GrantedAuthority. O que o
usuario apresenta no login continua decisao de produto."
```

---

### Task 3: Esqueleto da skill e os templates de build

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/SKILL.md`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/build/groovy/mcp-module.gradle.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/build/kts/mcp-module.gradle.kts.template`

**Interfaces:**
- Consumes: `make validate` verde (Task 1).
- Produces: o diretório da skill com `SKILL.md` (o validador exige um `SKILL.md` por subpasta de `skills/`), e os placeholders `{base}`, `{base-package}`, `{group}`, `{java-version}`, `{spring-ai-version}`, `{src-dir}`, `{dsl}`, `{dsl-ext}`, `{api-module}`, `{core-module}` que as Tasks 4–6 reutilizam.

O `SKILL.md` desta tarefa cobre só o que ela entrega: *Vocabulário* e os Passos 0–2. As Tasks 4, 5 e 6 acrescentam os Passos 3, 4 e 5–6 junto com os templates que cada um usa.

- [ ] **Step 1: Criar o `SKILL.md`**

```markdown
---
name: analizza-add-mcp-module
description: >-
  Acrescenta um servidor MCP a um projeto Spring Boot em camadas já existente
  (Java ou Kotlin, Gradle Groovy ou Kotlin DSL) como módulo de biblioteca
  {base}-mcp, servido por Streamable HTTP em /mcp no mesmo processo do -api.
  Detecta linguagem, DSL e pacote base, cria o módulo, liga a configuração
  STREAMABLE/SYNC, gera a ponte de autenticação que lê Authentication em vez do
  token, uma tool de exemplo a partir de um caso de uso de leitura do projeto,
  um teste de integração com cliente MCP real e o runbook de conferência. Use
  quando o usuário pedir "servidor MCP", "add mcp", "expor as consultas para
  uma IA", "tools MCP" ou "analizza add mcp module".
argument-hint: "Opcional: linguagem=java|kotlin modulo=<nome do módulo -api> papeis=<papéis exigidos pela tool> — valores passados viram padrão a confirmar"
---

# Servidor MCP como módulo de biblioteca

A skill entrega o encanamento de um servidor MCP e **uma** tool de exemplo — não
uma tool por caso de uso. Cada tool exposta é uma decisão de exposição de dado,
e isso não é de script: na implementação de referência, um campo `url` com SAS
de leitura de 3 anos só não vazou para o modelo porque uma pessoa reparou.

O módulo nasce de biblioteca: sem `main()` próprio, sem `bootJar`, servido pelo
mesmo Tomcat do `-api`. Processo e pod continuam um só.

## Vocabulário

| Placeholder | Valor |
|---|---|
| `{language}` | `kotlin` ou `java` — a linguagem do fonte de produção |
| `{src-dir}` | `kotlin` ou `java`, igual a `{language}` |
| `{dsl}` | `kts` ou `groovy` |
| `{dsl-ext}` | `.kts` quando `{dsl}=kts`, vazio quando `groovy` |
| `{base}` | `rootProject.name` do `settings.gradle{dsl-ext}` |
| `{base-package}` | pacote da classe `@SpringBootApplication` |
| `{api-module}` | módulo que tem a `@SpringBootApplication` |
| `{core-module}` | módulo de domínio do qual o MCP depende (o `-core`) |
| `{mcp-module}` | `{base}-mcp` |
| `{mcp-src}` | `{mcp-module}/src/main/{src-dir}/{base-package com / no lugar de .}/mcp` |
| `{group}`, `{java-version}` | lidos do build do `{api-module}` |
| `{spring-ai-version}` | `2.0.1` salvo se o projeto já fixar outra |

## Procedimento

### Passo 0 — Pré-requisitos

Só roda em projeto Gradle multi-módulo com Spring Boot 4.x. Confira:

```bash
find . -maxdepth 1 -name 'settings.gradle*'
grep -rlE '@SpringBootApplication' --include='*.kt' --include='*.java' . | grep '/src/main/'
grep -rhoE "org.springframework.boot['\"]? version ['\"][0-9]+" --include='build.gradle*' . | sort -u
```

Sem `settings.gradle*`, ou com Boot 3.x, **pare e diga**: o starter
`spring-ai-starter-mcp-server-webmvc` desta skill exige Boot 4.x. Não tente
adaptar.

### Passo 1 — Detectar e perguntar

Uma pergunta por vez, com o detectado como padrão. Diga o que detectou e de onde.

**Linguagem.**

```bash
find . -path '*/src/main/kotlin/*.kt' -not -path '*/build/*' | head -1   # achou: kotlin
find . -path '*/src/main/java/*.java' -not -path '*/build/*' | head -1   # achou: java
```

**DSL — não pergunte, informe.** `settings.gradle.kts` → `kts`; `settings.gradle` → `groovy`.

**Módulo `-api` e pacote base.** O `{api-module}` é o que tem a
`@SpringBootApplication`; se houver mais de um, pergunte qual recebe o MCP. O
`{base-package}` é o pacote dessa classe.

**Módulo de domínio.** O `{core-module}` é o módulo do qual o `{api-module}`
depende e que tem os handlers de leitura. Confirme com o usuário.

**A tool de exemplo.** Liste os casos de uso de **leitura** disponíveis e
pergunte qual vira a tool:

```bash
grep -rln "QueryHandler" --include='*.kt' --include='*.java' {core-module}/src/main | head -20
```

Escolha só leitura sem efeito colateral. Se o handler escolhido gravar algo
(auditoria, contador), diga ao usuário que a tool de exemplo precisa ser uma
leitura pura nesta fatia — um handler que escreve costuma precisar de algo que
mora no `-api`, e o módulo não pode depender dele.

### Passo 2 — O módulo

1. Acrescente ao `settings.gradle{dsl-ext}`: `include ':{base}-mcp'` (groovy)
   ou `include(":{base}-mcp")` (kts).
2. Grave `{mcp-module}/build.gradle{dsl-ext}` a partir de
   [mcp-module.gradle.template](./templates/build/groovy/mcp-module.gradle.template)
   (groovy) ou
   [mcp-module.gradle.kts.template](./templates/build/kts/mcp-module.gradle.kts.template)
   (kts). Grave só o bloco `<!-- se {language} -->` e remova os marcadores.
3. No `{api-module}/build.gradle{dsl-ext}`, acrescente a dependência:
   `implementation project(':{base}-mcp')` (groovy) ou
   `implementation(project(":{base}-mcp"))` (kts).
4. O módulo aplica plugins sem versão. Confirme que a raiz os declara com
   versão e `apply false`; se não declarar, leve as versões para a raiz.

**O pacote do módulo fica sob `{base-package}`** (`{base-package}.mcp`). É o que
faz o component scan do `@SpringBootApplication` alcançar as `@McpTool` sem
`@ComponentScan` extra. Não crie o módulo com pacote raiz próprio.

**O módulo nunca depende do `{api-module}`.** Se uma tool precisar de algo que
mora lá, esse algo desce para o `{core-module}`.

## Fora de escopo

Módulo com `main()` e pod próprios. Token de vida longa/revogável (PAT). Gerar
uma tool por handler do domínio. Promover projeto de módulo único a
multi-módulo.
```

- [ ] **Step 2: Criar o template de build Groovy**

`templates/build/groovy/mcp-module.gradle.template`:

```groovy
// build.gradle do modulo {base}-mcp.
// Biblioteca, nao aplicacao: sem main() e sem bootJar. As @McpTool daqui
// entram no contexto do {api-module}, que declara este modulo como
// dependencia -- processo e pod continuam um so.
plugins {
<!-- se kotlin -->
    id 'org.jetbrains.kotlin.jvm'
    id 'org.jetbrains.kotlin.plugin.spring'
<!-- fim se kotlin -->
<!-- se java -->
    id 'java-library'
<!-- fim se java -->
    id 'io.spring.dependency-management'
    // apply false: so para o BOM_COORDINATES abaixo resolver na classpath do
    // script deste modulo. O modulo continua sem aplicar o plugin do Boot.
    id 'org.springframework.boot' apply false
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

dependencyManagement {
    imports {
        mavenBom org.springframework.boot.gradle.plugin.SpringBootPlugin.BOM_COORDINATES
        mavenBom 'org.springframework.ai:spring-ai-bom:{spring-ai-version}'
    }
}

dependencies {
    // So o dominio. Este modulo nunca depende do {api-module}: quem precisa
    // saber quem chamou le a Authentication, nao uma classe do -api.
    implementation project(':{core-module}')

    // O starter -webmvc serve /mcp no mesmo Tomcat do {api-module}. O starter
    // sem o sufixo e o de stdio, que exigiria processo proprio.
    implementation 'org.springframework.ai:spring-ai-starter-mcp-server-webmvc'
    // SecurityContextHolder e Authentication vem daqui.
    implementation 'org.springframework.boot:spring-boot-starter-security'
<!-- se kotlin -->
    implementation 'org.jetbrains.kotlin:kotlin-reflect'
<!-- fim se kotlin -->
}

// Biblioteca: o jar comum basta, e nao ha bootJar a desabilitar porque o
// plugin do Boot nao esta aplicado.
tasks.named('test') {
    useJUnitPlatform()
}
```

- [ ] **Step 3: Criar o template de build Kotlin DSL**

`templates/build/kts/mcp-module.gradle.kts.template`:

```kotlin
// build.gradle.kts do modulo {base}-mcp.
// Biblioteca, nao aplicacao: sem main() e sem bootJar. As @McpTool daqui
// entram no contexto do {api-module}, que declara este modulo como
// dependencia -- processo e pod continuam um so.
plugins {
<!-- se kotlin -->
    kotlin("jvm")
    kotlin("plugin.spring")
<!-- fim se kotlin -->
<!-- se java -->
    `java-library`
<!-- fim se java -->
    id("io.spring.dependency-management")
    // apply false: so para o BOM_COORDINATES abaixo resolver na classpath do
    // script deste modulo. O modulo continua sem aplicar o plugin do Boot.
    id("org.springframework.boot") apply false
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

dependencyManagement {
    imports {
        mavenBom(org.springframework.boot.gradle.plugin.SpringBootPlugin.BOM_COORDINATES)
        mavenBom("org.springframework.ai:spring-ai-bom:{spring-ai-version}")
    }
}

dependencies {
    // So o dominio. Este modulo nunca depende do {api-module}: quem precisa
    // saber quem chamou le a Authentication, nao uma classe do -api.
    implementation(project(":{core-module}"))

    // O starter -webmvc serve /mcp no mesmo Tomcat do {api-module}. O starter
    // sem o sufixo e o de stdio, que exigiria processo proprio.
    implementation("org.springframework.ai:spring-ai-starter-mcp-server-webmvc")
    // SecurityContextHolder e Authentication vem daqui.
    implementation("org.springframework.boot:spring-boot-starter-security")
<!-- se kotlin -->
    implementation("org.jetbrains.kotlin:kotlin-reflect")
<!-- fim se kotlin -->
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

- [ ] **Step 4: Verificar**

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0` — o validador exige um `SKILL.md` por subpasta de `skills/`, e a pasta nova tem o seu.

Run: `grep -c "{base}-mcp" plugins/analizza-skills/skills/analizza-add-mcp-module/templates/build/groovy/mcp-module.gradle.template`
Expected: ao menos `1`.

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-add-mcp-module
git commit -m "Cria a analizza-add-mcp-module com o modulo de biblioteca

Passos 0-2: pre-requisitos, deteccao e criacao do {base}-mcp. O modulo nao
aplica o plugin do Boot (biblioteca, sem bootJar) e nunca depende do -api:
quem precisa saber quem chamou le a Authentication."
```

---

### Task 4: Templates de fonte — a ponte de autenticação, o erro e a tool de exemplo

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/CurrentMcpUser.kt.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/java/CurrentMcpUser.java.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/McpToolException.kt.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/java/McpToolException.java.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/Tools.kt.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/java/Tools.java.template`
- Modify: `plugins/analizza-skills/skills/analizza-add-mcp-module/SKILL.md` (acrescenta o Passo 3)

**Interfaces:**
- Consumes: `{base-package}`, `{mcp-src}`, `{language}` (Task 3).
- Produces: `CurrentMcpUser.identidade(): String` e `CurrentMcpUser.temPapel(vararg papeis: String): Boolean`; `McpToolException(mensagem)`; a classe `{Tools-class}` com uma `@McpTool` chamada `{tool-name}`. A Task 5 chama `{tool-name}` pelo cliente MCP.

- [ ] **Step 1: `CurrentMcpUser` em Kotlin**

`templates/source/kotlin/CurrentMcpUser.kt.template`:

```kotlin
package {base-package}.mcp

import org.springframework.security.authentication.AnonymousAuthenticationToken
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.stereotype.Component

private const val SEM_AUTENTICACAO = "nenhuma sessao autenticada nesta chamada"

/**
 * Le quem chamou a partir do que o SecurityFilterChain do projeto ja validou.
 *
 * Le a Authentication, nao o token: `getName()` devolve o `sub` num resource
 * server OAuth2 e o identificador do usuario num filtro de autenticacao
 * escrito a mao. Ler `principal as Jwt` amarraria a tool a um mecanismo so, e
 * devolveria null em qualquer projeto que use outro -- toda chamada morreria
 * como "nao autenticado".
 *
 * So funciona porque a tool roda na mesma thread servlet que autenticou a
 * requisicao, o que vale em spring.ai.mcp.server.type=SYNC. Em modo streaming
 * o ThreadLocal nao e garantido.
 */
@Component
class CurrentMcpUser {

    fun identidade(): String {
        val autenticacao = SecurityContextHolder.getContext().authentication
        if (autenticacao == null || !autenticacao.isAuthenticated || autenticacao is AnonymousAuthenticationToken) {
            throw McpToolException(SEM_AUTENTICACAO)
        }
        return autenticacao.name
    }

    /** Mesmo prefixo `ROLE_` que `hasAnyRole` usa no SecurityFilterChain. */
    fun temPapel(vararg papeis: String): Boolean {
        val autoridades = SecurityContextHolder.getContext().authentication?.authorities.orEmpty()
        return papeis.any { papel -> autoridades.any { it.authority == "ROLE_$papel" } }
    }
}
```

- [ ] **Step 2: `CurrentMcpUser` em Java**

`templates/source/java/CurrentMcpUser.java.template`:

```java
package {base-package}.mcp;

import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.Collection;
import java.util.List;

/**
 * Le quem chamou a partir do que o SecurityFilterChain do projeto ja validou.
 *
 * Le a Authentication, nao o token: getName() devolve o sub num resource
 * server OAuth2 e o identificador do usuario num filtro de autenticacao
 * escrito a mao. Ler o principal como Jwt amarraria a tool a um mecanismo so,
 * e devolveria null em qualquer projeto que use outro -- toda chamada morreria
 * como "nao autenticado".
 *
 * So funciona porque a tool roda na mesma thread servlet que autenticou a
 * requisicao, o que vale em spring.ai.mcp.server.type=SYNC. Em modo streaming
 * o ThreadLocal nao e garantido.
 */
@Component
public class CurrentMcpUser {

    private static final String SEM_AUTENTICACAO = "nenhuma sessao autenticada nesta chamada";

    public String identidade() {
        Authentication autenticacao = SecurityContextHolder.getContext().getAuthentication();
        if (autenticacao == null
                || !autenticacao.isAuthenticated()
                || autenticacao instanceof AnonymousAuthenticationToken) {
            throw new McpToolException(SEM_AUTENTICACAO);
        }
        return autenticacao.getName();
    }

    /** Mesmo prefixo ROLE_ que hasAnyRole usa no SecurityFilterChain. */
    public boolean temPapel(String... papeis) {
        Authentication autenticacao = SecurityContextHolder.getContext().getAuthentication();
        Collection<? extends GrantedAuthority> autoridades =
                autenticacao == null ? List.of() : autenticacao.getAuthorities();
        return Arrays.stream(papeis).anyMatch(papel ->
                autoridades.stream().anyMatch(a -> a.getAuthority().equals("ROLE_" + papel)));
    }
}
```

- [ ] **Step 3: `McpToolException` nas duas linguagens**

`templates/source/kotlin/McpToolException.kt.template`:

```kotlin
package {base-package}.mcp

/**
 * Erro que a tool devolve ao modelo. A mensagem e sempre texto curado: o Spring
 * AI repassa `message` (e a cadeia de `cause`) na resposta de erro da tool,
 * entao nunca passe aqui uma excecao de infraestrutura como `cause`.
 */
class McpToolException(mensagem: String) : RuntimeException(mensagem)
```

`templates/source/java/McpToolException.java.template`:

```java
package {base-package}.mcp;

/**
 * Erro que a tool devolve ao modelo. A mensagem e sempre texto curado: o Spring
 * AI repassa a message (e a cadeia de cause) na resposta de erro da tool,
 * entao nunca passe aqui uma excecao de infraestrutura como cause.
 */
public class McpToolException extends RuntimeException {

    public McpToolException(String mensagem) {
        super(mensagem);
    }
}
```

- [ ] **Step 4: A tool de exemplo em Kotlin**

`templates/source/kotlin/Tools.kt.template`:

```kotlin
package {base-package}.mcp

import org.slf4j.LoggerFactory
import org.springframework.ai.mcp.annotation.McpTool
import org.springframework.stereotype.Component
{handler-import}
{query-import}
{result-import}

private const val ERRO_INESPERADO = "Nao foi possivel concluir a consulta agora. Tente novamente em instantes."
{papel-constante}

/**
 * Tool de exemplo. As outras seguem esta forma.
 *
 * Antes de acrescentar uma tool, confira campo a campo o que o Result carrega:
 * o que sai daqui vai para um modelo de IA. Na implementacao de referencia um
 * campo `url` com link assinado de 3 anos so nao vazou porque uma pessoa
 * reparou -- ver a secao 3 do runbook.
 */
@Component
class {Tools-class}(
    private val handler: {handler-class},
    private val usuario: CurrentMcpUser,
) {

    private val log = LoggerFactory.getLogger(javaClass)

    @McpTool(name = "{tool-name}", description = "{tool-description}")
    fun {tool-method}(): {result-class} =
        protegido("{tool-name}") {
{papel-checagem}
            handler.handle({query-construcao})
        }

    private fun <T> protegido(nome: String, chamada: () -> T): T =
        try {
            chamada()
        } catch (erro: McpToolException) {
            throw erro
        } catch (erro: Exception) {
            // A excecao real fica no log do servidor; o modelo recebe so a
            // mensagem curada. Acrescente aqui um catch por excecao de dominio
            // que ja tenha mensagem propria, traduzindo-a como a rota HTTP faz.
            log.error("Falha inesperada na tool MCP {}", nome, erro)
            throw McpToolException(ERRO_INESPERADO)
        }
}
```

- [ ] **Step 5: A tool de exemplo em Java**

`templates/source/java/Tools.java.template`:

```java
package {base-package}.mcp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.stereotype.Component;

import java.util.function.Supplier;
{handler-import}
{query-import}
{result-import}

/**
 * Tool de exemplo. As outras seguem esta forma.
 *
 * Antes de acrescentar uma tool, confira campo a campo o que o Result carrega:
 * o que sai daqui vai para um modelo de IA. Na implementacao de referencia um
 * campo url com link assinado de 3 anos so nao vazou porque uma pessoa
 * reparou -- ver a secao 3 do runbook.
 */
@Component
public class {Tools-class} {

    private static final String ERRO_INESPERADO =
            "Nao foi possivel concluir a consulta agora. Tente novamente em instantes.";
{papel-constante}

    private static final Logger log = LoggerFactory.getLogger({Tools-class}.class);

    private final {handler-class} handler;
    private final CurrentMcpUser usuario;

    public {Tools-class}({handler-class} handler, CurrentMcpUser usuario) {
        this.handler = handler;
        this.usuario = usuario;
    }

    @McpTool(name = "{tool-name}", description = "{tool-description}")
    public {result-class} {tool-method}() {
        return protegido("{tool-name}", () -> {
{papel-checagem}
            return handler.handle({query-construcao});
        });
    }

    private <T> T protegido(String nome, Supplier<T> chamada) {
        try {
            return chamada.get();
        } catch (McpToolException erro) {
            throw erro;
        } catch (Exception erro) {
            // A excecao real fica no log do servidor; o modelo recebe so a
            // mensagem curada. Acrescente aqui um catch por excecao de dominio
            // que ja tenha mensagem propria, traduzindo-a como a rota HTTP faz.
            log.error("Falha inesperada na tool MCP {}", nome, erro);
            throw new McpToolException(ERRO_INESPERADO);
        }
    }
}
```

- [ ] **Step 6: Acrescentar o Passo 3 ao `SKILL.md`**

Inserir entre o Passo 2 e a seção `## Fora de escopo`:

```markdown
### Passo 3 — A ponte de autenticação, o erro e a tool

Grave em `{mcp-src}/`, a partir de `templates/source/{language}/`:

- `CurrentMcpUser` — [Kotlin](./templates/source/kotlin/CurrentMcpUser.kt.template),
  [Java](./templates/source/java/CurrentMcpUser.java.template). Sem substituição
  além de `{base-package}`.
- `McpToolException` — [Kotlin](./templates/source/kotlin/McpToolException.kt.template),
  [Java](./templates/source/java/McpToolException.java.template).
- A tool — [Kotlin](./templates/source/kotlin/Tools.kt.template),
  [Java](./templates/source/java/Tools.java.template), com:

| Placeholder | Como preencher |
|---|---|
| `{Tools-class}` | `<Agregado>Tools`, do caso de uso escolhido no Passo 1 |
| `{tool-name}` | `snake_case` do caso de uso (ex.: `list_documents`) |
| `{tool-method}` | `camelCase` do mesmo nome |
| `{tool-description}` | uma frase em português dizendo o que a tool devolve |
| `{handler-class}`, `{handler-import}` | o `QueryHandler` escolhido |
| `{query-class}`, `{query-import}`, `{query-construcao}` | a Query dele e como construí-la |
| `{result-class}`, `{result-import}` | o tipo que o handler devolve |

**Papéis.** Procure modelo de papel no projeto:

```bash
grep -rnE "hasRole|hasAnyRole|SimpleGrantedAuthority|ROLE_" --include='*.kt' --include='*.java' {api-module}/src/main | head
```

- **Achou:** pergunte quais papéis a tool exige. `{papel-constante}` vira
  `private const val PAPEL_INSUFICIENTE = "Seu papel nao tem acesso a esta consulta."`
  (Java: `private static final String PAPEL_INSUFICIENTE = ...;`) e
  `{papel-checagem}` vira
  `if (!usuario.temPapel("<PAPEL>")) throw McpToolException(PAPEL_INSUFICIENTE)`
  (Java: `if (!usuario.temPapel("<PAPEL>")) { throw new McpToolException(PAPEL_INSUFICIENTE); }`).
- **Não achou:** `{papel-constante}` e `{papel-checagem}` ficam **vazios**, e o
  relatório do Passo 6 diz, com todas as letras, que a tool não tem barreira de
  papel — só exige estar autenticado. Nunca gere a checagem num projeto de
  authorities vazias: ela negaria toda chamada.

Se `{papel-checagem}` ficou vazio, a tool não usa `usuario` — tire o parâmetro
`usuario` do construtor para o código não ficar com dependência morta.

### Passo 4 — Configuração e a guarda do `/mcp`

No `application.properties` do `{api-module}`:

```properties
# Servidor MCP servido no mesmo processo deste app.
# SYNC nao e preferencia: e o que garante a tool rodar na mesma thread servlet
# que autenticou a requisicao, deixando SecurityContextHolder legivel dentro
# do @McpTool (CurrentMcpUser depende disso).
spring.ai.mcp.server.protocol=STREAMABLE
spring.ai.mcp.server.type=SYNC
spring.ai.mcp.server.name={base}-mcp
spring.ai.mcp.server.streamable-http.mcp-endpoint=/mcp
```

Em `.yml`, a mesma árvore aninhada.

**Confirme que `/mcp` cai numa regra autenticada** antes de seguir:

```bash
grep -rn "anyRequest\|permitAll\|requestMatchers" --include='*.kt' --include='*.java' {api-module}/src/main | grep -i security
```

Se `anyRequest()` for `permitAll()`, ou se o projeto não tiver Spring Security,
**pare e avise**: o `/mcp` nasceria aberto a quem alcançar a porta, sem
autenticação nenhuma, e a `CurrentMcpUser` não teria o que ler. Só siga depois
que o usuário decidir como fechar.
```

- [ ] **Step 7: Verificar**

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `grep -c "principal as Jwt\|principal as? Jwt\|(Jwt)" plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/CurrentMcpUser.kt.template plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/java/CurrentMcpUser.java.template`
Expected: `0` nos dois — a ponte não pode ler o token (D4).

- [ ] **Step 8: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-add-mcp-module
git commit -m "Acrescenta a ponte de autenticacao, o erro e a tool de exemplo

CurrentMcpUser le Authentication.getName()/getAuthorities(), nunca o token:
e o que faz a skill funcionar tanto em resource server OAuth2 quanto em
filtro escrito a mao. Sem modelo de papel no projeto, a checagem nao e
gerada -- authorities vazias negariam toda chamada."
```

---

### Task 5: O teste que prova o transporte

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/McpEndpointIT.kt.template`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/java/McpEndpointIT.java.template`
- Modify: `plugins/analizza-skills/skills/analizza-add-mcp-module/SKILL.md` (acrescenta o Passo 5)

**Interfaces:**
- Consumes: `{tool-name}` (Task 4), `BaseIntegrationTest` do projeto alvo (gerado pela `analizza-integration-test`).
- Produces: o IT que a Task 6 cita no relatório e no runbook.

D8: o teste fala o protocolo por HTTP com um cliente MCP real. Um teste que chama a tool como método e popula o `SecurityContextHolder` à mão prova a lógica e **nada** sobre o transporte — foi só o cliente real que provou, na referência, que o contexto de segurança sobrevive ao dispatch do Spring AI.

- [ ] **Step 1: O IT em Kotlin**

`templates/source/kotlin/McpEndpointIT.kt.template`:

```kotlin
package {base-package}.mcp

import io.modelcontextprotocol.client.McpClient
import io.modelcontextprotocol.client.McpSyncClient
import io.modelcontextprotocol.client.transport.HttpClientStreamableHttpTransport
import io.modelcontextprotocol.spec.McpSchema
import {base-package}.support.BaseIntegrationTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Prova por HTTP de verdade, com cliente MCP real, que o SecurityContextHolder
 * sobrevive ao dispatch do Spring AI ate dentro do metodo @McpTool -- o que so
 * vale em spring.ai.mcp.server.type=SYNC. Chamar a tool como metodo e popular o
 * contexto a mao provaria a logica e nada sobre o transporte.
 */
class McpEndpointIT : BaseIntegrationTest() {

    private fun clienteMcp(token: String?): McpSyncClient {
        val transporte = HttpClientStreamableHttpTransport.builder("http://localhost:$port")
            .endpoint("/mcp")
            .apply {
                if (token != null) {
                    httpRequestCustomizer { builder, _, _, _, _ ->
                        builder.header("Authorization", "Bearer $token")
                    }
                }
            }
            .build()
        return McpClient.sync(transporte).build()
    }

    @Test
    fun `a tool responde por HTTP real para quem esta autenticado`() {
{semeadura}
        val cliente = clienteMcp({token-autenticado})
        try {
            cliente.initialize()

            val resultado = cliente.callTool(McpSchema.CallToolRequest("{tool-name}", emptyMap()))

            assertTrue(resultado.isError != true, "esperava sucesso, veio erro: ${resultado.content}")
{assercao-dado}
        } finally {
            cliente.closeGracefully()
        }
    }

    @Test
    fun `sem Authorization a requisicao e recusada antes de a tool rodar`() {
        val cliente = clienteMcp(null)
        try {
            val erro = kotlin.test.assertFails { cliente.initialize() }

            val cadeia = generateSequence<Throwable>(erro) { it.cause }.mapNotNull { it.message }
            assertTrue(
                cadeia.any { it.contains("401") || it.contains("Unauthorized") || it.contains("Authorization") },
                "esperava recusa de autenticacao, veio: ${erro.message}",
            )
        } finally {
            cliente.closeGracefully()
        }
    }
{teste-papel}
}
```

- [ ] **Step 2: O IT em Java**

`templates/source/java/McpEndpointIT.java.template`:

```java
package {base-package}.mcp;

import io.modelcontextprotocol.client.McpClient;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.client.transport.HttpClientStreamableHttpTransport;
import io.modelcontextprotocol.spec.McpSchema;
import {base-package}.support.BaseIntegrationTest;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Prova por HTTP de verdade, com cliente MCP real, que o SecurityContextHolder
 * sobrevive ao dispatch do Spring AI ate dentro do metodo @McpTool -- o que so
 * vale em spring.ai.mcp.server.type=SYNC. Chamar a tool como metodo e popular o
 * contexto a mao provaria a logica e nada sobre o transporte.
 */
class McpEndpointIT extends BaseIntegrationTest {

    private McpSyncClient clienteMcp(String token) {
        HttpClientStreamableHttpTransport.Builder construtor =
                HttpClientStreamableHttpTransport.builder("http://localhost:" + port).endpoint("/mcp");
        if (token != null) {
            construtor = construtor.httpRequestCustomizer(
                    (builder, metodo, uri, corpo, contexto) ->
                            builder.header("Authorization", "Bearer " + token));
        }
        return McpClient.sync(construtor.build()).build();
    }

    @Test
    void a_tool_responde_por_http_real_para_quem_esta_autenticado() {
{semeadura}
        McpSyncClient cliente = clienteMcp({token-autenticado});
        try {
            cliente.initialize();

            McpSchema.CallToolResult resultado =
                    cliente.callTool(new McpSchema.CallToolRequest("{tool-name}", Map.of()));

            assertNotEquals(Boolean.TRUE, resultado.isError(), "esperava sucesso, veio erro");
{assercao-dado}
        } finally {
            cliente.closeGracefully();
        }
    }

    @Test
    void sem_authorization_a_requisicao_e_recusada_antes_de_a_tool_rodar() {
        McpSyncClient cliente = clienteMcp(null);
        try {
            Exception erro = assertThrows(Exception.class, cliente::initialize);

            boolean recusou = false;
            for (Throwable t = erro; t != null; t = t.getCause()) {
                String m = t.getMessage();
                if (m != null && (m.contains("401") || m.contains("Unauthorized") || m.contains("Authorization"))) {
                    recusou = true;
                    break;
                }
            }
            assertTrue(recusou, "esperava recusa de autenticacao, veio: " + erro.getMessage());
        } finally {
            cliente.closeGracefully();
        }
    }
{teste-papel}
}
```

- [ ] **Step 3: Acrescentar o Passo 5 ao `SKILL.md`**

Inserir depois do Passo 4:

```markdown
### Passo 5 — O teste de integração

O IT mora onde os outros ITs do projeto moram — o módulo
`{base}-integration-tests` se a `analizza-integration-test` já rodou, senão o
`src/test` do `{api-module}`. Acrescente ao build **desse** módulo:

```groovy
testImplementation 'io.modelcontextprotocol.sdk:mcp-core:2.0.0'
testImplementation project(':{base}-mcp')
```

(kts: `testImplementation("io.modelcontextprotocol.sdk:mcp-core:2.0.0")` e
`testImplementation(project(":{base}-mcp"))`.)

Grave `McpEndpointIT` a partir de
[McpEndpointIT.kt.template](./templates/source/kotlin/McpEndpointIT.kt.template)
ou [McpEndpointIT.java.template](./templates/source/java/McpEndpointIT.java.template):

| Placeholder | Como preencher |
|---|---|
| `{token-autenticado}` | a expressão que o projeto já usa para emitir um token válido num IT (ex.: `tokenFor("alguem@exemplo.com")`). Sem helper assim, escreva um e diga no relatório. |
| `{semeadura}` | as linhas que gravam **uma** linha pelo repositório do agregado, para a tool ter o que devolver. Sem repositório acessível no IT, deixe vazio e **relate** que o teste prova protocolo e autenticação, mas não que a tool devolve dado. |
| `{assercao-dado}` | a asserção sobre o dado semeado (ex.: que o `structuredContent` contém o título gravado). Vazio se `{semeadura}` ficou vazio. |
| `{teste-papel}` | com papéis (Passo 3), um terceiro teste: token **sem** o papel exigido chama a tool e o resultado vem com `isError` verdadeiro. Sem papéis, vazio. |

O `{port}` vem do `BaseIntegrationTest` (`@LocalServerPort`).
```

- [ ] **Step 4: Verificar**

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `grep -n "closeGracefully" plugins/analizza-skills/skills/analizza-add-mcp-module/templates/source/kotlin/McpEndpointIT.kt.template`
Expected: dentro de um `finally` — cliente não pode vazar se a asserção falhar.

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-add-mcp-module
git commit -m "Acrescenta o IT com cliente MCP real

Fala o protocolo por HTTP contra /mcp de verdade. E o unico teste capaz de
provar que o SecurityContextHolder sobrevive ao dispatch do Spring AI ate
dentro do @McpTool -- chamar a tool como metodo prova a logica e nada
sobre o transporte."
```

---

### Task 6: Runbook, regras de projeto e o relatório

**Files:**
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/references/runbook-mcp.md`
- Create: `plugins/analizza-skills/skills/analizza-add-mcp-module/references/project-rules-mcp.md`
- Modify: `plugins/analizza-skills/skills/analizza-add-mcp-module/SKILL.md` (Passos 6 e 7)

**Interfaces:**
- Consumes: tudo das Tasks 3–5.
- Produces: o fim do `SKILL.md` — nenhuma tarefa depois depende dele.

- [ ] **Step 1: O runbook**

`references/runbook-mcp.md`:

```markdown
---
type: api
---

# Servidor MCP de {base}

As tools do `{base}-mcp` chamam os handlers de leitura direto, no mesmo
processo do `{api-module}`, e a identidade de quem chamou vem do
`Authorization` que chega em `/mcp`.

Pré-requisito: a aplicação rodando e um token válido.

## 1. O que precisa bater

Registre um servidor MCP HTTP apontando para `http://localhost:8080/mcp` com o
cabeçalho `Authorization: Bearer <token>`. Numa conversa nova, peça algo que
force a tool `{tool-name}`. Confira:

- a IA mostra que chamou `{tool-name}` antes de responder
- a resposta cita dado real do sistema, não algo inventado

## 2. O que tentar para ver se quebra

- **Token errado.** Troque o token por qualquer string. Esperado: recusa de
  autenticação antes de a tool rodar — nunca stack trace, nunca dado.
- **Sem o cabeçalho.** Remova o `Authorization`. Mesmo resultado.
- **Papel sem acesso** (se a tool exigir papel): token de alguém sem o papel.
  Esperado: a tool recusa com a mensagem de papel insuficiente, sem devolver
  dado nenhum.

## 3. O que não está na lista

**Confira campo a campo o que a tool devolveu.** É aqui que se decide o que um
modelo de IA pode ver, e nenhuma automação decide isso por você. Procure em
especial: URLs assinadas, tokens, caminhos internos, dados pessoais que a tela
equivalente não mostra, e qualquer campo que exista "porque o Result já
tinha". Na implementação de referência, um campo `url` com link assinado de 3
anos só não foi parar no modelo porque uma pessoa reparou nele nesta seção.

Estranhe também resposta da IA citando dado sem ter chamado tool nenhuma.

## 4. O que este checkpoint já pegou

(preencher depois de rodar, com data e achado real)
```

- [ ] **Step 2: As regras de projeto**

`references/project-rules-mcp.md`:

```markdown
### Servidor MCP

As tools MCP moram em `{base}-mcp`, módulo de biblioteca: sem `main()`, sem
`bootJar`, servido pelo mesmo Tomcat do `{api-module}` em `/mcp`. O módulo
**nunca** depende do `{api-module}` — quem precisar de algo que mora lá desce
esse algo para o `{core-module}`.

Quem chamou vem de `Authentication.getName()` e `getAuthorities()`, nunca do
objeto do token: é o que mantém a tool funcionando se o mecanismo de
autenticação mudar.

`spring.ai.mcp.server.type=SYNC` não é preferência. Em modo streaming o
`ThreadLocal` do `SecurityContextHolder` não é garantido, e a tool perderia a
identidade de quem chamou.

Toda tool nova precisa de um `<Nome>IT` — a regra ArchUnit
`EntrypointHasIntegrationTestIT` cobre `@McpTool` — e de uma passada pela seção
3 do runbook antes de ser liberada: o que a tool devolve vai para um modelo de
IA, e decidir isso é trabalho humano.

**Débito conhecido:** o MCP divide processo e pod com o `{api-module}`. Tráfego
de MCP mal-comportado degrada o app que pessoas usam. Fechar é módulo com
`main()`, Dockerfile, manifest e pipeline próprios.
```

- [ ] **Step 3: Acrescentar os Passos 6 e 7 ao `SKILL.md`**

Inserir depois do Passo 5:

```markdown
### Passo 6 — Runbook e regras de projeto

Grave `docs/checkpoints/mcp-server.md` a partir de
[runbook-mcp.md](./references/runbook-mcp.md), com os placeholders
substituídos. Se `docs/checkpoints/README.md` não existir, a
`analizza-integration-test` é quem o cria — diga ao usuário em vez de criar um
diferente aqui.

Acrescente ao arquivo de convenções do projeto — a mesma detecção da
`analizza-integration-test` (`openspec/PROJECT.md`, `specs/CONSTITUTION.md`,
`docs/superpowers/INSTRUCTIONS.md` ou `docs/INSTRUCTIONS.md`) — a seção de
[project-rules-mcp.md](./references/project-rules-mcp.md), se ela ainda não
existir (`grep -qE '^#{1,4} Servidor MCP$'`).

### Passo 7 — Verificar e relatar

Obrigatório. Redirecione a saída e leia o código de saída:

```bash
./gradlew build --console=plain > /tmp/mcp-build.log 2>&1; echo "EXIT=$?"
./gradlew integrationTest --tests '*McpEndpointIT*' --console=plain > /tmp/mcp-it.log 2>&1; echo "EXIT=$?"
```

Exija `EXIT=0` nos dois. Prove que a regra ArchUnit cobre a tool: renomeie
temporariamente `McpEndpointIT` para `McpEndpointTeste`, rode
`./gradlew integrationTest` e exija falha nomeando a classe da tool; desfaça e
rode de novo até verde.

Relate: linguagem, DSL, `{mcp-module}`, o caso de uso que virou tool, se há
barreira de papel (e **diga quando não há**), os `EXIT=`, o que o IT prova e o
que ele não prova (semeadura vazia, por exemplo), e que a seção 3 do runbook
ainda não foi conferida por ninguém.
```

- [ ] **Step 4: Verificar**

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `make check > /tmp/check.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `grep -c "^### Passo" plugins/analizza-skills/skills/analizza-add-mcp-module/SKILL.md`
Expected: `8` (Passos 0 a 7).

- [ ] **Step 5: Commit**

```bash
git add plugins/analizza-skills/skills/analizza-add-mcp-module
git commit -m "Fecha a skill com runbook, regras de projeto e verificacao

A secao 3 do runbook e onde se decide o que um modelo de IA pode ver --
a skill obriga a passada humana porque nao tem como decidir isso sozinha."
```

---

### Task 7: A regra ArchUnit passa a cobrir `@McpTool`, e o release

**Files:**
- Modify: `plugins/analizza-skills/skills/analizza-integration-test/templates/backend/source/kotlin/EntrypointHasIntegrationTestIT.kt.template:17-31,38,41,73-76`
- Modify: `plugins/analizza-skills/skills/analizza-integration-test/templates/backend/source/java/EntrypointHasIntegrationTestIT.java.template`
- Modify: `plugins/analizza-skills/skills/analizza-integration-test/references/testes-section.md`
- Modify: `plugins/analizza-skills/.claude-plugin/plugin.json`
- Modify: `plugins/analizza-skills/.codex-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: a skill completa (Tasks 3–6).
- Produces: nada — é a última tarefa.

D9: a regra guarda `org.springframework.ai.tool.annotation.Tool` (estilo
tool-calling, exposto por `ToolCallbackProvider`), mas o scanner de anotações do
servidor MCP — o caminho que esta skill gera — usa
`org.springframework.ai.mcp.annotation.McpTool`. Sem as duas, um projeto que
siga esta skill fica com guardrail que nunca dispara.

- [ ] **Step 1: Kotlin — acrescentar a constante e o predicado**

Em `EntrypointHasIntegrationTestIT.kt.template`, trocar no `companion object`:

```kotlin
        const val TOOL = "org.springframework.ai.tool.annotation.Tool"
```

por:

```kotlin
        const val TOOL = "org.springframework.ai.tool.annotation.Tool"
        const val MCP_TOOL = "org.springframework.ai.mcp.annotation.McpTool"
```

e no predicado:

```kotlin
                    it.isAnnotatedWith(Scheduled::class.java) || it.isAnnotatedWith(KAFKA_LISTENER) || it.isAnnotatedWith(TOOL)
```

por:

```kotlin
                    it.isAnnotatedWith(Scheduled::class.java) ||
                        it.isAnnotatedWith(KAFKA_LISTENER) ||
                        it.isAnnotatedWith(TOOL) ||
                        it.isAnnotatedWith(MCP_TOOL)
```

- [ ] **Step 2: Kotlin — atualizar a descrição e o KDoc**

Trocar a descrição do predicado:

```kotlin
        DescribedPredicate.describe("sao entrypoints (@RestController, @Scheduled, @KafkaListener ou @Tool)") { classe ->
```

por:

```kotlin
        DescribedPredicate.describe("sao entrypoints (@RestController, @Scheduled, @KafkaListener, @Tool ou @McpTool)") { classe ->
```

e no KDoc, trocar as duas menções:

```kotlin
 * Um unico trabalho: todo entrypoint -- @RestController, metodo @Scheduled,
 * metodo @KafkaListener ou metodo @Tool -- precisa de um <Nome>IT que estenda
```

por:

```kotlin
 * Um unico trabalho: todo entrypoint -- @RestController, metodo @Scheduled,
 * metodo @KafkaListener, @Tool ou @McpTool -- precisa de um <Nome>IT que estenda
```

e:

```kotlin
 * @KafkaListener e @Tool sao comparados pelo nome para a regra compilar sem
 * spring-kafka nem spring-ai. allowEmptyShould(true) porque um projeto novo
 * ainda nao tem entrypoint.
```

por:

```kotlin
 * @KafkaListener, @Tool e @McpTool sao comparados pelo nome para a regra
 * compilar sem spring-kafka nem spring-ai. As duas de tool sao anotacoes
 * diferentes: @Tool e tool-calling exposto por ToolCallbackProvider, @McpTool
 * e o scanner de anotacoes do servidor MCP. allowEmptyShould(true) porque um
 * projeto novo ainda nao tem entrypoint.
```

- [ ] **Step 3: Java — as mesmas mudanças**

Em `EntrypointHasIntegrationTestIT.java.template`, acrescentar depois da constante `TOOL`:

```java
    private static final String MCP_TOOL = "org.springframework.ai.mcp.annotation.McpTool";
```

trocar o predicado:

```java
                    || classe.getMethods().stream().anyMatch(m -> m.isAnnotatedWith(Scheduled.class)
                            || m.isAnnotatedWith(KAFKA_LISTENER)
                            || m.isAnnotatedWith(TOOL)));
```

por:

```java
                    || classe.getMethods().stream().anyMatch(m -> m.isAnnotatedWith(Scheduled.class)
                            || m.isAnnotatedWith(KAFKA_LISTENER)
                            || m.isAnnotatedWith(TOOL)
                            || m.isAnnotatedWith(MCP_TOOL)));
```

e a descrição:

```java
            "sao entrypoints (@RestController, @Scheduled, @KafkaListener ou @Tool)",
```

por:

```java
            "sao entrypoints (@RestController, @Scheduled, @KafkaListener, @Tool ou @McpTool)",
```

Atualize o Javadoc com as mesmas duas trocas de texto do Step 2.

- [ ] **Step 4: A seção *Testes* menciona as duas anotações**

Em `references/testes-section.md`, trocar:

```markdown
  método `@Scheduled`, `@KafkaListener` ou `@Tool` — precisa de um `<Nome>IT` que estenda
```

por:

```markdown
  método `@Scheduled`, `@KafkaListener`, `@Tool` ou `@McpTool` — precisa de um `<Nome>IT` que estenda
```

- [ ] **Step 5: Subir a versão nos dois manifestos e listar a skill**

`plugins/analizza-skills/.claude-plugin/plugin.json` e
`plugins/analizza-skills/.codex-plugin/plugin.json`: `"version": "0.3.3"` → `"version": "0.4.0"`
(feature nova, não correção).

Em `.claude-plugin/marketplace.json`, na `description` do plugin, acrescentar ao
fim, antes do fecho das aspas:

```
 A analizza-add-mcp-module acrescenta um servidor MCP como módulo de biblioteca a um projeto Spring Boot já existente, com a tool lendo quem chamou da Authentication e um teste de integração que fala o protocolo MCP de verdade.
```

- [ ] **Step 6: Verificar**

Run: `python3 tools/validate_plugin_manifests.py; echo "EXIT=$?"`
Expected: `EXIT=0` — as duas versões batem.

Run: `make validate > /tmp/validate.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `make check > /tmp/check.log 2>&1; echo "EXIT=$?"`
Expected: `EXIT=0`.

Run: `grep -c "McpTool" plugins/analizza-skills/skills/analizza-integration-test/templates/backend/source/kotlin/EntrypointHasIntegrationTestIT.kt.template plugins/analizza-skills/skills/analizza-integration-test/templates/backend/source/java/EntrypointHasIntegrationTestIT.java.template`
Expected: ao menos `3` em cada (constante, predicado, documentação).

- [ ] **Step 7: Commit**

```bash
git add plugins/analizza-skills .claude-plugin/marketplace.json
git commit -m "A regra ArchUnit passa a cobrir @McpTool, e sobe para 0.4.0

A regra guardava so @Tool (tool-calling via ToolCallbackProvider). O
scanner de anotacoes do servidor MCP usa @McpTool, outra anotacao -- entao
um projeto que seguisse a add-mcp-module ficaria com guardrail que nunca
dispara para as tools dele."
```

---

## Self-Review

**1. Cobertura do spec (entregas 1 e 3):** D1 (módulo de biblioteca) — Task 3, templates de build. D2 (nunca depende do `-api`, pacote sob o base) — Task 3, Passo 2 do `SKILL.md`, e reforçado em `project-rules-mcp.md` (Task 6). D3 (infra + uma tool) — Task 4. D4 (ponte pela `Authentication`) — Task 4, com verificação por `grep` no Step 7. D5 (detecta e pergunta papéis; sem papéis, relata) — Task 4, Passo 3. D6 (exposição de dado é humana) — Task 6, seção 3 do runbook. D7 (parar se `/mcp` não for autenticado) — Task 4, Passo 4. D8 (cliente MCP real) — Task 5. D9 (`@McpTool` na regra) — Task 7. D10 (convenção) — Task 2. **Fora deste plano por escopo declarado:** D11 e D12, que são a Entrega 2, no `analizza-auction`.

**2. Placeholder scan:** nenhum "TBD"/"a definir". Os `{...}` nos templates são placeholders **do produto** — a tabela do Passo 3 e a do Passo 5 dizem, um por um, como preenchê-los. A Task 1 existe porque a verificação das outras depende dela: sem ela, todo `make validate` deste plano falharia por um defeito que já está na `main`.

**3. Consistência de tipos:** `CurrentMcpUser` tem exatamente dois métodos — `identidade()` e `temPapel(vararg)` — e são esses dois que o template da tool (Task 4) e o texto do Passo 3 citam; nenhum outro nome aparece. `McpToolException` recebe só a mensagem, nas duas linguagens, e é o tipo que a tool lança e o `protegido` repassa. `{tool-name}` é definido na Task 4 e consumido na Task 5 (`CallToolRequest`) e na Task 6 (runbook). `{mcp-module}`/`{base}-mcp` aparecem com o mesmo valor no build, no `settings`, no IT e nas regras de projeto.
