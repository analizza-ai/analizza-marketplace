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
find . -maxdepth 1 \( -name 'docker-compose*.y*ml' -o -name 'compose*.y*ml' \) -exec grep -hoE 'image: *(postgres|gvenzl/oracle[^ ]*|container-registry.oracle[^ ]*|mysql)[^ ]*' {} +
```

Opções: `postgres`, `oracle`, `mysql`, outro. Com "outro", siga a seção
*Outro banco* de [containers.md](./templates/backend/containers.md).

**Layout.** Conte os `include` do `settings.gradle{dsl-ext}` e procure as
aplicações:

```bash
find . -maxdepth 1 -name 'settings.gradle*' -exec grep -E "include" {} +
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
find .github/instructions -name '*test*' 2>/dev/null; ls .github/copilot-instructions.md AGENTS.md 2>/dev/null
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
