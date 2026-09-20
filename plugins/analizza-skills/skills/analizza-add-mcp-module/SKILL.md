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
grep -rhoE "org\.springframework\.boot[\"')]* version [\"'][0-9]+" --include='build.gradle*' . | sort -u
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

## Fora de escopo

Módulo com `main()` e pod próprios. Token de vida longa/revogável (PAT). Gerar
uma tool por handler do domínio. Promover projeto de módulo único a
multi-módulo.
