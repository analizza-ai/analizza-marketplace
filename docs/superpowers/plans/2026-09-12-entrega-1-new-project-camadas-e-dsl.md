# Entrega 1 — `analizza-new-project`: camadas completas e DSL por linguagem — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `analizza-new-project` passa a gerar Gradle Kotlin DSL para `language=kotlin` e Groovy para `language=java`, e o template de convenções passa a carregar os sete itens de camada que faltavam.

**Architecture:** Só Markdown e templates de skill mudam — nenhum código de produção. Os três templates Gradle com marcadores `<!-- se kotlin/java -->` viram pares de arquivos (Groovy só Java, `.kts` só Kotlin). O `SKILL.md` e três referências passam a escolher o arquivo pela linguagem. O `architecture-conventions.md.template` ganha texto; o Passo 8 ganha três diretórios. A prova é executar a skill em diretório descartável nas duas linguagens.

**Tech Stack:** Markdown, Gradle (Groovy e Kotlin DSL), Spring Initializr API, Spring Boot 4.x, Kotlin 2.3, Java 25.

**Spec:** `docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md` (seção *Entrega 1*, decisões D1 e D7).

## Global Constraints

- Todo o trabalho acontece no worktree `/Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test`, branch `docs/spec-integration-test-e-camadas`. Nunca no checkout `analizza-marketplace` nem no `documents-eaf-system`.
- Raiz da skill (abreviada `$SKILL` nos comandos): `plugins/analizza-skills/skills/analizza-new-project`.
- D1: `language=kotlin` → Gradle Kotlin DSL (`.kts`); `language=java` → Gradle Groovy DSL. Nunca DSL misturada no mesmo build.
- Os marcadores `<!-- se kotlin -->` / `<!-- se java -->` saem **só** dos três templates Gradle; no `architecture-conventions.md.template` eles ficam.
- O conteúdo dos builds `.kts` é tradução do Groovy atual: nenhuma dependência nova nem removida.
- Nada de exemplo específico do `documents-eaf-system` (`AccessCode`, `DocuSign`, `com.eaf.documents`) nos textos: genérico, com placeholders `{project-name}`, `{package}`, `{language}`.
- A seção *Testes* do template de convenções **não** passa a apontar para a `analizza-integration-test` nesta entrega (isso é Entrega 3, D7); aqui só ganha os itens 3 e 7.
- Sem bump de versão do plugin nesta entrega (o `0.3.0` é da Entrega 4).
- Comentários dentro de templates Gradle seguem o estilo existente: português sem acento.
- Mensagens de commit em português, imperativo na 3ª pessoa como o histórico (`Leva para a skill…`, `Corrige…`), terminando com `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

---

## File Structure

| Arquivo | Responsabilidade | Tarefa |
|---|---|---|
| `$SKILL/templates/root-build.gradle.template` | build raiz Groovy, só Java | 1 |
| `$SKILL/templates/root-build.gradle.kts.template` (novo) | build raiz Kotlin DSL, só Kotlin | 1 |
| `$SKILL/templates/core-build.gradle.template` | build do `-core` Groovy, só Java | 1 |
| `$SKILL/templates/core-build.gradle.kts.template` (novo) | build do `-core` Kotlin DSL | 1 |
| `$SKILL/templates/buildingBlocks/build.gradle.template` | build do `buildingBlocks` Groovy, só Java | 1 |
| `$SKILL/templates/buildingBlocks/build.gradle.kts.template` (novo) | build do `buildingBlocks` Kotlin DSL | 1 |
| `$SKILL/SKILL.md` | Passos 4, 5 e 8 | 2, 4 |
| `$SKILL/references/initializr-api.md` | `type` segue a linguagem | 2 |
| `$SKILL/references/gradle-multi-module.md` | nomes e sintaxe nas duas DSLs | 2 |
| `$SKILL/references/pitfalls.md` | nome do template do core | 2 |
| `$SKILL/templates/architecture-conventions.md.template` | itens de camada 1–7 | 3, 4 |
| `docs/superpowers/specs/2026-09-12-…-design.md` | mover o ajuste de *Fora de escopo* para a Entrega 3 | 4 |

---

### Task 1: Templates Gradle por DSL

**Files:**
- Modify: `$SKILL/templates/root-build.gradle.template`
- Create: `$SKILL/templates/root-build.gradle.kts.template`
- Modify: `$SKILL/templates/core-build.gradle.template`
- Create: `$SKILL/templates/core-build.gradle.kts.template`
- Modify: `$SKILL/templates/buildingBlocks/build.gradle.template`
- Create: `$SKILL/templates/buildingBlocks/build.gradle.kts.template`

**Interfaces:**
- Consumes: nada.
- Produces: seis arquivos com os placeholders `{group}`, `{java-version}`, `{boot-version}`, `{kotlin-version}` (só no `.kts` raiz), `{dependency-management-version}`, `{project-name}` (só em comentário). A Tarefa 2 os referencia por esses caminhos exatos.

- [ ] **Step 1: Escrever a checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
SKILL=plugins/analizza-skills/skills/analizza-new-project
check_dsl_templates() {
  local ok=0
  for f in templates/root-build.gradle templates/core-build.gradle templates/buildingBlocks/build.gradle; do
    [ -f "$SKILL/$f.template" ]     || { echo "FALTA $f.template"; ok=1; }
    [ -f "$SKILL/$f.kts.template" ] || { echo "FALTA $f.kts.template"; ok=1; }
    grep -q '<!-- se' "$SKILL/$f.template" 2>/dev/null && { echo "MARCADOR em $f.template"; ok=1; }
    grep -q '<!-- se' "$SKILL/$f.kts.template" 2>/dev/null && { echo "MARCADOR em $f.kts.template"; ok=1; }
    grep -q 'kotlin' "$SKILL/$f.template" 2>/dev/null && { echo "KOTLIN no Groovy $f.template"; ok=1; }
  done
  return $ok
}
check_dsl_templates; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar**

Expected: linhas `FALTA …kts.template` para os três, `MARCADOR em …` para os três Groovy, e `EXIT=1`.

- [ ] **Step 3: Reescrever `root-build.gradle.template` (só Java)**

Conteúdo completo do arquivo:

```gradle
// Versoes dos plugins declaradas uma vez so, na raiz -- os subprojetos
// ({project-name}-core, {project-name}-api) aplicam sem versao. Um
// subprojeto so pode aplicar um plugin sem versao se ele ja estiver no
// classpath do buildscript herdado da raiz.
plugins {
    id 'org.springframework.boot' version '{boot-version}' apply false
    id 'io.spring.dependency-management' version '{dependency-management-version}' apply false
}
```

- [ ] **Step 4: Criar `root-build.gradle.kts.template` (só Kotlin)**

```kotlin
// Versoes dos plugins declaradas uma vez so, na raiz.
// Os subprojetos (buildingBlocks, {project-name}-core, {project-name}-api)
// aplicam sem versao -- o Kotlin Gradle Plugin nao suporta ser carregado com
// versao explicita em mais de um subprojeto, e um subprojeto so pode aplicar
// um plugin sem versao se ele ja estiver no classpath do buildscript herdado
// da raiz.
plugins {
    kotlin("jvm") version "{kotlin-version}" apply false
    kotlin("plugin.spring") version "{kotlin-version}" apply false
    kotlin("plugin.jpa") version "{kotlin-version}" apply false
    id("org.springframework.boot") version "{boot-version}" apply false
    id("io.spring.dependency-management") version "{dependency-management-version}" apply false
}
```

- [ ] **Step 5: Reescrever `core-build.gradle.template` (só Java)**

Conteúdo = o bloco `<!-- se java -->` atual (linhas 76–123), sem os marcadores:

```gradle
plugins {
    id 'java-library'
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

// O -core nao aplica o plugin org.springframework.boot: nao gera bootJar,
// continua biblioteca. Mas precisa do BOM para resolver as versoes dos
// starters sem escreve-las a mao. Sem versao aqui: io.spring.dependency-management
// reaproveita a versao ja resolvida no {project-name}-api (gerado pelo
// Initializr), que faz parte do mesmo build.
dependencyManagement {
    imports {
        mavenBom "org.springframework.boot:spring-boot-dependencies:{boot-version}"
    }
}

dependencies {
    api project(':buildingBlocks')

    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    // spring-boot-starter-flyway existe a partir do Boot 4.x; em Boot 3.x
    // troque por 'org.flywaydb:flyway-core' direto.
    implementation 'org.springframework.boot:spring-boot-starter-flyway'
    implementation 'org.flywaydb:flyway-database-postgresql'
    implementation 'org.springframework.boot:spring-boot-starter-mail'
    runtimeOnly 'org.postgresql:postgresql'

    testImplementation platform('org.junit:junit-bom:5.11.4')
    testImplementation 'org.junit.jupiter:junit-jupiter'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

- [ ] **Step 6: Criar `core-build.gradle.kts.template` (só Kotlin)**

```kotlin
plugins {
    `java-library`
    kotlin("jvm")
    kotlin("plugin.spring")
    kotlin("plugin.jpa")
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

// O -core nao aplica o plugin org.springframework.boot: nao gera bootJar,
// continua biblioteca. Mas precisa do BOM para resolver as versoes dos
// starters sem escreve-las a mao. Sem versao aqui: os plugins do Kotlin e o
// io.spring.dependency-management herdam a versao declarada no
// build.gradle.kts da raiz.
dependencyManagement {
    imports {
        mavenBom("org.springframework.boot:spring-boot-dependencies:{boot-version}")
    }
}

dependencies {
    api(project(":buildingBlocks"))

    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    // spring-boot-starter-flyway existe a partir do Boot 4.x; em Boot 3.x
    // troque por "org.flywaydb:flyway-core" direto.
    implementation("org.springframework.boot:spring-boot-starter-flyway")
    implementation("org.flywaydb:flyway-database-postgresql")
    implementation("org.springframework.boot:spring-boot-starter-mail")
    // Spring, Jackson e Hibernate leem classe Kotlin via reflexao; sem isso
    // alguns caminhos (serializacao, proxy de metodo) falham em runtime.
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    runtimeOnly("org.postgresql:postgresql")

    testImplementation(platform("org.junit:junit-bom:5.11.4"))
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

// domain/ e infrastructure/ nao sao module boundaries do Gradle -- sao pastas
// do mesmo modulo. Sem allOpen, uma classe Kotlin e final por padrao e nem
// o Hibernate (proxy de @Entity) nem o Spring (proxy de @Configuration)
// conseguem estender ela em runtime.
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
    annotation("org.springframework.context.annotation.Configuration")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

- [ ] **Step 7: Reescrever `buildingBlocks/build.gradle.template` (só Java)**

```gradle
plugins {
    id 'java-library'
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

dependencies {
    testImplementation platform('org.junit:junit-bom:5.11.4')
    testImplementation 'org.junit.jupiter:junit-jupiter'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

- [ ] **Step 8: Criar `buildingBlocks/build.gradle.kts.template` (só Kotlin)**

```kotlin
plugins {
    `java-library`
    kotlin("jvm")
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

dependencies {
    // Sem kotlin-reflect: nenhum dos contratos usa reflexao, e sem BOM
    // nem dependency-management neste modulo uma dependencia sem versao nao
    // resolveria. O kotlin-test-junit5 sem versao funciona porque o Kotlin
    // Gradle Plugin versiona kotlin-test sozinho.
    testImplementation(platform("org.junit:junit-bom:5.11.4"))
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

- [ ] **Step 9: Rodar a checagem e ver passar**

Rode `check_dsl_templates; echo "EXIT=$?"` do Step 1.
Expected: nenhuma linha de erro e `EXIT=0`.

- [ ] **Step 10: Commit**

```bash
git add $SKILL/templates/root-build.gradle.template $SKILL/templates/root-build.gradle.kts.template \
        $SKILL/templates/core-build.gradle.template $SKILL/templates/core-build.gradle.kts.template \
        $SKILL/templates/buildingBlocks/build.gradle.template $SKILL/templates/buildingBlocks/build.gradle.kts.template
git commit -m "Separa os templates Gradle da new-project por DSL

Groovy fica so com Java, Kotlin DSL so com Kotlin; os marcadores
condicionais saem dos tres builds.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `SKILL.md` e referências escolhem a DSL pela linguagem

**Files:**
- Modify: `$SKILL/SKILL.md` (Passo 4, linhas ~108–150; Passo 5, linhas ~152–183; tabela *Entradas*)
- Modify: `$SKILL/references/initializr-api.md:32-68`
- Modify: `$SKILL/references/gradle-multi-module.md` (inteiro onde cita `settings.gradle`/`build.gradle`)
- Modify: `$SKILL/references/pitfalls.md:217`

**Interfaces:**
- Consumes: os seis caminhos de template da Tarefa 1.
- Produces: o vocabulário `{dsl-ext}` = vazio quando `language=java`, `.kts` quando `language=kotlin`; e `{initializr-type}` = `gradle-project` / `gradle-project-kotlin`. A Tarefa 5 executa a skill com esse vocabulário.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
SKILL=plugins/analizza-skills/skills/analizza-new-project
check_dsl_docs() {
  local ok=0
  grep -n 'usa sempre `type=gradle-project`' $SKILL/references/initializr-api.md && ok=1
  grep -n 'Por que `type` não muda com `language`' $SKILL/SKILL.md && ok=1
  grep -n 'type` fica\s*$\|sempre `gradle-project`' $SKILL/SKILL.md && ok=1
  grep -n 'bloco condicional da `language`' $SKILL/SKILL.md $SKILL/references/gradle-multi-module.md && ok=1
  grep -q 'gradle-project-kotlin' $SKILL/SKILL.md || { echo "SKILL.md nao cita gradle-project-kotlin"; ok=1; }
  grep -q '{dsl-ext}' $SKILL/SKILL.md || { echo "SKILL.md nao define {dsl-ext}"; ok=1; }
  grep -q 'include(":' $SKILL/references/gradle-multi-module.md || { echo "gradle-multi-module sem sintaxe kts"; ok=1; }
  grep -q 'core-build.gradle.template` pina' $SKILL/references/pitfalls.md && { echo "pitfalls cita so o Groovy"; ok=1; }
  return $ok
}
check_dsl_docs; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar**

Expected: várias linhas apontando os trechos antigos e `EXIT=1`.

- [ ] **Step 3: `SKILL.md` — tabela *Entradas***

Acrescentar duas linhas derivadas logo abaixo de `db-name`:

```markdown
| `initializr-type` | Derivado de `language` | `gradle-project-kotlin` se `kotlin`, `gradle-project` se `java` |
| `dsl-ext` | Derivado de `language` | `.kts` se `kotlin`, vazio se `java` |
```

E, depois do parágrafo "Não invente a `boot-version`…", acrescentar:

```markdown
A DSL do Gradle segue a linguagem: Kotlin gera `build.gradle.kts` e
`settings.gradle.kts`; Java gera `build.gradle` e `settings.gradle`. Todo
template Gradle desta skill existe nas duas formas — `<nome>.gradle.template`
(Groovy, só Java) e `<nome>.gradle.kts.template` (Kotlin DSL, só Kotlin) — e
só o da linguagem escolhida entra no projeto. Nunca misture DSL no mesmo build.
```

- [ ] **Step 4: `SKILL.md` — Passo 2**

No parágrafo dos marcadores condicionais, trocar "Os templates desta skill marcam trechos…" por:

```markdown
O `architecture-conventions.md.template` marca trechos que divergem entre as
duas linguagens com `<!-- se kotlin -->` / `<!-- fim se kotlin -->` e
`<!-- se java -->` / `<!-- fim se java -->`: grave sempre **só um dos dois**
blocos e remova os marcadores e o bloco do idioma não escolhido — nunca os
dois juntos, nunca os marcadores sobrando no arquivo final. Os templates
Gradle não usam marcador: a escolha é pelo arquivo (`{dsl-ext}`).
```

- [ ] **Step 5: `SKILL.md` — Passo 4**

Substituir o primeiro parágrafo ("Baixe o `starter.zip` com … `type=gradle-project` — sempre, mesmo quando `language=kotlin` (ver nota abaixo) — …") e **a nota inteira** "Por que `type` não muda com `language`" por:

```markdown
Baixe o `starter.zip` com `artifactId={project-name}-api`,
`type={initializr-type}` e `language={language}` — os dois substituem os
literais `type=gradle-project` e `language=java` do exemplo de curl da
[referência do Initializr](./references/initializr-api.md).
**Inspecione antes de extrair**, e siga
[gradle-multi-module.md](./references/gradle-multi-module.md) para promover o
wrapper à raiz, empurrar o resto para `{project-name}-api/` e escrever o
`settings.gradle{dsl-ext}`.

> **Por que `type` muda com `language`:** na API do Initializr, `type` escolhe
> a **DSL** do build (`gradle-project` = Groovy, `gradle-project-kotlin` =
> Kotlin DSL) e `language` escolhe a linguagem do **código-fonte**. São eixos
> independentes na API, mas esta skill os amarra: o `build.gradle{dsl-ext}`
> que o Initializr gera para o `-api` precisa estar na mesma DSL dos templates
> que a skill grava para a raiz, o `-core` e o `buildingBlocks`, senão o build
> sai com DSL misturada. Ver tabela de `type` na
> [referência do Initializr](./references/initializr-api.md).
```

No parágrafo seguinte (build da raiz), trocar:
- `escreva o \`build.gradle\` da **raiz**` → `escreva o \`build.gradle{dsl-ext}\` da **raiz**`
- `\`plugins {}\` de \`{project-name}-api/build.gradle\`` → `\`plugins {}\` de \`{project-name}-api/build.gradle{dsl-ext}\``
- `grave-as em [root-build.gradle.template](./templates/root-build.gradle.template) — só o bloco condicional da \`language\` escolhida — como \`build.gradle\` da raiz` → `grave-as em [root-build.gradle.template](./templates/root-build.gradle.template) (java) ou [root-build.gradle.kts.template](./templates/root-build.gradle.kts.template) (kotlin) como \`build.gradle{dsl-ext}\` da raiz`

No parágrafo do `-core`, trocar `a partir de [core-build.gradle.template](./templates/core-build.gradle.template)` por `a partir de [core-build.gradle.template](./templates/core-build.gradle.template) (java) ou [core-build.gradle.kts.template](./templates/core-build.gradle.kts.template) (kotlin), gravado como \`{project-name}-core/build.gradle{dsl-ext}\`` e **apagar** a frase final "Grave só o bloco condicional da `language` escolhida."

- [ ] **Step 6: `SKILL.md` — Passo 5**

Trocar o parágrafo "Copie também [templates/buildingBlocks/build.gradle.template]… gravando só o bloco `<!-- se {language} -->` correspondente." por:

```markdown
Copie também
[templates/buildingBlocks/build.gradle.template](./templates/buildingBlocks/build.gradle.template)
(java) ou
[templates/buildingBlocks/build.gradle.kts.template](./templates/buildingBlocks/build.gradle.kts.template)
(kotlin) para `buildingBlocks/build.gradle{dsl-ext}`.
```

Trocar "Acrescente ao `settings.gradle`, junto dos dois `include` já escritos no Passo 4:" e o bloco `gradle` seguinte por:

````markdown
Acrescente ao `settings.gradle{dsl-ext}`, junto dos dois `include` já escritos
no Passo 4:

```gradle
include ':buildingBlocks'        // java   (settings.gradle)
include(":buildingBlocks")       // kotlin (settings.gradle.kts)
```
````

Na frase "o `build.gradle.template` deste módulo não declara `sourceSets`", trocar por "o build deste módulo não declara `sourceSets`".

- [ ] **Step 7: `references/initializr-api.md`**

No curl do "Passo 2 — Gerar", trocar a linha `--data-urlencode 'type=gradle-project' \` por `--data-urlencode 'type={initializr-type}' \` e `--data-urlencode 'language=java' \` por `--data-urlencode 'language={language}' \`.

Substituir o parágrafo das linhas 59–68 ("`type` escolhe o DSL do build script… nenhum benefício aqui.") por:

```markdown
`type` escolhe a DSL do build script, não a linguagem do código-fonte — quem
decide Java vs. Kotlin é `language`. Na API os dois são eixos independentes
(dá para pedir código Kotlin com build Groovy). Esta skill os amarra:
`language=kotlin` usa `type=gradle-project-kotlin` e `language=java` usa
`type=gradle-project`, porque todo template Gradle que ela grava existe nas
duas DSLs e o `-api` gerado pelo Initializr precisa estar na mesma DSL dos
módulos que a skill escreve. Misturar DSL no mesmo build não traz benefício e
dobra o que alguém precisa ler para mexer nele.
```

Na linha 113, trocar "O `rootProject.name` no `settings.gradle` é reescrito" por "O `rootProject.name` no `settings.gradle{dsl-ext}` é reescrito".

- [ ] **Step 8: `references/gradle-multi-module.md`**

1. Tabela "O que vai para onde": `settings.gradle` → `settings.gradle{dsl-ext}`; `build.gradle, src/, HELP.md` → `build.gradle{dsl-ext}, src/, HELP.md`. Acrescentar `.gitattributes` à linha do `.gitignore` (o zip atual do Initializr o traz): `| \`.gitignore\`, \`.gitattributes\` | raiz | os padrões deles casam em qualquer profundidade |`.
2. No bloco `bash` do Procedimento, trocar `"$tmp"/settings.gradle "$tmp"/.gitignore .` por `"$tmp"/settings.gradle{dsl-ext} "$tmp"/.gitignore "$tmp"/.gitattributes .`
3. Seção `## settings.gradle` → `## settings.gradle{dsl-ext}`, e o bloco de código vira:

````markdown
```gradle
// java — settings.gradle
rootProject.name = '{project-name}'
include ':{project-name}-api'
include ':{project-name}-core'
```

```kotlin
// kotlin — settings.gradle.kts
rootProject.name = "{project-name}"
include(":{project-name}-api")
include(":{project-name}-core")
```
````

4. Seção `## build.gradle da raiz` → `## build.gradle{dsl-ext} da raiz`. No texto, `build.gradle` → `build.gradle{dsl-ext}` onde se refere a arquivo do projeto gerado. Na lista de versões, a primeira linha vira: "a versão ao lado de `kotlin(\"jvm\")` (só existe quando `language=kotlin`) vira `{kotlin-version}`;". A frase final "Grave essas três em [root-build.gradle.template]… só o bloco condicional da `language` escolhida." vira: "Grave essas versões em [root-build.gradle.template](../templates/root-build.gradle.template) (java) ou [root-build.gradle.kts.template](../templates/root-build.gradle.kts.template) (kotlin) como `build.gradle{dsl-ext}` da raiz."
5. Seção `## {project-name}-api/build.gradle` → `## {project-name}-api/build.gradle{dsl-ext}`. Na lista de ids, trocar `org.jetbrains.kotlin.jvm`, `org.jetbrains.kotlin.plugin.spring`, `org.jetbrains.kotlin.plugin.jpa` por `kotlin("jvm")`, `kotlin("plugin.spring")`, `kotlin("plugin.jpa")`. O bloco da dependência de projeto vira:

````markdown
```gradle
	implementation project(':{project-name}-core')      // java
```

```kotlin
	implementation(project(":{project-name}-core"))     // kotlin
```
````

6. Seção `## {project-name}-core/build.gradle` → `## {project-name}-core/build.gradle{dsl-ext}`, e o link passa a citar os dois templates: "[core-build.gradle.template](../templates/core-build.gradle.template) (java) ou [core-build.gradle.kts.template](../templates/core-build.gradle.kts.template) (kotlin)".

- [ ] **Step 9: `references/pitfalls.md`**

Linha 217: "O `core-build.gradle.template` pina o `junit-bom`." → "Os dois templates do core (`core-build.gradle.template` e `core-build.gradle.kts.template`) pinam o `junit-bom`." Ajustar o verbo seguinte se necessário ("O core importa, sim, o BOM…" fica) e o exemplo de `mavenBom` ganha a forma kts entre parênteses: `(ou mavenBom("…") no .kts)`.

- [ ] **Step 10: Rodar a checagem e ver passar**

`check_dsl_docs; echo "EXIT=$?"` → nenhuma linha de erro, `EXIT=0`. E:

```bash
grep -rn 'bloco condicional\|<!-- se {language} -->' $SKILL/SKILL.md $SKILL/references/ \
  | grep -v 'architecture-conventions'
```

Expected: nenhuma ocorrência que se refira a template Gradle (só as do Passo 8, que falam do template de convenções).

- [ ] **Step 11: Commit**

```bash
git add $SKILL/SKILL.md $SKILL/references/initializr-api.md $SKILL/references/gradle-multi-module.md $SKILL/references/pitfalls.md
git commit -m "Faz a new-project gerar a DSL do Gradle da linguagem escolhida

Kotlin passa a sair com gradle-project-kotlin e build.gradle.kts;
Java continua Groovy.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Convenções — estrutura de entrada e testes (itens 1, 2, 3, 7) e árvore do Passo 8

**Files:**
- Modify: `$SKILL/templates/architecture-conventions.md.template` (árvore do `-api` l.51–67; *Falha* l.241–247; *Autenticação* l.282–288; *Testes* l.331–370)
- Modify: `$SKILL/SKILL.md` Passo 8 (bloco `mkdir`)

**Interfaces:**
- Consumes: `{src-dir}`, `{package-path}` já definidos no Passo 5/8 do `SKILL.md`.
- Produces: caminhos `presenter/jobs/`, `presenter/configuration/security/`, `presenter/configuration/exception/`, `support/TestConfig` — a Entrega 2 os usa com esses nomes.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
SKILL=plugins/analizza-skills/skills/analizza-new-project
T=$SKILL/templates/architecture-conventions.md.template
check_entrada() {
  local ok=0
  grep -q 'jobs/' $T || { echo "arvore sem jobs/"; ok=1; }
  grep -q 'relógio em vez de HTTP' $T || { echo "sem criterio de job como entrada"; ok=1; }
  grep -q 'presenter/configuration/exception/`' $T || { echo "GlobalExceptionHandler sem exception/"; ok=1; }
  grep -q 'presenter/configuration/security/`' $T || { echo "validacao sem security/"; ok=1; }
  grep -q '@Scheduled' $T || { echo "ArchUnit sem @Scheduled"; ok=1; }
  grep -q 'TestConfig' $T || { echo "sem TestConfig"; ok=1; }
  grep -q 'presenter/jobs' $SKILL/SKILL.md || { echo "mkdir sem jobs"; ok=1; }
  grep -q 'presenter/configuration/security' $SKILL/SKILL.md || { echo "mkdir sem security"; ok=1; }
  grep -q 'presenter/configuration/exception' $SKILL/SKILL.md || { echo "mkdir sem exception"; ok=1; }
  return $ok
}
check_entrada; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: as nove linhas e `EXIT=1`.

- [ ] **Step 3: Item 1 — árvore do `-api` com `jobs/`**

Substituir o bloco de árvore do `{project-name}-api` por:

```
Application                        ponto de entrada; a raiz do component scan
presenter/
  routes/<agregado>/<casoDeUso>/   uma Route por caso de uso, com o Request
                                   co-locado no mesmo arquivo
  jobs/                            jobs agendados: o agendamento e sua habilitação
  configuration/
    security/                      cadeia de filtros, validação de credencial
    exception/                     o handler global e as exceções de transporte
```

Logo depois do parágrafo "Não há mais nada neste módulo…", acrescentar:

```markdown
Um job agendado mora em `presenter/jobs/` pelo mesmo critério que uma Route
mora em `presenter/routes/`: ele é **entrada** — recebe um gatilho, monta o
Command, chama o handler e traduz o resultado em log. O gatilho é o relógio
em vez de HTTP, e só isso muda. Um job não tem regra de negócio, pelo mesmo
motivo que uma Route não tem.
```

- [ ] **Step 4: Item 2 — localizar handler global e validação**

Em *Falha e corpo de erro*, trocar `` `{project-name}-api/.../presenter/configuration/`, `` por `` `{project-name}-api/.../presenter/configuration/exception/`, ``.

No critério de `infrastructure/` (seção *O que mora onde*), trocar "e por isso mora no `-api`, em `presenter/configuration/`, não no `-core`" por "e por isso mora no `-api`, em `presenter/configuration/security/`, não no `-core`".

Em *Autenticação e autorização*, trocar "guarda de entrada (`presenter/configuration/` no `-api`)" por "guarda de entrada (`presenter/configuration/security/` no `-api`)".

- [ ] **Step 5: Item 3 — ArchUnit cobre jobs**

Em *Testes*, substituir o item da regra ArchUnit por:

```markdown
- Uma regra ArchUnit (por exemplo `EntrypointHasIntegrationTestIT`, em
  `{project-name}-api/src/test/.../architecture/`) com **um único
  trabalho**: todo entrypoint — `@RestController` ou classe com um método
  `@Scheduled` — precisa ter uma classe `<Nome>IT` que estenda
  `BaseIntegrationTest`. Um job entra na regra pelo mesmo motivo que um
  controller, e com mais razão: ninguém recebe um 500 quando um agendamento
  para de rodar, então o risco de ele quebrar em silêncio é maior, não menor.
  Não precisa de regra de pureza de pacote (nada impede hoje, por exemplo, um
  import de `infrastructure/` dentro de `domain/` — veja "`-core` pode usar
  Spring" acima).
```

- [ ] **Step 6: Item 7 — dublês dos serviços de saída**

Em *Testes*, logo depois do item "**O `-api` deve ser o único módulo com Testcontainers.**…", acrescentar:

```markdown
- Nenhuma mensagem nem chamada sai da suíte. Um `TestConfig` em
  `{project-name}-api/src/test/.../support/` registra, com `@Primary`, um
  dublê para cada serviço de saída que não tem container (e-mail, gateway de
  terceiro): o dublê guarda o que recebeu em memória para o teste afirmar
  sobre isso. O banco e o que tem container de verdade não ganham dublê — o
  teste de integração existe para exercitá-los.
```

- [ ] **Step 7: Passo 8 do `SKILL.md` — `mkdir` do `-api`**

Trocar a linha `mkdir -p "$api/presenter/routes" "$api/presenter/configuration"` por:

```bash
mkdir -p "$api/presenter/routes" "$api/presenter/jobs" \
         "$api/presenter/configuration/security" \
         "$api/presenter/configuration/exception"
```

- [ ] **Step 8: Rodar a checagem e ver passar** — `check_entrada; echo "EXIT=$?"` → `EXIT=0`.

- [ ] **Step 9: Commit**

```bash
git add $SKILL/templates/architecture-conventions.md.template $SKILL/SKILL.md
git commit -m "Leva jobs, security e exception para a camada de entrada da new-project

A regra ArchUnit passa a cobrir @Scheduled e os servicos de saida
ganham dubles no TestConfig.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Convenções — contratos, falhas e recursos de saída (itens 4, 5, 6)

**Files:**
- Modify: `$SKILL/templates/architecture-conventions.md.template` (*O que mora onde* do `-core`; *Os contratos do `buildingBlocks`*; *Falha e corpo de erro*)
- Modify: `docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md` (mover o ajuste de *Fora de escopo*)

**Interfaces:**
- Consumes: nada das tarefas anteriores além do arquivo já editado na Tarefa 3.
- Produces: texto; nenhuma interface nova.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
SKILL=plugins/analizza-skills/skills/analizza-new-project
T=$SKILL/templates/architecture-conventions.md.template
check_nuances() {
  local ok=0
  grep -q 'Handler magro é o preço de manter a seta' $T || { echo "sem handler magro"; ok=1; }
  grep -q 'argumento da fábrica' $T || { echo "sem Entity via fabrica"; ok=1; }
  grep -q 'sem Spring e sem banco' $T || { echo "sem domain/services puro"; ok=1; }
  grep -q '404' $T || { echo "sem not found 404"; ok=1; }
  grep -q 'o que o caso de uso \*\*decide\*\*' $T || { echo "sem falha inesperada no tipo fechado"; ok=1; }
  grep -q 'recursos de saída' $T || { echo "sem recursos de saida"; ok=1; }
  grep -qi 'AccessCode\|DocuSign\|com\.eaf' $T && { echo "exemplo especifico do EAF"; ok=1; }
  return $ok
}
check_nuances; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: seis linhas "sem …" e `EXIT=1`.

- [ ] **Step 3: Item 4a — `domain/services` puro**

Em *O que mora onde* do `-core`, substituir o parágrafo "Enquanto houver poucos agregados, `domain/` fica com os arquivos soltos…" por:

```markdown
Enquanto houver poucos agregados, `domain/` fica com os arquivos soltos na
raiz e `rules/`/`services/` vazios (`.gitkeep`). Quando eles ganharem
conteúdo real, o padrão é o mesmo: um arquivo por regra ou serviço, sem
sub-pastas por agregado — isso só se justifica se o número de agregados
crescer a ponto de a raiz de `domain/` ficar difícil de navegar.

Um serviço de `domain/services/` é lógica pura, sem Spring e sem banco — por
exemplo, transformar uma lista plana numa árvore, ou derivar um código a
partir de um nome. É isso que o mantém no `-core`: se ele morasse no `-web`,
teria de ser reescrito no `-mobile`.
```

- [ ] **Step 4: Item 6 — recursos de saída**

Em *O que mora onde* do `-core`, logo depois do parágrafo "`domain/repositories` guarda **interfaces**…", acrescentar:

```markdown
Os recursos de saída — templates de mensagem, layouts de documento gerado e
afins — moram em `{project-name}-core/src/main/resources/<saída>/` (por
exemplo `mail/templates/`), pelo mesmo critério das migrations: são saída,
pertencem ao `-core` e chegam ao classpath do `-api` pela dependência de
projeto. O prefixo não pode colidir com as pastas que o Spring Boot varre
sozinho (`templates/`, `static/`, `public/`): um `templates/` na raiz do
classpath liga resolução de view no `-api`, que é uma API JSON.
```

- [ ] **Step 5: Item 4b — handler magro**

Em *Os contratos do `buildingBlocks`*, substituir o item `ResultCommandHandler` por:

```markdown
- **`ResultCommandHandler<TCommand, TResult>`** — escrita com retorno. É o
  caso mais comum: a maioria dos casos de uso de escrita confirma algo ao
  chamador (id gerado, estado resultante). Um handler pode ser quase
  passthrough para uma porta de `infrastructure/` e ainda assim existir de
  propósito: é ele que impede a Route de injetar a porta direto e furar a
  regra de que o `-api` não importa `infrastructure/`. Handler magro é o preço de manter a seta,
  não sinal de camada sobrando. Repare que **`ResultCommand` não estende
  `Command`**: um `ResultCommand` não tem `id`. Se o caso de uso precisar de
  um identificador de correlação, declare o campo você mesmo — o contrato não
  empresta um.
```

- [ ] **Step 6: Item 4c — `Entity` e `RuleChecker` pela fábrica**

Substituir os itens `Entity` e `BusinessRule + RuleChecker` por:

```markdown
- **`Entity`** — base para agregado que valida sua própria invariante ao
  nascer, via `checkAllRules(...)`. Herdar de `Entity` **sem** chamar
  `checkAllRules` é caso normal, não esquecimento: quando a invariante depende
  de um argumento da fábrica e não de um campo do agregado, é a fábrica que
  chama um `RuleChecker` direto (veja o item seguinte).
```

(manter o item `Id` onde está, entre os dois)

```markdown
- **`BusinessRule` + `RuleChecker`** — regra que estoura
  `BusinessRulesBrokenException` quando quebrada. `Entity.checkAllRules` usa
  um `RuleChecker` internamente; uma fábrica chama um `RuleChecker` direto
  quando a regra olha um argumento da fábrica em vez de um campo do agregado —
  `checkAllRules` foi feito para uma entidade validar os próprios campos, não
  a entrada da fábrica.
```

- [ ] **Step 7: Item 5a — recurso inexistente vira 404**

Em *Falha e corpo de erro*, logo depois do parágrafo "**Padrão: exceção.**…", acrescentar:

```markdown
Nem toda falha é regra de negócio quebrada. Buscar um recurso que não existe
estoura uma exceção própria do `-core` (por exemplo `<Agregado>NotFoundException`),
e o mesmo `GlobalExceptionHandler` a converte em 404, com um corpo genérico
que não repete o identificador pedido nem diz se ele existiu e foi removido ou
nunca existiu.
```

- [ ] **Step 8: Item 5b — falha inesperada no tipo fechado**

Em *Falha e corpo de erro*, logo depois do parágrafo "Nesse caso o Handler devolve um tipo de resultado fechado…", acrescentar:

```markdown
O tipo fechado cobre só o que o caso de uso **decide**. Falha **inesperada**
— um template quebrado, o banco fora — não tem valor no tipo: ela sobe como
exceção, a `Route` não a traduz, e o resultado é 500. A distinção é o ponto,
não uma brecha: o tipo fechado existe para que decisão de negócio não vaze
pelo corpo do erro, e a exceção continua existindo para que defeito nosso não
se disfarce de sucesso. Por isso a `Route` de um caso de uso opaco não envolve
a chamada num "captura tudo e devolve o status de sucesso".
```

- [ ] **Step 9: Spec — mover o ajuste de *Fora de escopo***

No arquivo de spec, remover a subseção `#### Fora de escopo (ajuste)` inteira (título e parágrafo) da *Entrega 1*, e na *Entrega 3*, acrescentar um item à lista:

```markdown
- "Teste de arquitetura executável" sai da lista de *Fora de escopo* do `SKILL.md`: passa a ter
  dono. Fica nesta entrega, e não na 1, porque antes do Passo 11 existir ninguém o entrega.
```

- [ ] **Step 10: Rodar a checagem e ver passar** — `check_nuances; echo "EXIT=$?"` → `EXIT=0`.

- [ ] **Step 11: Commit**

```bash
git add $SKILL/templates/architecture-conventions.md.template docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md
git commit -m "Completa as convencoes da new-project com contratos, falhas e recursos de saida

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Executar a skill nas duas linguagens

Esta é a prova da entrega. Nenhum arquivo da skill muda aqui, a não ser que a execução revele defeito — nesse caso, corrigir no arquivo da tarefa de origem, commitar com mensagem `Corrige …`, e **refazer esta tarefa do zero** nas duas linguagens.

**Files:**
- Nenhum no repositório. Execuções em `$SCRATCH/kotlin-demo` e `$SCRATCH/java-demo`, onde `SCRATCH=/private/tmp/claude-501/-Users-diegolirio-Documents-Github-documents-eaf-system/e13ed494-3d49-436f-b7a1-ccf094781e90/scratchpad`.

**Interfaces:**
- Consumes: tudo das Tarefas 1–4.
- Produces: dois projetos gerados que as Entregas 2 e 3 reusam como alvo.

- [ ] **Step 1: Pré-requisitos**

```bash
java -version; node -v; npx -v; docker info > /dev/null 2>&1 && echo "docker OK"
curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 https://start.spring.io/metadata/client
lsof -i :5432 -i :8080 -i :3000 | grep LISTEN
```

Expected: JDK 25, Node e npx presentes, `docker OK`, `200`, e **nenhuma** porta 5432/8080/3000 ocupada (se estiverem, pare e avise — pode ser o `documents-eaf-system` de pé).

- [ ] **Step 2: Executar a skill com `language=kotlin`**

```bash
mkdir -p $SCRATCH/kotlin-demo && cd $SCRATCH/kotlin-demo
```

Siga `$SKILL/SKILL.md` (lido do **worktree**, não do plugin instalado) Passos 1–10 com: `project-name=kotlin-demo`, `language=kotlin`, `group=br.com.analizza`, `package=br.com.analizza.kotlindemo`, `java-version=25`, `dependencies=web,actuator,postgresql,data-jpa,flyway`.

- [ ] **Step 3: Conferir o projeto Kotlin**

```bash
cd $SCRATCH/kotlin-demo
find . -name '*.gradle*' -not -path '*/node_modules/*' -not -path './.gradle/*' | sort
find . -name '*.gradle' -not -path '*/node_modules/*' | wc -l          # espera 0
grep -rn '<!-- se' --include='*.gradle*' --include='*.md' . | grep -v node_modules | wc -l   # espera 0
./gradlew :buildingBlocks:test --console=plain > /tmp/kd-bb.log 2>&1; echo "EXIT=$?"
grep -cE 'NO-SOURCE' /tmp/kd-bb.log                                    # espera 0
src=kotlin-demo-api/src/main/kotlin/br/com/analizza/kotlindemo/presenter
ls -d $src/routes $src/jobs $src/configuration/security $src/configuration/exception
make build > /tmp/kd-build.log 2>&1; echo "EXIT=$?"
ls kotlin-demo-api/build/test-results/test/*.xml buildingBlocks/build/test-results/test/*.xml
grep -h -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' */build/test-results/test/*.xml
```

Expected: só `settings.gradle.kts` e `build.gradle.kts` (raiz, `buildingBlocks`, `-api`, `-core`); `0`; `0`; `EXIT=0`; `0`; os quatro diretórios listados; `EXIT=0`; XMLs existem; todos com `failures="0" errors="0"` e `tests` > 0.

Conferir também que o arquivo de convenções gravado (o caminho que o Passo 8 reportou) contém `presenter/jobs/`, `Handler magro` e `404`, e só o bloco Kotlin (`grep -c 'record' <arquivo>` = 0).

- [ ] **Step 4: Smoke test Kotlin (Passo 10 da skill) e encerramento**

Rodar o smoke test do Passo 10 como escrito na skill (`make run`, healthchecks 8080 e 3000, `grep -iE 'flyway|hikari'`), encerrar com SIGINT no grupo do make, confirmar 8080 e 3000 livres, `make db-down`.

Expected: `{"status":"UP"}`, `200`, log com Flyway e HikariPool; portas livres ao fim.

- [ ] **Step 5: Executar a skill com `language=java`**

```bash
mkdir -p $SCRATCH/java-demo && cd $SCRATCH/java-demo
```

Mesmos Passos 1–10, com `project-name=java-demo`, `language=java`, `package=br.com.analizza.javademo`, demais entradas iguais.

- [ ] **Step 6: Conferir o projeto Java**

```bash
cd $SCRATCH/java-demo
find . -name '*.gradle*' -not -path '*/node_modules/*' -not -path './.gradle/*' | sort
find . -name '*.kts' -not -path '*/node_modules/*' | wc -l               # espera 0
grep -rn '<!-- se' --include='*.gradle*' --include='*.md' . | grep -v node_modules | wc -l   # espera 0
./gradlew :buildingBlocks:test --console=plain > /tmp/jd-bb.log 2>&1; echo "EXIT=$?"
grep -cE 'NO-SOURCE' /tmp/jd-bb.log                                      # espera 0
src=java-demo-api/src/main/java/br/com/analizza/javademo/presenter
ls -d $src/routes $src/jobs $src/configuration/security $src/configuration/exception
make build > /tmp/jd-build.log 2>&1; echo "EXIT=$?"
grep -h -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' */build/test-results/test/*.xml
```

Expected: só `settings.gradle` e `build.gradle`; `0`; `0`; `EXIT=0`; `0`; os quatro diretórios; `EXIT=0`; todos `failures="0" errors="0"`. Arquivo de convenções sem `data class` (`grep -c 'data class'` = 0).

- [ ] **Step 7: Smoke test Java e encerramento** — igual ao Step 4.

- [ ] **Step 8: Registrar o resultado**

Anotar, para o relato da entrega: versões reais geradas (Boot, Kotlin, Java, Next, React, Expo) lidas dos arquivos, os `EXIT=` observados e as contagens de teste dos XMLs. Não commitar nada do scratchpad.

---

### Task 6: Pull request da Entrega 1

**Files:** nenhum.

- [ ] **Step 1: Conferir a árvore**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
git status --short          # espera vazio
git log --oneline origin/main..HEAD
make validate; echo "EXIT=$?"
make check; echo "EXIT=$?"
```

Expected: árvore limpa; commits das Tarefas 1–4 (+ correções, se houve) sobre o commit da spec; `EXIT=0` nos dois.

- [ ] **Step 2: Perguntar antes de publicar**

Push e PR são ação para fora: perguntar ao usuário se pode fazer `git push -u origin docs/spec-integration-test-e-camadas` e abrir o PR contra `main`. Só seguir com um sim.

- [ ] **Step 3: Abrir o PR (após o sim)**

```bash
git push -u origin docs/spec-integration-test-e-camadas
gh pr create --base main --title "Camadas completas e DSL por linguagem na analizza-new-project" --body "$(cat <<'EOF'
## O que muda

- Kotlin passa a gerar Gradle Kotlin DSL (`gradle-project-kotlin`, `.kts`); Java segue Groovy. Os três templates Gradle viram pares, sem marcadores condicionais.
- O template de convenções ganha: `presenter/jobs/` e o critério de job como entrada; `configuration/security/` e `configuration/exception/` localizados; ArchUnit cobrindo `@Scheduled`; handler magro; `Entity` validada pela fábrica; `domain/services` puro; 404 para recurso inexistente; falha inesperada fora do tipo fechado; recursos de saída no `-core`; dublês de saída no `TestConfig`.
- Passo 8 cria `presenter/jobs`, `configuration/security` e `configuration/exception`.
- Spec das quatro entregas incluída (`docs/superpowers/specs/2026-09-12-…`).

## Verificação

Skill executada do worktree em diretório descartável, nas duas linguagens:
<preencher com os EXIT= e contagens anotados na Tarefa 5, Step 8>

## O que não foi verificado

A skill instalada pelo marketplace publicado (`make update`) — conferência do mantenedor depois do merge.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

O `<preencher…>` é substituído pelos números reais antes de rodar o comando — nunca publicado assim.

---

## Self-Review

- **Cobertura da spec (Entrega 1):** DSL por linguagem → Tarefas 1 e 2; itens 1, 2, 3, 7 → Tarefa 3; itens 4, 5, 6 → Tarefa 4; árvore do Passo 8 → Tarefa 3 Step 7; ajuste de *Fora de escopo* → movido para a Entrega 3 (Tarefa 4 Step 9), com o motivo registrado na spec; verificação da spec → Tarefa 5.
- **Placeholders:** o único é o `<preencher…>` do corpo do PR, instruído a ser substituído por dado real antes do comando.
- **Consistência de nomes:** `{dsl-ext}` e `{initializr-type}` definidos na Tarefa 2 Step 3 e usados nos Steps 5–8; `presenter/configuration/exception/` com o mesmo nome no template (Tarefa 3) e no `mkdir`.
