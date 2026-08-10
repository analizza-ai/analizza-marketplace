---
name: analizza-java-integration-test
description: 'Configura testes de integracao em projetos Java + Spring Boot com Gradle Groovy DSL, adaptando-se automaticamente a estrutura do projeto: cria um modulo dedicado (`{base}-integration-tests`) em projetos multi-modulo, ou configura tudo dentro de `src/test/` quando o projeto for single-module (sem submodulos). Move os testes de integracao, centraliza o BaseIntegrationTest, isola libs pesadas de teste, configura jacoco, tasks Gradle test/integrationTest e regra ArchUnit de cobertura de entrypoints. Use quando o usuario pedir "criar modulo de testes de integracao java", "integration-tests module java", "separar testes de integracao", "reduzir tempo de testcontainers", "setup integration test module" ou "analizza java integration test".'
argument-hint: 'Opcional: nome base do projeto (ex: pp) e lista de modulos. Se omitido, a skill descobre a partir de settings.gradle.'
user-invocable: true
---

# Analizza Java Integration Test

Configura a infraestrutura de testes de integracao do projeto, reduzindo o tempo de carregamento de
Testcontainers e de contextos Spring. O caminho concreto depende da estrutura do projeto, detectada
automaticamente no Passo 1.5:

- **Projeto multi-modulo** (2+ modulos em `settings.gradle`): cria um modulo dedicado
  `{base}-integration-tests`, nao implantavel, que concentra toda a infraestrutura de integracao.
- **Projeto single-module** (0 ou 1 modulo, tudo em `./src/`): NAO cria um modulo novo. Toda a
  infraestrutura de integracao (BaseIntegrationTest, assets de Testcontainers, ArchUnit) e
  configurada dentro de `src/test/` do proprio modulo existente.

> ⚠️ **Regra valida nos dois caminhos, sem exceção:** assets de container (`Dockerfile`, `init.sql`
> e equivalentes) SEMPRE ficam em `src/test/resources/`, nunca em `src/main/resources/`. Isso vale
> tanto para o modulo dedicado (multi-modulo) quanto para o modulo unico (single-module).

Esta skill NAO promove um projeto single-module para multi-modulo. Se o usuario quiser um modulo
dedicado mas o projeto for single-module, informar que isso exigiria reestruturar o `src/main` do
projeto (fora do escopo desta skill) e prosseguir com o caminho single-module (dentro de `src/test/`).

## Stack alvo

- **Linguagem:** Java (`src/main/java`, `src/test/java`, arquivos `.java`).
- **Build:** Gradle com **Groovy DSL** (`build.gradle`, `settings.gradle`). Se o projeto usar Kotlin
  DSL (`build.gradle.kts`), aplicar a mesma semantica adaptando a sintaxe — ou preferir a skill
  irma `analizza-kotlin-integration-test`.
- **Spring Boot 4.x:** `RestTestClient`, slices `spring-boot-starter-*-test`,
  `spring-boot-testcontainers`.
- **Mocking:** Mockito + `@MockitoBean`/`@MockitoSpyBean` (via `spring-boot-starter-test`). Nao usar
  MockK/springmockk (equivalentes Kotlin).

> Para projetos Kotlin, use a skill `analizza-kotlin-integration-test`.

## Quando usar

- Projeto Java + Spring Boot (multi-modulo ou single-module) com testes de integracao
  desorganizados ou espalhados.
- Necessidade de reduzir tempo de build/testes isolando Testcontainers e contexto Spring pesado
  (multi-modulo) ou apenas de padronizar a estrutura de testes de integracao (single-module).
- Padronizar um unico `BaseIntegrationTest` (e, em multi-modulo, um unico `IntegrationTestApplication`).
- Garantir ITs para todos os entrypoints (e, em multi-modulo, cobertura agregada via Jacoco).

## Artefatos criados / modificados

### Caminho multi-modulo (2+ modulos)

```
settings.gradle                                            <- registra o novo modulo
build.gradle (raiz)                                        <- plugin jacoco-report-aggregation + agregacao + tasks
{base}-integration-tests/build.gradle                      <- libs pesadas de teste (novo)
{base}-integration-tests/src/test/java/**                  <- ITs movidos + BaseIntegrationTest + IntegrationTestApplication
{base}-integration-tests/src/test/resources/**             <- application.yml mesclado + archunit.properties + assets de container (oracle/Dockerfile, oracle/init.sql)
{outros modulos}/build.gradle                              <- remover libs pesadas de teste de integracao
```

> Substitua `{base}` pelo prefixo do projeto (ex.: `pp` para `pp-requests-core`).
> O novo modulo NAO e implantavel: `jar` e `bootJar` desabilitados.

### Caminho single-module (0 ou 1 modulo, tudo em `./src/`)

```
build.gradle (unico)                                       <- libs de teste + tasks test/integrationTest (sem aggregation)
src/test/java/**                                           <- ITs organizados + BaseIntegrationTest (usa a Application existente)
src/test/resources/**                                      <- archunit.properties + assets de container (oracle/Dockerfile, oracle/init.sql)
```

> Nao ha modulo novo, nem `settings.gradle`, nem merge de `Application`/`application.yml`
> (ja existe apenas um). O `BaseIntegrationTest` referencia a `Application` unica do projeto.

---

## Passo 1 - Descobrir base do projeto e modulos (via settings.gradle)

1. Ler `settings.gradle` (se existir) para obter `rootProject.name` e a lista COMPLETA de
   modulos declarados em `include ...`. Esta lista e a fonte de verdade para todos os passos
   seguintes (dependencias do novo modulo e `jacocoAggregation`, quando aplicavel).

   ```bash
   grep -E "^\s*include" settings.gradle
   ```

   Se o projeto usar Kotlin DSL, o arquivo sera `settings.gradle.kts` e o padrao `include(`.

2. Derivar o prefixo `{base}`:
   - Multi-modulo: prefixo comum dos nomes dos modulos (ex.: `pp-requests-core`,
     `pp-products-api` -> `{base}` = `pp`).
   - Single-module: `rootProject.name` (ou nome do diretorio do projeto, se nao houver
     `settings.gradle`).
3. Localizar todos os modulos que possuem classe principal Spring Boot (para mesclar Applications
   em multi-modulo, ou identificar a Application unica em single-module):

   ```bash
   grep -rl "@SpringBootApplication" --include="*.java" .
   ```

4. Localizar os `BaseIntegrationTest` existentes e os testes que os estendem:

   ```bash
   grep -rl "BaseIntegrationTest" --include="*.java" .
   ```

---

## Passo 1.5 - Detectar estrutura do projeto (multi-modulo vs. single-module)

Classificar o projeto contando os modulos declarados em `settings.gradle` (Passo 1):

```
2+ modulos em include              -> MULTI-MODULO
0 ou 1 modulo (ou sem              -> SINGLE-MODULE
settings.gradle, tudo em
./src/)
```

Com base na classificacao, definir o `{integration.target}`:

| Estrutura detectada | `{integration.target}`                          | O que sera feito                                                   |
|----------------------|--------------------------------------------------|----------------------------------------------------------------------|
| Multi-modulo          | modulo dedicado `{base}-integration-tests`        | Passos 2-7 no modo "multi-modulo" (cria modulo novo)                 |
| Single-module         | dentro de `src/test/` do proprio modulo existente | Passos 2-7 no modo "single-module" (sem modulo novo)                 |

**Sempre informar o usuario** do caminho detectado antes de prosseguir (e um aviso, nao uma escolha
livre — a estrutura do projeto e que decide):

> "Detectei que o projeto e **[multi-modulo / single-module]**. Vou **[criar o modulo dedicado
> `{base}-integration-tests` / configurar os testes de integracao dentro de `src/test/` deste
> modulo]**. Prosseguindo."

Esta skill nao promove um projeto single-module para multi-modulo (nao move `src/main`, nao cria
`settings.gradle` do zero). Se o usuario pedir explicitamente um modulo dedicado em um projeto
single-module, explicar que isso exigiria reestruturar o modulo de producao (fora do escopo desta
skill) e seguir pelo caminho single-module.

---

## Passo 2 - Criar (ou nao) o modulo `{base}-integration-tests`

### Se MULTI-MODULO

1. Registrar o modulo em `settings.gradle` (`include '{base}-integration-tests'`).
2. Criar `build.gradle` do modulo a partir de
   [integration-tests-build.gradle.template](./templates/integration-tests-build.gradle.template).
   Substituir o marcador `{project-dependencies}` por uma linha
   `testImplementation project(':<modulo>')` para CADA modulo do `settings.gradle`
   (Passo 1), exceto o proprio `{base}-integration-tests`.
3. O modulo NAO e implantavel: `jar` e `bootJar` ficam desabilitados (ja no template).

### Se SINGLE-MODULE

Nao criar modulo novo, nem alterar/criar `settings.gradle`. As libs de teste de integracao
(Testcontainers, WireMock, Awaitility, ArchUnit, `spring-boot-starter-test`, etc. — a mesma lista do
template
[integration-tests-build.gradle.template](./templates/integration-tests-build.gradle.template),
ignorando o bloco `{project-dependencies}`) sao adicionadas diretamente no `build.gradle` unico
do projeto, como `testImplementation`. Nao desabilitar `jar`/`bootJar` (o modulo continua
implantavel normalmente).

---

## Passo 3 - Isolar libs pesadas de teste

### Se MULTI-MODULO

- Remover dos `build.gradle` dos demais modulos (e da raiz, se estiverem la) as libs pesadas
  usadas apenas por testes de integracao: `spring-boot-testcontainers`, `testcontainers-*`,
  `wiremock-standalone`, `awaitility`, `archunit-junit5`, slices de teste
  (`spring-boot-starter-*-test`) que so sao necessarias na integracao.
- Manter nos modulos apenas o minimo para testes unitarios (`spring-boot-starter-test`,
  `junit-platform-launcher`).

### Se SINGLE-MODULE

**Pular este passo.** So existe um modulo — nao ha "outros modulos" de onde isolar as libs; elas
ja foram adicionadas nele mesmo no Passo 2.

### Regras (multi-modulo)

- Nao remover dependencias usadas por testes unitarios que permanecem no modulo.
- Preservar ordem/indentacao/convencoes do arquivo (aspas simples do Groovy DSL, sem parenteses).
- Nao duplicar dependencias.

---

## Passo 4 - Configurar Jacoco e tasks Gradle

### Se MULTI-MODULO

No `build.gradle` da raiz, aplicar os trechos de
[root-build-jacoco-aggregation.gradle.template](./templates/root-build-jacoco-aggregation.gradle.template):

1. Aplicar o plugin `jacoco-report-aggregation`.
2. Substituir o marcador `{jacoco-aggregation}` por uma linha
   `jacocoAggregation project(':<modulo>')` para CADA modulo do `settings.gradle`
   (Passo 1); o template ja inclui `{base}-integration-tests`.
3. Em `subprojects` (ou equivalente):
   - `test` roda apenas testes unitarios: `useJUnitPlatform { excludeTags 'integration' }`.
   - registrar `integrationTest` que roda apenas `@Tag("integration")` com
     `useJUnitPlatform { includeTags 'integration' }` e `failOnNoMatchingTests = false`.
   - configurar `JacocoReport` para agregar `test.exec` + `integrationTest.exec`.
4. Configurar `testCodeCoverageReport` (relatorio agregado XML/HTML) e a task
   `jacocoAggregatedCoverageVerification` com minimos de LINE e BRANCH (ex.: `0.80`).

### Se SINGLE-MODULE

No `build.gradle` unico, aplicar os trechos de
[single-module-jacoco.gradle.template](./templates/single-module-jacoco.gradle.template)
(sem `jacoco-report-aggregation` e sem `jacocoAggregation ...`, ja que ha apenas um modulo):

1. `test` roda apenas testes unitarios: `useJUnitPlatform { excludeTags 'integration' }`.
2. Registrar `integrationTest` que roda apenas `@Tag("integration")` com
   `useJUnitPlatform { includeTags 'integration' }` e `failOnNoMatchingTests = false`.
3. Configurar `jacocoTestReport`/`jacocoTestCoverageVerification` normal do proprio modulo (sem
   agregacao entre projetos), agregando `test.exec` + `integrationTest.exec`, com minimos de LINE e
   BRANCH (ex.: `0.80`).

### Regras

- Adaptar os trechos a estrutura existente (ex.: se ja ha bloco `subprojects`/tasks de teste,
  mesclar em vez de duplicar).
- Nao sobrescrever regras de cobertura existentes sem confirmar com o usuario.
- Em Groovy DSL, `minimum` aceita literal decimal (`0.80`) — nao usar `new BigDecimal("0.80")`.

---

## Passo 5 - Application, application.yml e organizacao dos ITs

### Se MULTI-MODULO

1. Criar um unico `IntegrationTestApplication` no novo modulo, mesclando os `@SpringBootApplication`
   dos demais modulos (component scan abrangente). Base em
   [IntegrationTestApplication.java.template](./templates/IntegrationTestApplication.java.template).
2. Mesclar os `application.yml`/`application.properties` dos modulos em
   `{base}-integration-tests/src/test/resources/`. O `BaseIntegrationTest` usa
   `spring.config.name=core-application,application` para carregar ambos.
3. Criar/centralizar o `BaseIntegrationTest` a partir de
   [BaseIntegrationTest.java.template](./templates/BaseIntegrationTest.java.template):
   - Se ja existir em outros modulos, mesclar o conteudo e mover para o novo modulo.
   - Se nao existir, criar do zero.
4. Mover TODOS os testes que estendem `BaseIntegrationTest` para o novo modulo, mantendo os packages.

### Se SINGLE-MODULE

1. NAO criar `IntegrationTestApplication` nem mesclar `application.yml` — ja existe apenas uma
   `@SpringBootApplication` e um `application.yml`/`application.properties` no proprio modulo.
2. Criar/centralizar o `BaseIntegrationTest` em `src/test/java/` a partir de
   [BaseIntegrationTest.java.template](./templates/BaseIntegrationTest.java.template), adaptado para
   referenciar a `Application` ja existente do projeto em `@SpringBootTest(classes = ...)` (em
   vez de um `IntegrationTestApplication` dedicado) e usando `spring.config.name=application`
   (sem `core-application`, ja que nao ha modulo core separado).
3. Organizar os testes que estendem `BaseIntegrationTest` dentro de `src/test/java/` (mantendo os
   packages), sem necessidade de mover entre modulos.

### Regras (ambos os caminhos)

- Garantir que todos os testes de integracao tenham `@Tag("integration")` e que os demais testes
  unitarios NAO tenham esta tag.
- Caso necessario, renomear os testes movidos/organizados para `<Nome>IT`
  (ex.: `UserControllerTest` -> `UserControllerIT`). Em Java, renomear o arquivo junto com a classe.
- Testes de integracao devem percorrer todo o fluxo real: acessar banco de dados e HTTP.
- Nao deixar `BaseIntegrationTest` duplicado.
- Campos/metodos estaticos (container, WireMock, `@DynamicPropertySource`) vivem direto na classe —
  Java nao tem `companion object`. O `@DynamicPropertySource` deve ser `static`.

### Passo 5.1 - Assets de container (Dockerfile/init.sql)

> ⚠️ Assets de container (ex.: `Dockerfile`/`init.sql` do Oracle) devem viver SEMPRE em
> `src/test/resources/<engine>/` (ex.: `.../resources/oracle/`) — **nunca** em
> `src/main/resources/`. Esta regra vale nos dois caminhos:

- **Multi-modulo:** `src/test/resources/<engine>/` DENTRO do modulo `{base}-integration-tests`.
  Se ja existirem em outro modulo (ex.: `{modulo}-core/src/test/resources/`), MOVE-los
  (`git mv`) para o novo modulo.
- **Single-module:** `src/test/resources/<engine>/` do proprio modulo existente. Se ja existirem
  em outro caminho (ex.: acidentalmente em `src/main/resources/`), MOVE-los (`git mv`) para
  `src/test/resources/<engine>/`.

Em ambos os casos, carregar os assets pelo **classpath** (limpo e explicito) no `BaseIntegrationTest`,
nunca por caminho relativo com `..`:

```java
String oracleImage = new ImageFromDockerfile()
        .withFileFromClasspath("Dockerfile", "oracle/Dockerfile")
        .withFileFromClasspath("init.sql", "oracle/init.sql")
        .get();
```

Assim o modulo (dedicado ou unico) fica autocontido e nao depende do `workingDir` do Gradle nem da
estrutura de outros modulos.

---

## Passo 6 - Regra ArchUnit (entrypoints exigem IT)

No modulo que concentra os testes de integracao (`{base}-integration-tests` em multi-modulo, ou o
proprio modulo unico em single-module):

1. Criar `src/test/resources/archunit.properties` a partir de
   [archunit.properties.template](./templates/archunit.properties.template).
2. Criar `EntrypointHasIntegrationTestRuleIT` a partir de
   [EntrypointHasIntegrationTestRuleIT.java.template](./templates/EntrypointHasIntegrationTestRuleIT.java.template),
   ajustando o package base (`importPackages(...)`) e o import do `BaseIntegrationTest`.

A regra garante que todo entrypoint (`@RestController`, `@KafkaListener`, `@Scheduled`) tenha um IT
`<Nome>IT` que estenda `BaseIntegrationTest`.

---

## Passo 7 - Ajustar skills e instructions do projeto

Procurar por instructions de teste existentes no projeto (ex.: `.github/instructions/*test*.instructions.md`,
`.github/copilot-instructions.md`, `AGENTS.md`):

```bash
grep -rli "integration\|test" .github/instructions AGENTS.md .github/copilot-instructions.md 2>/dev/null
```

- **Se existir** instruction relacionada a testes, atualiza-la para refletir que:
  - Novos testes de integracao devem ser criados no local definido pelo `{integration.target}`
    (modulo dedicado `{base}-integration-tests` ou `src/test/` do modulo unico).
  - Controllers, Endpoints, Consumers e Schedulers DEVEM ter teste de integracao.
  - Os testes de integracao devem percorrer todo o processo, acessando banco de dados e HTTP.
- **Se NAO existir** nenhuma instruction de testes, perguntar ao usuario se deseja criar uma
  (ex.: `.github/instructions/testing-conventions.instructions.md` com `applyTo: "**/*IT.java"`)
  contendo as mesmas regras acima. Criar apenas se confirmado.

Alem disso, documentar a organizacao adotada:

- **Multi-modulo:** incluir a descricao do modulo `{base}-integration-tests` (proposito, nao
  implantavel, onde ficam os ITs, `BaseIntegrationTest`/`IntegrationTestApplication` e como rodar
  `./gradlew integrationTest`) nas instructions do projeto.
- **Single-module:** incluir a descricao de que os ITs vivem em `src/test/` do proprio modulo, sem
  modulo dedicado, e como rodar `./gradlew integrationTest`.
- Atualizar o `README.md` do projeto com uma secao/entrada descrevendo a organizacao adotada e o
  fluxo de testes de integracao.

---

## Passo 8 - Integracoes opcionais (perguntar ao usuario)

Ao final, perguntar se deseja configurar via outras skills (validas nos dois caminhos):

- **quality-setup-testcontainers-arch-kafka** — caso o `BaseIntegrationTest` ainda nao tenha Kafka.
- **quality-setup-testcontainers-oracle** — caso o `BaseIntegrationTest` ainda nao tenha Oracle.
- **quality-setup-testcontainers-redis** — caso o projeto use Redis e o `BaseIntegrationTest` ainda nao o tenha.

E perguntar sobre **WireMock**: caso o projeto dependa de HTTP externo e precise de mock nos testes,
aplicar o bloco de [references/wiremock.md](./references/wiremock.md) quando solicitado.

---

## Checklist de conclusao

- [ ] Estrutura do projeto detectada (multi-modulo ou single-module) e informada ao usuario.
- [ ] Multi-modulo: modulo `{base}-integration-tests` criado e registrado em `settings.gradle`,
      com `jar`/`bootJar` desabilitados. Single-module: nenhum modulo novo criado.
- [ ] Libs pesadas de teste isoladas (removidas dos demais modulos, em multi-modulo; N/A em single-module).
- [ ] Jacoco configurado: agregado entre modulos (multi-modulo) ou simples no proprio modulo (single-module).
- [ ] Tasks `test` (exclui integration) e `integrationTest` (inclui integration) configuradas.
- [ ] Multi-modulo: `IntegrationTestApplication` unico + `application.yml` mesclado. Single-module:
      `BaseIntegrationTest` referencia a Application existente, sem merge.
- [ ] `BaseIntegrationTest` centralizado; ITs organizados/movidos e com `@Tag("integration")`.
- [ ] Assets de container (Dockerfile/init.sql) em `src/test/resources/<engine>/` (nunca em `main/`).
- [ ] `archunit.properties` + `EntrypointHasIntegrationTestRuleIT` criados.
- [ ] Skills/instructions do projeto atualizadas (ou criada instruction de testes, se confirmado).
- [ ] Organizacao adotada documentada nas instructions e no `README.md` do projeto.
- [ ] Perguntado sobre Kafka/Oracle/Redis/WireMock.
