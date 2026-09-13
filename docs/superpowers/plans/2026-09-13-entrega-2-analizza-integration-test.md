# Entrega 2 — `analizza-integration-test` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `analizza-integration-test`, que junta as duas skills de integração atuais (Java e Kotlin), escolhe fonte pela linguagem e build pela DSL do projeto, pergunta banco e layout, e acrescenta guardrails de frontend e regras de projeto.

**Architecture:** Só Markdown e templates de skill. A skill nova mora em `plugins/analizza-skills/skills/analizza-integration-test/` e não toca nas duas antigas (apagadas na Entrega 4). A infraestrutura de teste parte do que o projeto de referência (`documents-eaf-system`) já provou rodando com Spring Boot 4 — não das skills antigas, cujos templates têm defeitos listados abaixo. A prova é executar a skill em quatro alvos descartáveis.

**Tech Stack:** Markdown; Gradle Groovy e Kotlin DSL; Spring Boot 4.1; Testcontainers 2 (`testcontainers-postgresql`, `-oracle-free`, `-mysql`) com `@ServiceConnection`; ArchUnit 1.4 (artefato `archunit`, sem engine JUnit); JaCoCo; Next.js 16 + Vitest + Testing Library; Expo 57 + `jest-expo` + `expo-router/testing-library`.

**Spec:** `docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md` (decisões D1–D5 e seção *Entrega 2*).

## Global Constraints

- Worktree: `/Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test`, branch `feat/analizza-integration-test` (a partir de `origin/main` 4270d14). Nunca no checkout `analizza-marketplace` nem no `documents-eaf-system` (este só é lido, e copiado por `git clone` para o scratchpad na Tarefa 7).
- Raiz da skill (abreviada `$IT` nos comandos): `plugins/analizza-skills/skills/analizza-integration-test`.
- `SCRATCH=/private/tmp/claude-501/-Users-diegolirio-Documents-Github-documents-eaf-system/e13ed494-3d49-436f-b7a1-ccf094781e90/scratchpad`.
- D1: projeto novo → `kotlin` usa Kotlin DSL (`.kts`), `java` usa Groovy. D2: projeto existente → a DSL do build que já existe vence. Fonte escolhido pela linguagem (`templates/backend/source/<linguagem>/`), build pela DSL (`templates/backend/build/<groovy|kts>/`).
- D3: linguagem, banco e layout são detectados e perguntados, um por vez, com o detectado como padrão; a DSL é só informada.
- D4: layout é pergunta — **módulo dedicado `{base}-integration-tests` (recomendado)** ou **aplicar no módulo existente**; single-module recusa o dedicado com a explicação.
- D5: frontend = typecheck + teste unitário (Vitest no `-web`, `jest-expo` no `-mobile`) + checkpoints. Sem Playwright.
- As skills `analizza-java-integration-test` e `analizza-kotlin-integration-test` **não** são alteradas nem apagadas nesta entrega.
- Nada específico do `documents-eaf-system` nos templates e textos (`com.eaf`, `AccessCode`, `DocuSign`, `Azurite`, `eaf-runbook`): genérico, com placeholders.
- Comentários em templates de código e build: português sem acento. Markdown: português com acento.
- Commits em português, 3ª pessoa do presente como o histórico, terminando com `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Sem bump de versão do plugin (é da Entrega 4).

## Decisões deste plano (divergem das skills antigas ou afinam a spec)

Registradas na spec pela Tarefa 1, porque a spec é a autoridade:

- **P1 — IT se separa por nome, não por tag.** `test` exclui `*IT` e `integrationTest` inclui `*IT`, como o projeto de referência faz. A regra ArchUnit já obriga o sufixo `IT`; uma `@Tag("integration")` seria um segundo marcador que alguém esquece. A spec dizia "por `@Tag("integration")`".
- **P2 — ArchUnit sem `archunit-junit5` e sem `FreezingArchRule`.** O engine `archunit-junit5` traz uma JUnit Platform que conflita com a do Boot 4; o freeze com `allowStoreCreation=false` falha num projeto sem store, e um store só esconderia entrypoint sem teste. A regra usa `allowEmptyShould(true)` (projeto novo não tem entrypoint nenhum) e compara `@KafkaListener` pelo nome (compila sem `spring-kafka`). Nome da classe: `EntrypointHasIntegrationTestIT`, o mesmo do template de convenções da new-project.
- **P3 — Container por `@ServiceConnection` num campo estático do `BaseIntegrationTest`**, iniciado na mão (um container para a suíte inteira). Imagens: `postgres:17-alpine`, `gvenzl/oracle-free:23-slim-faststart`, `mysql:8.4`. O `Dockerfile`/`init.sql` próprio de Oracle só é usado se o projeto já o tiver.
- **P4 — `IntegrationTestApplication` só quando o build tem mais de uma `@SpringBootApplication`.** Com uma só, o `BaseIntegrationTest` aponta para ela.
- **P5 — JaCoCo sem limiar.** Relatório de cobertura sim; a verificação de 80% das skills antigas não entra (quebraria todo projeto novo) e a variável `excludeFromCoverageJacoco`, que elas usavam sem definir, passa a ser definida.
- **P6 — O teste `*ApplicationTests` do Initializr vira `ApplicationContextIT`**, estendendo `BaseIntegrationTest` e afirmando que a conexão com o banco do container é válida. Assim `./gradlew test` deixa de precisar de banco.

Defeitos das skills antigas que este plano não herda: `excludeFromCoverageJacoco` indefinida; `import org.springframework.kafka...` que não compila sem `spring-kafka`; `org.springframework.test.web.server.RestTestClient` (pacote inexistente) no template Kotlin; `FreezingArchRule` sem store; oferta de três skills `quality-setup-testcontainers-*` que não existem.

---

## File Structure

| Arquivo (sob `$IT/`) | Responsabilidade | Tarefa |
|---|---|---|
| `SKILL.md` | procedimento completo | 5 |
| `templates/backend/source/kotlin/BaseIntegrationTest.kt.template` | base dos ITs Kotlin | 2 |
| `templates/backend/source/kotlin/TestConfig.kt.template` | dublês de saída Kotlin | 2 |
| `templates/backend/source/kotlin/EntrypointHasIntegrationTestIT.kt.template` | regra ArchUnit Kotlin | 2 |
| `templates/backend/source/kotlin/IntegrationTestApplication.kt.template` | app de teste multi-app Kotlin | 2 |
| `templates/backend/source/kotlin/ApplicationContextIT.kt.template` | IT que substitui o teste do Initializr | 2 |
| `templates/backend/source/java/*.java.template` | os mesmos cinco em Java | 2 |
| `templates/backend/containers.md` | módulo Testcontainers, import, tipo e construtor por banco | 2 |
| `templates/backend/build/kts/integration-tests-module.gradle.kts.template` | build do módulo dedicado (Kotlin DSL) | 3 |
| `templates/backend/build/kts/existing-module.gradle.kts.template` | trechos para o módulo existente (Kotlin DSL) | 3 |
| `templates/backend/build/groovy/integration-tests-module.gradle.template` | build do módulo dedicado (Groovy) | 3 |
| `templates/backend/build/groovy/existing-module.gradle.template` | trechos para o módulo existente (Groovy) | 3 |
| `templates/frontend/web/vitest.config.mts.template` | config do Vitest | 4 |
| `templates/frontend/web/vitest.setup.ts.template` | setup do Testing Library | 4 |
| `templates/frontend/web/page.test.tsx.template` | teste mínimo da tela inicial | 4 |
| `templates/frontend/mobile/tela-inicial-test.tsx.template` | teste mínimo da tela inicial | 4 |
| `templates/frontend/makefile-targets.md` | alvos `test-*` do Makefile | 4 |
| `references/checkpoints-readme.md` | README genérico de `docs/checkpoints/` | 4 |
| `references/claude-md-obligation.md` | bloco da obrigação de runbook no `CLAUDE.md` | 4 |
| `references/project-rules.md` | regras de projeto do Passo 8 | 4 |
| `references/wiremock.md` | WireMock em Java e Kotlin | 4 |
| `docs/superpowers/specs/2026-09-12-…-design.md` (raiz do repo) | P1–P6 registradas | 1 |

---

### Task 1: Registrar P1–P6 na spec

**Files:**
- Modify: `docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md` (seção *Entrega 2*)

**Interfaces:**
- Consumes: nada.
- Produces: a spec como autoridade das decisões P1–P6 para as Tarefas 2–7.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
S=docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md
c() { local ok=0
  grep -q '#### Decisões do plano da Entrega 2' $S || { echo "sem secao de decisoes"; ok=1; }
  grep -q 'includeTestsMatching\|sufixo `IT`' $S || { echo "sem P1"; ok=1; }
  grep -q 'allowEmptyShould' $S || { echo "sem P2"; ok=1; }
  grep -q '@ServiceConnection' $S || { echo "sem P3"; ok=1; }
  grep -q 'mais de uma `@SpringBootApplication`' $S || { echo "sem P4"; ok=1; }
  grep -q 'ApplicationContextIT' $S || { echo "sem P6"; ok=1; }
  grep -q 'por `@Tag("integration")`' $S && { echo "ainda cita tag"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: seis linhas "sem …", "ainda cita tag", `EXIT=1`.

- [ ] **Step 3: Editar a spec**

Em *Entrega 2 → Fluxo → Passos 2–6 — Backend*, trocar "jacoco + tasks `test`/`integrationTest` por `@Tag("integration")`" por "jacoco + tasks `test`/`integrationTest` separadas pelo sufixo `IT`".

Logo antes de `#### Limpeza em relação às skills antigas`, inserir:

```markdown
#### Decisões do plano da Entrega 2

Tomadas ao planejar, lendo as skills antigas ao lado da infraestrutura de teste que o projeto de
referência já roda com Spring Boot 4:

- **P1 — IT se separa por nome.** `test` exclui `*IT` e `integrationTest` inclui `*IT`
  (`excludeTestsMatching`/`includeTestsMatching`). A regra ArchUnit já obriga o sufixo `IT`; uma
  tag seria um segundo marcador para esquecer.
- **P2 — ArchUnit com o artefato `archunit`, sem `archunit-junit5` e sem `FreezingArchRule`.** O
  engine do `archunit-junit5` conflita com a JUnit Platform do Boot 4; freeze sem store falha e,
  com store, esconde entrypoint sem teste. A regra usa `allowEmptyShould(true)` — projeto novo não
  tem entrypoint — e compara `@KafkaListener` pelo nome, para compilar sem `spring-kafka`. A classe
  se chama `EntrypointHasIntegrationTestIT`, como no template de convenções da new-project.
- **P3 — Um container de banco para a suíte inteira**, num campo estático do `BaseIntegrationTest`
  com `@ServiceConnection`, iniciado na mão. Imagens padrão: `postgres:17-alpine`,
  `gvenzl/oracle-free:23-slim-faststart`, `mysql:8.4`; `Dockerfile` próprio de Oracle só se o
  projeto já tiver um.
- **P4 — `IntegrationTestApplication` só quando o build tem mais de uma `@SpringBootApplication`.**
  Com uma, o `BaseIntegrationTest` aponta direto para ela.
- **P5 — JaCoCo gera relatório, sem limiar de cobertura.** Um mínimo de 80% quebraria todo projeto
  novo; quem quiser um limiar o acrescenta depois.
- **P6 — O teste `*ApplicationTests` gerado pelo Initializr vira `ApplicationContextIT`**, estendendo
  `BaseIntegrationTest` e afirmando que a conexão com o banco do container é válida, para que
  `./gradlew test` não precise mais de banco.
```

- [ ] **Step 4: Rodar a checagem e ver passar** — `EXIT=0`.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-09-12-analizza-integration-test-e-camadas-design.md
git commit -m "Registra na spec as decisoes do plano da analizza-integration-test

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Templates de fonte do backend e tabela de containers

**Files:**
- Create: `$IT/templates/backend/source/kotlin/{BaseIntegrationTest.kt,TestConfig.kt,EntrypointHasIntegrationTestIT.kt,IntegrationTestApplication.kt,ApplicationContextIT.kt}.template`
- Create: `$IT/templates/backend/source/java/{BaseIntegrationTest.java,TestConfig.java,EntrypointHasIntegrationTestIT.java,IntegrationTestApplication.java,ApplicationContextIT.java}.template`
- Create: `$IT/templates/backend/containers.md`

**Interfaces:**
- Consumes: nada.
- Produces: placeholders que o `SKILL.md` (Tarefa 5) substitui: `{base-package}`, `{app-class}` (nome simples da classe de aplicação usada pelo contexto), `{app-package}` (pacote dela), `{container-import}`, `{container-type}`, `{container-new}`. Pacotes gerados: `{base-package}.support` (base, `TestConfig`, `ApplicationContextIT`) e `{base-package}.architecture` (regra). A Tarefa 3 usa o módulo Testcontainers de `containers.md` como `{testcontainers-db-module}`.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
IT=plugins/analizza-skills/skills/analizza-integration-test
c() { local ok=0 d=$IT/templates/backend/source
  for n in BaseIntegrationTest TestConfig EntrypointHasIntegrationTestIT IntegrationTestApplication ApplicationContextIT; do
    [ -f $d/kotlin/$n.kt.template ] || { echo "falta kotlin/$n"; ok=1; }
    [ -f $d/java/$n.java.template ] || { echo "falta java/$n"; ok=1; }
  done
  [ -f $IT/templates/backend/containers.md ] || { echo "falta containers.md"; ok=1; }
  grep -rq 'org.springframework.kafka' $d 2>/dev/null && { echo "import de kafka"; ok=1; }
  grep -rq 'FreezingArchRule\|@Tag' $d 2>/dev/null && { echo "freeze ou tag"; ok=1; }
  grep -rq 'test.web.server.RestTestClient' $d 2>/dev/null && { echo "pacote errado de RestTestClient"; ok=1; }
  [ "$(grep -rl 'allowEmptyShould(true)' $d 2>/dev/null | wc -l)" -eq 2 ] || { echo "allowEmptyShould ausente"; ok=1; }
  [ "$(grep -rl 'ServiceConnection' $d 2>/dev/null | wc -l)" -eq 2 ] || { echo "ServiceConnection ausente"; ok=1; }
  grep -rqiE 'com\.eaf|AccessCode|DocuSign|Azurite' $d $IT/templates/backend/containers.md 2>/dev/null && { echo "nome do projeto de referencia"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: "falta …" para os onze arquivos e `EXIT=1`.

- [ ] **Step 3: `kotlin/BaseIntegrationTest.kt.template`**

```kotlin
package {base-package}.support

import {app-package}.{app-class}
import org.junit.jupiter.api.BeforeEach
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.boot.test.web.server.LocalServerPort
import org.springframework.boot.testcontainers.service.connection.ServiceConnection
import org.springframework.context.annotation.Import
import org.springframework.http.client.JdkClientHttpRequestFactory
import org.springframework.test.web.servlet.client.RestTestClient
import {container-import}

/**
 * Base de todo teste de integracao: toda classe terminada em IT a estende.
 *
 * Um container de banco para a suite inteira, iniciado na mao e sem @Container:
 * o ciclo do @Container e por classe e reiniciaria o banco a cada IT. O Ryuk do
 * Testcontainers derruba o container no fim do build.
 */
@SpringBootTest(
    classes = [{app-class}::class],
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
)
@Import(TestConfig::class)
abstract class BaseIntegrationTest {

    @LocalServerPort
    private var port: Int = 0

    protected lateinit var http: RestTestClient

    @BeforeEach
    fun prepararCliente() {
        // O JdkClientHttpRequestFactory vai explicito porque bindToServer() sem
        // argumento escolhe o cliente HTTP pelo classpath: uma dependencia nova
        // pode trocar o transporte do teste -- e o retry dele -- sem aviso.
        http = RestTestClient.bindToServer(JdkClientHttpRequestFactory())
            .baseUrl("http://localhost:$port")
            .build()
    }

    companion object {
        // O @field: manda a anotacao para o campo estatico que o Spring
        // inspeciona, e nao para a property, qualquer que seja o
        // -Xannotation-default-target do modulo.
        @JvmStatic
        @field:ServiceConnection
        val database: {container-type} = {container-new}.also { it.start() }
    }
}
```

- [ ] **Step 4: `java/BaseIntegrationTest.java.template`**

```java
package {base-package}.support;

import {app-package}.{app-class};
import org.junit.jupiter.api.BeforeEach;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Import;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.test.web.servlet.client.RestTestClient;
import {container-import};

/**
 * Base de todo teste de integracao: toda classe terminada em IT a estende.
 *
 * <p>Um container de banco para a suite inteira, iniciado na mao e sem
 * {@code @Container}: o ciclo do {@code @Container} e por classe e reiniciaria
 * o banco a cada IT. O Ryuk do Testcontainers derruba o container no fim do build.
 */
@SpringBootTest(
        classes = {app-class}.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT
)
@Import(TestConfig.class)
public abstract class BaseIntegrationTest {

    @ServiceConnection
    protected static final {container-type} DATABASE = {container-new};

    static {
        DATABASE.start();
    }

    @LocalServerPort
    private int port;

    protected RestTestClient http;

    @BeforeEach
    void prepararCliente() {
        // O JdkClientHttpRequestFactory vai explicito porque bindToServer() sem
        // argumento escolhe o cliente HTTP pelo classpath: uma dependencia nova
        // pode trocar o transporte do teste -- e o retry dele -- sem aviso.
        http = RestTestClient.bindToServer(new JdkClientHttpRequestFactory())
                .baseUrl("http://localhost:" + port)
                .build();
    }
}
```

- [ ] **Step 5: `kotlin/TestConfig.kt.template`**

```kotlin
package {base-package}.support

import org.springframework.boot.test.context.TestConfiguration

/**
 * Dubles dos servicos de saida que nao tem container: e-mail, gateway de
 * terceiro. Cada um entra como @Bean @Primary e guarda em memoria o que
 * recebeu, para o teste afirmar sobre isso -- nenhuma mensagem nem chamada sai
 * da suite. O banco, e tudo que tem container de verdade, nao ganha duble: o
 * teste de integracao existe para exercita-los.
 *
 * Forma de um duble, para uma porta `MailService` do -core:
 *
 *     class InMemoryMailService : MailService {
 *         val enviadas = mutableListOf<MailMessage>()
 *         override fun send(message: MailMessage) { enviadas += message }
 *     }
 *
 *     @Bean @Primary
 *     fun mailService() = InMemoryMailService()
 *
 * O estado de um duble e da suite inteira (o contexto e compartilhado): limpe-o
 * num @BeforeEach do BaseIntegrationTest.
 */
@TestConfiguration(proxyBeanMethods = false)
class TestConfig {
{doubles}
}
```

- [ ] **Step 6: `java/TestConfig.java.template`**

```java
package {base-package}.support;

import org.springframework.boot.test.context.TestConfiguration;

/**
 * Dubles dos servicos de saida que nao tem container: e-mail, gateway de
 * terceiro. Cada um entra como {@code @Bean @Primary} e guarda em memoria o que
 * recebeu, para o teste afirmar sobre isso -- nenhuma mensagem nem chamada sai
 * da suite. O banco, e tudo que tem container de verdade, nao ganha duble: o
 * teste de integracao existe para exercita-los.
 *
 * <p>Forma de um duble, para uma porta {@code MailService} do -core:
 *
 * <pre>
 * static class InMemoryMailService implements MailService {
 *     final List&lt;MailMessage&gt; enviadas = new ArrayList&lt;&gt;();
 *     public void send(MailMessage message) { enviadas.add(message); }
 * }
 *
 * &#64;Bean &#64;Primary
 * InMemoryMailService mailService() { return new InMemoryMailService(); }
 * </pre>
 *
 * <p>O estado de um duble e da suite inteira (o contexto e compartilhado):
 * limpe-o num {@code @BeforeEach} do BaseIntegrationTest.
 */
@TestConfiguration(proxyBeanMethods = false)
public class TestConfig {
{doubles}
}
```

- [ ] **Step 7: `kotlin/EntrypointHasIntegrationTestIT.kt.template`**

```kotlin
package {base-package}.architecture

import com.tngtech.archunit.base.DescribedPredicate
import com.tngtech.archunit.core.domain.JavaClass
import com.tngtech.archunit.core.domain.JavaClasses
import com.tngtech.archunit.core.importer.ClassFileImporter
import com.tngtech.archunit.lang.ArchCondition
import com.tngtech.archunit.lang.ConditionEvents
import com.tngtech.archunit.lang.SimpleConditionEvent
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes
import {base-package}.support.BaseIntegrationTest
import org.junit.jupiter.api.Test
import org.springframework.scheduling.annotation.Scheduled
import org.springframework.web.bind.annotation.RestController

/**
 * Um unico trabalho: todo entrypoint -- @RestController, metodo @Scheduled ou
 * metodo @KafkaListener -- precisa de um <Nome>IT que estenda BaseIntegrationTest.
 * Um job entra pelo mesmo motivo que um controller, e com mais razao: ninguem
 * recebe um 500 quando um agendamento para de rodar.
 *
 * Sem FreezingArchRule: um store de freeze so viraria lugar de esconder
 * entrypoint sem teste. Sem archunit-junit5 (@ArchTest): aquele engine traz uma
 * JUnit Platform que conflita com a do Spring Boot 4; um @Test comum basta.
 *
 * @KafkaListener e comparado pelo nome para a regra compilar sem spring-kafka.
 * allowEmptyShould(true) porque um projeto novo ainda nao tem entrypoint.
 */
class EntrypointHasIntegrationTestIT {

    private val importadas: JavaClasses = ClassFileImporter().importPackages("{base-package}")

    private val saoEntrypoints: DescribedPredicate<JavaClass> =
        DescribedPredicate.describe("sao entrypoints (@RestController, @Scheduled ou @KafkaListener)") { classe ->
            classe.isAnnotatedWith(RestController::class.java) ||
                classe.methods.any { it.isAnnotatedWith(Scheduled::class.java) || it.isAnnotatedWith(KAFKA_LISTENER) }
        }

    private fun temIntegrationTest(todas: JavaClasses) =
        object : ArchCondition<JavaClass>("ter um <Nome>IT que estenda BaseIntegrationTest") {
            override fun check(entrypoint: JavaClass, eventos: ConditionEvents) {
                val esperado = "${entrypoint.simpleName}IT"
                val achou = todas.any { it.simpleName == esperado && it.isAssignableTo(BaseIntegrationTest::class.java) }
                if (achou) {
                    eventos.add(SimpleConditionEvent.satisfied(entrypoint, "$esperado existe"))
                } else {
                    eventos.add(
                        SimpleConditionEvent.violated(
                            entrypoint,
                            "${entrypoint.name} nao tem '$esperado' estendendo BaseIntegrationTest",
                        ),
                    )
                }
            }
        }

    @Test
    fun `todo entrypoint tem teste de integracao`() {
        classes()
            .that(saoEntrypoints)
            .should(temIntegrationTest(importadas))
            .allowEmptyShould(true)
            .because("todo entrypoint precisa de ao menos um teste de integracao")
            .check(importadas)
    }

    private companion object {
        const val KAFKA_LISTENER = "org.springframework.kafka.annotation.KafkaListener"
    }
}
```

- [ ] **Step 8: `java/EntrypointHasIntegrationTestIT.java.template`**

```java
package {base-package}.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import {base-package}.support.BaseIntegrationTest;
import org.junit.jupiter.api.Test;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.RestController;

/**
 * Um unico trabalho: todo entrypoint -- {@code @RestController}, metodo
 * {@code @Scheduled} ou metodo {@code @KafkaListener} -- precisa de um
 * {@code <Nome>IT} que estenda BaseIntegrationTest. Um job entra pelo mesmo
 * motivo que um controller, e com mais razao: ninguem recebe um 500 quando um
 * agendamento para de rodar.
 *
 * <p>Sem FreezingArchRule: um store de freeze so viraria lugar de esconder
 * entrypoint sem teste. Sem archunit-junit5 ({@code @ArchTest}): aquele engine
 * traz uma JUnit Platform que conflita com a do Spring Boot 4; um {@code @Test}
 * comum basta.
 *
 * <p>{@code @KafkaListener} e comparado pelo nome para a regra compilar sem
 * spring-kafka. {@code allowEmptyShould(true)} porque um projeto novo ainda nao
 * tem entrypoint.
 */
class EntrypointHasIntegrationTestIT {

    private static final String KAFKA_LISTENER = "org.springframework.kafka.annotation.KafkaListener";

    private final JavaClasses importadas = new ClassFileImporter().importPackages("{base-package}");

    private final DescribedPredicate<JavaClass> saoEntrypoints = DescribedPredicate.describe(
            "sao entrypoints (@RestController, @Scheduled ou @KafkaListener)",
            classe -> classe.isAnnotatedWith(RestController.class)
                    || classe.getMethods().stream().anyMatch(m ->
                            m.isAnnotatedWith(Scheduled.class) || m.isAnnotatedWith(KAFKA_LISTENER)));

    private ArchCondition<JavaClass> temIntegrationTest(JavaClasses todas) {
        return new ArchCondition<>("ter um <Nome>IT que estenda BaseIntegrationTest") {
            @Override
            public void check(JavaClass entrypoint, ConditionEvents eventos) {
                String esperado = entrypoint.getSimpleName() + "IT";
                boolean achou = todas.stream().anyMatch(c ->
                        c.getSimpleName().equals(esperado) && c.isAssignableTo(BaseIntegrationTest.class));
                if (achou) {
                    eventos.add(SimpleConditionEvent.satisfied(entrypoint, esperado + " existe"));
                } else {
                    eventos.add(SimpleConditionEvent.violated(entrypoint,
                            entrypoint.getName() + " nao tem '" + esperado + "' estendendo BaseIntegrationTest"));
                }
            }
        };
    }

    @Test
    void todoEntrypointTemTesteDeIntegracao() {
        classes()
                .that(saoEntrypoints)
                .should(temIntegrationTest(importadas))
                .allowEmptyShould(true)
                .because("todo entrypoint precisa de ao menos um teste de integracao")
                .check(importadas);
    }
}
```

- [ ] **Step 9: `kotlin/IntegrationTestApplication.kt.template`**

```kotlin
package {base-package}

import org.springframework.boot.SpringBootConfiguration
import org.springframework.boot.autoconfigure.AutoConfigurationExcludeFilter
import org.springframework.boot.autoconfigure.EnableAutoConfiguration
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.TypeExcludeFilter
import org.springframework.context.annotation.ComponentScan
import org.springframework.context.annotation.FilterType

/**
 * So existe quando o build tem mais de uma @SpringBootApplication: junta o
 * component scan de todas num contexto so para os testes de integracao.
 *
 * Nao e @SpringBootApplication de proposito: o scan dela nao aceita filtro de
 * exclusao, e as aplicacoes originais precisam ficar fora dele para nao
 * aplicarem a autoconfiguracao uma segunda vez.
 */
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(
    basePackages = ["{base-package}"],
    excludeFilters = [
        ComponentScan.Filter(type = FilterType.CUSTOM, classes = [TypeExcludeFilter::class]),
        ComponentScan.Filter(type = FilterType.CUSTOM, classes = [AutoConfigurationExcludeFilter::class]),
        ComponentScan.Filter(type = FilterType.ANNOTATION, classes = [SpringBootApplication::class]),
    ],
)
class IntegrationTestApplication
```

- [ ] **Step 10: `java/IntegrationTestApplication.java.template`**

```java
package {base-package};

import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.AutoConfigurationExcludeFilter;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.TypeExcludeFilter;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.FilterType;

/**
 * So existe quando o build tem mais de uma {@code @SpringBootApplication}: junta
 * o component scan de todas num contexto so para os testes de integracao.
 *
 * <p>Nao e {@code @SpringBootApplication} de proposito: o scan dela nao aceita
 * filtro de exclusao, e as aplicacoes originais precisam ficar fora dele para
 * nao aplicarem a autoconfiguracao uma segunda vez.
 */
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(
        basePackages = "{base-package}",
        excludeFilters = {
                @ComponentScan.Filter(type = FilterType.CUSTOM, classes = TypeExcludeFilter.class),
                @ComponentScan.Filter(type = FilterType.CUSTOM, classes = AutoConfigurationExcludeFilter.class),
                @ComponentScan.Filter(type = FilterType.ANNOTATION, classes = SpringBootApplication.class)
        }
)
public class IntegrationTestApplication {
}
```

- [ ] **Step 11: `kotlin/ApplicationContextIT.kt.template`**

```kotlin
package {base-package}.support

import javax.sql.DataSource
import kotlin.test.assertTrue
import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Autowired

/**
 * Substitui o teste de contexto que o Spring Initializr gera: o mesmo "o
 * contexto sobe", agora contra o banco do container, e fora do ./gradlew test,
 * que deixa de precisar de banco.
 */
class ApplicationContextIT : BaseIntegrationTest() {

    @Autowired
    private lateinit var dataSource: DataSource

    @Test
    fun `o contexto sobe conectado ao banco do container`() {
        dataSource.connection.use { conexao ->
            assertTrue(conexao.isValid(2), "a conexao com o banco do container nao e valida")
        }
    }
}
```

- [ ] **Step 12: `java/ApplicationContextIT.java.template`**

```java
package {base-package}.support;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * Substitui o teste de contexto que o Spring Initializr gera: o mesmo "o
 * contexto sobe", agora contra o banco do container, e fora do ./gradlew test,
 * que deixa de precisar de banco.
 */
class ApplicationContextIT extends BaseIntegrationTest {

    @Autowired
    private DataSource dataSource;

    @Test
    void oContextoSobeConectadoAoBancoDoContainer() throws Exception {
        try (Connection conexao = dataSource.getConnection()) {
            assertTrue(conexao.isValid(2), "a conexao com o banco do container nao e valida");
        }
    }
}
```

- [ ] **Step 13: `containers.md`**

````markdown
# Container de banco por banco escolhido

Valores que substituem os placeholders do `BaseIntegrationTest` e o
`{testcontainers-db-module}` do build. Todos os artefatos são gerenciados pelo
BOM do Spring Boot: nenhum leva versão.

| Banco | `{testcontainers-db-module}` | `{container-import}` | `{container-type}` |
|---|---|---|---|
| `postgres` | `org.testcontainers:testcontainers-postgresql` | `org.testcontainers.postgresql.PostgreSQLContainer` | `PostgreSQLContainer` |
| `oracle` | `org.testcontainers:testcontainers-oracle-free` | `org.testcontainers.oracle.OracleContainer` | `OracleContainer` |
| `mysql` | `org.testcontainers:testcontainers-mysql` | `org.testcontainers.mysql.MySQLContainer` | `MySQLContainer` |

## `{container-new}`

| Banco | Kotlin | Java |
|---|---|---|
| `postgres` | `PostgreSQLContainer("{image}")` | `new PostgreSQLContainer("{image}")` |
| `oracle` | `OracleContainer("{image}")` | `new OracleContainer("{image}")` |
| `mysql` | `MySQLContainer("{image}")` | `new MySQLContainer("{image}")` |

`{image}`: a mesma imagem e tag que o `docker-compose.yml` do projeto usa para
aquele banco, se ele tiver uma — o teste roda contra a versão que o
desenvolvedor usa. Sem `docker-compose`, o padrão:

| Banco | Imagem padrão |
|---|---|
| `postgres` | `postgres:17-alpine` |
| `oracle` | `gvenzl/oracle-free:23-slim-faststart` |
| `mysql` | `mysql:8.4` |

## Oracle com `Dockerfile` próprio

Só quando o projeto **já tem** um `Dockerfile` (e `init.sql`) de Oracle para
testes. Ele fica em `src/test/resources/oracle/` do módulo que recebe os ITs —
nunca em `src/main/resources/` — e é carregado pelo classpath, sem caminho
relativo:

```kotlin
// {container-import} ganha tambem:
//   org.testcontainers.images.builder.ImageFromDockerfile
//   org.testcontainers.utility.DockerImageName
//   java.time.Duration
OracleContainer(
    DockerImageName.parse(
        ImageFromDockerfile()
            .withFileFromClasspath("Dockerfile", "oracle/Dockerfile")
            .withFileFromClasspath("init.sql", "oracle/init.sql")
            .get(),
    ).asCompatibleSubstituteFor("gvenzl/oracle-free"),
).withStartupTimeout(Duration.ofMinutes(6))
```

```java
new OracleContainer(
        DockerImageName.parse(new ImageFromDockerfile()
                .withFileFromClasspath("Dockerfile", "oracle/Dockerfile")
                .withFileFromClasspath("init.sql", "oracle/init.sql")
                .get())
                .asCompatibleSubstituteFor("gvenzl/oracle-free"))
        .withStartupTimeout(Duration.ofMinutes(6))
```

Se o arquivo estiver em `src/main/resources/`, mova-o com `git mv` antes.

## Outro banco

A skill não adivinha módulo do Testcontainers. Diga ao usuário que o banco não
está nesta tabela, peça o módulo (`org.testcontainers:testcontainers-<banco>`)
e a classe do container, e só siga com os dois confirmados.

## Kafka, Redis e outros serviços

Não fazem parte desta skill. Para acrescentar um, siga a mesma forma do banco:
um campo estático no `BaseIntegrationTest`, iniciado na mão, com
`@ServiceConnection` quando o Spring Boot conhecer o serviço e
`@DynamicPropertySource` quando não conhecer.
````

- [ ] **Step 14: Rodar a checagem e ver passar** — `EXIT=0`.

- [ ] **Step 15: Commit**

```bash
git add $IT/templates/backend/source $IT/templates/backend/containers.md
git commit -m "Cria os templates de fonte dos testes de integracao em Java e Kotlin

Base com um container por suite via @ServiceConnection, regra ArchUnit
sem freeze e sem engine JUnit, duble de saida e o IT de contexto.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Templates de build por DSL

**Files:**
- Create: `$IT/templates/backend/build/kts/integration-tests-module.gradle.kts.template`
- Create: `$IT/templates/backend/build/kts/existing-module.gradle.kts.template`
- Create: `$IT/templates/backend/build/groovy/integration-tests-module.gradle.template`
- Create: `$IT/templates/backend/build/groovy/existing-module.gradle.template`

**Interfaces:**
- Consumes: `{testcontainers-db-module}` (Tarefa 2, `containers.md`).
- Produces: placeholders `{group}`, `{java-version}`, `{boot-version}`, `{src-dir}` (`kotlin` ou `java`), `{project-dependencies}`, `{coverage-modules}`; tarefas Gradle `test`, `integrationTest`, `integrationTestCoverageReport` (módulo dedicado) e `jacocoTestReport` (módulo existente). Blocos `<!-- se kotlin -->`/`<!-- se java -->` para a linguagem do fonte.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
IT=plugins/analizza-skills/skills/analizza-integration-test
c() { local ok=0 b=$IT/templates/backend/build
  for f in kts/integration-tests-module.gradle.kts kts/existing-module.gradle.kts groovy/integration-tests-module.gradle groovy/existing-module.gradle; do
    [ -f $b/$f.template ] || { echo "falta $f"; ok=1; continue; }
    grep -q "includeTestsMatching" $b/$f.template || { echo "$f sem includeTestsMatching"; ok=1; }
    grep -q "excludeFromCoverageJacoco *=" $b/$f.template || grep -q "val excludeFromCoverageJacoco\|def excludeFromCoverageJacoco" $b/$f.template || { echo "$f sem definicao de excludeFromCoverageJacoco"; ok=1; }
    grep -q "{testcontainers-db-module}" $b/$f.template || { echo "$f sem modulo do banco"; ok=1; }
    grep -qE "archunit-junit5|excludeTags|includeTags|minimum *=" $b/$f.template && { echo "$f com tag, junit5 ou limiar"; ok=1; }
  done
  grep -q '(' $b/groovy/*.template 2>/dev/null && grep -qE 'testImplementation\(' $b/groovy/*.template && { echo "sintaxe kts no groovy"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: quatro "falta …", `EXIT=1`.

- [ ] **Step 3: `kts/integration-tests-module.gradle.kts.template`**

```kotlin
// build.gradle.kts do modulo {base}-integration-tests.
// Nao e implantavel: nao aplica o plugin do Spring Boot e nao gera jar. So
// compila e roda os testes de integracao contra os modulos de producao.
plugins {
<!-- se kotlin -->
    kotlin("jvm")
    kotlin("plugin.spring")
<!-- fim se kotlin -->
<!-- se java -->
    java
<!-- fim se java -->
    jacoco
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

// Sem o plugin do Boot, o BOM vem importado a mao para versionar starters e
// modulos do Testcontainers.
dependencyManagement {
    imports {
        mavenBom("org.springframework.boot:spring-boot-dependencies:{boot-version}")
    }
}

dependencies {
    // Um testImplementation(project(":<modulo>")) por modulo de producao do build.
{project-dependencies}

    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.boot:spring-boot-testcontainers")
    // spring-web e spring-context entram explicitos: os modulos de producao os
    // declaram como implementation, que nao chega ao classpath de compilacao
    // deste modulo, e a base e a regra ArchUnit importam classes dos dois.
    testImplementation("org.springframework:spring-web")
    testImplementation("org.springframework:spring-context")
    testImplementation("org.testcontainers:testcontainers-junit-jupiter")
    testImplementation("{testcontainers-db-module}")
    testImplementation("com.tngtech.archunit:archunit:1.4.1")
<!-- se kotlin -->
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
<!-- fim se kotlin -->
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.named<Jar>("jar") {
    enabled = false
}

// Neste modulo tudo e integracao; `test` fica vazio sem falhar.
tasks.named<Test>("test") {
    useJUnitPlatform()
    filter {
        excludeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
}

val integrationTest = tasks.register<Test>("integrationTest") {
    description = "Testes de integracao (classes *IT), sobre Testcontainers."
    group = "verification"
    testClassesDirs = sourceSets.test.get().output.classesDirs
    classpath = sourceSets.test.get().runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
    shouldRunAfter(tasks.named("test"))
}

// Classes que nao tem comportamento a cobrir: ponto de entrada e configuracao.
val excludeFromCoverageJacoco = listOf("**/*Application*", "**/configuration/**")

// Um testImplementation(project(...)) acima corresponde a uma entrada aqui.
val modulosCobertos = listOf({coverage-modules})

tasks.register<JacocoReport>("integrationTestCoverageReport") {
    description = "Cobertura dos testes de integracao sobre os modulos de producao."
    group = "verification"
    dependsOn(integrationTest)
    executionData(integrationTest.get())
    sourceDirectories.from(modulosCobertos.map { project(it).file("src/main/{src-dir}") })
    classDirectories.from(
        modulosCobertos.map { modulo ->
            project(modulo).layout.buildDirectory.dir("classes/{src-dir}/main").map { dir ->
                dir.asFileTree.matching { exclude(excludeFromCoverageJacoco) }
            }
        },
    )
    reports {
        xml.required = true
        html.required = true
    }
}
```

- [ ] **Step 4: `kts/existing-module.gradle.kts.template`**

```kotlin
// Trechos para o build.gradle.kts do modulo que recebe os testes de integracao
// (o -api de um projeto -api/-core, ou o modulo unico). Mesclar no arquivo
// existente: acrescentar ao plugins {} e ao dependencies {} que ja existem, e
// substituir qualquer configuracao anterior das tasks test e jacocoTestReport.

plugins {
    jacoco
}

dependencies {
    testImplementation("org.springframework.boot:spring-boot-testcontainers")
    testImplementation("org.testcontainers:testcontainers-junit-jupiter")
    testImplementation("{testcontainers-db-module}")
    testImplementation("com.tngtech.archunit:archunit:1.4.1")
}

tasks.named<Test>("test") {
    useJUnitPlatform()
    description = "Testes unitarios. Nao sobe container nem banco."
    filter {
        excludeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
}

val integrationTest = tasks.register<Test>("integrationTest") {
    description = "Testes de integracao (classes *IT), sobre Testcontainers."
    group = "verification"
    testClassesDirs = sourceSets.test.get().output.classesDirs
    classpath = sourceSets.test.get().runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching("*IT")
        isFailOnNoMatchingTests = false
    }
    shouldRunAfter(tasks.named("test"))
}

// Classes que nao tem comportamento a cobrir: ponto de entrada e configuracao.
val excludeFromCoverageJacoco = listOf("**/*Application*", "**/configuration/**")

tasks.named<JacocoReport>("jacocoTestReport") {
    mustRunAfter(tasks.named("test"), integrationTest)
    // Junta a cobertura de `test` e de `integrationTest`, do que tiver rodado.
    executionData.setFrom(
        fileTree(layout.buildDirectory).include("jacoco/test.exec", "jacoco/integrationTest.exec"),
    )
    classDirectories.setFrom(
        sourceSets.main.get().output.asFileTree.matching { exclude(excludeFromCoverageJacoco) },
    )
    reports {
        xml.required = true
        html.required = true
    }
}
```

- [ ] **Step 5: `groovy/integration-tests-module.gradle.template`**

```groovy
// build.gradle do modulo {base}-integration-tests.
// Nao e implantavel: nao aplica o plugin do Spring Boot e nao gera jar. So
// compila e roda os testes de integracao contra os modulos de producao.
plugins {
<!-- se kotlin -->
    id 'org.jetbrains.kotlin.jvm'
    id 'org.jetbrains.kotlin.plugin.spring'
<!-- fim se kotlin -->
<!-- se java -->
    id 'java'
<!-- fim se java -->
    id 'jacoco'
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

// Sem o plugin do Boot, o BOM vem importado a mao para versionar starters e
// modulos do Testcontainers.
dependencyManagement {
    imports {
        mavenBom "org.springframework.boot:spring-boot-dependencies:{boot-version}"
    }
}

dependencies {
    // Um testImplementation project(':<modulo>') por modulo de producao do build.
{project-dependencies}

    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    // spring-web e spring-context entram explicitos: os modulos de producao os
    // declaram como implementation, que nao chega ao classpath de compilacao
    // deste modulo, e a base e a regra ArchUnit importam classes dos dois.
    testImplementation 'org.springframework:spring-web'
    testImplementation 'org.springframework:spring-context'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation '{testcontainers-db-module}'
    testImplementation 'com.tngtech.archunit:archunit:1.4.1'
<!-- se kotlin -->
    testImplementation 'org.jetbrains.kotlin:kotlin-test-junit5'
<!-- fim se kotlin -->
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

tasks.named('jar') {
    enabled = false
}

// Neste modulo tudo e integracao; `test` fica vazio sem falhar.
tasks.named('test', Test) {
    useJUnitPlatform()
    filter {
        excludeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
}

def integrationTest = tasks.register('integrationTest', Test) {
    description = 'Testes de integracao (classes *IT), sobre Testcontainers.'
    group = 'verification'
    testClassesDirs = sourceSets.test.output.classesDirs
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
    shouldRunAfter tasks.named('test')
}

// Classes que nao tem comportamento a cobrir: ponto de entrada e configuracao.
def excludeFromCoverageJacoco = ['**/*Application*', '**/configuration/**']

// Um testImplementation project(...) acima corresponde a uma entrada aqui.
def modulosCobertos = [{coverage-modules}]

tasks.register('integrationTestCoverageReport', JacocoReport) {
    description = 'Cobertura dos testes de integracao sobre os modulos de producao.'
    group = 'verification'
    dependsOn integrationTest
    executionData integrationTest.get()
    sourceDirectories.from(modulosCobertos.collect { project(it).file('src/main/{src-dir}') })
    classDirectories.from(modulosCobertos.collect { modulo ->
        project(modulo).layout.buildDirectory.dir('classes/{src-dir}/main').map { dir ->
            dir.asFileTree.matching { exclude excludeFromCoverageJacoco }
        }
    })
    reports {
        xml.required = true
        html.required = true
    }
}
```

- [ ] **Step 6: `groovy/existing-module.gradle.template`**

```groovy
// Trechos para o build.gradle do modulo que recebe os testes de integracao
// (o -api de um projeto -api/-core, ou o modulo unico). Mesclar no arquivo
// existente: acrescentar ao plugins {} e ao dependencies {} que ja existem, e
// substituir qualquer configuracao anterior das tasks test e jacocoTestReport.

plugins {
    id 'jacoco'
}

dependencies {
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:testcontainers-junit-jupiter'
    testImplementation '{testcontainers-db-module}'
    testImplementation 'com.tngtech.archunit:archunit:1.4.1'
}

tasks.named('test', Test) {
    useJUnitPlatform()
    description = 'Testes unitarios. Nao sobe container nem banco.'
    filter {
        excludeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
}

def integrationTest = tasks.register('integrationTest', Test) {
    description = 'Testes de integracao (classes *IT), sobre Testcontainers.'
    group = 'verification'
    testClassesDirs = sourceSets.test.output.classesDirs
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform()
    filter {
        includeTestsMatching '*IT'
        failOnNoMatchingTests = false
    }
    shouldRunAfter tasks.named('test')
}

// Classes que nao tem comportamento a cobrir: ponto de entrada e configuracao.
def excludeFromCoverageJacoco = ['**/*Application*', '**/configuration/**']

tasks.named('jacocoTestReport', JacocoReport) {
    mustRunAfter tasks.named('test'), integrationTest
    // Junta a cobertura de `test` e de `integrationTest`, do que tiver rodado.
    executionData.setFrom(fileTree(layout.buildDirectory).include('jacoco/test.exec', 'jacoco/integrationTest.exec'))
    classDirectories.setFrom(sourceSets.main.output.asFileTree.matching { exclude excludeFromCoverageJacoco })
    reports {
        xml.required = true
        html.required = true
    }
}
```

- [ ] **Step 7: Rodar a checagem e ver passar** — `EXIT=0`. (A validade real destes builds só aparece nas Tarefas 6 e 7.)

- [ ] **Step 8: Commit**

```bash
git add $IT/templates/backend/build
git commit -m "Cria os builds dos testes de integracao em Groovy e Kotlin DSL

Modulo dedicado e trechos para o modulo existente, com test e
integrationTest separados pelo sufixo IT e cobertura sem limiar.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Frontend e referências de projeto

**Files:**
- Create: `$IT/templates/frontend/web/vitest.config.mts.template`
- Create: `$IT/templates/frontend/web/vitest.setup.ts.template`
- Create: `$IT/templates/frontend/web/page.test.tsx.template`
- Create: `$IT/templates/frontend/mobile/tela-inicial-test.tsx.template`
- Create: `$IT/templates/frontend/makefile-targets.md`
- Create: `$IT/references/checkpoints-readme.md`
- Create: `$IT/references/claude-md-obligation.md`
- Create: `$IT/references/project-rules.md`
- Create: `$IT/references/wiremock.md`

**Interfaces:**
- Consumes: nada.
- Produces: `{web-dir}`, `{mobile-dir}`, `{app-dir}` (`./app` ou `./src/app`) como placeholders; seções `## Variáveis de ambiente`, `## Checkpoints de conferência`, `## Débitos técnicos` e o parágrafo de *Testes* em `project-rules.md`, que o Passo 8 da skill acrescenta ao arquivo de convenções.

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
IT=plugins/analizza-skills/skills/analizza-integration-test
c() { local ok=0
  for f in templates/frontend/web/vitest.config.mts.template templates/frontend/web/vitest.setup.ts.template templates/frontend/web/page.test.tsx.template templates/frontend/mobile/tela-inicial-test.tsx.template templates/frontend/makefile-targets.md references/checkpoints-readme.md references/claude-md-obligation.md references/project-rules.md references/wiremock.md; do
    [ -f $IT/$f ] || { echo "falta $f"; ok=1; }; done
  grep -q 'tsc --noEmit' $IT/templates/frontend/makefile-targets.md 2>/dev/null || { echo "sem typecheck"; ok=1; }
  grep -q 'renderRouter' $IT/templates/frontend/mobile/tela-inicial-test.tsx.template 2>/dev/null || { echo "mobile sem renderRouter"; ok=1; }
  for s in '## Variáveis de ambiente' '## Checkpoints de conferência' '## Débitos técnicos' 'escrito à mão'; do
    grep -q "$s" $IT/references/project-rules.md 2>/dev/null || { echo "project-rules sem: $s"; ok=1; }; done
  grep -q '```kotlin' $IT/references/wiremock.md 2>/dev/null && grep -q '```java' $IT/references/wiremock.md || { echo "wiremock sem as duas linguagens"; ok=1; }
  grep -rqiE 'com\.eaf|AccessCode|DocuSign|Azurite|eaf-runbook|Mailpit' $IT/templates/frontend $IT/references 2>/dev/null && { echo "nome do projeto de referencia"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: nove "falta …" e as demais, `EXIT=1`.

- [ ] **Step 3: `web/vitest.config.mts.template`**

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  // Resolve o alias "@/*" do tsconfig sem plugin extra.
  resolve: { tsconfigPaths: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
```

- [ ] **Step 4: `web/vitest.setup.ts.template`**

```ts
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Sem isto, o que um teste renderizou continua no document do seguinte.
afterEach(() => {
  cleanup();
});
```

- [ ] **Step 5: `web/page.test.tsx.template`** (gravado ao lado do `page.tsx` da rota raiz, `src/app/page.test.tsx`)

```tsx
import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "./page";

// Teste minimo: prova que a suite roda e que a tela inicial renderiza.
// Troque pelo primeiro teste de comportamento quando a tela ganhar um.
test("a tela inicial renderiza", () => {
  const { container } = render(<Home />);
  expect(container.querySelector("main")).not.toBeNull();
});
```

- [ ] **Step 6: `mobile/tela-inicial-test.tsx.template`** (gravado em `{mobile-dir}/__tests__/tela-inicial-test.tsx`, fora da pasta de rotas — o expo-router trataria um arquivo dentro de `app/` como rota)

```tsx
import { renderRouter, screen } from "expo-router/testing-library";

// Teste minimo: prova que a suite roda e que o roteador abre a tela inicial.
// Troque pelo primeiro teste de comportamento quando a tela ganhar um.
test("a tela inicial abre na rota raiz", () => {
  renderRouter("{app-dir}");
  expect(screen).toHavePathname("/");
});
```

- [ ] **Step 7: `frontend/makefile-targets.md`**

````markdown
# Alvos de teste do Makefile

Se o projeto tem `Makefile` na raiz, os alvos abaixo substituem os de mesmo
nome e são acrescentados ao `test`. Receitas com **TAB**, não espaço. Se não
há `Makefile`, os mesmos comandos entram como `scripts` no `package.json` de
cada frontend (`"test"`, `"typecheck"`) e nada é criado na raiz.

```makefile
.PHONY: test
test: test-backend test-integration test-web test-mobile ## Roda todos os testes

.PHONY: test-backend
test-backend: ## Testes unitarios do backend (nao sobe banco)
	$(GRADLEW) test

.PHONY: test-integration
test-integration: ## Testes de integracao (*IT) sobre Testcontainers
	$(GRADLEW) integrationTest

.PHONY: test-web
test-web: $(WEB_DIR)/node_modules ## Lint, tipos e testes do web
	cd $(WEB_DIR) && npm run lint
	cd $(WEB_DIR) && npm run typecheck
	cd $(WEB_DIR) && npm test

.PHONY: test-mobile
test-mobile: $(MOBILE_DIR)/node_modules ## Tipos e testes do mobile
	cd $(MOBILE_DIR) && npm run typecheck
	cd $(MOBILE_DIR) && npm test
```

Retire do `test` o que não existir no projeto (sem `-mobile`, sem
`test-mobile`; sem backend, sem os dois primeiros). `test-backend` **não**
depende de `db-up`: depois desta skill, `./gradlew test` não sobe banco.

## `scripts` do `package.json`

| Frontend | `test` | `typecheck` |
|---|---|---|
| `-web` (Next) | `vitest run` | `next typegen && tsc --noEmit` |
| `-mobile` (Expo) | `jest --ci` | `tsc --noEmit` |

O `next typegen` gera os tipos de rota que o `next build` geraria; sem ele, o
`tsc` sozinho acusa import de tipos que ainda não existem.

O `typecheck` existe porque lint e teste não fazem checagem de tipo: uma
mudança num tipo compartilhado pode quebrar um arquivo que nenhum teste
importa, e o alvo que as pessoas rodam fica verde com a regressão dentro.
````

- [ ] **Step 8: `references/checkpoints-readme.md`** — gravado como `docs/checkpoints/README.md` no projeto

````markdown
# Runbooks de checkpoint

Um arquivo por funcionalidade, descrevendo como **uma pessoa** confere que
aquilo funciona rodando. O arquivo de convenções do projeto diz quando um
checkpoint é devido; esta pasta é onde o roteiro dele mora.

## Não é suíte de teste

Teste é o que roda sozinho e falha sozinho. Checkpoint é o que alguém olha — e
existe justamente para o que teste nenhum pega: a tela que sumiu com a suíte
verde, o CORS que só quebra no navegador, a migration que não casou uma linha.

Por isso a pasta não se chama `tests` nem `e2e`. Nomear assim convida a
automatizar o conteúdo, e automatizar destrói a propriedade que o faz valer.

## Um arquivo por funcionalidade

O nome descreve a funcionalidade, sem data e sem número de fatia:

```
docs/checkpoints/cadastro-de-cliente.md
docs/checkpoints/emissao-de-boleto.md
```

Quando a funcionalidade muda, **é este arquivo que muda**. Dois arquivos
datados descrevendo a mesma tela é como um deles envelhece em silêncio e
alguém confere pelo roteiro errado.

## O tipo, no topo do arquivo

Todo runbook abre declarando onde a conferência acontece:

```markdown
---
type: screen-web
---
```

| valor | significa |
|---|---|
| `screen-web` | há uma tela do `-web` para olhar |
| `screen-mobile` | há uma tela do `-mobile` para olhar |
| `api` | terminal e HTTP; não há tela |
| `inbox` | a conferência é numa caixa de entrada |

**O tipo descreve onde a *conferência* acontece, não o setup.** Um runbook
que pede para subir um arquivo pela tela e depois confere tudo no terminal é
`api`: subir é preparação.

## A forma, e por que ela é essa

Quatro seções, nesta ordem. Quem lê de cima para baixo faz primeiro o que
confirma, depois o que tenta quebrar.

**1. O que precisa bater.** A lista de sempre, cada item com o comando ou o
clique e o valor esperado. É a parte que parece um checklist e é a menos
valiosa.

**2. O que tentar para ver se quebra.** Não é lista de conferência, é
provocação: o arquivo corrompido, o campo vazio, o identificador inventado. É
aqui que os defeitos aparecem.

**3. O que não está na lista.** Um parágrafo lembrando de estranhar qualquer
número que apareça sem ter sido pedido. Existe porque a lista é, por
construção, feita das coisas em que já se pensou.

**4. O que este checkpoint já pegou.** Preenchido *depois*, com data e com o
achado real.

A seção 4 transforma a pasta em memória em vez de burocracia: quem for
conferir da próxima vez sabe o que procurar, porque está escrito o que a
última pessoa não teria achado se tivesse só marcado caixinhas.

## O risco desta pasta existir

Um checkpoint a cada tarefa treina quem revisa a carimbar sem olhar, e um
roteiro pronto tem o mesmo defeito, mais forte: lista pronta vira lista
marcada. A defesa são as seções 2 e 3 — as partes que não dá para responder
sem olhar. Um runbook que virou só a seção 1 parou de servir; vale mais
apagá-lo do que mantê-lo.

## Quem executa

Uma pessoa, na mão. Um agente pode preparar o ambiente, atualizar o runbook e
dizer o que não conseguiu verificar; a conferência e a decisão de aprovar são
de quem olha.
````

- [ ] **Step 9: `references/claude-md-obligation.md`** — bloco acrescentado ao `CLAUDE.md` da raiz

````markdown
# Obrigação de runbook no `CLAUDE.md`

Acrescente ao fim do `CLAUDE.md` da raiz (crie o arquivo com este bloco se ele
não existir). `{conventions-file}` é o arquivo de convenções em que o Passo 8
gravou as regras de projeto.

```markdown
## O que "pronto" inclui

**Toda funcionalidade criada ou alterada produz ou atualiza o runbook dela em
`docs/checkpoints/<funcionalidade>.md`.** Faz parte do trabalho, não é um passo
depois dele: uma fatia que entrega código sem o runbook está incompleta. Não
entregue assim, e não peça permissão para pular.

**Como** escrever o runbook — um arquivo por funcionalidade, o tipo no topo, as
quatro seções e por que elas são essas — está em
[docs/checkpoints/README.md](docs/checkpoints/README.md). **Quando** propor a
conferência está em [{conventions-file}]({conventions-file}), na seção
*Checkpoints de conferência*.

Esta obrigação mora aqui, e não só no arquivo de convenções, porque este
arquivo entra em contexto sozinho: uma definição de pronto que mora apenas no
arquivo que pode não ser lido se perde em silêncio — e o runbook é o que mais
se perde, porque a fatia *parece* terminada sem ele.
```
````

- [ ] **Step 10: `references/project-rules.md`**

````markdown
# Regras de projeto

Seções acrescentadas pelo Passo 8 ao arquivo de convenções do projeto. Cada
uma entra **só se o arquivo ainda não tiver uma seção com o mesmo título**
(`grep -q '^## <título>'`); nunca sobrescreva uma existente. O parágrafo de
*Testes* vai para dentro da seção *Testes* que já existir, ou para uma nova.

## Variáveis de ambiente

**Toda variável lida pela configuração da aplicação (`${NOME}` ou
`${NOME:padrao}`) está em dois lugares além dela, no mesmo commit que a
introduz:**

1. **`README.md`, seção *Variáveis de ambiente*, sem valor** — sempre `NOME=`,
   mesmo quando há padrão e mesmo quando o valor não é segredo. O padrão mora
   só na configuração: copiá-lo para o README é criar um segundo lugar para
   ele envelhecer.
2. **`.env.local` da raiz, se o arquivo existir na máquina** — com o padrão da
   configuração preenchido, ou vazio (`NOME=`) quando não há padrão. O arquivo
   não é versionado, então isto é um passo na máquina de quem mexeu, não uma
   linha do diff: não crie o arquivo se ele não existe.

Renomear ou remover uma variável mexe nas mesmas duas listas.

O porquê: o `.env.local` não vai para o repositório, e o README é a única
lista versionada do que a aplicação precisa para subir. Sem ela, uma variável
nova sem padrão faz a aplicação parar de subir em toda máquina, e ninguém sabe
que ela existe até o boot recusar.

## Checkpoints de conferência

Um checkpoint é uma parada onde **uma pessoa olha o resultado rodando** antes
de o trabalho seguir. Ele não substitui teste: existe para o que teste nenhum
pega.

**Proponha um checkpoint sem esperar que peçam** sempre que o critério de
aceite mora fora da suíte de testes:

- **Aparência.** Uma tela nova ou redesenhada, comparada com um print, um
  protótipo ou uma descrição.
- **Contrato com serviço externo.** A primeira chamada real a um storage, a um
  SMTP, a uma API de terceiro. Container e emulador provam a forma, não provam
  a conta de produção, o CORS nem a credencial.
- **Migration que muda dado que já existe.** Rodar contra uma cópia e conferir
  as linhas antes de rodar contra o ambiente de verdade.
- **Qualquer coisa irreversível ou de fora**: apagar dado, publicar, mandar
  mensagem para gente de verdade, mexer em configuração compartilhada.

**Não proponha checkpoint** para o que a suíte já cobre: regra de domínio,
handler, contrato HTTP entre os próprios módulos, refactor com teste verde
antes e depois. Um checkpoint a cada tarefa treina quem revisa a carimbar sem
olhar.

**Como propor.** Diga o que olhar e como olhar, não "confira por favor", e
aponte o runbook da funcionalidade em `docs/checkpoints/`. Diga também, sem
que perguntem, **o que você não conseguiu verificar** — é isso que a pessoa
confere primeiro.

**Quem executa é uma pessoa, na mão.** Não rode o fluxo e apresente a saída
como se fosse a conferência. Num plano de implementação, o checkpoint é uma
seção própria entre as fases, e a fase seguinte não começa sem o aval.

## Débitos técnicos

Coisas já implementadas que funcionam mas carregam uma dívida conhecida. Cada
item diz o que está errado, por que foi aceito e o que o fecha. Nenhum bloqueia
o uso em desenvolvimento; quem mexer na área decide se fecha junto.

Um item entra no mesmo commit que cria a dívida, não depois. Um débito que só
existe na cabeça de quem o criou é um defeito esperando para ser redescoberto.

## Testes — parágrafo

**Um exemplo escrito à mão do formato de saída de outro sistema não é
evidência sobre o que aquele sistema produz.** Teste de adapter que monta à
mão uma URL, um JSON ou uma mensagem "como o SDK devolveria" prova só que o
código entende o exemplo. O teste que protege a integração usa a saída real —
do SDK, do container, do serviço — ao menos uma vez.
````

- [ ] **Step 11: `references/wiremock.md`**

````markdown
# WireMock no `BaseIntegrationTest`

Só quando o projeto depende de HTTP externo e o usuário confirmar. Um servidor
para a suíte inteira, na mesma forma do container de banco: campo estático,
iniciado na mão, porta dinâmica e `resetAll()` antes de cada teste.

## Dependência

```kotlin
testImplementation("org.wiremock:wiremock-standalone:3.13.1")   // build.gradle.kts
```

```groovy
testImplementation 'org.wiremock:wiremock-standalone:3.13.1'    // build.gradle
```

## Kotlin

```kotlin
import com.github.tomakehurst.wiremock.WireMockServer
import com.github.tomakehurst.wiremock.core.WireMockConfiguration.options
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource

// dentro do BaseIntegrationTest
@BeforeEach
fun limparWireMock() {
    wireMock.resetAll()
}

companion object {
    @JvmStatic
    val wireMock: WireMockServer = WireMockServer(options().dynamicPort()).also { it.start() }

    @JvmStatic
    @DynamicPropertySource
    fun propriedadesDoHttpExterno(registry: DynamicPropertyRegistry) {
        // Troque pela propriedade real da URL base do cliente HTTP.
        registry.add("<cliente.base-url>") { "http://localhost:${wireMock.port()}" }
    }
}
```

## Java

```java
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.options;

import com.github.tomakehurst.wiremock.WireMockServer;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

// dentro do BaseIntegrationTest
protected static final WireMockServer WIRE_MOCK = new WireMockServer(options().dynamicPort());

static {
    WIRE_MOCK.start();
}

@BeforeEach
void limparWireMock() {
    WIRE_MOCK.resetAll();
}

@DynamicPropertySource
static void propriedadesDoHttpExterno(DynamicPropertyRegistry registry) {
    // Troque pela propriedade real da URL base do cliente HTTP.
    registry.add("<cliente.base-url>", () -> "http://localhost:" + WIRE_MOCK.port());
}
```

Um `companion object`/bloco `static` só por classe: mescle com o do container
de banco em vez de declarar um segundo.
````

- [ ] **Step 12: Rodar a checagem e ver passar** — `EXIT=0`.

- [ ] **Step 13: Commit**

```bash
git add $IT/templates/frontend $IT/references
git commit -m "Cria os guardrails de frontend e as regras de projeto da analizza-integration-test

Vitest no web, jest-expo no mobile, typecheck no Makefile, README de
checkpoints, obrigacao de runbook e regras de projeto genericas.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: `SKILL.md`

**Files:**
- Create: `$IT/SKILL.md`

**Interfaces:**
- Consumes: todos os caminhos e placeholders das Tarefas 2–4.
- Produces: argumentos `escopo=`, `linguagem=`, `banco=`, `layout=` (usados pela `analizza-new-project` na Entrega 3).

- [ ] **Step 1: Checagem que deve falhar**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
IT=plugins/analizza-skills/skills/analizza-integration-test
c() { local ok=0 s=$IT/SKILL.md
  [ -f $s ] || { echo "falta SKILL.md"; return 1; }
  head -1 $s | grep -q '^---$' || { echo "sem frontmatter"; ok=1; }
  grep -q '^name: analizza-integration-test$' $s || { echo "name errado"; ok=1; }
  for p in 'Passo 0' 'Passo 1' 'Passo 2' 'Passo 3' 'Passo 4' 'Passo 5' 'Passo 6' 'Passo 7' 'Passo 8' 'Passo 9' 'Passo 10' 'Passo 11'; do grep -q "### $p " $s || { echo "sem $p"; ok=1; }; done
  # todo link relativo existe
  grep -oE '\]\(\./[^)]+\)' $s | sed -E 's/\]\(\.\/(.*)\)/\1/' | sort -u | while read l; do [ -e "$IT/$l" ] || echo "link quebrado: $l"; done | grep . && ok=1
  grep -qE 'quality-setup-testcontainers|FreezingArchRule|@Tag\("integration"\)' $s && { echo "resto das skills antigas"; ok=1; }
  grep -qiE 'com\.eaf|AccessCode|DocuSign|Azurite' $s && { echo "nome do projeto de referencia"; ok=1; }
  return $ok; }; c; echo "EXIT=$?"
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: "falta SKILL.md", `EXIT=1`.

- [ ] **Step 3: Escrever `SKILL.md`**

````markdown
---
name: analizza-integration-test
description: >-
  Configura testes de integração e guardrails de teste num projeto Spring Boot
  (Java ou Kotlin, Gradle Groovy ou Kotlin DSL) e nos seus frontends Next.js e
  Expo. Detecta e pergunta linguagem, banco (Postgres, Oracle, MySQL) e layout —
  módulo dedicado {base}-integration-tests (recomendado) ou o módulo existente —,
  cria BaseIntegrationTest com um container por suíte, tasks test/integrationTest
  separadas pelo sufixo IT, regra ArchUnit que exige IT para todo entrypoint,
  dublês de saída, cobertura JaCoCo; no frontend, typecheck, Vitest e jest-expo;
  e grava as regras de projeto (variáveis de ambiente, checkpoints com runbook por
  funcionalidade, débitos técnicos). Use quando o usuário pedir "testes de
  integração", "integration tests", "guardrails de teste", "módulo de testes de
  integração", "reduzir tempo de testcontainers", "analizza integration test",
  ou quando a analizza-new-project oferecer os guardrails.
argument-hint: "Opcional: escopo=backend|frontend|ambos linguagem=java|kotlin banco=postgres|oracle|mysql layout=dedicado|existente — valores passados viram padrão a confirmar"
---

# Testes de integração e guardrails de teste

A skill trabalha em duas partes independentes — **backend** e **frontend** — e
grava regras de projeto que valem para as duas. Ela nunca promove um projeto de
módulo único a multi-módulo e nunca escreve teste de domínio: entrega a
infraestrutura, um IT de contexto e a regra que obriga os próximos.

## Vocabulário

| Placeholder | Valor |
|---|---|
| `{language}` | `kotlin` ou `java` — a linguagem do fonte de produção |
| `{src-dir}` | `kotlin` ou `java`, igual a `{language}` |
| `{dsl}` | `kts` ou `groovy` |
| `{dsl-ext}` | `.kts` quando `{dsl}=kts`, vazio quando `groovy` |
| `{db}` | `postgres`, `oracle` ou `mysql` |
| `{layout}` | `dedicado` ou `existente` |
| `{base}` | `rootProject.name` do `settings.gradle{dsl-ext}` |
| `{base-package}` | pacote raiz comum às classes de produção (ex.: `br.com.analizza.loja`) |
| `{it-module}` | `{base}-integration-tests` (dedicado), o `-api` (projeto `-api`/`-core`) ou `.` (módulo único) |
| `{it-src}` | `{it-module}/src/test/{src-dir}/{base-package com / no lugar de .}` |
| `{group}`, `{java-version}`, `{boot-version}` | lidos do build do módulo que aplica o plugin do Spring Boot |

## Procedimento

### Passo 0 — Escopo

Com `escopo=` nos argumentos, ele é o padrão a confirmar. Senão, pergunte:
backend, frontend ou os dois. Ofereça frontend só se existir um diretório com
`package.json` que dependa de `next` (o `{web-dir}`) ou de `expo` (o
`{mobile-dir}`):

```bash
for p in $(find . -maxdepth 2 -name package.json -not -path '*/node_modules/*'); do
  d=$(dirname "$p"); grep -q '"next"' "$p" && echo "web: $d"; grep -q '"expo"' "$p" && echo "mobile: $d"
done
```

Ofereça backend só se existir `settings.gradle` ou `settings.gradle.kts`. Para
frontend sem backend, pule para o Passo 7.

### Passo 1 — Detectar e perguntar

Uma pergunta por vez, sempre com o detectado (ou o argumento recebido) como
padrão. Diga o que detectou e de onde.

**Linguagem.**

```bash
find . -path '*/src/main/kotlin/*.kt' -not -path '*/build/*' | head -1   # achou: kotlin
find . -path '*/src/main/java/*.java' -not -path '*/build/*' | head -1   # achou: java
```

Se achar os dois, pergunte sem padrão.

**DSL — não pergunte, informe.** `settings.gradle.kts` → `kts`;
`settings.gradle` → `groovy`. Sem `settings`, a regra é a linguagem: `kotlin` →
`kts`, `java` → `groovy`. O build que já existe vence a regra: um projeto Kotlin
com `build.gradle` recebe Groovy.

**Banco.**

```bash
grep -rhoE 'org\.postgresql:postgresql|com\.oracle\.database\.jdbc:ojdbc[0-9]*|com\.mysql:mysql-connector-j' --include='build.gradle*' . | sort -u
grep -rhoE 'jdbc:(postgresql|oracle|mysql)' --include='application*.properties' --include='application*.y*ml' . | sort -u
grep -hoE 'image: *(postgres|gvenzl/oracle[^ ]*|container-registry.oracle[^ ]*|mysql)[^ ]*' docker-compose*.y*ml compose*.y*ml 2>/dev/null
```

Opções: `postgres`, `oracle`, `mysql`, outro. Com "outro", siga a seção
*Outro banco* de [containers.md](./templates/backend/containers.md).

**Layout.** Conte os `include` do `settings.gradle{dsl-ext}` e procure as
aplicações:

```bash
grep -E "include" settings.gradle* 2>/dev/null
grep -rlE '@SpringBootApplication' --include='*.kt' --include='*.java' . | grep '/src/main/'
```

- **Módulo único** (nenhum `include`, fonte em `./src`): não pergunte; informe
  que os ITs vão para `src/test` do próprio módulo (`{layout}=existente`,
  `{it-module}=.`). Se o usuário pedir módulo dedicado, explique que isso exige
  reestruturar o `src/main` do projeto, fora do escopo desta skill, e siga no
  módulo único.
- **Multi-módulo**: pergunte com **módulo dedicado `{base}-integration-tests`
  (recomendado)** primeiro e **aplicar no módulo existente** em segundo. No
  existente, `{it-module}` é o módulo que tem a `@SpringBootApplication`; se
  houver mais de um, pergunte qual.

### Passo 2 — Módulo e dependências

**Dedicado.**

1. Acrescente o módulo ao `settings.gradle{dsl-ext}`:
   `include ':{base}-integration-tests'` (groovy) ou
   `include(":{base}-integration-tests")` (kts).
2. Grave `{base}-integration-tests/build.gradle{dsl-ext}` a partir de
   [integration-tests-module.gradle.template](./templates/backend/build/groovy/integration-tests-module.gradle.template)
   (groovy) ou
   [integration-tests-module.gradle.kts.template](./templates/backend/build/kts/integration-tests-module.gradle.kts.template)
   (kts). Grave só o bloco `<!-- se {language} -->` e remova os marcadores.
   - `{project-dependencies}`: uma linha por módulo de produção do
     `settings` — `testImplementation project(':<m>')` (groovy) ou
     `testImplementation(project(":<m>"))` (kts). Módulo de produção é todo
     `include` exceto o próprio `-integration-tests`.
   - `{coverage-modules}`: os mesmos módulos, entre aspas e separados por
     vírgula (`':loja-api', ':loja-core'` em groovy; `":loja-api", ":loja-core"`
     em kts). Módulos sem `src/main/{src-dir}` (um `buildingBlocks` em outra
     linguagem, por exemplo) ficam fora.
   - `{testcontainers-db-module}`: coluna de mesmo nome em
     [containers.md](./templates/backend/containers.md).
3. O módulo aplica plugins sem versão. Confirme que o build da raiz os declara
   com versão e `apply false`; se não declarar, leve as versões para a raiz
   (o Kotlin Gradle Plugin não aceita versão explícita em mais de um
   subprojeto).
4. Tire dos outros módulos as dependências de teste que só a integração usa:
   `spring-boot-testcontainers`, `testcontainers-*`, `archunit*`, `wiremock*`,
   `awaitility`. Mantenha o que teste unitário usa.

**Existente.** Mescle no `{it-module}/build.gradle{dsl-ext}` os trechos de
[existing-module.gradle.template](./templates/backend/build/groovy/existing-module.gradle.template)
(groovy) ou
[existing-module.gradle.kts.template](./templates/backend/build/kts/existing-module.gradle.kts.template)
(kts): acrescente ao `plugins {}` e ao `dependencies {}` que já existem, sem
duplicar linha, e substitua configurações anteriores de `test` e
`jacocoTestReport`. Uma configuração que aplique JUnit a todo `Test`
(`tasks.withType<Test>`) pode ficar: ela não conflita.

### Passo 3 — Aplicação do contexto de teste

Conte as `@SpringBootApplication` do Passo 1.

- **Uma:** `{app-class}` é o nome simples dela e `{app-package}`, o pacote.
- **Mais de uma:** grave `{it-src}/IntegrationTestApplication.{kt|java}` a
  partir de
  [IntegrationTestApplication.kt.template](./templates/backend/source/kotlin/IntegrationTestApplication.kt.template)
  ou
  [IntegrationTestApplication.java.template](./templates/backend/source/java/IntegrationTestApplication.java.template);
  `{app-class}=IntegrationTestApplication`, `{app-package}={base-package}`. Se
  os módulos têm `application.properties`/`.yml` com nomes diferentes, liste
  todos em `spring.config.name` numa `properties` do `@SpringBootTest`.

A configuração da aplicação chega ao classpath dos ITs pela dependência de
projeto: não copie `application.properties` para o módulo de testes.

### Passo 4 — Base, dublês e IT de contexto

A partir de `templates/backend/source/{language}/`, grave em
`{it-src}/support/`:

- [BaseIntegrationTest](./templates/backend/source/kotlin/BaseIntegrationTest.kt.template)
  ([Java](./templates/backend/source/java/BaseIntegrationTest.java.template)),
  com `{container-import}`, `{container-type}` e `{container-new}` de
  [containers.md](./templates/backend/containers.md).
- [TestConfig](./templates/backend/source/kotlin/TestConfig.kt.template)
  ([Java](./templates/backend/source/java/TestConfig.java.template)). Em
  `{doubles}`, para cada **interface** de serviço de saída sem container — as
  de `infrastructure/data/anticorruptionLayer/**` e `infrastructure/security/**`
  num projeto em camadas; num projeto de outro formato, as interfaces
  implementadas por classes que falam com SMTP, HTTP externo ou mensageria —
  escreva uma classe em memória que registra o que recebeu e um `@Bean
  @Primary` que a devolve, na forma do comentário do template. Sem nenhuma
  interface assim, `{doubles}` fica vazio.
- [ApplicationContextIT](./templates/backend/source/kotlin/ApplicationContextIT.kt.template)
  ([Java](./templates/backend/source/java/ApplicationContextIT.java.template)).
  Apague o teste de contexto que o Spring Initializr gerou
  (`*ApplicationTests.{kt,java}` com um único `contextLoads`) — ele é substituído
  por este. Se o `*ApplicationTests` tiver mais que `contextLoads`, não apague:
  renomeie para `*ApplicationIT`, faça-o estender `BaseIntegrationTest` e diga
  ao usuário.

Se já existir um `BaseIntegrationTest`, **mescle** em vez de gravar outro:
mantenha os containers e `@DynamicPropertySource` que ele tem, acrescente o do
banco escolhido se faltar, e deixe um só no build.

Mova para `{it-src}` (mantendo o pacote) todo teste que estenda
`BaseIntegrationTest` e esteja em outro módulo, com `git mv`. Todo teste que
estende a base termina em `IT`; renomeie os que não terminam.

Assets de container (`Dockerfile`, `init.sql`) ficam em
`{it-module}/src/test/resources/<banco>/`, nunca em `src/main/resources/`.

### Passo 5 — Regra ArchUnit

Grave `{it-src}/architecture/EntrypointHasIntegrationTestIT.{kt|java}` a partir
de [EntrypointHasIntegrationTestIT.kt.template](./templates/backend/source/kotlin/EntrypointHasIntegrationTestIT.kt.template)
ou [EntrypointHasIntegrationTestIT.java.template](./templates/backend/source/java/EntrypointHasIntegrationTestIT.java.template).
Se o projeto já tiver uma regra de mesmo propósito com outro nome, substitua-a
por esta e diga ao usuário.

### Passo 6 — Documentar o layout nas convenções

Se o projeto tem arquivo de convenções com uma seção *Testes* (o que a
`analizza-new-project` grava — procure `^### Testes` ou `^## Testes` em
`docs/INSTRUCTIONS.md`, `docs/superpowers/INSTRUCTIONS.md`,
`.specify/memory/constitution.md` e `openspec/project.md`):

- **Dedicado:** troque a frase de que o `-api` é o único módulo com
  Testcontainers por: "**O `{base}-integration-tests` é o único módulo com
  Testcontainers.** Nenhum módulo de produção tem dependência de teste de
  container; é o módulo dedicado, pela dependência de projeto sobre os outros,
  quem sobe os containers e testa a infraestrutura de ponta a ponta através
  do `BaseIntegrationTest`." e troque todo caminho
  `{project-name}-api/src/test/...` da seção por
  `{base}-integration-tests/src/test/...`.
- **Os dois layouts:** a seção deixa de dizer que a infraestrutura "não existe
  ainda" e passa a dizer que `./gradlew test` roda só o que não precisa de banco
  e `./gradlew integrationTest` sobe os containers.

Sem arquivo de convenções, este passo não faz nada; o Passo 8 cria um.

### Passo 7 — Frontend

Para cada `{web-dir}` e `{mobile-dir}` do Passo 0:

**`-web` (Next.js).**

```bash
cd {web-dir}
npm install --save-dev vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom
```

Grave `vitest.config.mts` e `vitest.setup.ts` a partir de
[vitest.config.mts.template](./templates/frontend/web/vitest.config.mts.template)
e [vitest.setup.ts.template](./templates/frontend/web/vitest.setup.ts.template),
e o teste mínimo ao lado da página raiz (`src/app/page.test.tsx`, ou
`app/page.test.tsx` sem `src/`) a partir de
[page.test.tsx.template](./templates/frontend/web/page.test.tsx.template).
Não sobrescreva um `vitest.config.*` existente: mescle.

**`-mobile` (Expo).**

```bash
cd {mobile-dir}
npx expo install jest-expo jest @types/jest @testing-library/react-native -- --save-dev
```

No `package.json`, acrescente `"jest": { "preset": "jest-expo" }` se não
houver configuração de jest. Grave `__tests__/tela-inicial-test.tsx` a partir
de [tela-inicial-test.tsx.template](./templates/frontend/mobile/tela-inicial-test.tsx.template),
com `{app-dir}` = `./src/app` se existir `src/app`, senão `./app`. Se o
`tsc --noEmit` reclamar de `expo-env.d.ts` ausente, crie-o com
`/// <reference types="expo/types" />` (é o que o `expo start` geraria).

**Os dois.** Acrescente os `scripts` `test` e `typecheck` e os alvos do
`Makefile` de [makefile-targets.md](./templates/frontend/makefile-targets.md).

**Checkpoints.** Grave `docs/checkpoints/README.md` a partir de
[checkpoints-readme.md](./references/checkpoints-readme.md) se ele não
existir, e acrescente ao `CLAUDE.md` da raiz o bloco de
[claude-md-obligation.md](./references/claude-md-obligation.md) se ele não
tiver uma seção `## O que "pronto" inclui`. Os checkpoints entram também num
projeto só com backend: um runbook `api` é tão devido quanto um de tela.

### Passo 8 — Regras de projeto

Destino: o arquivo de convenções do Passo 6; sem nenhum, `docs/INSTRUCTIONS.md`
(crie com um título `# {base}`). Acrescente as seções de
[project-rules.md](./references/project-rules.md) que o arquivo ainda não
tiver, e o parágrafo de *Testes* dentro da seção *Testes*. Nunca sobrescreva.
Se criou o arquivo, diga no relatório — e confira que o bloco do `CLAUDE.md`
aponta para ele em `{conventions-file}`.

### Passo 9 — Instructions de teste e README

Procure instructions de teste de outras ferramentas:

```bash
ls .github/instructions/*test* .github/copilot-instructions.md AGENTS.md 2>/dev/null
```

Se existirem, acrescente as mesmas regras: ITs em `{it-module}`, todo
entrypoint com IT, IT percorre banco e HTTP de verdade, `./gradlew test` vs
`./gradlew integrationTest`. Se não existirem, não crie.

No `README.md`, acrescente (ou atualize) uma seção *Testes* com os comandos
`make test-backend`, `make test-integration`, `make test-web`,
`make test-mobile` — ou os `./gradlew`/`npm` equivalentes sem `Makefile` — e
onde os ITs moram.

### Passo 10 — Verificar

Obrigatório. Redirecione a saída e leia o código de saída, nunca por pipe:

```bash
./gradlew test --console=plain > /tmp/it-unit.log 2>&1; echo "EXIT=$?"
./gradlew integrationTest --console=plain > /tmp/it-integration.log 2>&1; echo "EXIT=$?"
find . -path '*/build/test-results/integrationTest/*.xml' -not -path '*/node_modules/*' \
  -exec grep -ho 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' {} \;
```

Exija `EXIT=0` nos dois e, nos XML de `integrationTest`, `failures="0"
errors="0"` com `ApplicationContextIT` e `EntrypointHasIntegrationTestIT`
presentes (`tests` ≥ 1 em cada). `./gradlew test` não pode subir container:
`grep -c 'Creating container' /tmp/it-unit.log` deve ser `0`.

Prove que a regra falha quando deve: crie um controller descartável sem IT,
rode de novo e exija falha nomeando-o; apague-o e rode de novo até verde.

```kotlin
// {it-module de producao}/src/main/{src-dir}/{base-package}/SemTesteController.kt (descartavel)
@org.springframework.web.bind.annotation.RestController
class SemTesteController
```

Frontend: `make test-web` e `make test-mobile` (ou `npm run typecheck && npm
test` em cada diretório) com exit 0. Prove o typecheck: acrescente num arquivo
`.ts` do `-web` a linha `const quebra: number = "texto";`, exija falha do
`typecheck`, desfaça.

### Passo 11 — Relatar e oferecer WireMock

Informe: escopo, linguagem, DSL, banco, layout e `{it-module}`; os arquivos
criados e movidos; os `EXIT=` e as contagens dos XML; as provas de falha (regra
e typecheck); onde as regras de projeto foram gravadas; e o que não verificou.

Se o projeto chama HTTP externo (cliente `RestClient`, `WebClient`, `Feign` ou
SDK de terceiro no `-core`), pergunte se quer WireMock no `BaseIntegrationTest`
e aplique [wiremock.md](./references/wiremock.md) só com um sim.

## Fora de escopo

Teste de ponta a ponta automatizado de tela (Playwright): automatizar o que é
conferência humana destrói a propriedade que a faz valer. CI/CD. Limiar de
cobertura. Containers de Kafka, Redis e afins (a forma está em
[containers.md](./templates/backend/containers.md)). Promover módulo único a
multi-módulo.
````

- [ ] **Step 4: Rodar a checagem e ver passar** — `EXIT=0`. E:

```bash
make validate > /tmp/it-validate.log 2>&1; echo "EXIT=$?"; tail -3 /tmp/it-validate.log
make check > /tmp/it-check.log 2>&1; echo "EXIT=$?"; tail -1 /tmp/it-check.log
```

Expected: `EXIT=0` nos dois.

- [ ] **Step 5: Commit**

```bash
git add $IT/SKILL.md
git commit -m "Escreve o procedimento da analizza-integration-test

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Executar em projetos gerados pela new-project (alvos A e B)

A prova da entrega. Nenhum arquivo da skill muda aqui, a não ser que a execução revele defeito: nesse caso registrar no relatório (arquivo, passo, texto, o que aconteceu, correção sugerida), contornar o mínimo para seguir e reportar `DONE_WITH_CONCERNS` — a correção é despachada à parte e revisada.

**Files:** nenhum no repositório. Alvos em `$SCRATCH`.

**Interfaces:**
- Consumes: Tarefas 1–5; os projetos `$SCRATCH/kotlin-demo` (Kotlin, `.kts`, Postgres, `-api`/`-core`, `-web`, `-mobile`) e `$SCRATCH/java-demo` (Java, Groovy, mesmo formato), gerados na Entrega 1.
- Produces: evidência para o PR.

- [ ] **Step 1: Pré-requisitos e cópia limpa dos alvos**

```bash
lsof -nP -iTCP:5432 -iTCP:8080 -iTCP:3000 -sTCP:LISTEN; docker info >/dev/null 2>&1 && echo "docker OK"
cd $SCRATCH && rm -rf alvo-a alvo-b && cp -R kotlin-demo alvo-a && cp -R java-demo alvo-b
for d in alvo-a alvo-b; do (cd $d && git status --short | head -3 && git log --oneline -1); done
```

Expected: `docker OK`; portas livres não são exigidas (ITs usam portas aleatórias), mas registre o que estiver ocupado. Se os alvos tiverem mudanças não commitadas, commite-as no próprio alvo antes (`git add -A && git commit -m base`), para o diff da skill ficar legível.

- [ ] **Step 2: Alvo A — Kotlin, `.kts`, layout dedicado, escopo ambos**

Em `$SCRATCH/alvo-a`, siga `$IT/SKILL.md` do **worktree**, Passos 0–11, respondendo: escopo `ambos`, linguagem `kotlin` (detectada), banco `postgres` (detectado), layout `dedicado`. WireMock: não.

- [ ] **Step 3: Conferir o alvo A**

```bash
cd $SCRATCH/alvo-a
grep -n 'integration-tests' settings.gradle.kts
ls kotlin-demo-integration-tests/build.gradle.kts
find kotlin-demo-integration-tests/src/test -name '*.kt' | sort
find . -name '*ApplicationTests.kt' -not -path '*/build/*' | wc -l      # espera 0
grep -rn 'testcontainers' kotlin-demo-api/build.gradle.kts kotlin-demo-core/build.gradle.kts | wc -l   # espera 0
./gradlew test --console=plain > /tmp/a-unit.log 2>&1; echo "EXIT=$?"; grep -c 'Creating container' /tmp/a-unit.log
./gradlew integrationTest --console=plain > /tmp/a-it.log 2>&1; echo "EXIT=$?"
grep -ho 'testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' kotlin-demo-integration-tests/build/test-results/integrationTest/*.xml
./gradlew :kotlin-demo-integration-tests:integrationTestCoverageReport --console=plain > /tmp/a-cov.log 2>&1; echo "EXIT=$?"
ls kotlin-demo-integration-tests/build/reports/jacoco/integrationTestCoverageReport/*.xml
grep -o '<counter type="CLASS" missed="[0-9]*" covered="[0-9]*"/>' kotlin-demo-integration-tests/build/reports/jacoco/integrationTestCoverageReport/*.xml | tail -1
```

Expected: `include(":kotlin-demo-integration-tests")`; build existe; `ApplicationContextIT.kt`, `BaseIntegrationTest.kt`, `TestConfig.kt` em `support/` e `EntrypointHasIntegrationTestIT.kt` em `architecture/`; `0`; `0`; `EXIT=0` e `0` containers no `test`; `EXIT=0`; as duas suítes com `failures="0" errors="0"` e `tests` ≥ 1; `EXIT=0`; XML existe; contador `CLASS` presente (qualquer `covered`).

- [ ] **Step 4: Prova de falha da regra (alvo A)**

Criar `kotlin-demo-api/src/main/kotlin/br/com/analizza/kotlindemo/SemTesteController.kt` com o conteúdo do Passo 10 da skill; rodar `./gradlew integrationTest --tests '*EntrypointHasIntegrationTestIT' --console=plain > /tmp/a-rule.log 2>&1; echo "EXIT=$?"`; exigir `EXIT≠0` e `grep -c 'SemTesteController' /tmp/a-rule.log` > 0. Apagar o arquivo, rodar de novo, exigir `EXIT=0`.

- [ ] **Step 5: Frontend do alvo A**

```bash
cd $SCRATCH/alvo-a
make test-web > /tmp/a-web.log 2>&1; echo "EXIT=$?"; grep -E 'Tests? +[0-9]+ passed|passed' /tmp/a-web.log | tail -2
make test-mobile > /tmp/a-mobile.log 2>&1; echo "EXIT=$?"; grep -E 'Tests:' /tmp/a-mobile.log | tail -1
ls docs/checkpoints/README.md CLAUDE.md
grep -n '## O que "pronto" inclui' CLAUDE.md
grep -n '^## Variáveis de ambiente\|^## Checkpoints de conferência\|^## Débitos técnicos' docs/INSTRUCTIONS.md docs/superpowers/INSTRUCTIONS.md 2>/dev/null
```

Expected: `EXIT=0` com 1 teste passando em cada; os dois arquivos; a seção no `CLAUDE.md`; as três seções no arquivo de convenções. Depois, a prova do typecheck do Passo 10 da skill: plantar `const quebra: number = "texto";` num `.ts` do `-web`, `make test-web` com `EXIT≠0`, desfazer, `EXIT=0`.

- [ ] **Step 6: Alvo B — Java, Groovy, layout existente, escopo backend**

Em `$SCRATCH/alvo-b`, Passos 0–11 com: escopo `backend`, linguagem `java`, banco `postgres`, layout `existente` (`{it-module}=java-demo-api`). WireMock: não.

- [ ] **Step 7: Conferir o alvo B**

```bash
cd $SCRATCH/alvo-b
find . -name '*.kts' -not -path '*/node_modules/*' | wc -l                      # espera 0
grep -c 'integration-tests' settings.gradle                                    # espera 0
find java-demo-api/src/test -name '*.java' | sort
grep -n 'includeTestsMatching\|testcontainers-postgresql\|archunit' java-demo-api/build.gradle
./gradlew test --console=plain > /tmp/b-unit.log 2>&1; echo "EXIT=$?"; grep -c 'Creating container' /tmp/b-unit.log
./gradlew integrationTest --console=plain > /tmp/b-it.log 2>&1; echo "EXIT=$?"
grep -ho 'testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' java-demo-api/build/test-results/integrationTest/*.xml
./gradlew :java-demo-api:jacocoTestReport --console=plain > /tmp/b-cov.log 2>&1; echo "EXIT=$?"
ls java-demo-api/build/reports/jacoco/test/*.xml
```

Expected: `0`; `0`; os quatro `.java` em `support/` e `architecture/`; as três linhas no build; `EXIT=0` e `0`; `EXIT=0`; suítes com `failures="0" errors="0"`; `EXIT=0`; XML existe. Prova de falha da regra como no Step 4, com `SemTesteController.java`:

```java
package br.com.analizza.javademo;

@org.springframework.web.bind.annotation.RestController
public class SemTesteController {
}
```

- [ ] **Step 8: Limpeza e relatório**

`./gradlew --stop` nos dois alvos; `docker ps --format '{{.Names}}'` sem container dos alvos (o Ryuk derruba). Relatório com, por alvo: respostas dadas, arquivos criados/movidos (`git -C <alvo> status --short`), cada checagem com saída e `EXIT`, provas de falha, e a seção "Defeitos da skill encontrados" (ou "nenhum"). Nada commitado no repositório da skill.

---

### Task 7: Executar em módulo único e em projeto existente (alvos C e D)

Mesma regra da Tarefa 6 para defeitos.

**Files:** nenhum no repositório.

**Interfaces:**
- Consumes: Tarefas 1–5.
- Produces: evidência para o PR.

- [ ] **Step 1: Alvo C — gerar módulo único Kotlin com Oracle**

```bash
cd $SCRATCH && rm -rf alvo-c && mkdir alvo-c && cd alvo-c
curl -sS --max-time 90 -o starter.zip -G https://start.spring.io/starter.zip \
  --data-urlencode type=gradle-project-kotlin --data-urlencode language=kotlin \
  --data-urlencode groupId=br.com.analizza --data-urlencode artifactId=unico \
  --data-urlencode packageName=br.com.analizza.unico --data-urlencode javaVersion=25 \
  --data-urlencode dependencies=web,actuator,data-jpa,oracle
unzip -q starter.zip && rm starter.zip && chmod +x gradlew
git init -q && git add -A && git commit -qm base
```

- [ ] **Step 2: Executar a skill no alvo C**

Passos 0–11 com: escopo `backend` (não há frontend), linguagem `kotlin`, banco `oracle` (detectado pelo `ojdbc`), layout — a skill deve **informar** módulo único, sem perguntar. Responda "quero módulo dedicado" uma vez para conferir que a skill recusa com a explicação e segue no módulo único.

- [ ] **Step 3: Conferir o alvo C**

```bash
cd $SCRATCH/alvo-c
ls settings.gradle.kts; grep -c include settings.gradle.kts             # espera 0
find src/test -name '*.kt' | sort
grep -n 'testcontainers-oracle-free' build.gradle.kts
grep -n 'gvenzl/oracle-free:23-slim-faststart' src/test/kotlin/br/com/analizza/unico/support/BaseIntegrationTest.kt
./gradlew test --console=plain > /tmp/c-unit.log 2>&1; echo "EXIT=$?"; grep -c 'Creating container' /tmp/c-unit.log
./gradlew integrationTest --console=plain > /tmp/c-it.log 2>&1; echo "EXIT=$?"
grep -ho 'testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' build/test-results/integrationTest/*.xml
ls docs/checkpoints/README.md CLAUDE.md docs/INSTRUCTIONS.md
```

Expected: `0` includes; os quatro arquivos de teste; a dependência Oracle; a imagem; `EXIT=0` e `0` containers; `EXIT=0` (o Oracle pode levar minutos — timeout de 10 min no comando); suítes com `failures="0" errors="0"`; os três arquivos (sem convenções prévias, `docs/INSTRUCTIONS.md` foi criado).

- [ ] **Step 4: Alvo D — cópia do projeto de referência, só frontend**

```bash
cd $SCRATCH && rm -rf alvo-d && git clone -q /Users/diegolirio/Documents/Github/documents-eaf-system alvo-d
cd alvo-d && git log --oneline -1 && ls
```

Passos 0–11 com escopo `frontend`. Este projeto **já tem** Vitest, `vitest.config.mts`, testes, `docs/checkpoints/README.md` e o bloco no `CLAUDE.md`; o que se prova é que a skill detecta e **não duplica nem sobrescreve**, e acrescenta só o que falta (o `typecheck` do `-web` e os alvos/scripts do `-mobile`).

- [ ] **Step 5: Conferir o alvo D**

```bash
cd $SCRATCH/alvo-d
git status --short
git diff --stat
git diff -- docs/checkpoints/README.md CLAUDE.md documents-eaf-system-web/vitest.config.mts | wc -l   # espera 0
git status --short -- '*.gradle' '*.gradle.kts' '*/src/test/*' | wc -l                               # espera 0
grep -n 'typecheck' documents-eaf-system-web/package.json documents-eaf-system-mobile/package.json Makefile
cd documents-eaf-system-web && npm ci > /tmp/d-web-ci.log 2>&1; echo "EXIT=$?"; cd ..
make test-web > /tmp/d-web.log 2>&1; echo "EXIT=$?"
cd documents-eaf-system-mobile && npm ci > /tmp/d-mob-ci.log 2>&1; echo "EXIT=$?"; cd ..
make test-mobile > /tmp/d-mobile.log 2>&1; echo "EXIT=$?"
```

Expected: diff só em `package.json`/lockfiles/`Makefile` e no teste mínimo do `-mobile` se ele não tinha nenhum; `0` linhas de diff nos três arquivos que já existiam; `0` builds Gradle tocados; `typecheck` presente; `EXIT=0` em todos. Se `make test-web` falhar por erro de tipo que já existia no projeto de referência antes da skill, isso **não** é defeito da skill: registre o erro e confirme rodando o mesmo `tsc --noEmit` no clone antes da mudança (`git stash`).

- [ ] **Step 6: Limpeza e relatório**

Mesmo formato da Tarefa 6, Step 8. Nenhum processo, container ou daemon Gradle deixado de pé; nada tocado fora de `$SCRATCH`.

---

### Task 8: Pull request

**Files:** nenhum.

- [ ] **Step 1: Conferir**

```bash
cd /Users/diegolirio/Documents/Github/analizza-marketplace-wt-integration-test
git status --short
git log --oneline origin/main..HEAD
make validate > /tmp/it-validate.log 2>&1; echo "EXIT=$?"
make check > /tmp/it-check.log 2>&1; echo "EXIT=$?"
git diff --stat origin/main..HEAD -- plugins/analizza-skills/skills/analizza-java-integration-test plugins/analizza-skills/skills/analizza-kotlin-integration-test | tail -1   # espera vazio
```

- [ ] **Step 2: Perguntar antes de publicar**

Push e PR são ação para fora: perguntar ao usuário. Só seguir com um sim.

- [ ] **Step 3: Abrir o PR (após o sim)**

```bash
git push -u origin feat/analizza-integration-test
gh pr create --base main --title "Cria a analizza-integration-test unificada" --body-file <arquivo com o corpo>
```

O corpo traz: o que a skill faz; P1–P6; os quatro alvos com respostas, `EXIT=` e contagens reais das Tarefas 6 e 7; as provas de falha; o que não foi verificado (`IntegrationTestApplication` com mais de uma aplicação — nenhum alvo tem; MySQL — nenhum alvo usa; a skill instalada pelo marketplace publicado); e que as skills antigas saem na Entrega 4. Termina com `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

---

## Self-Review

- **Cobertura da spec (Entrega 2):** estrutura de pastas → Tarefas 2–4 (com `containers.md` único no lugar de `containers/*.md`, e build por layout no lugar de jacoco-aggregation/single-module — mesmo conteúdo, organizado pelo que o usuário escolhe); Passo 0 escopo → Tarefa 5; Passo 1 detecção/perguntas (D3, D4) → Tarefa 5; Passos 2–6 backend (matriz linguagem × DSL, "aplicar no existente" no `-api`, containers por banco, ArchUnit com `@RestController`/`@Scheduled`/`@KafkaListener`, `TestConfig`, atualização da seção *Testes*) → Tarefas 2, 3, 5; Passo 7 frontend (typecheck, Vitest, `jest-expo`, checkpoints, `CLAUDE.md`) → Tarefas 4, 5; Passo 8 regras → Tarefas 4, 5; Passo 9 instructions/README → Tarefa 5; Passo 10 verificar → Tarefa 5 e provas nas 6–7; Passo 11 WireMock → Tarefas 4, 5; limpeza (sem `quality-setup-*`, WireMock único, layout como pergunta) → Tarefas 4, 5; verificação da spec (quatro alvos, regra falhando, typecheck falhando) → Tarefas 6, 7. Os números de passo da skill seguem os da spec com o Passo 6 (documentar layout) separado, porque a spec o punha dentro dos Passos 2–6.
- **Pendências herdadas da Entrega 1:** assimetria `tasks.withType<Test>` (kts) × `tasks.named('test')` (Groovy) → resolvida no Passo 2 "Existente" (configura `test` explicitamente e deixa o `withType`); nome da regra → `EntrypointHasIntegrationTestIT` (P2); tamanho da reescrita de *Testes* → Passo 6.
- **Placeholders:** nenhum TBD; o corpo do PR é montado com dados reais das Tarefas 6–7.
- **Consistência:** `{base-package}`, `{app-class}`, `{app-package}`, `{container-*}`, `{testcontainers-db-module}`, `{project-dependencies}`, `{coverage-modules}`, `{src-dir}`, `{doubles}`, `{app-dir}`, `{conventions-file}` definidos e usados com o mesmo nome; pacote `support` e `architecture` iguais nos templates, no `SKILL.md` e nas conferências.
