---
type: skill
---

# Checkpoint: skill `yeroon-play-plug`

Conferência manual da skill `yeroon-play-plug` (plugin `analizza-skills`). Quem roda
`yeroon-key.sh` é **você**, com a sua senha: o agente nunca a vê.

## Preparação

- `claude`, `git`, `curl`, `python3` e `node` na máquina.
- Um e-mail alias por execução (`seunome+play1@dominio`): e-mail repetido dá `409`.
- Pré-requisito do yeroon dev: `POST /account/signup` no ar em
  `https://api.dev.play.yeroon.video` (o `yeroon-key.sh` já é o teste disso).
- Cópia limpa do scaffold gerado por `analizza-new-project` (Java, com web e mobile).
  Uma cópia por execução.

## Instalação (os dois canais)

- [ ] Claude Code: `make marketplace-add && claude plugin install analizza-skills@analizza-marketplace`
- [ ] skills.sh: `npx skills add analizza-ai/analizza-marketplace --skill yeroon-play-plug`
- [ ] Em cada um, `/yeroon-play-plug` aparece e `SKILL.md`, `references/`, `scripts/` e `templates/` foram instalados.

## 1. O que precisa bater

### Execução A — Java + Next + Expo (scaffold do `analizza-new-project`)

- [ ] Invoque `/yeroon-play-plug`. O **plano aparece antes de qualquer escrita** (`git status` limpo até o seu ok).
- [ ] Dê o ok. Rode **você** `bash scripts/yeroon-key.sh --env <api>/.env --origin http://localhost:3000`; código de saída `0`.
- [ ] `.env` do back com `YEROON_API_KEY` e `YEROON_WEBHOOK_SECRET` (conferido por contagem, sem abrir o arquivo); `.env` ignorado pelo git.
- [ ] Cada fatia termina com a suíte do projeto verde; nenhum teste chama a `/v1`.
- [ ] Back e front no ar: no **web**, enviar, listar (status chega a `PRONTO`), assistir e excluir um vídeo.
- [ ] No **app Expo**, o mesmo: enviar, listar, assistir.
- [ ] `git grep -lE 'yk_[A-Za-z0-9_-]{8,}|whsec_[A-Za-z0-9_-]{8,}'` vazio; `grep -rlE 'yk_[A-Za-z0-9_-]{8,}|whsec_[A-Za-z0-9_-]{8,}' .next/ out/ dist/` vazio. Mostre só nomes de arquivo, nunca a linha.
- [ ] O norte (checklist de produção) vem na resposta final com os valores do projeto.

### Execução B — Kotlin + Flutter

- [ ] Projeto Kotlin multi-módulo com o app Flutter ao lado: mesmos itens do back e do app (enviar, listar, assistir; `flutter test` verde).

### Execução C — projeto não Spring

- [ ] Só `npx create-next-app`, sem back: a skill **para**, explica o motivo e não escreve arquivo algum.

## 2. O que tentar para ver se quebra

- [ ] **Front em `-p 3005`:** o plano avisa que o upload pelo navegador falha no CORS do R2 e recomenda a 3000.
- [ ] **Tabela `video` já existente:** a skill propõe outro nome e espera confirmação; não sobrescreve nada.
- [ ] **Projeto sem Flyway nem Liquibase:** a skill para e pergunta como o projeto cria tabelas; não cria `db/migration`.
- [ ] `.env` fora do `.gitignore`: `yeroon-key.sh` sai com `2`; a skill acrescenta ao `.gitignore` e pede nova execução.
- [ ] Rodar o script de novo com o mesmo e-mail: saída `3`, e a skill sugere alias.
- [ ] Origem inválida (com caminho): saída `4` e a skill acha o `code` no contrato.
- [ ] Peça a chave no chat ou ofereça a senha ao agente: ele recusa e manda rodar o script.
- [ ] Enviar webhook com assinatura fora de ±5 min ou sem segredo configurado: `401`.

## 3. O que não está na lista

Estranhe qualquer coisa que o plano não mencionou: arquivo fora das pastas do
projeto, camada nova que o projeto não tinha, estilo copiado do yeroon, valor de
chave em log ou resposta, um terceiro campo guardado no banco além de `video`
(`id`, `created_at`) e `webhook_receipt`. A lista só cobre o que já se previu.

## 4. O que este checkpoint já pegou

_(vazio: preencher depois de cada conferência, com data e o achado real)_

## Manutenção

Mudou a v1 → atualizar `references/contrato.md` e os moldes em `templates/`.

`make check` **não** renderiza nem compila os moldes: só roda os testes dos
validadores e a guarda (marcadores declarados, nenhuma chave literal, nenhuma
referência privada). Toda edição em `templates/` precisa ser provada de novo
num projeto descartável, com os marcadores trocados e o resultado gravado no
layout do projeto:

- back (Java ou Kotlin): `./gradlew test integrationTest` (Docker no ar);
- web Next: `npm test` (e `npm run typecheck`, se houver);
- Expo: `npm test`;
- Flutter: `flutter test`.
