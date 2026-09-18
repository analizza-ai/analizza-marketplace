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

Todo entrypoint precisa de dois testes — um unitário rápido do handler, com
dublê da dependência externa cobrindo os ramos de erro, e um IT real sobre
`BaseIntegrationTest` — e nenhum substitui o outro (ver
[testes-section.md](./references/testes-section.md) e o parágrafo *Testes*
de [project-rules.md](./references/project-rules.md)). Esta skill entrega só
a metade de integração e a regra ArchUnit que a garante; o unitário do
handler não tem guardrail automático aqui.

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
| `{group}`, `{java-version}` | lidos do build do módulo que aplica o plugin do Spring Boot |

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
find . -path '*/src/main/kotlin/*.kt' -not -path '*/build/*' -not -path '*/node_modules/*' | head -1   # achou: kotlin
find . -path '*/src/main/java/*.java' -not -path '*/build/*' -not -path '*/node_modules/*' | head -1   # achou: java
```

Se achar os dois, pergunte sem padrão.

**DSL — não pergunte, informe.** `settings.gradle.kts` → `kts`;
`settings.gradle` → `groovy`. Sem `settings`, a regra é a linguagem: `kotlin` →
`kts`, `java` → `groovy`. O build que já existe vence a regra: um projeto Kotlin
com `build.gradle` recebe Groovy.

**Banco.**

```bash
grep -rhoE 'org\.postgresql:postgresql|com\.oracle\.database\.jdbc:ojdbc[0-9]*|com\.mysql:mysql-connector-j|mysql:mysql-connector-java' --include='build.gradle*' --include='libs.versions.toml' . | sort -u
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
5. Todo `testImplementation` de starter de teste do Spring Boot
   (`spring-boot-starter-*-test`) que um módulo de origem declarar por causa
   de um teste que o Passo 4 move para cá, leve para
   `{base}-integration-tests`; tire do módulo de origem só se nada mais lá
   depender dele.

**Existente.** Mescle no `{it-module}/build.gradle{dsl-ext}` os trechos de
[existing-module.gradle.template](./templates/backend/build/groovy/existing-module.gradle.template)
(groovy) ou
[existing-module.gradle.kts.template](./templates/backend/build/kts/existing-module.gradle.kts.template)
(kts): acrescente ao `plugins {}` e ao `dependencies {}` que já existem, sem
duplicar linha, e substitua configurações anteriores de `test` e
`jacocoTestReport`. Uma configuração que aplique JUnit a todo `Test`
(`tasks.withType<Test>`) pode ficar: ela não conflita.

### Passo 3 — Aplicação do contexto de teste

**Existente:** `{app-class}` é o nome simples da `@SpringBootApplication` de
dentro do próprio `{it-module}` e `{app-package}`, o pacote dela — não conte
`@SpringBootApplication` de outros módulos, e não grave
`IntegrationTestApplication`: neste layout ela nunca existe.

**Dedicado:** conte as `@SpringBootApplication` do Passo 1 em todos os
módulos de produção do build.

- **Uma:** `{app-class}` é o nome simples dela e `{app-package}`, o pacote.
- **Mais de uma:** grave `{it-src}/IntegrationTestApplication.{kt|java}` a
  partir de
  [IntegrationTestApplication.kt.template](./templates/backend/source/kotlin/IntegrationTestApplication.kt.template)
  ou
  [IntegrationTestApplication.java.template](./templates/backend/source/java/IntegrationTestApplication.java.template);
  `{app-class}=IntegrationTestApplication`, `{app-package}={base-package}`.
  Copie para ela toda anotação das classes `@SpringBootApplication`
  originais além da própria `@SpringBootApplication` (ex.: `@EnableScheduling`,
  `@EnableAsync`, `@EnableKafka`, `@ConfigurationPropertiesScan`,
  `@EnableConfigurationProperties`, `@EntityScan`), com os imports
  correspondentes — o template já deixa um comentário lembrando disto. Se os
  módulos têm `application.properties`/`.yml` com nomes diferentes, liste
  todos em `spring.config.name` numa `properties` do `@SpringBootTest`; se
  dois módulos tiverem arquivo de configuração com o **mesmo nome**, avise o
  usuário e use `spring.config.import`, com o caminho de classpath explícito
  de cada um, em vez de `spring.config.name`.

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
  interface assim, `{doubles}` fica vazio. Em Kotlin, não escreva um glob com
  `/*` ou `**/` dentro de um KDoc (`/** … */`): Kotlin aninha comentários de
  bloco, e a sequência `*/` embutida no glob fecha o comentário antes da hora
  e o arquivo para de compilar — escreva o caminho sem o glob (ex.:
  `infrastructure/data/anticorruptionLayer`, sem o `/**` final).
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

Resolva `{conventions-file}` com a mesma ordem de detecção da
`analizza-new-project` — pare no primeiro sinal que bater (tabela "Detecção"
de
[sdd-frameworks.md](../analizza-new-project/references/sdd-frameworks.md)):

```bash
if   [ -d openspec ];                then conventions_file=openspec/PROJECT.md
elif [ -d specs ] || [ -d .specify ]; then conventions_file=specs/CONSTITUTION.md
elif [ -d docs/superpowers ];         then conventions_file=docs/superpowers/INSTRUCTIONS.md
else                                       conventions_file=docs/INSTRUCTIONS.md
fi
```

Se `{conventions-file}` existir e tiver uma seção *Testes*
(`grep -qE '^#{1,4} Testes$'` — o título conta como existente em qualquer
nível de heading), troque o **corpo inteiro** da seção — mantendo o heading
dela — pelo texto de
[testes-section.md](./references/testes-section.md), com os placeholders
substituídos. Parágrafos da seção antiga que não são sobre a infraestrutura de
teste (ex.: uma lição aprendida) ficam depois do novo corpo.

Sem `{conventions-file}` ainda no disco, ou sem seção *Testes* nele, este
passo não faz nada; o Passo 9 cria o arquivo e/ou acrescenta a seção, com o
mesmo corpo de [testes-section.md](./references/testes-section.md).

### Passo 7 — Frontend

Só roda se existir `{web-dir}` ou `{mobile-dir}` (Passo 0). Para cada um:

**`-web` (Next.js).**

Confira `@types/node` antes de instalar: o Vitest atual (via Vite) exige
`@types/node ^22 || >=24` como peer, e o scaffold padrão do Next.js fixa uma
major mais velha (ex.: `^20`), o que derruba o `npm install` com `ERESOLVE`.

```bash
(cd {web-dir} && node -p "require('./package.json').devDependencies?.['@types/node'] ?? ''")
```

Se a major for menor que 22, troque `devDependencies["@types/node"]` para
`"^24"` no `package.json` antes de instalar. Nunca use `--legacy-peer-deps`
para contornar o `ERESOLVE`: isso deixa o `vite` fora do `package-lock.json` e
quebra o `npm ci` depois.

```bash
(cd {web-dir} && npm install --save-dev vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom)
```

Grave `vitest.config.mts` e `vitest.setup.ts` a partir de
[vitest.config.mts.template](./templates/frontend/web/vitest.config.mts.template)
e [vitest.setup.ts.template](./templates/frontend/web/vitest.setup.ts.template),
e o teste mínimo ao lado da página raiz (`src/app/page.test.tsx`, ou
`app/page.test.tsx` sem `src/`). Se já existir um `page.test.tsx`, não
sobrescreva. Senão, confira antes o corpo da página raiz:

```bash
grep -nE '\b(permanentRedirect|redirect)\(' <página raiz>
```

Se a página só faz essa chamada — o corpo da página é só a chamada, sem JSX
próprio — use
[page-redirect.test.tsx.template](./templates/frontend/web/page-redirect.test.tsx.template)
com `{redirect-target}` = o caminho passado a `redirect`/`permanentRedirect` e
`{redirect-fn}` = qual das duas o grep achou; o template mocka as duas
funções, para não quebrar se a página trocar de uma para a outra sem que este
arquivo seja atualizado. Senão, use
[page.test.tsx.template](./templates/frontend/web/page.test.tsx.template).
Não sobrescreva um `vitest.config.*` existente: mescle.

**`-mobile` (Expo).**

```bash
(cd {mobile-dir} && npx expo install jest-expo jest @types/jest @testing-library/react-native -- --save-dev)
```

No `package.json`, acrescente `"jest": { "preset": "jest-expo" }` se não
houver configuração de jest. Siga
[mobile-jest.md](./references/mobile-jest.md) antes de escrever o teste — ele
cobre gaps do Expo/Reanimated/Worklets/NativeWind que o `jest-expo` sozinho
não resolve. Grave `__tests__/tela-inicial-test.tsx` a partir de
[tela-inicial-test.tsx.template](./templates/frontend/mobile/tela-inicial-test.tsx.template),
com `{app-dir}` = `./src/app` se existir `src/app`, senão `./app`. Se o
`tsc --noEmit` reclamar de `expo-env.d.ts` ausente, crie-o com
`/// <reference types="expo/types" />` (é o que o `expo start` geraria).

### Passo 8 — Makefile e checkpoints

Roda para todo escopo, inclusive backend sem frontend: um projeto só de API
também precisa de `make test-backend`/`make test-integration` e de um
runbook.

**Makefile.** Acrescente os alvos do `Makefile` de
[makefile-targets.md](./templates/frontend/makefile-targets.md) e, para cada
frontend do Passo 0, os `scripts` `test` e `typecheck` do `package.json` —
só os alvos e os `scripts` das partes que existirem (sem `-mobile`, sem
`test-mobile`; sem backend, sem `test-backend`/`test-integration`).

**Checkpoints.** Decida `{conventions-file}` — a resolução do Passo 6, ou
`docs/INSTRUCTIONS.md` a ser criado se nenhuma bateu — **antes** de gravar o
bloco do `CLAUDE.md` abaixo, porque ele referencia esse caminho. Grave
`docs/checkpoints/README.md` a partir de
[checkpoints-readme.md](./references/checkpoints-readme.md) se ele não
existir, e acrescente ao `CLAUDE.md` da raiz o bloco de
[claude-md-obligation.md](./references/claude-md-obligation.md) — com
`{conventions-file}` substituído — se
`grep -qE '^#{1,4} O que "pronto" inclui$' CLAUDE.md` não achar — a seção conta
como existente em qualquer nível de heading. Os checkpoints entram também num
projeto só com backend: um runbook `api` é tão devido quanto um de tela.

### Passo 9 — Regras de projeto

Destino: `{conventions-file}` do Passo 6; sem nenhuma ainda resolvida, crie
`docs/INSTRUCTIONS.md` (com um título `# {base}`). Acrescente as seções de
[project-rules.md](./references/project-rules.md) que o arquivo ainda não
tiver — pelo `grep -qE '^#{1,4} <título>$'` de lá, que conta um título em
qualquer nível de heading como já existente, não só `##` — e o parágrafo de
*Testes* dentro da seção *Testes* (pule esse parágrafo se
`grep -q 'não é evidência sobre o que aquele sistema produz'` já achar). Se
`{conventions-file}` não tiver seção *Testes* ainda (o Passo 6 não achou uma),
crie-a agora com o corpo de
[testes-section.md](./references/testes-section.md), placeholders
substituídos, e só então acrescente o parágrafo de *Testes* dentro dela. Nunca
sobrescreva. Quando as seções entram
num arquivo cujas seções irmãs são `###` (ex.: aninhadas sob `##
Arquitetura`), acrescente-as no mesmo nível dessas irmãs. Se criou o arquivo,
diga no relatório — e confira que o bloco do `CLAUDE.md` aponta para ele em
`{conventions-file}`.

### Passo 10 — Instructions de teste e README

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
onde os ITs moram. Sem `README.md` na raiz, crie-o com um título `# {base}` e
essa seção *Testes*.

### Passo 11 — Verificar

Obrigatório. Redirecione a saída e leia o código de saída, nunca por pipe:

```bash
./gradlew test --console=plain > /tmp/it-unit.log 2>&1; echo "EXIT=$?"
./gradlew integrationTest --console=plain > /tmp/it-integration.log 2>&1; echo "EXIT=$?"
find . -path '*/build/test-results/integrationTest/*.xml' -not -path '*/node_modules/*' \
  -exec grep -ho 'testsuite name="[^"]*" tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' {} \;
find . -path '*/build/test-results/test/*.xml' -not -path '*/node_modules/*' \
  -exec grep -l 'Creating container' {} +
```

Exija `EXIT=0` nos dois e, nos XML de `integrationTest`, `failures="0"
errors="0"` com `ApplicationContextIT` e `EntrypointHasIntegrationTestIT`
presentes (`tests` ≥ 1 em cada). `./gradlew test` não pode subir container: o
segundo `find` acima — sobre os XML de `test`, nunca sobre os de
`integrationTest` — não pode imprimir nenhum arquivo; um `grep -c` sobre o log
do console não serve, porque o console pode não imprimir a mensagem do
Testcontainers mesmo quando um container sobe.

Prove que a regra falha quando deve: crie um controller descartável sem IT,
rode de novo e exija falha nomeando-o — o nome aparece na saída do console de
`integrationTest` (o `testLogging` do build o imprime) e também em
`build/test-results/integrationTest/*.xml`; apague-o e rode de novo até
verde.

```kotlin
// {it-module de producao}/src/main/{src-dir}/{base-package}/SemTesteController.kt (descartavel)
@org.springframework.web.bind.annotation.RestController
class SemTesteController
```

```java
// {it-module de producao}/src/main/{src-dir}/{base-package}/SemTesteController.java (descartavel)
package {base-package};

@org.springframework.web.bind.annotation.RestController
public class SemTesteController {
}
```

Frontend: `make test-web` e `make test-mobile` (ou `npm run typecheck && npm
test` em cada diretório) com exit 0. Prove o typecheck: acrescente num arquivo
`.ts` do `-web` a linha `const quebra: number = "texto";`, exija falha do
`typecheck`, desfaça.

### Passo 12 — Relatar e oferecer WireMock

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
