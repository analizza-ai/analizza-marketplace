---
name: analizza-new-project
description: >-
  Cria do zero um monorepo de quatro módulos: backend Java Spring Boot separado
  em {project-name}-api (controllers) e {project-name}-core (Clean Architecture +
  CQRS), mais {project-name}-web em Next.js e {project-name}-mobile em Expo. O
  backend vem da API do Spring Initializr e é refatorado para multi-módulo
  Gradle, com Postgres em docker-compose e migrations Flyway no core. As
  convenções de arquitetura são gravadas no arquivo do framework de
  Spec-Driven Development em uso, não como código de exemplo. Use quando o
  usuário pedir "novo projeto", "criar monorepo de quatro módulos", "projeto
  Java com core e api", "monorepo com web e mobile", ou invocar
  /analizza-new-project. Para Kotlin multi-módulo, use setup-kotlin-gradle.
argument-hint: "Sem argumentos — o nome vem da pasta raiz; group, pacote, versão do Java e dependências são perguntados com defaults"
---

# Novo projeto: monorepo de quatro módulos

```
{project-name}/
├── settings.gradle              rootProject.name + os dois include
├── gradlew, gradle/             wrapper do Initializr, na raiz
├── {project-name}-api/          Spring Boot: controllers, adapters, config
├── {project-name}-core/         Java puro: domínio e casos de uso
├── {project-name}-web/          Next.js
├── {project-name}-mobile/       Expo
├── docker-compose.yml           Postgres
├── Makefile
├── .gitignore
└── <arquivo do SDD>             convenções de arquitetura
```

## Quando usar

- Projeto novo, do zero, com backend Java separado em api e core
- Precisa de web e mobile no mesmo repositório
- **Não** use para o monorepo simples de dois módulos
- **Não** use para Kotlin multi-módulo com Oracle — essa é a `setup-kotlin-gradle`

## Entradas

| Entrada | Origem | Default |
|---|---|---|
| `project-name` | Nome da pasta raiz do workspace | — |
| `group` | Perguntar | `br.com.analizza` |
| `package` | Perguntar | `{group}.{project-name}` |
| `java-version` | Perguntar | `25` |
| `dependencies` | Perguntar | `web,actuator,postgresql,data-jpa,flyway` |
| `boot-version` | Do metadata do Initializr | `default` do metadata |
| `db-name` | Derivado | `{project-name}` com `-` trocado por `_` |

Não invente a `boot-version`: leia do metadata (passo 3).

## Procedimento

### Passo 1 — Verificar o ambiente

```bash
java -version; node -v; npx -v; docker info > /dev/null 2>&1 && echo "docker OK"
curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://start.spring.io/metadata/client
```

Precisa de JDK compatível com a `java-version`, Node com npx, Docker rodando, e
a API respondendo `200`. **Sem rede, pare e avise** — não escreva `build.gradle`
à mão (ver [referência do Initializr](./references/initializr-api.md)).

Se a pasta não estiver vazia, mostre o conteúdo e confirme com o usuário antes
de escrever qualquer coisa.

### Passo 2 — Coletar as entradas

Pergunte `group`, `package`, `java-version` e `dependencies` com os defaults da
tabela. O `project-name` vem da pasta; o `db-name` é derivado.

### Passo 3 — Validar o metadata

Siga [referência do Initializr](./references/initializr-api.md), seção "Validar
o metadata". Confirme que a `java-version` e a `boot-version` pretendidas
existem em `values`. Se não existirem, use o `default` do metadata e informe a
mudança ao usuário.

### Passo 4 — Gerar e reorganizar o backend

Baixe o `starter.zip` com `artifactId={project-name}-api`, **inspecione antes de
extrair**, e siga [gradle-multi-module.md](./references/gradle-multi-module.md)
para promover o wrapper à raiz, empurrar o resto para `{project-name}-api/`,
escrever o `settings.gradle`, criar o `{project-name}-core` a partir de
[core-build.gradle.template](./templates/core-build.gradle.template) e
acrescentar a dependência de projeto no api.

Confirme com `./gradlew projects` que os dois subprojetos aparecem.

### Passo 5 — Gerar web e mobile

**Antes de gerar, garanta que a raiz já é um repositório Git** — rode `git init`
se ainda não for (o Passo 8 repete essa checagem, então rodar aqui de novo não
tem custo). Sem um repositório na raiz, o `create-next-app` e o
`create-expo-app` criam um `.git` **próprio** dentro de cada pasta; um `git add
-A` posterior grava esses módulos como referência de submódulo (gitlink, modo
`160000`) em vez do conteúdo real, e o `grep` de auditoria do Passo 8 não
detecta isso — os dois módulos inteiros somem do repositório em silêncio (ver
[armadilhas](./references/pitfalls.md)).

```bash
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || git init

npx --yes create-next-app@latest {project-name}-web \
  --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes

npx --yes create-expo-app@latest {project-name}-mobile
```

Depois confirme que nenhum dos dois nasceu com repositório Git aninhado e que o
mobile veio com o template certo (ver [armadilhas](./references/pitfalls.md)):

```bash
for d in {project-name}-web {project-name}-mobile; do
  [ -d "$d/.git" ] && echo "ATENÇÃO: .git aninhado em $d"
done
[ -f {project-name}-mobile/package.json ] && { [ -d {project-name}-mobile/app ] || [ -d {project-name}-mobile/src/app ]; } \
  && echo "mobile OK" || echo "mobile FALHOU"
```

### Passo 6 — Arquivos da raiz

Copie [Makefile.template](./templates/Makefile.template) para `Makefile` e
[docker-compose.template](./templates/docker-compose.template) para
`docker-compose.yml`, substituindo `{project-name}` e `{db-name}`. Acrescente
[gitignore-extra.template](./templates/gitignore-extra.template) ao fim do
`.gitignore` que veio do Initializr — não o substitua.

Confirme que a indentação das receitas do Makefile ficou com TAB:

```bash
[ "$(grep -c $'^\t' Makefile)" -gt 30 ] && echo "TAB OK" || echo "TAB FALHOU"
```

Acrescente ao `{project-name}-api/src/main/resources/application.properties`:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/{db-name}
spring.datasource.username={db-name}
spring.datasource.password={db-name}
spring.jpa.hibernate.ddl-auto=none
```

É a única configuração que a skill escreve, e existe porque sem ela o
`make run` não sobe. Ela precisa casar com o `docker-compose.yml`.

### Passo 7 — Gravar as convenções de arquitetura

Siga [sdd-frameworks.md](./references/sdd-frameworks.md): detecte o framework,
escolha o destino e grave
[architecture-conventions.md.template](./templates/architecture-conventions.md.template)
com os placeholders substituídos.

Se o arquivo de destino já existir, **acrescente uma seção**, nunca sobrescreva.

**Não crie os pacotes descritos no template e não escreva código de domínio.** O
documento é a especificação do que deve ser construído; o scaffold entrega
apenas a estrutura mínima. Essa distinção é o ponto desta skill.

### Passo 8 — Git

Se ainda não for repositório, `git init`. Antes de commitar, audite o que entrou:

```bash
git add -A
git diff --cached --name-only | grep -cE 'node_modules|\.next/|\.expo/|build/'
git ls-files --stage | grep -c '^160000'
```

Os dois `grep` precisam devolver `0`. O segundo pega gitlinks (submódulo
implícito) — se `{project-name}-web` ou `{project-name}-mobile` aparecer como
gitlink em vez de conteúdo real, o `git init` do início do Passo 5 não rodou a
tempo; remova o `.git` aninhado da pasta afetada, rode `git rm -r --cached
<pasta>` e `git add -A` de novo antes de commitar. Faça um commit para o
scaffold.

### Passo 9 — Verificar

Obrigatório. Sem isso não há como afirmar que o scaffold funciona.

```bash
make build > /tmp/build.log 2>&1; echo "EXIT=$?"
```

`build-backend` e `test-backend` dependem de `db-up`: o teste padrão que o
Initializr gera sobe o contexto Spring inteiro, o que aciona o Flyway e falha
sem Postgres de pé. Por isso `make build` já sobe o banco sozinho — não é
preciso rodar `db-up` à parte antes.

Exija `EXIT=0` e confirme o resultado dos testes no XML, não pela ausência de
erro (ver [armadilhas](./references/pitfalls.md), seção "Verificação").

Smoke test com o banco de pé:

```bash
make run > /tmp/run.log 2>&1 &
# Até 60 tentativas de 2s (2min). Se estourar sem os dois healthchecks
# responderem, NÃO siga adiante: leia /tmp/run.log e reporte a falha.
for i in $(seq 60); do
  curl -sf http://localhost:8080/actuator/health >/dev/null 2>&1 \
    && curl -sf http://localhost:3000 >/dev/null 2>&1 && break
  sleep 2
done
curl -s http://localhost:8080/actuator/health   # espera status UP
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000   # espera 200
grep -iE 'flyway|hikari' /tmp/run.log | head
```

Se o loop estourar as 60 tentativas sem os dois healthchecks responderem, não
prossiga: leia `/tmp/run.log` (o `make run` está em background com log
redirecionado, então o erro não aparece em lugar nenhum além dele) e reporte a
falha ao usuário.

O log precisa mostrar o Flyway relatando zero migrations e o HikariPool
inicializando — é o que prova que o Postgres foi conectado de fato.

Encerre com SIGINT no grupo de processos do make, confirme que 8080 e 3000
ficaram livres e que não sobrou processo órfão. Depois `make doctor-mobile` e,
por último, `make db-down`.

### Passo 10 — Relatar

Informe ao usuário:

- Versões reais geradas (Boot, Java, Next, React, Expo) — leia dos arquivos, não
  repita as desta skill
- Resultado da verificação com os códigos de saída observados
- As vulnerabilidades do `npm audit` de web e mobile, deixando explícito que
  **não** foram corrigidas e por quê (ver armadilhas)
- Que o banco sobe sem schema: Flyway com zero migrations e nenhuma entidade é o
  esperado, não defeito
- Em qual arquivo as convenções de arquitetura foram gravadas

## Fora de escopo

Endpoint ou entidade de exemplo, autenticação, CORS, formato de erro, paginação,
upload de arquivos, teste de arquitetura executável, Dockerfile da aplicação,
CI/CD e integração entre os frontends e o backend.

A skill entrega a forma. A primeira fatia vertical é escrita por quem for
implementar, seguindo o arquivo do SDD.

## Notas

- Sem Turborepo, Nx ou workspaces npm/pnpm. `-web` e `-mobile` compilam
  independentes, e workspaces não abrangeriam os módulos Java de qualquer forma.
- O `create-next-app` também gera `AGENTS.md` e `CLAUDE.md` dentro do `-web`.
- `test-web` roda lint, não testes: o scaffold do Next não traz framework de
  teste. Troque quando houver um.
- `make run` não sobe o mobile. O Metro fica em `run-mobile`.
