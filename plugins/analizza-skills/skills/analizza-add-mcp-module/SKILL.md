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
| `{it-module}` | módulo onde os ITs do projeto moram (o `{base}-integration-tests` da `analizza-integration-test`) |
| `{mcp-module}` | `{base}-mcp` |
| `{mcp-src}` | `{mcp-module}/src/main/{src-dir}/{base-package com / no lugar de .}/mcp` |
| `{group}`, `{java-version}` | lidos do build do `{api-module}` |
| `{base-integration-test-fqn}` | nome completo da `BaseIntegrationTest` do projeto, localizado no Passo 5 — pode ou não ter subpacote |
| `{spring-ai-version}` | `2.0.1` salvo se o projeto já fixar outra |

## Procedimento

### Passo 0 — Pré-requisitos

Só roda em projeto Gradle multi-módulo com Spring Boot 4.x. Confira:

```bash
find . -maxdepth 1 -name 'settings.gradle*'
grep -rlE '@SpringBootApplication' --include='*.kt' --include='*.java' . | grep '/src/main/'
# Groovy e Kotlin DSL, com espaço repetido: id 'org.springframework.boot' version '4.0.0'
grep -rhoE "org\.springframework\.boot[\"')]*[[:space:]]+version[[:space:]]+[\"'][0-9]+" --include='build.gradle*' . | sort -u
# Version catalog: alias(libs.plugins.springBoot) ou version libs.versions.boot.get()
find . -name 'libs.versions.toml' -not -path '*/build/*' -exec grep -nE "spring-?boot|springBoot|^[[:space:]]*boot[[:space:]]*=" {} +
```

Decida assim, e só assim:

- **Sem `settings.gradle*`** — pare e diga: a skill só roda em projeto Gradle
  multi-módulo.
- **Boot 3.x detectado** — pare e diga: o starter
  `spring-ai-starter-mcp-server-webmvc` desta skill exige Boot 4.x. Não tente
  adaptar.
- **Boot 4.x detectado** — siga.
- **Nada detectado** (nem o grep dos `build.gradle*` nem o do catálogo
  devolveram versão) — **não siga**.
  Pergunte ao usuário qual versão do Spring Boot o projeto usa e espere a
  resposta. Só continue se ele confirmar 4.x; com 3.x, ou sem resposta, pare
  pelo mesmo motivo do caso acima. Esta é a única porta entre um projeto Boot
  3.x e um starter que só existe no 4 — não a atravesse no escuro.

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
4. No **mesmo** `{api-module}/build.gradle{dsl-ext}`, importe também o
   `spring-ai-bom` — ver o bloco logo abaixo, que explica por quê.
5. O módulo aplica plugins sem versão. Confirme que a raiz os declara com
   versão e `apply false`; se não declarar, leve as versões para a raiz.
6. Se o build da raiz usar `jacoco-report-aggregation`
   (`grep -n "jacoco-report-aggregation\|jacocoAggregation" build.gradle*`),
   acrescente o módulo novo ao bloco de agregação:
   `jacocoAggregation project(':{base}-mcp')` (groovy) ou
   `jacocoAggregation(project(":{base}-mcp"))` (kts). Sem isso as classes das
   tools ficam fora do relatório agregado mesmo sendo exercitadas pelo IT do
   Passo 5 — a cobertura não cai, ela some da conta, que é pior.

**O BOM do Spring AI se importa em todo módulo que _resolve_ a dependência,
não só no que a declara.** O `io.spring.dependency-management` gerencia versão
por projeto que resolve a configuração. O `{mcp-module}` declara
`spring-ai-starter-mcp-server-webmvc` sem versão; quem recebe esse starter
transitivamente — o `{api-module}` aqui, o `{it-module}` no Passo 5 — monta o
próprio `runtimeClasspath`/`testRuntimeClasspath` e, sem o mesmo import de BOM,
resolve com versão **vazia**. O sintoma é `./gradlew build` morrer em
`:{api-module}:bootJar` com
`Could not find org.springframework.ai:spring-ai-starter-mcp-server-webmvc:.`
— o ponto final é a versão que faltou. Repita o import nos dois módulos:

```groovy
dependencyManagement {
    imports {
        mavenBom 'org.springframework.ai:spring-ai-bom:{spring-ai-version}'
    }
}
```

(kts: `mavenBom("org.springframework.ai:spring-ai-bom:{spring-ai-version}")`
dentro do mesmo `dependencyManagement { imports { ... } }`.)

Se o módulo que consome **não** aplicar `io.spring.dependency-management`, o
equivalente é declarar a plataforma na própria configuração:
`implementation platform('org.springframework.ai:spring-ai-bom:{spring-ai-version}')`
(no `{it-module}`, `testImplementation platform(...)`).

**Isso não é duplicação para limpar depois.** Apagar o import de qualquer um
desses módulos devolve o build ao erro de versão vazia. Deixe junto o
comentário dizendo isso, para quem passar depois não "arrumar".

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
| `{Tools-class}` | `<Agregado>Tools`, do caso de uso escolhido no Passo 1. O mesmo valor volta no Passo 5, no nome do IT |
| `{tool-name}` | `snake_case` do caso de uso (ex.: `list_documents`) |
| `{tool-method}` | `camelCase` do mesmo nome |
| `{tool-description}` | uma frase em português dizendo o que a tool devolve |
| `{handler-class}`, `{handler-import}` | o `QueryHandler` escolhido |
| `{query-import}`, `{query-construcao}` | a Query dele e como construí-la |
| `{result-class}`, `{result-import}` | o tipo que o handler devolve |

A tool lê a identidade de quem chamou como **primeira** linha do bloco
protegido (`val quemChamou = usuario.identidade()`), e o template já registra
essa identidade em `log.debug`. Se a Query do projeto receber quem chamou — um
`solicitante`, um `usuarioId`, um filtro por dono —, `{query-construcao}`
passa `quemChamou` para ela (`{Query}(quemChamou)`) em vez de deixar a
identidade só no log. Se a Query não receber ninguém, o `log.debug` já é uso
suficiente: não invente parâmetro que o domínio não tem.

**O tipo de `quemChamou` é `String`, e a Query pode querer outro.**
`identidade()` devolve `Authentication#getName()`, que cai no
`principal.toString()` quando o filtro do projeto autentica com um principal
que não é texto — um `UUID`, por exemplo. Se a Query exigir esse `UUID` (ou um
`Long`, ou um value object), `{Query}(quemChamou)` **não compila**. Antes de
preencher `{query-construcao}`, abra a Query, veja o tipo do parâmetro e
converta na construção: `{Query}(UUID.fromString(quemChamou))`,
`{Query}(UsuarioId(quemChamou))`, o que o domínio pedir — acrescentando o
import que a conversão exigir. Diga a conversão no relatório do Passo 7: quem
ler depois precisa saber que a identidade atravessa a ponte como texto e é
reconstruída aqui.

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
  relatório do Passo 7 diz, com todas as letras, que a tool não tem barreira de
  papel — só exige estar autenticado. Nunca gere a checagem num projeto de
  authorities vazias: ela negaria toda chamada.

**Nos dois casos o `usuario` fica no construtor.** Sem papéis a tool continua
chamando `usuario.identidade()`, que exige sessão autenticada e é o que o
`{Tools-class}IT` do Passo 5 prova sobreviver ao dispatch do Spring AI. Tirar o parâmetro
num projeto sem modelo de papel deixaria a `CurrentMcpUser` sem chamador
nenhum, e o IT provaria protocolo e mais nada.

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

**O módulo de teste pode ter um `application.properties` que sombreia esse por
completo.** Confira antes de seguir:

```bash
find {it-module}/src/test/resources \( -name 'application*.properties' -o -name 'application*.yml' \)
```

Se o `{it-module}` (o módulo onde o IT do Passo 5 vai rodar) tiver o próprio
`application.properties`/`.yml`, **espelhe as mesmas propriedades lá também**.
O Spring Boot não mescla dois recursos de mesmo nome no classpath: o do módulo
de teste vence, e o do `{api-module}` some inteiro da rodada de teste — não só
as linhas conflitantes.

O sintoma dessa falta **não parece configuração faltando**: o servidor MCP sobe
sem `STREAMABLE`/`SYNC`, a chamada da tool estoura por dentro, o erro vira um
forward para `/error` que a cadeia de segurança recusa, e o IT falha com
**401 sobre um token genuinamente válido**. Erro de autenticação é o disfarce
padrão dessa lacuna. Se o IT do Passo 5 recusar um token que você sabe que é
bom, volte aqui antes de mexer em qualquer coisa de segurança.

**Confirme que `/mcp` cai numa regra autenticada** antes de seguir:

```bash
grep -rn "anyRequest\|permitAll\|requestMatchers" --include='*.kt' --include='*.java' {api-module}/src/main | grep -i security
```

Se `anyRequest()` for `permitAll()`, ou se o projeto não tiver Spring Security,
**pare e avise**: o `/mcp` nasceria aberto a quem alcançar a porta, sem
autenticação nenhuma, e a `CurrentMcpUser` não teria o que ler. Só siga depois
que o usuário decidir como fechar.

### Passo 5 — O teste de integração

O IT mora onde os outros ITs do projeto moram: o `{it-module}` que a
`analizza-integration-test` criou. Ache a base que ele herda:

```bash
grep -rl "abstract class BaseIntegrationTest\|class BaseIntegrationTest" --include='*.kt' --include='*.java' . | grep -v '/build/'
# e o pacote dela, que e o que o template importa:
grep -rh "^package " $(grep -rl "class BaseIntegrationTest" --include='*.kt' --include='*.java' . | grep -v '/build/')
```

O nome completo que sair daí é o `{base-integration-test-fqn}` do template.
**Não presuma um subpacote `.support`**: há projeto que guarda a base direto em
`{base-package}`, e um import inventado só falha na compilação do IT, já no
Passo 7.

**Sem `BaseIntegrationTest` no projeto, pare aqui**: rode a
`analizza-integration-test` primeiro e volte depois. O template herda dessa
base, o Passo 7 roda a task `integrationTest`, e as duas só existem quando
aquela skill rodou. Escrever o IT em `src/test` do `{api-module}` sem ela
produziria um arquivo que não compila e um comando que não existe.

Acrescente ao build do `{it-module}`:

```groovy
dependencyManagement {
    imports {
        // O mesmo BOM do Passo 2: este modulo tambem RESOLVE o starter do
        // Spring AI que vem transitivamente do {base}-mcp. Sem esta linha,
        // testRuntimeClasspath tenta resolver com versao vazia.
        mavenBom 'org.springframework.ai:spring-ai-bom:{spring-ai-version}'
    }
}

dependencies {
    testImplementation 'io.modelcontextprotocol.sdk:mcp-core:2.0.0'
    testImplementation project(':{base}-mcp')
}
```

(kts: `mavenBom("org.springframework.ai:spring-ai-bom:{spring-ai-version}")`,
`testImplementation("io.modelcontextprotocol.sdk:mcp-core:2.0.0")` e
`testImplementation(project(":{base}-mcp"))`. Se o `{it-module}` não aplicar
`io.spring.dependency-management`, use
`testImplementation platform('org.springframework.ai:spring-ai-bom:{spring-ai-version}')`
no lugar do bloco `dependencyManagement`.)

O `2.0.0` acompanha a `{spring-ai-version}` padrão. Se o projeto fixar outra
Spring AI, confira a versão do SDK que ela traz e alinhe o pin:

```bash
./gradlew :{it-module}:dependencies --configuration testRuntimeClasspath | grep mcp
```

Grave o IT **como `{Tools-class}IT`** — o mesmo `{Tools-class}` do Passo 3 —
a partir de
[McpEndpointIT.kt.template](./templates/source/kotlin/McpEndpointIT.kt.template)
ou [McpEndpointIT.java.template](./templates/source/java/McpEndpointIT.java.template).
O nome do template é histórico; o nome do arquivo gerado é
`{Tools-class}IT.{kt|java}`, porque é isso que a regra ArchUnit exige de um
entrypoint chamado `{Tools-class}`. Substitua também:

| Placeholder | Como preencher |
|---|---|
| `{Tools-class}` | o mesmo do Passo 3 — vira o nome da classe de teste, `{Tools-class}IT` |
| `{base-integration-test-fqn}` | o nome completo da `BaseIntegrationTest` que o grep acima achou (ex.: `{base-package}.support.BaseIntegrationTest` **ou** `{base-package}.BaseIntegrationTest`). O template não assume subpacote nenhum |
| `{token-autenticado}` | a expressão que o projeto já usa para emitir um token válido num IT (ex.: `tokenFor("alguem@exemplo.com")`). Sem helper assim, escreva um e diga no relatório. |
| `{semeadura}` | as linhas que gravam **uma** linha pelo repositório do agregado, para a tool ter o que devolver. Sem repositório acessível no IT, deixe vazio e **relate** que o teste prova protocolo e autenticação, mas não que a tool devolve dado. |
| `{assercao-dado}` | a asserção sobre o dado semeado (ex.: que o `structuredContent` contém o título gravado). Vazio se `{semeadura}` ficou vazio. Se a asserção pedir um helper que o template não importa (`assertEquals`, por exemplo), acrescente o import. |
| `{teste-papel}` | com papéis (Passo 3), um terceiro teste: token **sem** o papel exigido chama a tool e o resultado vem com `isError` verdadeiro. Sem papéis, vazio. |

A porta vem de um `@LocalServerPort` **do próprio IT** (`portaMcp`), já no
template: o campo `port` da `BaseIntegrationTest` é `private` e subclasse
nenhuma o enxerga. Não troque por herança.

**A regra ArchUnit do projeto precisa conhecer `@McpTool`.** A cópia que o
projeto tem foi gerada por uma versão anterior da `analizza-integration-test`
e pode guardar só `@Tool`.

Ache o arquivo **antes** de procurar `McpTool` dentro dele: o nome varia entre
releases da sibling (`EntrypointHasIntegrationTestIT.java`,
`EntrypointHasIntegrationTestRuleIT.java`, `...RuleIT.kt`), e justamente os
projetos gerados pelas releases antigas — os que mais precisam deste passo —
são os de nome diferente. Um glob fechado num nome só acha nada e faz parecer
que a regra não existe:

```bash
# 1. o arquivo, por prefixo, sem fechar no sufixo
grep -rl "EntrypointHasIntegrationTest" --include='*.kt' --include='*.java' . | grep -v '/build/'
# 2. so entao, McpTool dentro do que o passo 1 devolveu
grep -rn "McpTool" $(grep -rl "EntrypointHasIntegrationTest" --include='*.kt' --include='*.java' . | grep -v '/build/')
```

- **Achou o arquivo e ele já cita `McpTool`** — nada a fazer.
- **Achou o arquivo e ele não cita `McpTool`** — acrescente a constante e a
  cláusula do predicado do mesmo jeito que o template da sibling faz hoje: uma
  constante `MCP_TOOL = "org.springframework.ai.mcp.annotation.McpTool"` e um
  `it.isAnnotatedWith(MCP_TOOL)` (Java: `m.isAnnotatedWith(MCP_TOOL)`) ao lado
  do `TOOL`, atualizando também a descrição do predicado. **Comparada pelo
  nome, nunca importada**: a regra tem de compilar sem `spring-ai` no
  classpath do `{it-module}`. Como alternativa, diga ao usuário para rodar a
  `analizza-integration-test` de novo, que regrava o arquivo.
- **Não achou arquivo nenhum** — aí sim a regra não existe neste projeto:
  diga ao usuário e siga; o Passo 7 relata que a cobertura da tool ficou sem
  guarda de arquitetura.

**Mexer na descrição do predicado tem preço.** Se o projeto congela violações
com `FreezingArchRule`, o texto da descrição faz parte da identidade da regra,
e editá-lo cria uma regra nova aos olhos do freeze — cujo primeiro resultado
verde não prova nada. O Passo 7 trata disso antes da prova; não pule aquele
passo achando que é zelo.

O relatório do Passo 7 diz qual dos quatro aconteceu: já cobria, foi remendada
aqui, não existe no projeto, ou ficou para o usuário rodar a sibling.

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
./gradlew integrationTest --tests '*{Tools-class}IT*' --console=plain > /tmp/mcp-it.log 2>&1; echo "EXIT=$?"
```

Exija `EXIT=0` nos dois. Depois prove que a regra ArchUnit cobre a tool — em
duas partes, nesta ordem, porque a segunda mente sem a primeira.

**Parte 1, o baseline limpo.** Só se aplica quando o projeto congela violações:

```bash
grep -rn "FreezingArchRule" --include='*.kt' --include='*.java' . | grep -v '/build/'
```

Se achou, faça a Parte 1 inteira — sempre, e em especial quando o Passo 5
editou a descrição do predicado. O `archunit_store` chaveia o arquivo de violações
pelo **texto completo da regra, descrição do predicado inclusa**. Ao acrescentar
`@McpTool` àquela descrição, você criou uma regra que o freeze nunca viu — e no
primeiro encontro com uma regra nova o ArchUnit **congela como baseline aceito
todas as violações existentes naquele instante, sem falhar**. É o comportamento
documentado para adotar a regra em código legado, e aqui ele engole a prova.

```bash
# com o codigo como esta, sem nenhuma violacao de proposito
./gradlew integrationTest --tests '*EntrypointHasIntegrationTest*' --console=plain \
  > /tmp/mcp-arch-baseline.log 2>&1; echo "EXIT=$?"
# o arquivo de violacoes da identidade nova tem de ter 0 linhas
wc -l {it-module}/archunit_store/*
```

Exija `EXIT=0` **e** arquivo vazio para a regra em questão (o
`archunit_store/stored.rules` mapeia o texto da regra para o nome do arquivo).
Se vier com linhas, são violações congeladas: apague esse arquivo e rode de
novo — com o código limpo, o congelamento novo nasce vazio.

**Parte 2, a prova.** Crie em `{mcp-src}/` uma classe descartável com `@McpTool`
e sem IT correspondente — `ArchUnitProofDecoyTools`, um método, sem lógica e
**sem `@Component`**: a regra olha a anotação do método, não o bean, e assim a
decoy não entra no contexto de ninguém. Rode a mesma task e exija que ela
**falhe** citando
`ArchUnitProofDecoyTools` e o teste que falta,
`'ArchUnitProofDecoyToolsIT'`. É o formato do nome exigido que está sendo
provado, o mesmo que o `{Tools-class}IT` cumpre. Apague a classe descartável e
rode de novo até voltar o verde.

**Verde onde você esperava vermelho não é boa notícia — é o falso-verde acima.**
Quer dizer que a violação da decoy virou baseline: volte à Parte 1, zere o
arquivo de violações e refaça. Não relaxe a regra e não mexa no
`{Tools-class}IT` de verdade para o build passar: a prova se faz com a classe
descartável, nunca renomeando nem removendo um teste que existe para valer.

Relate: linguagem, DSL, `{mcp-module}`, o caso de uso que virou tool, se há
barreira de papel (e **diga quando não há**), a conversão de tipo na construção
da Query se houve alguma (Passo 3), em quais módulos o `spring-ai-bom` teve de
ser importado (Passo 2) e se as propriedades do Passo 4 tiveram de ser
espelhadas no `{it-module}`, o que aconteceu com a regra ArchUnit do projeto
(já cobria `@McpTool`, foi remendada no Passo 5, não existe, ou ficou para o
usuário rodar a `analizza-integration-test`) e como o baseline do freeze foi
tratado, os `EXIT=`, o que o IT prova e o que ele não prova (semeadura vazia,
por exemplo), e que a seção 3 do runbook ainda não foi conferida por ninguém.

## Fora de escopo

Módulo com `main()` e pod próprios. Token de vida longa/revogável (PAT). Gerar
uma tool por handler do domínio. Promover projeto de módulo único a
multi-módulo.
