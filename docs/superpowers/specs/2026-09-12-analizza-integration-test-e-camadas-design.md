# Design: `analizza-integration-test` unificada e arquitetura em camadas completa na `analizza-new-project`

Data: 2026-09-12

## Objetivo

Duas coisas, que se encontram no fim:

1. A `analizza-new-project` passa a carregar **todo** o template da arquitetura em camadas do
   projeto de referência (`documents-eaf-system`), escrito de forma genérica, e passa a gerar a
   DSL do Gradle que corresponde à linguagem escolhida.
2. As skills `analizza-java-integration-test` e `analizza-kotlin-integration-test` são fundidas
   numa só, `analizza-integration-test`, que ganha guardrails de frontend e as regras de projeto que
   no projeto de referência garantem qualidade fora da suíte. A `analizza-new-project` oferece
   essa skill ao fim do scaffold. As duas antigas são apagadas.

## Contexto: o que foi conferido

Comparação entre `documents-eaf-system` (`docs/INSTRUCTIONS.md` e código) e a skill em
`0.2.2`:

- Os 15 contratos Kotlin do `buildingBlocks` são idênticos aos templates depois de trocar
  `com.eaf.documents` por `{package}`. O `build.gradle` do módulo bate.
- Módulos, seta `-api → -core → buildingBlocks`, split package, árvores de `-api` e `-core`,
  fatia vertical, CQRS, ProblemDetail + 422, exceção de opacidade, auth, CORS e migrations já estão
  no `architecture-conventions.md.template`, genéricos.
- Faltam sete itens de camada (seção *Entrega 1*) e as regras de projeto que viraram a parte nova
  da `analizza-integration-test` (seção *Entrega 2*).

As skills de integração atuais divergem da convenção da new-project: criam módulo dedicado
`{base}-integration-tests` em multi-módulo, fixam Oracle, e usam Kotlin DSL (kotlin) / Groovy
(java). A new-project diz que o `-api` é o único módulo com Testcontainers, usa Postgres e gera
Groovy para as duas linguagens. As decisões abaixo resolvem essa divergência.

## Decisões

**D1 — DSL segue a linguagem.** `language=kotlin` → Gradle Kotlin DSL (`.kts`);
`language=java` → Gradle Groovy DSL. Vale para as duas skills. Cada template Gradle existe nas duas
DSLs como **arquivos separados**, e só o equivalente à linguagem entra no projeto — nunca DSL
misturada dentro de um mesmo build.

**D2 — Na `analizza-integration-test`, a DSL existente vence.** A skill detecta a DSL do build que
já existe e usa o template dela. A regra de D1 só decide quando não há build para detectar.
Consequência: um projeto Kotlin com Groovy (como o `documents-eaf-system`) recebe Groovy.

**D3 — Linguagem, banco e layout são detectados e perguntados.** A skill detecta cada um e
pergunta, uma pergunta por vez, com o valor detectado como padrão. A DSL não é perguntada — só
informada (D2).

**D4 — Layout é pergunta.** Opções: **módulo dedicado `{base}-integration-tests` (recomendado)**
ou **aplicar no módulo existente** — o `-api` num projeto `-api`/`-core`, `src/test` num
single-module. A skill não promove single-module para multi-módulo (regra que as skills atuais já
têm, mantida): em single-module a opção de módulo dedicado é recusada com a explicação.

**D5 — Guardrails de frontend: typecheck, teste unitário e checkpoints.** Teste de ponta a ponta
automatizado (Playwright) fica fora: automatizar o que é conferência humana destrói a propriedade
que a faz valer, e pediria desenho próprio.

**D6 — Paginação não entra em nenhuma das duas skills.** Continua em *Não está decidido* no
template de convenções: a escolha entre offset e cursor depende do produto.

**D7 — O "como" dos testes mora num lugar só.** A seção *Testes* do template de convenções da
new-project deixa de descrever como montar a infraestrutura (dependências, task
`integrationTest`) e aponta para a `analizza-integration-test`. A convenção (unitário no `-core`
sem Spring, IT terminado em `IT`, ArchUnit com um único trabalho) continua no template.

**D8 — Uma spec, quatro entregas, um plano por entrega.** Cada entrega é um PR revisável sozinho.

## Entregas

| # | Entrega | Depende de |
|---|---|---|
| 1 | `analizza-new-project`: itens de camada 1–7 + DSL por linguagem | — |
| 2 | `analizza-integration-test` nova | — |
| 3 | `analizza-new-project` oferece a `analizza-integration-test` ao fim | 1, 2 |
| 4 | Remoção de `analizza-java-integration-test` e `analizza-kotlin-integration-test` | 2 |

Todo o trabalho acontece num worktree do `analizza-marketplace`.

### Entrega 1 — `analizza-new-project`: camadas e DSL

#### DSL por linguagem

| Hoje | Passa a ser |
|---|---|
| `templates/root-build.gradle.template` (marcadores kotlin/java) | `root-build.gradle.template` (só Java) + `root-build.gradle.kts.template` (só Kotlin) |
| `templates/core-build.gradle.template` (marcadores) | `core-build.gradle.template` (Java) + `core-build.gradle.kts.template` (Kotlin) |
| `templates/buildingBlocks/build.gradle.template` (marcadores) | `build.gradle.template` (Java) + `build.gradle.kts.template` (Kotlin) |

- Os marcadores `<!-- se kotlin/java -->` saem desses três arquivos: a escolha passa a ser por
  arquivo. No `architecture-conventions.md.template`, que é texto, os marcadores ficam.
- Passo 4: `type=gradle-project-kotlin` quando `language=kotlin`, `type=gradle-project` quando
  `language=java`. `settings.gradle` / `settings.gradle.kts` e a sintaxe do `include` (Passo 5)
  seguem a DSL.
- `references/initializr-api.md`: reescrever o parágrafo que afirma "usa sempre
  `type=gradle-project`" e a nota "Por que `type` não muda com `language`" do `SKILL.md`, que passa
  a dizer por que muda.
- `references/gradle-multi-module.md` e `references/pitfalls.md`: nomes de arquivo passam a
  `build.gradle(.kts)` / `settings.gradle(.kts)` onde a DSL importa; exemplos de sintaxe nas duas
  formas quando diferirem (`include ':x'` vs `include(":x")`, `plugins { id '…' }` vs
  `plugins { id("…") }`).
- O conteúdo dos builds Kotlin DSL é tradução do Groovy atual, sem dependência nova nem removida.

#### Itens de camada no `architecture-conventions.md.template`

1. **`presenter/jobs/`** na árvore do `-api`, com o critério: um job agendado é **entrada** pelo
   mesmo motivo que uma Route — recebe um gatilho, monta o Command, chama o handler, traduz o
   resultado em log. Só o gatilho muda (relógio em vez de HTTP).
2. **`presenter/configuration/security/` e `presenter/configuration/exception/`**: já desenhadas
   na árvore; o texto de *Falha e corpo de erro* passa a localizar o `GlobalExceptionHandler` em
   `presenter/configuration/exception/` (hoje diz `presenter/configuration/`), e *Autenticação*
   localiza a validação de credencial em `presenter/configuration/security/`.
3. **Regra ArchUnit cobre jobs**: em *Testes*, todo entrypoint — `@RestController` ou classe com
   método `@Scheduled` — precisa de um `<Nome>IT`. O porquê: o risco de parar em silêncio é maior
   num job, porque ninguém recebe um 500 quando um agendamento para de rodar.
4. **Nuances dos contratos**, em *Os contratos do `buildingBlocks`*:
   - `ResultCommandHandler`: um handler quase passthrough para uma porta existe de propósito — é
     ele que impede a Route de injetar a porta direto e furar a regra de que o `-api` não importa
     `infrastructure/`. Handler magro é o preço de manter a seta.
   - `Entity`: herdar sem chamar `checkAllRules` é caso normal quando a invariante depende de um
     argumento da fábrica, não de um campo do agregado; aí a fábrica chama um `RuleChecker` direto.
   - `domain/services` (em *O que mora onde*): lógica pura, sem Spring e sem banco — é isso que a
     mantém no `-core` e não reescrita em `-web` e `-mobile`.
5. **Falhas**, em *Falha e corpo de erro*:
   - Nem toda falha é regra quebrada: recurso inexistente estoura uma exceção própria do `-core`,
     convertida em 404 pelo mesmo `GlobalExceptionHandler`, com corpo genérico que não repete o id
     nem diz se ele existiu.
   - No resultado fechado, o tipo cobre só o que o caso de uso **decide**. Falha inesperada
     (template quebrado, banco fora) não tem valor no tipo: sobe como exceção e vira 500. O tipo
     fechado existe para que decisão de negócio não vaze; a exceção existe para que defeito não se
     disfarce de sucesso.
6. **Recursos de saída no `-core`**, em *O que mora onde*: templates de mensagem e afins moram em
   `{project-name}-core/src/main/resources/<saída>/` (ex.: `mail/templates/`), pelo mesmo critério
   das migrations, e chegam ao `-api` pela dependência de projeto. O prefixo não pode colidir com
   as pastas que o Boot varre sozinho (`templates/`, `static/`).
7. **Dublês dos serviços de saída**, em *Testes*: um `support/TestConfig` no módulo de ITs registra
   `@Primary` com dublês de cada serviço de saída (e-mail, gateway externo), para que nenhuma
   mensagem nem chamada saia da suíte.

#### Árvore do Passo 8

O `mkdir` do `-api` passa a criar `presenter/routes`, `presenter/jobs`,
`presenter/configuration/security` e `presenter/configuration/exception`.

#### Fora de escopo (ajuste)

"Teste de arquitetura executável" sai da lista de *Fora de escopo* do `SKILL.md`: passa a ter dono
(Entrega 3).

### Entrega 2 — `analizza-integration-test`

Pasta `plugins/analizza-skills/skills/analizza-integration-test/`.

#### Estrutura

```
SKILL.md
references/
  wiremock.md                 fundido das duas antigas, exemplos em Java e Kotlin
  project-rules.md            texto das regras de projeto (Passo 8)
  checkpoints-readme.md       README genérico de docs/checkpoints/
templates/
  backend/
    source/                   escolhido pela linguagem
      java/
        BaseIntegrationTest.java.template
        IntegrationTestApplication.java.template
        EntrypointHasIntegrationTestRuleIT.java.template
        TestConfig.java.template
      kotlin/
        (mesmos nomes, extensão .kt)
    build/                    escolhido pela DSL (D2), independente da linguagem
      groovy/
        integration-tests-build.gradle.template
        root-build-jacoco-aggregation.gradle.template
        single-module-jacoco.gradle.template
      kts/
        (mesmos nomes, extensão .gradle.kts)
    archunit.properties.template
    containers/               trecho de container do BaseIntegrationTest por banco
      postgres.md
      oracle.md
      mysql.md
  frontend/
    web/                      vitest.config + teste mínimo + trecho do package.json
    mobile/                   jest (jest-expo) + teste mínimo + trecho do package.json
```

Fonte e build ficam em eixos separados porque D2 permite linguagem e DSL divergirem num projeto
que já existe (Kotlin com Groovy, por exemplo). Os trechos de build declaram dependências do
Kotlin (`kotlin-test-junit5`, `springmockk`) e do Java (`mockito`) em blocos marcados por
linguagem, e só o bloco da linguagem do projeto é gravado. Em projeto novo (D1) as combinações
são sempre `java` + `groovy` ou `kotlin` + `kts`.

#### Fluxo

**Passo 0 — Escopo.** Perguntar o que aplicar: backend, frontend ou os dois. Frontend só é
oferecido se existir `-web` ou `-mobile` (ou `package.json` com `next`/`expo`).

**Passo 1 — Detectar e perguntar** (só para backend). Uma pergunta por vez, detectado como padrão:

| Item | Detecção | Pergunta |
|---|---|---|
| Linguagem | extensão das fontes em `src/main` | java / kotlin |
| DSL | `build.gradle` vs `build.gradle.kts`; sem build, D1 | não pergunta, informa |
| Banco | driver no build, `spring.datasource.url`, serviços do `docker-compose` | postgres / oracle / mysql / outro |
| Layout | nº de módulos em `settings.gradle(.kts)`; formato `-api`/`-core` | módulo dedicado (recomendado) / aplicar no existente |

Quando invocada pela `analizza-new-project` (Entrega 3), os valores chegam preenchidos e cada
pergunta vira uma confirmação.

**Passos 2–6 — Backend.** Os passos atuais das duas skills (criar módulo ou não, isolar libs
pesadas, jacoco + tasks `test`/`integrationTest` por `@Tag("integration")`, `BaseIntegrationTest`
e organização dos ITs, assets de container em `src/test/resources/<engine>/`, ArchUnit), com:

- Fonte escolhido pela linguagem (`source/<linguagem>/`), build pela DSL (`build/<dsl>/`).
- Layout "aplicar no existente" num projeto `-api`/`-core`: ITs, `BaseIntegrationTest`,
  `TestConfig` e ArchUnit vão para `{project-name}-api/src/test/`; o `-core` não ganha dependência
  de container; sem `IntegrationTestApplication` (a `Application` do `-api` já faz o scan do
  `-core`).
- Container do `BaseIntegrationTest` montado a partir de `templates/backend/containers/<banco>.md`.
  Postgres e MySQL usam o módulo Testcontainers do banco; Oracle mantém o `Dockerfile`/`init.sql`
  por classpath das skills atuais.
- `EntrypointHasIntegrationTestRuleIT` cobre `@RestController`, `@Scheduled` e `@KafkaListener`.
- `TestConfig` com `@Primary` e um dublê por serviço de saída encontrado (interfaces em
  `infrastructure/data/anticorruptionLayer/**` ou equivalente); se nenhum for encontrado, o arquivo
  nasce com o comentário do padrão e nenhum bean.
- Layout módulo dedicado num projeto gerado pela new-project: atualizar a seção *Testes* do
  arquivo de convenções, trocando "o `-api` é o único módulo com Testcontainers" pelo módulo
  dedicado.

**Passo 7 — Frontend.** Para cada um de `-web` e `-mobile` que existir:

- **Typecheck:** `tsc --noEmit` no alvo `test-web` / `test-mobile` do `Makefile` (criar o alvo se
  não existir; se não houver `Makefile`, em `scripts.test` do `package.json`).
- **Teste unitário:** `-web` com Vitest (+ Testing Library), `-mobile` com `jest-expo`; um teste
  mínimo que renderiza a tela inicial; o alvo passa a rodar teste de verdade, não só lint.
- **Checkpoints:** `docs/checkpoints/README.md` a partir de `references/checkpoints-readme.md`
  (não é suíte de teste; um arquivo por funcionalidade, sem data; o `type` no topo; as quatro
  seções) e, no `CLAUDE.md` da raiz (criar se não existir; acrescentar se existir), a obrigação:
  toda funcionalidade criada ou alterada produz ou atualiza seu runbook.

**Passo 8 — Regras de projeto.** Acrescentar ao arquivo de convenções — o do SDD em uso, detectado
como na new-project (`references/sdd-frameworks.md` dela é a referência), senão
`docs/INSTRUCTIONS.md` — nunca sobrescrever:

- *Variáveis de ambiente*: toda variável lida pela configuração está no `README.md` sem valor e no
  `.env.local` se ele existir, no mesmo commit que a introduz.
- *Checkpoints de conferência*: quando propor (aparência, contrato com serviço externo, migration
  que muda dado existente, qualquer coisa irreversível), quando não propor (o que a suíte cobre), e
  que quem executa é uma pessoa.
- *Débitos técnicos*: seção vazia, com a regra de entrada (o que funciona mas carrega dívida
  conhecida, e o que fecha).
- Em *Testes*: um exemplo escrito à mão do formato de saída de outro sistema não é evidência sobre
  o que aquele sistema produz — teste de adapter usa a saída real do SDK/serviço.

**Passo 9 — Instructions e README.** O Passo 7 atual das skills antigas (atualizar instructions de
teste existentes e documentar a organização no `README.md`), mantido.

**Passo 10 — Verificar.** `./gradlew test` e `./gradlew integrationTest` com exit 0 e resultados
lidos no XML; `make test-web` / `make test-mobile` com exit 0.

**Passo 11 — Opcionais.** Perguntar sobre WireMock quando o projeto depende de HTTP externo.

#### Limpeza em relação às skills antigas

- Removida a oferta das skills `quality-setup-testcontainers-kafka/oracle/redis`, que não existem
  no marketplace. Oracle é coberto pelo Passo 1; Kafka e Redis ficam como nota de extensão no
  `BaseIntegrationTest`, sem skill externa.
- `references/wiremock.md` único no lugar das duas cópias.
- Os caminhos multi-módulo e single-module deixam de ser detectados-e-impostos: viram a pergunta de
  layout (D4).

### Entrega 3 — new-project oferece a skill

- Novo **Passo 11**, antes do relato: perguntar *"quer usar a `analizza-integration-test` para
  adicionar guardrails de testes de backend e frontend?"*. Se sim, invocar a skill passando
  `language`, DSL, banco (`postgres`), layout detectado (`-api`/`-core`) e a existência de `-web` e
  `-mobile`.
- "Relatar" vira **Passo 12** e informa se os guardrails foram aplicados e com quais respostas.
- A seção *Testes* do template de convenções aponta para a skill (D7).

### Entrega 4 — Remoção das antigas

- Apagar `skills/analizza-java-integration-test/` e `skills/analizza-kotlin-integration-test/`.
- `README.md`: as duas linhas da tabela viram uma, da `analizza-integration-test`.
- `.claude-plugin/marketplace.json`: `description` do plugin atualizada.
- `plugins/analizza-skills/.claude-plugin/plugin.json`: `0.2.2` → `0.3.0` (remover skill quebra
  quem a invocava pelo nome).
- Specs e planos antigos em `docs/superpowers/` ficam intactos: são histórico.

## Verificação

Skill não tem suíte automática; a prova é executar a skill em diretório descartável (scratchpad) e
o projeto gerado passar no build.

**Entrega 1.** Scaffold completo com `language=kotlin` e com `language=java`. Em cada um:
só a DSL esperada (`find . -name '*.gradle*'`); nenhum `<!-- se` sobrando; `./gradlew
:buildingBlocks:test` sem `NO-SOURCE`; `make build` com `EXIT=0` e testes lidos no XML; árvore do
Passo 8 com `presenter/jobs`, `configuration/security` e `configuration/exception`.

**Entrega 2.** Quatro execuções:

| Alvo | Linguagem / DSL | Layout | Banco |
|---|---|---|---|
| Scaffold Kotlin da Entrega 1 | kotlin / kts | módulo dedicado | postgres |
| Scaffold Java da Entrega 1 | java / groovy | aplicar no `-api` | postgres |
| Single-module do Initializr | kotlin / kts | `src/test` | oracle |
| Cópia do `documents-eaf-system` | kotlin / groovy (detectado) | só frontend | — |

Em cada uma: `./gradlew test` e `./gradlew integrationTest` com `EXIT=0` quando houver backend;
a regra ArchUnit **falha** ao remover um `IT` de propósito; `make test-web` **falha** com um erro de
tipo plantado. A última linha roda numa cópia, nunca no checkout do `documents-eaf-system`.

**Entrega 3.** Scaffold Kotlin respondendo "sim" no Passo 11: a `analizza-integration-test` só pede
confirmação, não repete as perguntas.

**Entrega 4.** `make validate`, `pytest tools/tests` e
`grep -rn "analizza-java-integration-test\|analizza-kotlin-integration-test"` fora de
`docs/superpowers/` devolvendo vazio.

**Não verificável pelo agente:** o plugin instalado pelo marketplace publicado (`make update`) e a
invocação `/analizza-skills:analizza-integration-test` a partir dele. Conferência do mantenedor,
depois do merge.

## Fora de escopo

Paginação (D6), teste de ponta a ponta automatizado (D5), CI/CD, skills de Testcontainers para
Kafka e Redis, migração de projetos que já usam as skills antigas, tag e release.
