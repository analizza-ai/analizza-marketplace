# Design: skill `test-runbook` no marketplace

Data: 2026-09-18

## Objetivo

Criar uma skill nova, `test-runbook`, em `plugins/analizza-skills/skills/test-runbook/`,
generalizando a skill local `eaf-runbook` do `documents-eaf-system` (que conduz checkpoints de
conferência manual a partir de `docs/checkpoints/`). A `analizza-integration-test` passa a
implantá-la automaticamente em todo projeto que configurar, fechando a promessa que sua descrição
já faz ("checkpoints com runbook por funcionalidade").

## Contexto: o que já existe

- `documents-eaf-system/.claude/skills/eaf-runbook/` — skill local desse projeto, com `SKILL.md`
  (conduz o checkpoint: preflight, lista runbooks, pergunta qual, pergunta como executar, caminho
  manual ou navegador, fecha com "verificado / não verificado") e `scripts/preflight.sh`, ambos
  cheios de específicos do projeto (containers, portas 8080/3000/9200/8025, query SQL de uma
  tabela, `MAIL_HOST` do `.env.local`).
- `analizza-integration-test/references/checkpoints-readme.md` — já é o guia de formato do
  runbook (tipo no topo, quatro seções, por que essa forma). Hoje só é copiado para
  `docs/checkpoints/README.md` no **Passo 8** da skill; não existe nada que **conduza** o
  checkpoint depois disso.
- `analizza-integration-test/references/claude-md-obligation.md` — bloco gravado no `CLAUDE.md`
  da raiz dizendo que toda funcionalidade produz/atualiza seu runbook; hoje só aponta para o
  "como" (`docs/checkpoints/README.md`), não para nenhum jeito de **rodar** a conferência.
- `analizza-integration-test/references/project-rules.md`, seção *Checkpoints de conferência* —
  o "quando" propor um checkpoint. Não muda neste design.

Este design não altera `documents-eaf-system`; o `eaf-runbook` de lá continua como está e serve só
de fonte para generalizar.

## Decisões

**D1 — Skill própria, não templates internos.** `test-runbook` ganha entrada própria no
marketplace (pasta com `SKILL.md`, `references/`, `templates/`), instalável/atualizável sozinha,
e a `analizza-integration-test` a implanta como parte do seu próprio setup.

**D2 — Geração dirigida pelo agente, sem parser dedicado.** Quem implanta a skill (o agente,
seguindo o `SKILL.md` de `test-runbook`) lê `docker-compose.yml`, `application.properties`/`.yml`
e `Makefile` do projeto de destino e preenche os templates diretamente — mesmo padrão que
`analizza-integration-test` já usa para seus próprios templates. Não existe script de detecção
separado.

**D3 — `analizza-integration-test` sempre implanta.** No Passo 8, depois de gravar
`docs/checkpoints/README.md`, a skill implanta `test-runbook` sem perguntar — a mesma decisão que
já vale para o restante do Passo 8 (Makefile, checkpoints), que também não é opcional.

**D4 — Nunca sobrescreve.** Os três artefatos gerados
(`.claude/skills/test-runbook/SKILL.md`, `.claude/skills/test-runbook/scripts/preflight.sh`,
`docs/checkpoints/README.md`) só são escritos se ainda não existirem no projeto de destino. Reflete
a mesma regra que o Passo 8 já aplica a `docs/checkpoints/README.md` hoje, estendida aos dois
arquivos novos — importante porque a seção "Cuidados específicos deste projeto" do `SKILL.md`
implantado acumula conhecimento ao longo do tempo (como a seção 4 de cada runbook) e uma
reimplantação não pode apagar isso.

**D5 — O que generaliza e o que fica de fora do template.** Do `eaf-runbook`, entram no template:
preflight, listar runbooks + `AskUserQuestion`, a segunda pergunta por `type` (com os dois rótulos
literais, sem reescrever), caminho manual, caminho navegador — inclusive as dicas que são
limitação da própria ferramenta de navegador embutido (contorno de upload de arquivo via
`DataTransfer`, preencher campos separados um a um), fechar com as duas listas
(verificado / não verificado), e atualizar a seção 4 do runbook quando achar algo. Ficam de fora
(só como exemplo aqui, não no template): a query SQL de uma tabela específica, o aviso de SMTP de
verdade, o contorno de Azurite vs backend, o hash de PDF — tudo isso é conhecimento específico do
`documents-eaf-system`. No lugar, o template ganha uma seção **"Cuidados específicos deste
projeto"**, vazia na primeira implantação, com um comentário instruindo a preencher conforme
forem descobertos.

**D6 — `preflight.sh` por blocos condicionais.** O bloco de containers/portas (detectados do
compose) sempre entra. O bloco de banco faz um health-check genérico (ex.: o comando de "está
pronto" do banco detectado), nunca uma query de negócio — fica um comentário convidando a
enriquecer depois. O bloco de e-mail só entra se o agente detectar uma variável tipo `MAIL_HOST`
ou um serviço de e-mail (mailhog/mailpit/smtp) no compose ou no `.env`/`.env.local` do projeto;
caso não detecte, o bloco é omitido inteiro, não deixado com placeholder.

**D7 — Ajuste mínimo em `claude-md-obligation.md`.** Acrescenta uma frase dizendo que a
conferência é conduzida pela skill implantada (`/test-runbook`), para o bloco do `CLAUDE.md`
também apontar como **rodar**, não só como escrever.

**D8 — Fonte única do formato do runbook.** `checkpoints-readme.md` migra de
`analizza-integration-test/references/` para `test-runbook/references/`. A
`analizza-integration-test` para de ter cópia própria e usa a de `test-runbook` no Passo 8.

## Estrutura de arquivos

```
plugins/analizza-skills/skills/test-runbook/
  SKILL.md                          # instrui o agente a IMPLANTAR isto num projeto de destino
  references/
    checkpoints-readme.md           # migrado de analizza-integration-test/references/
  templates/
    conducting-skill.md.template    # generalização do SKILL.md do eaf-runbook (D5)
    preflight.sh.template           # esqueleto com blocos condicionais (D6)
```

## Comportamento ao implantar (o `SKILL.md` de `test-runbook`)

1. Detecta, lendo os arquivos do projeto de destino (nunca perguntando, D2): porta da API, porta
   do web, nome do container/imagem do banco, serviços extras do compose (busca, e-mail, fila).
2. Para cada um dos três artefatos (D4): se já existe, não toca e registra no relatório que já
   existia; se não existe, gera a partir do template correspondente com os valores detectados.
3. `docs/checkpoints/README.md` é cópia direta de `references/checkpoints-readme.md`, sem
   placeholders (o arquivo já é genérico).
4. `.claude/skills/test-runbook/SKILL.md` vem de `templates/conducting-skill.md.template`, com os
   nomes/portas encontrados preenchidos e a seção "Cuidados específicos deste projeto" vazia.
5. `.claude/skills/test-runbook/scripts/preflight.sh` vem de `templates/preflight.sh.template`,
   com os blocos condicionais de D6 resolvidos.
6. Relata o que gerou, o que já existia (e por isso não tocou), e o que não conseguiu detectar
   (para a pessoa preencher à mão).

## Integração com `analizza-integration-test`

No **Passo 8 — Makefile e checkpoints**: depois do trecho atual que grava
`docs/checkpoints/README.md`, adiciona a chamada para implantar `test-runbook` no projeto (D3),
seguindo exatamente o comportamento descrito acima. `checkpoints-readme.md` some de
`analizza-integration-test/references/` (D8) — o passo passa a referenciar
`../test-runbook/references/checkpoints-readme.md`.

Em `references/claude-md-obligation.md`, acrescenta a frase de D7 no bloco que é gravado no
`CLAUDE.md` da raiz.

## Marketplace e versionamento

- `.claude-plugin/marketplace.json`: descrição do plugin `analizza-skills` passa a citar
  `test-runbook`.
- `plugins/analizza-skills/.claude-plugin/plugin.json`: `version` `0.3.1` → `0.3.2`.
- `make validate` (que roda `claude plugin validate .`, `claude plugin validate
  plugins/analizza-skills` e `tools/validate_plugin_manifests.py`) precisa passar limpo no final.

## Fora de escopo

- Migrar `documents-eaf-system` para usar `test-runbook` no lugar do `eaf-runbook` local — fica
  para quando (e se) alguém decidir reimplantar lá.
- Sub-projeto 2 (implantar `test-runbook` no `analizza-auction` e escrever o runbook real de
  cadastro e login) — depende deste, tem plano próprio, feito no repositório `analizza-auction`.
- Qualquer mudança em `analizza-new-project`.
