# Do zip do Initializr ao multi-módulo

O `starter.zip` vem como projeto de módulo único, sem diretório raiz: os
arquivos estão no nível superior do zip. A reorganização move quatro coisas para
a raiz do monorepo e empurra o resto para `{project-name}-api/`.

## O que vai para onde

| Do zip | Destino | Por quê |
|---|---|---|
| `gradlew`, `gradlew.bat`, `gradle/` | raiz | um wrapper para o build inteiro |
| `settings.gradle` | raiz | é ele que declara os módulos |
| `.gitignore` | raiz | os padrões dele casam em qualquer profundidade |
| `build.gradle`, `src/`, `HELP.md` | `{project-name}-api/` | é o módulo de aplicação |

## Procedimento

Extraia em diretório temporário, nunca direto na raiz — extrair na raiz
espalharia `src/` no lugar errado e seria trabalhoso desfazer.

```bash
tmp=$(mktemp -d)
unzip -q starter.zip -d "$tmp"
mkdir -p {project-name}-api
mv "$tmp"/gradlew "$tmp"/gradlew.bat "$tmp"/gradle "$tmp"/settings.gradle "$tmp"/.gitignore .
mv "$tmp"/* "$tmp"/.[!.]* {project-name}-api/ 2>/dev/null
rmdir "$tmp"
chmod +x gradlew
```

O `chmod +x` é necessário: o bit de execução não sobrevive ao zip do Initializr
em toda combinação de ferramenta e sistema, e sem ele o `make build` morre com
"permission denied" antes de qualquer coisa útil acontecer.

## `settings.gradle`

O do Initializr traz apenas o `rootProject.name`. Reescreva o nome e acrescente
os dois `include`:

```gradle
rootProject.name = '{project-name}'
include ':{project-name}-api'
include ':{project-name}-core'
```

Os diretórios têm o mesmo nome dos projetos, então não é preciso
`project(':x').projectDir`.

## `{project-name}-api/build.gradle`

Não reescreva. O arquivo do Initializr funciona como subprojeto sem alteração
nenhuma — o único acréscimo é a dependência de projeto, dentro do bloco
`dependencies` que já existe:

```gradle
	implementation project(':{project-name}-core')
```

## `{project-name}-core/build.gradle`

Escrito do zero a partir de
[core-build.gradle.template](../templates/core-build.gradle.template). Ele **não**
aplica o plugin do Spring Boot: se aplicasse, o Gradle tentaria produzir um jar
executável de um módulo que não tem `main`, e o `bootJar` falharia.

O core também não conhece o `-api`. A seta é sempre `api → core`; nenhuma regra
extra é necessária para impedir o ciclo, porque um ciclo de projetos Gradle
simplesmente não configura.

## As migrations moram no core

`{project-name}-core/src/main/resources/db/migration/`. Elas chegam ao classpath
do `-api` pela dependência de projeto, então o `classpath:db/migration` padrão do
Flyway resolve sem nenhuma configuração adicional.

Crie o diretório com um `.gitkeep` — diretório vazio não sobrevive ao Git, e o
lugar precisa estar visível antes da primeira migration existir.

## Verificar que ficou de pé

```bash
./gradlew projects
```

Deve listar os dois subprojetos. Se listar só o raiz, o `include` não entrou.
