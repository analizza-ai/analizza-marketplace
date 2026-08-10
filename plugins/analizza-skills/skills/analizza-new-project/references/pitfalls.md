# Armadilhas conhecidas

Cada item aqui custou tempo de depuração real. Leia antes de "corrigir" algo que
parece estranho no scaffold gerado.

## Makefile

### `sed` engole a saída dos serviços

Prefixar log com `| sed 's/^/[backend] /'` funciona num terminal e falha em
qualquer outro lugar: o `sed` passa a usar buffer de bloco quando a saída não é
um TTY. Com `make run > log.txt`, o arquivo fica **sem nenhuma linha** dos
serviços, mesmo com tudo rodando normalmente.

Use `awk` com `fflush()`:

```make
| awk '{ print "[backend]  " $$0; fflush() }'
```

O `fflush()` do awk é portável entre BSD (macOS) e GNU. O modo unbuffered do sed
não é: `-l` no BSD, `-u` no GNU.

Dentro do Makefile o `$0` do awk vira `$$0`, senão o make interpreta como
variável dele.

### `trap` com `echo` imprime várias vezes

Todo subshell do grupo herda o `trap` e executa o corpo dele. Um
`trap 'echo "encerrando..."; kill 0' INT` imprimiu a mensagem **7 vezes** num
Ctrl+C. Mantenha o trap silencioso: `trap 'kill 0' INT TERM`.

### `make run` sai com código diferente de zero

`kill 0` derruba o grupo de processos inteiro, incluindo o próprio make. O
Ctrl+C portanto encerra com código ≠ 0 (144 no teste). É esperado para um alvo
que sobe servidor. Para CI, use `run-api` / `run-web` com controle
próprio de ciclo de vida.

### Receitas precisam de TAB

Indentação de receita no Makefile é TAB, não espaços. Ao gerar o arquivo,
confirme:

```bash
grep -c $'^\t' Makefile
```

## Spring Boot 4.x

### Os starters foram renomeados

Memória muscular do Boot 3.x gera dependências inexistentes:

| Boot 3.x | Boot 4.x |
|---|---|
| `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| (console embutido) | `spring-boot-h2console` |
| `spring-boot-starter-test` | granulares: `-actuator-test`, `-data-jdbc-test`, `-webmvc-test` |

Este é o motivo de a skill chamar a API do Initializr em vez de manter um
`build.gradle` estático.

### `HELP.md` já vem ignorado

O `.gitignore` gerado pelo Initializr tem `HELP.md` na primeira linha. Um
`git mv HELP.md` falha com "not under version control". Use `mv` comum.

## Frontends

### Nunca rode `npm audit fix --force`

O `npm audit` acusa vulnerabilidades high em dependências transitivas do Next
(`sharp`, `postcss`). A correção proposta instala `next@9.3.3` — sete majors
para trás, quebrando o projeto inteiro. A remediação é pior que o problema.

Reporte as vulnerabilidades ao usuário e **não faça nada**. A resolução real
depende do upstream do Next atualizar o range do `sharp`.

### `create-next-app` e `create-expo-app` precisam de um Git já existente na raiz

Os dois detectam um repositório Git existente e não criam outro dentro da
pasta gerada. O problema é a **ordem**: se o Passo 5 (gerar web e mobile) rodar
antes de qualquer `git init` na raiz, os dois comandos criam um `.git` **cada
um o seu**, porque não encontram repositório nenhum acima deles.

O estrago não aparece na hora: ele aparece no Passo 8. Um `git add -A` sobre
uma pasta com `.git` próprio não copia o conteúdo dela — grava um **gitlink**
(entrada de modo `160000`, o mesmo mecanismo de submódulo), e o `grep` de
auditoria do Passo 8 (`node_modules|\.next/|\.expo/|build/`) não pega isso,
porque não é nenhum desses padrões. O commit fica "limpo" segundo a auditoria
e mesmo assim `{project-name}-web` e `{project-name}-mobile` inteiros ficam de
fora do repositório — um `git clone` do monorepo traria as duas pastas vazias.

A correção é causal, não posterior: rode `git init` (idempotente, ver
`git rev-parse --is-inside-work-tree`) **antes** de gerar web e mobile, não
depois. Confirme mesmo assim que nenhum `.git` aninhado sobrou:

```bash
[ -d {project-name}-web/.git ] && echo "ATENÇÃO: .git aninhado em {project-name}-web"
[ -d {project-name}-mobile/.git ] && echo "ATENÇÃO: .git aninhado em {project-name}-mobile"
```

E, no Passo 8, confirme que nada virou gitlink:

```bash
git ls-files --stage | grep -c '^160000'   # precisa ser 0
```

### `create-expo-app` muda de flags e de layout entre versões

As flags de template do `create-expo-app` mudam com frequência, e uma flag
inválida faz o comando cair no modo interativo em vez de falhar. Não confie no
código de saída: confirme o resultado.

```bash
[ -f {project-name}-mobile/package.json ] && { [ -d {project-name}-mobile/app ] || [ -d {project-name}-mobile/src/app ]; } \
  && echo "mobile OK" || echo "mobile FALHOU"
```

O diretório do expo-router mudou de `app/` para `src/app/` a partir do SDK 57
— por isso a checagem aceita os dois. O que importa é a presença de **um dos
dois**, não a raiz `app/` especificamente: é isso que distingue o template com
expo-router do template mínimo.

### `tsc --noEmit` falha num scaffold recém-gerado, antes de qualquer código

`build-mobile` roda `npx tsc --noEmit` para checar tipos sem pagar o custo de
`expo export`. Num checkout novo isso falha com `TS2307`/`TS2882` em imports de
CSS (`*.module.css`, `global.css`) do próprio template padrão — não é um erro
introduzido depois, é o estado inicial.

A causa: a declaração ambiente que cobre esses imports mora em
`expo-env.d.ts` (`/// <reference types="expo/types" />`), e esse arquivo **não
vem no template** — a CLI do Expo só o escreve quando `expo start` roda pela
primeira vez (é gerado em tempo de execução, por isso está no
`.gitignore` do próprio scaffold). Como o Metro fica fora do `make build` e do
`make run` (ver abaixo), nunca haveria um `expo start` para gerar o arquivo.

A correção não é rodar `expo start`: é escrever o mesmo conteúdo de um jeito
que não precise de servidor. `build-mobile` cria o arquivo se ele não existir,
antes do `tsc`:

```make
cd $(MOBILE_DIR) && [ -f expo-env.d.ts ] || echo '/// <reference types="expo/types" />' > expo-env.d.ts
```

É texto estático e documentado pela própria CLI do Expo (não é um número que
envelhece como o `junit-bom` do core), então não precisa de manutenção.

### O Metro não entra no smoke test

O `create-expo-app` não gera alvo de build de CI — `expo export` empacota para
publicação e é caro demais para uma verificação de scaffold. O que se verifica é
`npx tsc --noEmit` (compila) e `npx expo-doctor` (dependências coerentes com a
versão do SDK).

O Metro quer o terminal e não tem healthcheck HTTP comparável ao do backend ou
do Next. Por isso ele fica fora do `make run`, no alvo `run-mobile`.

### Avisos de install script do npm 11

O npm 11 bloqueia postinstall de `sharp` e `unrs-resolver` pelo gate
`allow-scripts`. O build de produção passa mesmo assim. Só libere com
`npm approve-scripts sharp` se a otimização de imagens der problema.

## Postgres e Flyway

### `make build` falha sem o banco de pé, mesmo sem nenhuma migration

O teste `contextLoads()` que o Initializr gera sobe o `ApplicationContext`
inteiro. Com `data-jpa`, `postgresql` e `flyway` no classpath, subir o contexto
aciona o autoconfigure do Flyway, que tenta conectar no Postgres **na
inicialização do bean**, antes de qualquer migration rodar. Sem banco, o teste
falha com `FlywaySqlUnableToConnectToDbException`, e `./gradlew build` sai com
código diferente de zero — num scaffold que ainda não tem uma linha de código
de domínio.

Isso não é um defeito do teste gerado nem algo para "corrigir" no `-api`: é o
comportamento padrão do Spring Boot com essas dependências. A correção é
`build-backend` e `test-backend` dependerem de `db-up` no Makefile, para que
`make build` funcione sozinho, na ordem em que o Passo 9 o executa, sem exigir
que quem roda o comando saiba de antemão que precisa subir o banco primeiro.
`db-up` usa `docker compose up -d --wait`, então chamar duas vezes (por
exemplo `make build` seguido de `make run`) não tem custo — o segundo `db-up`
só confirma que o healthcheck já passou.

### `db/migration` vazio não derruba a aplicação

Com zero migrations, o Flyway do Spring Boot registra que não encontrou nada e
segue. O `spring.flyway.fail-on-missing-locations` é `false` por padrão, então
nem a ausência do diretório derruba a subida.

Ainda assim, crie o diretório com `.gitkeep`: o lugar canônico das migrations
precisa estar visível antes da primeira existir, e diretório vazio não sobrevive
ao Git.

Um projeto que sobe com banco sem tabela nenhuma é o **resultado esperado** deste
scaffold, não defeito. Diga isso ao usuário no relatório final, senão ele vai
procurar o que não quebrou.

### `docker compose up -d` retorna antes do banco aceitar conexão

O container fica `running` muito antes do Postgres aceitar conexão, e o backend
sobe primeiro e morre no HikariPool. Use o healthcheck do compose junto com
`--wait`:

```bash
docker compose up -d --wait
```

O `--wait` bloqueia até o healthcheck passar. Sem ele, o `make run` fica com
uma corrida que falha de forma intermitente — o pior tipo de falha.

### A única versão de dependência Java pinada da skill

O `core-build.gradle.template` pina o `junit-bom`, porque o core não tem o BOM
do Spring Boot para gerenciar versões. É o único número congelado entre as
dependências Java da skill (o `docker-compose.template` também pina o
`postgres:17-alpine`, mas isso é a imagem do banco, não uma dependência Java).
BOM desatualizado não quebra build; ao notar que envelheceu, bump direto no
template.

O `-api` não tem esse problema: as versões dele vêm do Initializr.

## Verificação

### `-q` do Gradle esconde o resultado

`./gradlew build -q | tail` suprime o "BUILD SUCCESSFUL", e num pipe o `$?`
passa a ser o da última etapa do pipeline, não o do gradle. Redirecione para
arquivo e capture o código explicitamente:

```bash
./gradlew build > /tmp/be.log 2>&1; echo "EXIT=$?"
```

### Jar gerado não prova que funciona

O build produz o jar antes de rodar os testes. Confirme o resultado real no XML:

```bash
python3 -c "
import glob, xml.etree.ElementTree as ET
for f in glob.glob('*/build/test-results/test/*.xml'):
    r = ET.parse(f).getroot()
    print(r.get('name'), 'tests=', r.get('tests'), 'failures=', r.get('failures'))
"
```

No smoke test do `make run`, o log precisa mostrar o Flyway relatando zero
migrations e o HikariPool inicializando — é isso que prova que o Postgres foi
realmente conectado, e não apenas que o projeto compilou.
