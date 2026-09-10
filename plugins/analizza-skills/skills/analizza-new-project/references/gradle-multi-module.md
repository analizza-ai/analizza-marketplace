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

## `build.gradle` da raiz

O zip do Initializr não traz `build.gradle` de raiz — o zip é um projeto de
módulo único, e depois da reorganização acima a raiz só tem `settings.gradle`
e o wrapper. Sem um `build.gradle` na raiz, `buildingBlocks` e
`{project-name}-core` (que aplicam plugins do Kotlin e o
`io.spring.dependency-management` **sem** número de versão, ver os dois
templates) não têm de onde herdar essa versão: um subprojeto só aplica um
plugin sem versão se ele já estiver no classpath do buildscript herdado da
**raiz** — nunca de um subprojeto irmão. Sem esse arquivo, o build inteiro
morre com `Plugin [id: '...'] was not found ... plugin dependency must
include a version number`, nas duas linguagens.

A correção é o padrão usual de multi-módulo Gradle para plugin versionado: os
plugins entram na raiz com `apply false` e a versão explícita; os
subprojetos aplicam o mesmo `id` sem versão nenhuma, herdando-a do classpath
do buildscript da raiz.

Escreva-o **antes** de qualquer `./gradlew`, com as versões que o Initializr
já resolveu — não invente números. Leia-as do `plugins {}` de
`{project-name}-api/build.gradle`, que o Initializr acabou de gerar:

- a versão ao lado de `org.jetbrains.kotlin.jvm` (só existe quando
  `language=kotlin`) vira `{kotlin-version}`;
- a versão ao lado de `org.springframework.boot` vira `{boot-version}` — a
  mesma que o Passo 3 já validou no metadata, então bate com o que foi
  pedido;
- a versão ao lado de `io.spring.dependency-management` vira
  `{dependency-management-version}`.

Grave essas três em
[root-build.gradle.template](../templates/root-build.gradle.template) como
`build.gradle` da raiz, só o bloco condicional da `language` escolhida.

## `{project-name}-api/build.gradle`

Não reescreva o resto do arquivo. Duas alterações, as duas consequência
direta do `build.gradle` da raiz acima:

1. **Remova o número de versão** de cada `id` do `plugins {}` que também
   apareceu na raiz (`org.jetbrains.kotlin.jvm`,
   `org.jetbrains.kotlin.plugin.spring`, `org.jetbrains.kotlin.plugin.jpa`
   quando `language=kotlin`; `org.springframework.boot` e
   `io.spring.dependency-management` sempre). O plugin continua aplicado —
   só a versão que muda de dono, da folha para a raiz. Aplicar a mesma versão
   nos dois lugares reintroduz o conflito que a raiz existe para evitar (o
   Kotlin Gradle Plugin não aceita ser carregado com versão explícita em mais
   de um subprojeto).
2. Acrescente a dependência de projeto, dentro do bloco `dependencies` que já
   existe:

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
