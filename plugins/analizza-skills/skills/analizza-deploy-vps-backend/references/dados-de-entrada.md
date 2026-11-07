# Dados de entrada

Procure primeiro no projeto: `settings.gradle(.kts)` (módulos), as classes com
`@SpringBootApplication` (aplicações), `application.properties`/`.yml` (porta,
datasource, variáveis lidas com `${NOME}`), `docker-compose.yml` local,
`Makefile` e `.github/workflows/`. O que faltar vira **uma pergunta só**, no
começo, com todos os itens juntos.

Nunca peça nem aceite na conversa: senha da VPS, chave SSH privada, token do
Docker Hub, senha de banco ou qualquer valor de secret. A pessoa grava esses
valores no GitHub pelo terminal dela.

## Do projeto

| Dado | Como obter | Marcador |
|---|---|---|
| Aplicações | módulos com `@SpringBootApplication` e o plugin `org.springframework.boot`; confirme quais sobem | `{app-module}` (uma por bloco `por app`) |
| Porta de cada aplicação | `server.port` (padrão 8080) | `{app-port}` |
| Versão do Java | `toolchain`/`sourceCompatibility` do Gradle | `{java-version}` |
| Banco | datasource `postgresql` → bloco `postgres`; outro banco → pare e diga que o molde só cobre Postgres | `postgres` |
| Variáveis de ambiente | `${NOME}` e `${NOME:padrão}` nos `application.*` de cada aplicação; as sem padrão são obrigatórias | `{var}`, `{required-vars}`, `{all-vars}` |
| Repositório | `git remote get-url origin` | `{github-repo}` |
| Branch padrão | `git symbolic-ref refs/remotes/origin/HEAD` | `{default-branch}` |
| Fontes de versão | `gradle.properties` sempre; mais o `app.json` de cada app Expo e o `package.json` do web, se o produto vai versionar junto (pergunte) | `.github/versao.fontes` |

## Do ambiente

| Dado | Pergunta | Exemplo |
|---|---|---|
| Ambiente | "Qual ambiente montar agora?" (sugira `dev`) | `dev` |
| Host público da API | "Em que endereço a API responde?" | `api.dev.exemplo.com` |
| Health | `<https://host>/actuator/health` se houver actuator; senão pergunte | `https://api.dev.exemplo.com/actuator/health` |
| Pasta na VPS | sugira `/root/<projeto>/<env>`; confirme | `/root/meu-app/dev` |
| Nome do compose | sugira `<projeto>-<env>`; precisa ser único na VPS | `meu-app-dev` |
| Rede do proxy | "Qual a rede Docker externa do proxy reverso na VPS?" | `web` |
| Container que o proxy chama | sugira `<projeto>-api-<env>` | `meu-app-api-dev` |
| Memória | "Quanta memória livre a VPS tem?" (`free -m`); distribua `mem_limit` | api `512m`, postgres `256m` |
| Usuário SSH | "Com que usuário o deploy entra na VPS?" | `root` |
| Autenticação SSH | chave (recomendado) ou senha; bloco `ssh-chave` ou `ssh-senha` | chave |
| Environment do GitHub | sugira `<env>` ou `<projeto>-<env>` | `development` |
| Valores não secretos | para cada variável que não é segredo (URL pública, lista de e-mails): o valor | `PLAYER_BASE_URL=https://…` |

## A spec que a skill grava

Quando os dados vieram da entrevista, grave
`docs/superpowers/specs/AAAA-MM-DD-deploy-backend-<env>-design.md` com: as
aplicações e portas, o banco, a VPS (host público, pasta, rede do proxy,
memória), o environment do GitHub com os **nomes** dos secrets e variáveis, a
autenticação SSH (chave ou senha, sem valor) e as fontes de versão. Nenhum
segredo entra nesse arquivo.
