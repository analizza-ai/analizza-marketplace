---
name: analizza-deploy-vps-backend
description: Leva o backend Spring Boot (Gradle, uma ou mais aplicações) a um ambiente numa VPS com Docker. Implementa no repositório o pipeline de GitHub Actions (build e testes, imagens no Docker Hub, docker compose na VPS por SSH, health check), disparado só à mão de qualquer branch, com "gerar_tag" na branch padrão; a versão única do produto (gradle.properties junto do app e do web) com a tag v<versão> compartilhada entre os deploys; o compose com limites de memória, sem porta publicada e com a tag das imagens fora do .env; as guardas locais e o runbook. Depois conduz a preparação (DNS, proxy, Docker Hub, secrets do environment) e o primeiro deploy. Use quando pedirem "deploy do backend na VPS", "subir a api na VPS", "pipeline de deploy do Spring Boot", "docker compose na VPS pelo GitHub Actions" ou invocarem /analizza-deploy-vps-backend.
---

# analizza-deploy-vps-backend

Monta, num projeto **Spring Boot com Gradle**, o deploy de um ambiente (normalmente
`dev`) numa **VPS com Docker**, compartilhada com outros projetos:

- **Disparo só manual** (Run workflow), de qualquer branch. Push nenhum publica.
- **gerar_tag**, só na branch padrão: depois do deploy, um job separado (o único
  com permissão de escrita) cria `v<versão>`. A tag só marca o commit.
- **Versão única do produto:** `gradle.properties` (`version=`) e, se o produto
  tiver, o `app.json` dos apps Expo e o `package.json` do web carregam a mesma
  `X.Y.Z`. `make version V=X.Y.Z` grava em todas; todo deploy recusa versões
  divergentes. A tag `v<versão>` é a mesma para backend, web e apps: o primeiro
  deploy que a cria vence, os outros no mesmo commit a acham pronta.
- **Compose seguro para VPS compartilhada:** nome próprio, `mem_limit` em todo
  serviço, nenhuma porta publicada (o proxy reverso da VPS alcança a API pela
  rede externa), a tag das imagens fora do `.env` para um deploy não recriar o
  banco. O porquê de cada decisão: [references/vps-e-proxy.md](references/vps-e-proxy.md).

A pessoa assiste. Ela grava os segredos pelo terminal dela e aprova cada passo
que muda algo fora do repositório. A skill **nunca** lê nem digita senha, chave
SSH privada, token ou valor de secret.

**Não faz:** ambiente de produção com promoção por tag (só o ambiente disparado à
mão), Kubernetes, ECS ou PaaS, banco que não seja Postgres, configuração do proxy
reverso (só confere de fora; ver a referência), Maven, CI fora do GitHub Actions.
O frontend no Cloudflare é a `analizza-deploy-cloudflare-frontend`; os apps
móveis, a `analizza-expo-testflight` e a `analizza-expo-play`.

## Vocabulário dos moldes

Os moldes em `templates/` usam marcadores `{nome}` e blocos em linhas próprias:
`# se <bloco>` … `# fim se <bloco>` (YAML, shell, env) e
`<!-- se <bloco> -->` … `<!-- fim se <bloco> -->` (Markdown). Mantenha só os
blocos que valem, remova as linhas de abertura e fechamento, e troque todos os
marcadores. Blocos `por app` e `por variavel` se **repetem**, um por aplicação ou
por variável. Nenhum marcador pode sobrar no arquivo gerado (confira com
`grep -nE '\{[a-z][a-z0-9-]*\}|\{Env\}' <arquivo>`).

**Blocos:**
- `postgres`: o projeto usa Postgres (sobe junto no compose).
- `ssh-chave` ou `ssh-senha` (exatamente um): como o deploy entra na VPS.
- `por app`: uma vez por aplicação Spring Boot que sobe.
- `por variavel`: uma vez por variável de ambiente que a aplicação lê, além das
  do banco.

| Marcador | Valor | Exemplo |
|---|---|---|
| `{env}` / `{Env}` | ambiente, minúsculo / com inicial maiúscula | `dev` / `Dev` |
| `{project}` | nome do projeto | `meu-app` |
| `{default-branch}` | branch padrão | `main` |
| `{github-repo}` | `dono/repo` do `origin` | `empresa/meu-app` |
| `{github-environment}` | environment do GitHub | `development` |
| `{java-version}` | versão do Java do toolchain | `25` |
| `{app-module}` | módulo Gradle da aplicação = nome da imagem no Docker Hub | `meu-app-api` |
| `{app-service}` | serviço no compose | `api` |
| `{app-container}` | nome do container (o proxy chama por ele) | `meu-app-api-dev` |
| `{app-tag-var}` | variável da tag da imagem no `images.env` | `API_IMAGE_TAG` |
| `{app-port}` | `server.port` | `8080` |
| `{app-mem}` | `mem_limit` da aplicação | `512m` |
| `{app-networks}` | `internal` e, só para a que o proxy chama, `{proxy-network}` | `internal, web` |
| `{compose-name}` | `name:` do compose, único na VPS | `meu-app-dev` |
| `{remote-dir}` | pasta na VPS | `/root/meu-app/dev` |
| `{proxy-network}` | rede Docker externa do proxy reverso | `web` |
| `{proxy-upstream}` | `{app-container}:{app-port}` da aplicação pública | `meu-app-api-dev:8080` |
| `{public-host}` / `{public-url}` | host e URL pública da API | `api.dev.exemplo.com` |
| `{health-url}` | URL do health check | `https://api.dev.exemplo.com/actuator/health` |
| `{postgres-mem}` | `mem_limit` do Postgres | `256m` |
| `{mem-total}` | soma dos `mem_limit` | `768 MB` |
| `{db-name}` / `{db-user}` | banco e usuário | `meu_app` |
| `{var}` / `{fonte}` | nome da variável / `secrets` ou `vars` | `PAYMENT_TOKEN` / `secrets` |
| `{required-vars}` | variáveis sem padrão no `application.*`, separadas por espaço (com `POSTGRES_PASSWORD` no bloco `postgres`) | `POSTGRES_PASSWORD PAYMENT_TOKEN` |
| `{all-vars}` | todas as `{var}`, separadas por espaço | `PAYMENT_TOKEN SITE_URL` |
| `{secrets-list}` | nomes dos secrets: `VPS_HOST VPS_USER VPS_SSH_KEY` (ou `VPS_SSH_PASSWORD`) `DOCKERHUB_USERNAME DOCKERHUB_TOKEN`, `POSTGRES_PASSWORD` e as `{var}` de `secrets` | — |
| `{vars-commands}` | um `gh variable set <NOME> --env … -R … --body <valor>` por variável de `vars`, ou "nenhuma" | — |

## Fase 0 — ler e entrevistar

1. **É Spring Boot com Gradle?** Procure o plugin `org.springframework.boot` e as
   classes com `@SpringBootApplication`. Sem Gradle ou sem Spring Boot, pare e
   diga por quê.
2. **O que já existe.** `.github/workflows/backend-deploy*.yml`,
   `deploy/docker-compose.*.yml`, `Dockerfile`s, `.github/scripts/version.sh`,
   `.github/versao.fontes`, `docs/checkpoints/deploy-backend-*.md`. Um deploy que
   já existe **não é reescrito**: aponte as diferenças em relação a estes moldes
   e ofereça a migração como passo separado, só com o ok da pessoa.
3. **Os dados.** Siga [references/dados-de-entrada.md](references/dados-de-entrada.md):
   tudo o que falta numa pergunta só. Grave a spec descrita lá.

## Fase 1 — implementar no repositório

Numa branch nova (`feat/deploy-backend-<env>`):

| Molde | Destino | Como |
|---|---|---|
| [templates/github/scripts/version.sh](templates/github/scripts/version.sh) e `version.test.sh` | `.github/scripts/` | cópia, `chmod +x`; só se não existir |
| [templates/github/scripts/release-tag.sh](templates/github/scripts/release-tag.sh) e `release-tag.test.sh` | `.github/scripts/` | cópia, `chmod +x`; só se não existir |
| (sem molde) | `.github/versao.fontes` | um caminho por linha: `gradle.properties` e as outras fontes combinadas; se já existir, acrescente o que falta |
| (sem molde) | `gradle.properties` | `version=` com a versão combinada (a do app, se houver; senão `1.0.0`); se já existir, acrescente a linha |
| (sem molde) | cada `build.gradle(.kts)` | remova o `version = '…'` de cada módulo: a versão vem do `gradle.properties` |
| [templates/gradle/bootjar.gradle](templates/gradle/bootjar.gradle) ou `.kts` | fim do `build.gradle(.kts)` de cada aplicação | só se o `bootJar` ainda não tiver nome fixo |
| [templates/docker/Dockerfile.template](templates/docker/Dockerfile.template) | `<app-module>/Dockerfile` | um por aplicação; se existir, só ajuste o `COPY` para o nome fixo do jar |
| [templates/github/workflows/backend-deploy.yml.template](templates/github/workflows/backend-deploy.yml.template) | `.github/workflows/backend-deploy-{env}.yml` | blocos `por app`, `por variavel`, `postgres`, `ssh-*` |
| [templates/deploy/docker-compose.yml.template](templates/deploy/docker-compose.yml.template) | `deploy/docker-compose.{env}.yml` | idem |
| [templates/deploy/env.example.template](templates/deploy/env.example.template) | `deploy/.env.{env}.example` | só nomes, nenhum valor |
| [templates/deploy/images.env.example.template](templates/deploy/images.env.example.template) | `deploy/images.env.example` | um `{app-tag-var}=` por aplicação |
| [templates/deploy/check-compose.sh.template](templates/deploy/check-compose.sh.template) | `deploy/check-compose.sh` | `chmod +x` |
| [templates/makefile/deploy-backend.mk.template](templates/makefile/deploy-backend.mk.template) | fim do `Makefile` da raiz | alvos que não existirem (`deploy-check`, `version`); cria o `Makefile` se não houver |
| [templates/docs/deploy-backend.md.template](templates/docs/deploy-backend.md.template) | `docs/checkpoints/deploy-backend-{env}.md` | blocos como acima |

**Regras:**
- `deploy/.env.*` sem `.example` no `.gitignore`.
- Se o projeto já tem workflows de deploy de app (Expo) que leem a versão do
  `app.json` direto, acrescente o `app.json` em `.github/versao.fontes` e diga no
  relatório que eles continuam válidos: a guarda do backend garante que as
  versões batem.
- Rode antes do commit: `bash .github/scripts/version.test.sh`,
  `bash .github/scripts/release-tag.test.sh`, `make version`,
  `./gradlew build bootJar`, `docker build` de cada aplicação (o `COPY` acha o
  jar) e `make deploy-check` (precisa de Docker e `jq`). Rode o actionlint no
  workflow se houver Docker
  (`docker run --rm -v "$PWD:/repo" --workdir /repo rhysd/actionlint:latest`).
- O runbook gerado cumpre a regra de runbook por funcionalidade, se o projeto
  tiver; a `test-runbook` conduz a conferência.
- Commits pequenos. **Push e PR só com o ok da pessoa.**

## Fase 2 — preparação fora do repositório

Siga a seção **Preparação, uma vez** do runbook gerado, um bloco por vez, e espere
a confirmação de cada um. Antes de cada passo, olhe se ele já foi feito (veja
Retomada).

- **VPS:** a skill confere de fora, só leitura: `dig +short {public-host}`,
  `ssh <vps> 'docker network inspect {proxy-network}'`, `ssh <vps> free -m`
  (só com o ok da pessoa para entrar na VPS). Nada é instalado, parado ou
  apagado lá sem um ok para aquele comando.
- **DNS e proxy:** a pessoa faz (ou a skill, pelo navegador embutido, com um ok
  por clique de salvar). Mudança no repositório do proxy é PR separado lá.
- **Docker Hub:** a pessoa cria os repositórios e o token de acesso.
- **Secrets:** entregue o laço `gh secret set` do runbook. **A pessoa roda no
  terminal dela**; a skill não vê os valores. Variáveis não secretas: a skill
  pode rodar o `gh variable set` com o ok da pessoa.
- **Aprovação no environment** (Required reviewers), se a pessoa quiser: só com
  o ok, mostrando o `gh api` antes.

## Fase 3 — primeiro deploy e conferência

1. Merge do PR pela pessoa: o botão "Run workflow" só aparece com o workflow na
   branch padrão.
2. Peça o disparo (ou rode `gh workflow run`, com o ok) e acompanhe com
   `gh run watch`.
3. Proponha a conferência do runbook `docs/checkpoints/deploy-backend-{env}.md`
   (pela `test-runbook`, se o projeto tiver).

## Retomada

- DNS: `dig +short {public-host}` já dá o IP da VPS.
- Proxy: `curl -sI https://{public-host}` responde com certificado válido (502
  antes do primeiro deploy é esperado).
- Docker Hub: `docker manifest inspect <usuario>/{app-module}:{env}` responde (só
  depois do primeiro deploy).
- GitHub: `gh secret list --env {github-environment}` mostra os nomes (só nomes).

Nunca crie uma segunda cópia do que já existe.

## Segurança

- A skill nunca digita nem lê senha, chave SSH privada, token do Docker Hub ou
  valor de secret.
- O workflow passa `github.ref`, `inputs` e secrets por `env:`, nunca
  interpolados num `run:`.
- As actions ficam fixadas por SHA.
- Na VPS compartilhada, nada de outro projeto é parado, apagado ou alterado.
- Nenhum valor de cliente (empresa, host, IP) entra nesta skill; tudo vem da spec
  do projeto.

## Relatório final

Em poucas linhas:
- **Pronto:** arquivos gerados, testes rodados, PR, o que foi feito fora do
  repositório.
- **Pendente e com quem:** DNS, proxy, secrets, merge, primeiro disparo.
- **Débitos:** SSH por senha, aplicação sem actuator, worker que reinicia a cada
  deploy.
- **Próximo:** o frontend (`analizza-deploy-cloudflare-frontend`), se o produto
  tiver web.
