---
name: yeroon-play-plug
description: >-
  Pluga o yeroon play (hospedagem de vídeo como serviço) num projeto que já
  existe: back Spring Boot (Java ou Kotlin) e front Next.js, app Expo ou app
  Flutter. Detecta a stack e as convenções do projeto, mostra o plano e espera o
  ok, pede que a pessoa rode um script que cria a conta de teste e grava a
  chave no .env do back (o agente não vê senha nem chave), implementa em fatias
  — cliente da /v1, rotas de repasse, webhook assinado, migration, telas de
  enviar, listar e assistir — com testes que não chamam a /v1, e termina com o
  checklist do que falta para produção. Use quando pedirem "plugar o yeroon
  play", "integrar yeroon", "hospedar vídeo das aulas no yeroon", "yeroon play
  no meu projeto" ou invocarem /yeroon-play-plug. Não constrói plataforma de
  vídeo própria, não copia o visual do yeroon e não mexe em deploy.
---

# yeroon play no projeto cliente

O yeroon play guarda, converte e entrega o vídeo; o projeto cliente guarda só o
`videoId`. A skill liga os dois sem impor arquitetura: o código entra nas
pastas, no estilo e no jeito de testar que o projeto já tem.

Duas regras valem do começo ao fim, sem exceção:

- **`YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` só no `.env` do back.** Nunca no
  front, no app, em log, em molde com valor ou no git. Você **não** exibe o
  `.env` — nada de `cat`, `grep -o`, `sed -n`, `head` nem abrir o arquivo. Para
  saber se uma variável existe, conte (Passo 3).
- **A senha da conta yeroon nunca passa por você.** Quem roda
  `yeroon-key.sh` é a pessoa, no terminal dela.

Referências — leia quando o passo mandar; esta página não as repete:

- [references/contrato.md](./references/contrato.md) — o que o cliente usa da `/v1`, webhook, erros, conta de teste.
- [references/detectar-stack.md](./references/detectar-stack.md) — comandos e tabelas de decisão da detecção, e quando parar.
- [references/norte.md](./references/norte.md) — checklist de produção entregue no fim.

## O que esta skill não faz

- **Não constrói plataforma de vídeo própria.** Nada de guardar arquivo, partes,
  status, renditions ou URL de mídia no cliente; nada de converter vídeo. Para
  construir ou manter a plataforma em si, esta não é a skill.
- **Não copia o visual do yeroon.** As telas usam os componentes e o estilo do
  projeto; os moldes de componente vêm sem estilo próprio.
- **Não mexe em deploy** (pipeline, Dockerfile, secrets do ambiente). O que
  falta para produção vai no norte, para a pessoa fazer.
- **Não cobre domínio do cliente** (curso, aula, aluno, progresso): entrega
  enviar, listar, assistir e excluir vídeo, e o webhook.
- **Não cria camadas** (`presenter/application/domain`) que o projeto não tem.

## Vocabulário

Marcadores usados nos moldes de `templates/`. Os valores saem do Passo 1; o
número entre parênteses é a seção de `detectar-stack.md`.

| Marcador | Valor e de onde vem |
|---|---|
| `{language}` | `java` ou `kotlin` — maioria dos fontes em `src/main` (1). Escolhe `templates/back-{language}-spring/` |
| `{base-package}` | pacote da classe `@SpringBootApplication` do back (1) |
| `{base-package-path}` | `{base-package}` com `/` no lugar de `.` |
| `{api-module}` | módulo com a `@SpringBootApplication` (ou o `-api`) (1). Em módulo único, `.` (a raiz) |
| `{core-module}` | o `-core`, se existir (1); em módulo único, igual a `{api-module}` |
| `{it-module}` | onde os testes de integração moram: módulo dedicado (`{base}-integration-tests`) ou o `src/test` do `{api-module}` (6) |
| `{base-integration-test-fqn}` | nome completo da classe base de IT do projeto (6). Sem classe base, os ITs usam `@SpringBootTest` direto — diga no plano |
| `{migration-dir}` | pasta de migration existente: `db/migration` (Flyway) ou a do changelog mestre (Liquibase) (3) |
| `{migration-version}` | próxima versão Flyway, seguindo a numeração atual (3). Em Liquibase, o id do novo changeset no padrão do changelog |
| `{video-entity}` | `Video`, ou o nome confirmado com a pessoa se houver conflito (5) |
| `{video-table}` | `video`, ou o nome confirmado com a pessoa se houver conflito (5) |
| `{back-url-env}` | nome da variável que o front/app já usa para a URL do back, sem `NEXT_PUBLIC_`/`EXPO_PUBLIC_` (7); sem nenhuma, `BACK_URL`. No Expo vira `EXPO_PUBLIC_{back-url-env}`; no Flutter, `--dart-define` |
| `{front-origin}` | `http://localhost:` + porta do Next (4); sem Next, `http://localhost:3000` |
| `{back-public-url}` | URL pública do back publicado, perguntada à pessoa; sem resposta, "a definir" |
| `{api-routes-prefix}` | prefixo de **mapeamento** comum às rotas existentes (`@RequestMapping`, ex.: `/api`) (7); os moldes o escrevem nas rotas novas. Sem prefixo comum, vazio |
| `{context-path}` | valor de `server.servlet.context-path` (7); vazio se não houver. Só entra em URL pública (webhook, URL do back no front), **nunca** em mapeamento — senão vira `/api/api/videos` |

Moldes também têm blocos `<!-- se x -->…<!-- fim se x -->`: grave só o bloco
que vale para este projeto e remova as linhas de marcação. Nenhum marcador
pode sobrar no arquivo gravado.

## Procedimento

### Passo 0 — Pré-requisitos e o que sai

Precisa de um back Spring Boot (Java ou Kotlin; Gradle ou Maven) com migration
Flyway ou Liquibase e, opcionalmente, front Next.js, app Expo ou app Flutter;
`git`, `curl` e `python3` na máquina da pessoa; o `.env` do back no
`.gitignore`. Sai: cliente da `/v1` atrás de uma interface, rotas de repasse no
back, webhook `POST {context-path}{api-routes-prefix}/webhooks/yeroon` assinado, tabelas
`{video-table}` e `webhook_receipt`, telas de enviar/listar/assistir no web e
no app, testes com dublê, runbook se o projeto exigir, e o norte preenchido.

### Passo 1 — Detectar

Siga [detectar-stack.md](./references/detectar-stack.md) seção por seção, da
raiz do projeto. Diga à pessoa o que encontrou e de onde, e preencha a tabela
do *Vocabulário*. As paradas vêm antes de qualquer outra coisa:

- **Back não é Spring Boot** → pare, diga o que achou, não escreva arquivo algum.
- **Sem Flyway nem Liquibase** → pare e pergunte como o projeto cria tabelas; não crie `db/migration`.
- **Nome `video` (ou `webhook_receipt`) já usado** → proponha outro nome e confirme.
- **Front não reconhecido** → avise qual pasta será pulada e siga com o resto.
- **Dúvida entre duas opções** (linguagem empatada, várias `@SpringBootApplication`) → pergunte, uma pergunta por vez, com o detectado como padrão.

Veja também como o back carrega o `.env` (dependência de dotenv,
`spring.config.import=optional:file:.env[.properties]`, ou o que o
`CLAUDE.md`/`AGENTS.md` disser) — sem abrir o `.env`. Se não carrega, a
ligação entra no plano.

### Passo 2 — Mostrar o plano e esperar o ok

**Nenhum arquivo é escrito antes do ok explícito da pessoa** — nem o script do
Passo 3. Mostre:

1. **Stack:** linguagem e build do back, módulos (`{api-module}`, `{core-module}`, `{it-module}`), fronts reconhecidos e pulados.
2. **Arquivos por camada:** o que entra em cada módulo/pasta, a partir dos moldes adaptados ao layout do projeto, e o que muda em arquivo existente (handler global de exceção, `application.properties`/`.yml`, `.env.example`, `.gitignore`).
3. **Migration:** arquivo e versão (`{migration-dir}`, `{migration-version}`), tabelas `{video-table}` e `webhook_receipt`.
4. **Variáveis novas:** `YEROON_API_URL` (padrão `https://api.dev.play.yeroon.video`), `YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` no `.env` do back; `{back-url-env}` no front/app (só a URL do back). Documentadas onde o projeto documenta variáveis, com valor vazio.
5. **Testes:** quais e onde; nenhum chama a `/v1`.
6. **Runbook:** só se o `CLAUDE.md`/`AGENTS.md` do projeto exigir runbook por funcionalidade; diga o caminho que a regra manda.
7. **Script da chave:** `scripts/yeroon-key.sh` no projeto. Se já existir, compare com o desta skill (`cmp`) e, se diferir, pergunte antes de sobrescrever.
8. **Avisos:** porta do Next diferente de 3000 (o upload pelo navegador falha no CORS do R2 do yeroon; recomende a 3000 em dev); nome trocado por conflito; ausência de classe base de IT; `.env` fora do `.gitignore`.

Espere um ok claro. Pedido de mudança → refaça o plano e mostre de novo.

### Passo 3 — Chave

A chave aparece uma única vez, no signup. Pergunte se a pessoa **já tem** chave
yeroon para este projeto.

**Não tem — script.** Copie `scripts/yeroon-key.sh` desta skill para
`scripts/yeroon-key.sh` do projeto (como ficou no plano) e peça que **a pessoa** rode, no terminal
dela, da raiz do projeto:

```bash
bash scripts/yeroon-key.sh --env {api-module}/.env --origin {front-origin}
```

- `--env`: o `.env` que o back de fato lê (Passo 1); omita se for `./.env`.
- `--origin`: uma origem só, sem caminho — **não há rota para trocar depois**.
- `--webhook URL`: só se a pessoa já tiver endereço público:
  `{back-public-url}{context-path}{api-routes-prefix}/webhooks/yeroon`, ou
  `<url do túnel cloudflared>{context-path}{api-routes-prefix}/webhooks/yeroon`.
  Monte com o prefixo e confira com a pessoa antes: também não muda depois. Sem
  ele, nenhum aviso chega em dev.
- `--api URL`: só para outro ambiente do yeroon.

Você **não** roda o script, não preenche os prompts e não pede a senha. Peça só
o código de saída (`echo $?`) e a última mensagem, e aja:

| Saída | Significa | O que fazer |
|---|---|---|
| `0` | Conta criada; chave e segredo no `.env` | A mensagem mostra só os 7 primeiros caracteres da chave — é esperado, nada mais a fazer com ela. Conferir presença (abaixo) e seguir |
| `1` | Uso errado, termos recusados, falta `python3`/`curl`, ou `.env` sem permissão de escrita | Ler a mensagem com a pessoa, corrigir a causa e pedir que rode de novo |
| `2` | `.env` fora do `.gitignore` | Acrescentar o `.env` ao `.gitignore` (estava no plano) e pedir que rode de novo |
| `3` | E-mail já tem conta (`409`); a chave antiga não é recuperável | Rodar de novo com alias (`nome+projeto@dominio`) — uma conta por projeto — ou a pessoa cola a chave que já tem |
| `4` | Regra quebrada (`422`); os `code` saem no stderr | Achar o código em [contrato.md](./references/contrato.md) (ex.: origem fora do formato), corrigir o argumento e rodar de novo |
| `5` | O `.env` já tem `YEROON_API_KEY` ou `YEROON_WEBHOOK_SECRET` **com valor** (linhas vazias, como as copiadas do `.env.example`, não contam: o script as preenche no lugar) | Conferir presença e seguir. `--force` só se a pessoa quiser **outra** conta, sabendo que a chave atual sai do `.env` |
| `6` | Falha de rede | Conferir conexão e `--api`; rodar de novo |
| `7` | Resposta inesperada, ou conta criada sem conseguir gravar o `.env` | Se a mensagem cita um arquivo salvo fora do repositório: a pessoa move as duas linhas dele para o `.env` e apaga o arquivo — você não o abre. Senão, informe o HTTP e tente mais tarde; repetir com o mesmo e-mail pode dar `3` |

**Já tem — colar.** A pessoa cola `YEROON_API_KEY=…` e `YEROON_WEBHOOK_SECRET=…`
no `.env` do back ela mesma. Não peça a chave no chat; se ela mandar, não
repita o valor e recomende pedir chave nova.

**Conferir presença, sem ver valor:**

```bash
git check-ignore -q {api-module}/.env && echo ignorado
grep -cE "^[[:space:]]*(export[[:space:]]+)?YEROON_API_KEY[[:space:]]*=[[:space:]]*[\"']?[^\"'[:space:]#]" {api-module}/.env
grep -cE "^[[:space:]]*(export[[:space:]]+)?YEROON_WEBHOOK_SECRET[[:space:]]*=[[:space:]]*[\"']?[^\"'[:space:]#]" {api-module}/.env
```

Tem que dar `ignorado`, `1` e `1`. Qualquer outra coisa → volte à tabela.
`YEROON_API_URL` não é segredo: pode ir no `.env` ou ficar no padrão da
configuração.

### Passo 4 — Implementar em fatias

Uma fatia por vez, nesta ordem. Ao fim de cada uma, rode a suíte **do projeto**
(a que ele já usa: `./gradlew test integrationTest`, `mvn verify`, `npm test`,
`flutter test`…) e só passe à próxima com ela verde. Os moldes são ponto de
partida: leve pastas e pacotes para o layout do projeto, siga o estilo de
código e de teste que já existe e substitua todos os marcadores.

1. **Back** — `templates/back-{language}-spring/`:
   - `core/` → `{core-module}`: propriedades `YEROON_*`; cliente da `/v1` atrás de uma interface (`RestClient`, timeout curto, `Authorization: Bearer`) com o mapa de erros do contrato (`422` repassa `errors[]`, `404`, `409`, `401`/rede → `502` logando só o prefixo da chave); casos de uso de vídeo e de webhook; entidade `{video-entity}`; repositórios; migration em `{migration-dir}`.
   - `api/` → `{api-module}`: rotas de repasse mapeadas sob `{api-routes-prefix}/videos` (o `{context-path}` o Spring já põe na frente); playback devolvendo só `embedUrl`, `hlsUrl` e `expiresAt` (token pedido a cada abertura, nunca guardado); webhook com HMAC-SHA256 sobre o corpo bruto, comparação em tempo constante, recusa fora de ±5 min ou sem segredo, dedupe por `X-Yeroon-Delivery`; trechos para o handler global de exceção e para a configuração.
   - Em módulo único, `core/` e `api/` vão para o mesmo módulo, nas pastas que já existem.
2. **Web** — `templates/front-next/`: Route Handlers que repassam ao back por `{back-url-env}` (o navegador fala só com o Next e com o R2), upload multipart com retomada, lista com status, player em `<iframe>` com `embedUrl`. Componentes sem estilo: encaixe nos do projeto.
3. **Mobile** — `templates/mobile-expo/` ou `templates/mobile-flutter/`: cliente HTTP para as rotas do back (nunca para a `/v1`), upload por partes nas URLs assinadas com progresso e retomada, `hlsUrl` no player nativo. Pule o que não foi reconhecido.
4. **Testes** — `templates/back-{language}-spring/it/` → `{it-module}`: dublê do cliente da `/v1` com `@Primary`, um IT por rota, unitário da assinatura do webhook; testes do web e do app com o runner que o projeto já usa. **Nenhum teste chama a `/v1` de verdade.** Se o projeto exige IT para todo entrypoint (regra ArchUnit, por exemplo), as rotas novas também cumprem.
5. **Runbook** — só se o projeto exigir: escreva a partir de `templates/runbook-yeroon-play.md.template`, no caminho e no formato que a regra do projeto manda. Documente as variáveis novas onde o projeto documenta (`.env.example` com valor vazio).

Antes de fechar o Passo 4, confira que a chave não vazou:

```bash
git status --porcelain | grep -E '[ /]\.env$'               # vazio
git grep -lE 'yk_[A-Za-z0-9]{8,}|whsec_[A-Za-z0-9]{8,}'       # vazio; -l lista só o arquivo, nunca a linha
```

Se houver build do web, `grep -rl 'yk_' .next/ out/ dist/ 2>/dev/null` também
tem que sair vazio.

### Passo 5 — Norte

Preencha [norte.md](./references/norte.md) com os valores deste projeto
(`{front-origin}` de dev e a de produção que a pessoa informar,
`{back-public-url}`, `{context-path}`, `{api-routes-prefix}`, a porta do back no
item do túnel) e entregue à pessoa na
resposta final, junto com: o que foi feito em cada fatia, a suíte que passou, o
que foi pulado e por quê, e como testar localmente (subir back e front, enviar
um vídeo, esperar `PRONTO`, assistir). Sem `webhookUrl`, diga que o status
chega pela consulta, não pelo aviso.
