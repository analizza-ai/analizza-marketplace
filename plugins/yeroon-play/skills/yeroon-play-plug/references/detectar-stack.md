# Detectar a stack do projeto

Rode da raiz do projeto cliente. Os comandos funcionam em macOS e Linux. Se alguma tabela
abaixo não decidir, pergunte à pessoa em vez de supor.

## 1. Back (Spring Boot)

```bash
# Arquivos de build (ignora dependências e saídas)
find . -type f \( -name build.gradle -o -name build.gradle.kts -o -name pom.xml \) \
  -not -path '*/node_modules/*' -not -path '*/build/*' -not -path '*/target/*'

# Qual deles usa Spring Boot
grep -lE 'org\.springframework\.boot|spring-boot' \
  $(find . -type f \( -name build.gradle -o -name build.gradle.kts -o -name pom.xml \) \
    -not -path '*/node_modules/*' -not -path '*/build/*' -not -path '*/target/*')

# Linguagem: maioria dos fontes em src/main
echo "java: $(find . -path '*/src/main/*' -name '*.java' | wc -l)  kotlin: $(find . -path '*/src/main/*' -name '*.kt' | wc -l)"

# Módulos Gradle
cat settings.gradle settings.gradle.kts 2>/dev/null | grep -E 'include'
# Módulos Maven
grep -E '<module>' pom.xml 2>/dev/null

# Onde está a classe @SpringBootApplication
grep -rlE '@SpringBootApplication' --include='*.java' --include='*.kt' . | grep -v '/build/'
```

| Achado | Decisão |
|---|---|
| `build.gradle.kts` | Gradle KTS |
| `build.gradle` | Gradle Groovy |
| `pom.xml` | Maven |
| Mais `.kt` que `.java` em `src/main` | Back Kotlin (molde `back-kotlin-spring`) |
| Mais `.java` que `.kt` | Back Java (molde `back-java-spring`) |
| Empate ou mistura | Perguntar; padrão: a linguagem da classe `@SpringBootApplication` |
| Módulos `{base}-api` e `{base}-core` | Rotas e webhook no `-api`; cliente da `/v1`, entidade e migration no `-core` (Spring é permitido lá). Respeite o que o `-api` e o `-core` já fazem |
| Módulo único | Tudo nele, nas pastas que já existem. Não crie `presenter/application/domain` se o projeto não tem |
| Vários módulos com `@SpringBootApplication` | Perguntar em qual plugar |
| Nenhum build com Spring Boot | **Parar** (ver "Quando não reconhece") |

O módulo do back é o que contém a classe `@SpringBootApplication` (ou o `-api`). O `.env` e o
`application.yml` que valem são os dele.

## 2. Front e mobile

```bash
# Web / Expo
find . -name package.json -not -path '*/node_modules/*' | while read f; do
  if grep -q '"next"' "$f"; then echo "next: $f"; fi
  if grep -q '"expo"' "$f"; then echo "expo: $f"; fi
done

# Flutter
find . -name pubspec.yaml -not -path '*/.dart_tool/*' -not -path '*/node_modules/*' \
  | while read f; do grep -q 'flutter' "$f" && echo "flutter: $f"; done
```

| Achado | Decisão |
|---|---|
| `package.json` com `next` | Front Next (molde `front-next`) |
| `package.json` com `expo` | Mobile Expo (molde `mobile-expo`) |
| `pubspec.yaml` com `flutter` | Mobile Flutter (molde `mobile-flutter`) |
| Vários | Plugar em **todos** os reconhecidos |
| `package.json` sem `next` nem `expo` (React puro, Vite, React Native sem Expo…) | Não reconhecido: avisar e seguir sem ele |

Runner de teste do front: leia `scripts` e `devDependencies` do `package.json` (`vitest`, `jest`,
`jest-expo`) e use o que já existe.

## 3. Mecanismo de migration

```bash
grep -rlE 'flyway' --include='build.gradle' --include='build.gradle.kts' --include='pom.xml' .
grep -rlE 'liquibase' --include='build.gradle' --include='build.gradle.kts' --include='pom.xml' .
find . -type d \( -path '*/db/migration' -o -path '*/db/changelog' \) -not -path '*/build/*' -not -path '*/target/*'
ls $(find . -type d -path '*/db/migration' -not -path '*/build/*' | head -1) 2>/dev/null | tail -5   # versão atual
```

| Achado | Decisão |
|---|---|
| Flyway (dependência ou `db/migration`) | `V{próxima}__video.sql` na pasta existente, seguindo a numeração e o padrão de nome atuais |
| Liquibase (dependência ou `db/changelog`) | Novo changeset no changelog mestre existente |
| Nenhum dos dois | **Parar e perguntar** como o projeto cria tabelas. Nunca criar um `db/migration` solto |

## 4. Porta do front

```bash
grep -nE '"(dev|start)"' package.json                 # scripts
grep -rnE 'next dev( |.*)(-p|--port)[ =]*[0-9]+' package.json
grep -rnE '^PORT=' .env .env.local .env.development 2>/dev/null
grep -rnE 'expo start.*--port' package.json
```

Ordem: `next dev -p N` / `--port N` → `PORT=N` no `.env*` → padrão **3000**. A porta define a
origem de dev: `http://localhost:{porta}`, a que vai no signup e em `{front-origin}`.

| Porta | Aviso |
|---|---|
| 3000 | Nada |
| Diferente de 3000 | **Avisar**: o CORS do R2 do yeroon só libera `http://localhost:3000`; o upload pelo navegador vai falhar. Recomendar rodar o front na 3000 em dev, ou pedir ao time do yeroon para incluir a origem. App Expo/Flutter não é afetado |

## 5. Conflito de nome `video`

O molde cria uma entidade `Video` e a tabela `video` (mais `webhook_receipt`). Antes de planejar:

```bash
grep -rniE 'create table( if not exists)? +"?video"?[ (]' --include='*.sql' --include='*.xml' --include='*.yml' .
grep -rnE '@Table\(.*name *= *"video"' --include='*.java' --include='*.kt' .
grep -rnE '(class|data class) +Video\b' --include='*.java' --include='*.kt' . | grep -v '/build/'
grep -rniE 'create table( if not exists)? +"?webhook_receipt"?' --include='*.sql' .
```

| Achado | Decisão |
|---|---|
| Nada | Usar `Video` / `video` |
| Já existe entidade ou tabela `video` | **Propor outro nome e confirmar com a pessoa** (ex.: `HostedVideo` / `hosted_video`, `YeroonVideo` / `yeroon_video`). Nunca reaproveitar nem alterar a tabela existente |

Guarde a decisão em `{video-entity}` e `{video-table}` e use nos moldes. Mesma checagem para
`webhook_receipt`.

## 6. Convenções da casa

```bash
ls CLAUDE.md AGENTS.md docs/superpowers/INSTRUCTIONS.md 2>/dev/null
grep -rlE 'BaseIntegrationTest|IntegrationTest' --include='*.java' --include='*.kt' . | head -5
ls .env.example .env.sample 2>/dev/null; grep -n '\.env' .gitignore
grep -rniE 'runbook|checkpoint' CLAUDE.md AGENTS.md 2>/dev/null | head
```

Leia o que existir e siga: pastas de camada, classe base de teste de integração, onde o projeto
documenta variáveis de ambiente, regra de runbook. O `.env` precisa estar no `.gitignore`.

## Quando não reconhece

| Situação | Ação |
|---|---|
| Back não é Spring Boot (Node, Django, Go, Spring sem Boot…) | **Parar.** Dizer o que foi encontrado e que a skill só cobre Spring Boot. Não escrever arquivo algum |
| Front não reconhecido | Avisar qual pasta foi pulada e seguir com o resto |
| Sem migration reconhecível | Parar e perguntar; não criar `db/migration` |
| Nome `video` já usado | Propor outro nome e confirmar |
| Dúvida entre duas opções | Perguntar; não adivinhar |
