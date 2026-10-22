# yeroon-play-plug — skill para plugar o yeroon play num projeto cliente — design

Data: 2026-10-22. Status: para aprovação (revisado pelo builder check).

## Intenção

Plugar o yeroon play no analizza-tube deu certo, e o caminho ficou registrado lá
(`analizza-tube/docs/superpowers/specs/2026-10-21-yeroon-play-plugado-design.md`).
A skill **`yeroon-play-plug`** repete esse caminho em qualquer outro projeto:
identifica a tecnologia do back e do front, implementa a integração seguindo o
jeito do projeto, e no fim dá um **norte** do que falta para ir a produção.

O que mais pesou no analizza-tube não foi o código, foi **conseguir a chave**
`yk_…` (e o segredo `whsec_…`) e pôr no lugar certo. A skill tem que tirar esse
peso.

## Critério de sucesso

1. Num projeto Spring Boot (Java ou Kotlin) com front Next.js e/ou mobile Expo ou Flutter, rodar
   `/yeroon-play-plug` termina com: enviar, listar e assistir vídeo funcionando
   localmente contra o yeroon dev, e o webhook coberto por teste.
2. A chave chega ao `.env` do back sem a pessoa abrir o site do yeroon, copiar e
   colar à mão — a não ser que ela prefira colar uma chave que já tem.
3. A chave e o segredo nunca vão para o front, o app, log ou git.
4. Antes de escrever qualquer arquivo, a skill mostra o plano (stack detectada,
   arquivos a criar/mexer, variáveis) e espera o ok.
5. No fim, a pessoa sabe exatamente o que falta para produção.

## Não-objetivos

- Stacks fora de Spring Boot + Next.js/Expo/Flutter (Node, Django, React puro,
  React Native sem Expo…). A skill reconhece que não sabe e para, dizendo o que encontrou.
- Curso, aula, aluno, progresso por aluno ou qualquer domínio do cliente. A skill
  entrega só o equivalente à "primeira parte" do analizza-tube.
- Deploy do projeto cliente.
- Copiar o **visual** do yeroon play. O analizza-tube copiou; aqui o front usa os
  componentes e o estilo que o projeto já tem.

## Anti-objetivos

- `YEROON_API_KEY` ou `YEROON_WEBHOOK_SECRET` no front, no app, em log ou
  versionados. (O analizza-tube versionou o `.env` com a chave no commit
  `2d17145`; a skill não pode repetir isso.)
- O agente que roda a skill vendo ou digitando a **senha** da conta yeroon.
- Guardar no cliente o que é da plataforma: arquivo, partes, status, renditions,
  URL de mídia. O cliente guarda só o `videoId`.
- Testes chamando a `/v1` de verdade.
- Impor uma arquitetura: se o projeto não tem `presenter/application/domain`, a
  skill não cria essas pastas — segue o que existe.

## Onde mora

No marketplace **público** `analizza-ai/analizza-marketplace`, num plugin
próprio `yeroon-play` (não dentro do `analizza-skills`: outro produto, e quem
pluga o yeroon não precisa do scaffolding da Analizza). Um lugar só serve os
dois canais:
- Claude Code: instalar o plugin `yeroon-play` do marketplace.
- skills.sh: `npx skills add analizza-ai/analizza-marketplace --skill yeroon-play-plug`
  (a CLI descobre skills declaradas no `.claude-plugin/marketplace.json`; o
  ranking do skills.sh vem sozinho, pelas instalações).

Consequências:
- **Sem cópia neste repositório** (`bjjdream/yeroon-play` é privado), para não
  haver duas versões divergindo.
- **A skill se basta:** o resumo do contrato da `/v1`, os templates e o script da
  chave vão dentro dela. Nada de apontar para `docs/api/v1.md` deste repo, para o
  analizza-tube ou para o `CLAUDE.md` daqui. O contrato embutido é uma cópia
  resumida; ao mudar a `/v1`, atualizar a skill (vai no runbook).
- `SKILL.md` só com `name` e `description` no frontmatter (o que o skills.sh
  aceita). Regra de runbook e convenções vêm do projeto onde ela roda, se existirem.
- Neste repositório só muda a **descrição da `yeroon-video-streaming`**: deixa
  explícito que ela é para construir ou manter a plataforma, não para consumir,
  para não disputar o gatilho com a `yeroon-play-plug`.

## Estrutura da skill

```
plugins/yeroon-play/skills/yeroon-play-plug/
├── SKILL.md                    instruções: o fluxo abaixo, curto
├── references/
│   ├── contrato.md             o que o cliente precisa da /v1 (resumo de docs/api/v1.md),
│   │                           regras: chave só no servidor, só o videoId, HMAC, dedupe
│   ├── detectar-stack.md       como identificar back e front, e o que fazer se não reconhecer
│   └── norte.md                checklist de produção (abaixo)
├── scripts/
│   └── yeroon-key.sh           gera a conta de teste e grava a chave no .env (abaixo)
└── templates/
    ├── back-java-spring/
    ├── back-kotlin-spring/
    ├── front-next/
    ├── mobile-expo/
    └── mobile-flutter/
```

Templates são **moldes** com marcadores no padrão do marketplace (`{base-package}`,
`{video-entity}`…, arquivos `.template`), não código para copiar cego: a skill adapta cada um às pastas,
ao estilo e ao jeito de testar do projeto.

## Fluxo do SKILL.md

1. **Detectar a stack** (`detectar-stack.md`):
   - Back: `build.gradle`/`build.gradle.kts`/`pom.xml` com Spring Boot; linguagem
     pela maioria dos fontes em `src/main` (`.java` ou `.kt`); módulos
     (`-api`/`-core` ou módulo único).
   - Front: `package.json` com `next` → Next; `package.json` com `expo` → Expo;
     `pubspec.yaml` com `flutter` → Flutter. Pode haver web e mobile; pluga em
     todos os reconhecidos.
   - Convenções da casa: `CLAUDE.md`, `AGENTS.md`, `docs/superpowers/INSTRUCTIONS.md`,
     pastas de camada, classe base de teste de integração, onde o projeto
     documenta variáveis de ambiente, regra de runbook.
   - Se o back não for Spring Boot: para e diz o que achou. Um front não
     reconhecido é avisado e pulado; a skill segue com o resto.
2. **Mostrar o plano** e esperar o ok: stack, arquivos a criar/mexer por camada,
   migration, variáveis novas, testes, runbook (se o projeto exigir).
3. **Chave** (abaixo).
4. **Implementar em fatias**, rodando os testes do projeto a cada uma:
   back (cliente /v1 → rotas → webhook → migration) → front(s) → testes →
   runbook/documentação de variáveis.
5. **Norte**: entregar o checklist de produção preenchido para este projeto.

## A chave

A conta de teste do yeroon é self-service: `POST /account/signup`
(`{name,email,password,origin,webhookUrl,acceptedTerms}`) devolve `201` com
`apiKey` e `webhookSecret`.

- A skill gera `scripts/yeroon-key.sh` **no projeto cliente** (ou roda o da skill)
  e pede para **a pessoa** executá-lo no terminal. O script pergunta nome,
  e-mail e senha (senha com `read -s`), a origem do front (padrão
  `http://localhost:3000`), chama o signup na `YEROON_API_URL` e grava
  `YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` no `.env` do back. Assim o agente
  nunca vê a senha nem precisa digitar a chave.
- Antes de gravar, o script confere que o `.env` está no `.gitignore` e para se
  não estiver.
- Alternativa: a pessoa já tem chave e cola no `.env` ela mesma; a skill só
  confere que as variáveis existem (sem imprimir o valor).
- `YEROON_API_URL` padrão: `https://api.dev.play.yeroon.video`.
- *Decisão minha:* o signup recusa e-mail que já tem conta, e não há rota para
  pegar a chave de novo. Nesse caso o script explica e oferece duas saídas:
  colar a chave que a pessoa já tem, ou repetir com um alias
  (`nome+projeto@dominio`) — uma conta por projeto cliente.
- *Decisão minha:* a origem enviada no signup é a porta detectada do front
  (`next dev -p`, `PORT`), com `http://localhost:3000` como padrão. Se não for
  3000, a skill avisa que o upload pelo navegador vai falhar no CORS do R2 do
  yeroon e recomenda rodar o front na 3000 em dev. O signup aceita **uma**
  origem e não há rota para trocar origem nem `webhookUrl` depois; mudar isso é
  pedido ao administrador do yeroon (`/admin/tenants`), e o norte diz isso.
- *Pré-requisito a conferir antes de construir:* `POST /account/signup` no ar em
  `api.dev.play.yeroon.video` (hoje um `GET` lá devolve `401`, o que não
  confirma nada). Os testes da própria skill criam contas reais no yeroon dev,
  uma por execução, com alias de e-mail.

## O que cada template entrega

Referência de comportamento: o analizza-tube (Java + Next). Kotlin, Expo e
Flutter saem do contrato. Contrato:
`docs/api/v1.md` deste repo.

**Back (Java e Kotlin, Spring Boot):**
- Cliente da `/v1` atrás de uma interface (`RestClient`, timeout curto,
  `Authorization: Bearer`), com as operações `initUpload`, `partUrls`,
  `uploadedParts`, `complete`, `cancel`, `get`, `list`, `delete`, `playbackToken`.
- Mapa de erros: `422` repassa `errors[]`, `404` → `404`, `409` → `409`,
  `401`/rede → `502` genérico, logando só o prefixo da chave.
- Rotas próprias que repassam (upload multipart com retomada, lista filtrada aos
  vídeos do cliente, consulta, exclusão, playback devolvendo `embedUrl`,
  `hlsUrl` e `expiresAt`).
- Tabela `video(id uuid = videoId, created_at)` e `webhook_receipt` para
  deduplicar; migration no padrão do projeto (Flyway se houver).
- Webhook `POST /webhooks/yeroon`: HMAC-SHA256 de `"<epoch>.<corpo bruto>"`,
  comparação em tempo constante, recusa epoch > 5 min ou sem segredo, dedupe
  por `X-Yeroon-Delivery`, responde `2xx` rápido.
- Testes: dublê do cliente (`@Primary`) e um teste de integração por rota;
  unitário da assinatura.

**Front Next:**
- Route Handlers que repassam ao back (o navegador só fala com o Next e com o
  R2), upload multipart direto ao R2 com retomada, tela com lista e status,
  player em `<iframe src={embedUrl}>` com o token pedido a cada abertura.
- Testes com o runner que o projeto já usa.

**Mobile Expo:**
- Sem implementação de referência (o `-mobile` do analizza-tube é só o scaffold
  do Expo): sai do contrato, espelhando o web, sobre o projeto que o
  `analizza-new-project` gera.
- Cliente HTTP para as rotas do back (nunca para a `/v1`), URL do back por
  variável `EXPO_PUBLIC_*`.
- Envio: `expo-document-picker`/`expo-image-picker`, partes lidas por faixa com
  `expo-file-system` e PUT direto nas URLs assinadas, com progresso e retomada.
- Assistir: `hlsUrl` no `expo-video`.
- Testes com `jest-expo` para lista e player.

**Mobile Flutter:**
- Sem projeto de referência: escrito a partir do contrato e espelhando o Expo.
- Cliente HTTP para as rotas do back (nunca para a `/v1`).
- Envio: escolher arquivo, subir as partes nas URLs assinadas (PUT direto ao
  R2), com progresso e retomada.
- Assistir: o `hlsUrl` num player nativo (`video_player`) como padrão, com o
  `embedUrl` em WebView como alternativa.
- Testes de widget para lista e player.

## O norte (checklist de produção)

Preenchido para o projeto ao final:
- Conta real em vez da conta de teste (limite de 3 vídeos de 1 GB).
- `allowedOrigins` do cliente no yeroon com o domínio de produção do front.
- **CORS do R2 do yeroon**: o upload do navegador vai direto ao R2, e
  `deploy/r2-cors.json` deste repo só libera `localhost:3000` e o próprio
  yeroon. Uma origem nova precisa entrar lá (pedido ao time do yeroon). O app
  Flutter não depende disso.
- `webhookUrl` apontando para o back publicado; em dev, opcional via
  `cloudflared tunnel`.
- `YEROON_*` como secrets do ambiente de deploy, nunca no repo.
- Conferir que `yk_` não aparece nos bundles do front nem no app.

## Testes da própria skill

- Rodar a skill num projeto Java + Next + Expo de scaffold vazio (gerado por
  `analizza-new-project`, que já traz o `-mobile` em Expo) e conferir o critério
  de sucesso no web e no app.
- Rodar num projeto Kotlin + Flutter de scaffold vazio (criado com
  `flutter create` ao lado de um back gerado por `analizza-new-project` em
  Kotlin, já que não há gerador Kotlin + Flutter).
- Rodar num projeto que não é Spring e conferir que ela para e explica.

## Pronto inclui (CLAUDE.md deste repo)

Runbook da skill descrevendo a conferência das três execuções acima, mais a
instalação pelos dois canais (plugin e `npx skills add`). Ele mora junto da
skill, no padrão de documentação do `analizza-marketplace`.

## Deixado para o builder

- Os nomes exatos dos arquivos dentro de `templates/`.
- Quanto do código do analizza-tube vira template literal e quanto vira
  descrição em `references/`.
- O formato dos marcadores nos templates.
