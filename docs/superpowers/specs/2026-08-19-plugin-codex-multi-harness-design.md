# Plugin `analizza-skills` para Codex

Data: 2026-08-19
Repositório: `analizza-ai/analizza-marketplace`
Status: aprovado em brainstorming, aguardando plano de implementação

## Objetivo

Distribuir `analizza-skills` para Codex sem retirar nem alterar o suporte
existente ao Claude Code. As 3 skills do plugin (`analizza-kotlin-integration-test`,
`analizza-java-integration-test`, `analizza-new-project`), atuais e futuras,
devem ter uma única fonte de verdade e estar disponíveis a todos os
harnesses. Este desenho espelha a decisão já aprovada e implementada em
`analizza-ai/business-marketplace` (`docs/superpowers/specs/2026-08-18-plugin-codex-multi-harness-design.md`),
adaptada para um plugin com múltiplas skills e para um repositório que hoje
não tem nenhuma infraestrutura Python.

## Decisão

Adotar um plugin multi-harness no mesmo diretório do produto. A árvore
`plugins/analizza-skills/skills/` é canônica: contém as 3 `SKILL.md`
existentes com seus templates e references. Os harnesses recebem somente
manifestos próprios para reconhecer essa mesma árvore.

```text
plugins/analizza-skills/
├── .claude-plugin/plugin.json  # manifesto Claude Code existente
├── .codex-plugin/plugin.json   # novo manifesto Codex
└── skills/                     # fonte única, compartilhada, 3 skills
    ├── analizza-kotlin-integration-test/
    ├── analizza-java-integration-test/
    └── analizza-new-project/
```

Não haverá cópia de skills por harness, links simbólicos nem um repositório
separado de conteúdo.

## Manifesto Codex

O arquivo `.codex-plugin/plugin.json` declarará:

```json
{
  "name": "analizza-skills",
  "version": "0.2.1",
  "description": "Skills da Analizza para scaffolding e qualidade de projetos",
  "author": {"name": "Diego Lirio", "email": "diegolirio.dl@gmail.com"},
  "homepage": "https://github.com/analizza-ai/analizza-marketplace",
  "repository": "https://github.com/analizza-ai/analizza-marketplace",
  "keywords": ["kotlin", "java", "spring-boot", "scaffolding", "testes de integração"],
  "skills": "./skills/",
  "hooks": {},
  "interface": {
    "displayName": "Analizza Skills",
    "shortDescription": "Scaffolding e qualidade para projetos Kotlin/Java + Spring Boot",
    "longDescription": "Cria monorepos do zero (api, core, web, mobile) e configura infraestrutura de testes de integração em projetos Kotlin ou Java com Spring Boot.",
    "developerName": "Diego Lirio",
    "category": "Developer Tools",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": ["Crie um novo projeto Kotlin com Spring Boot."]
  }
}
```

`skills` aponta explicitamente à árvore canônica `./skills/`. O plugin não
adiciona hooks, MCP servers, aplicações ou assets nesta versão — a entrega é
a habilidade existente, não uma integração nova.

## Comportamento e compatibilidade

As 3 skills mantêm exatamente o contrato atual: mesmos gatilhos de
ativação, templates, references e formato de resposta. O Codex deve
carregar cada `skills/<nome>/SKILL.md` diretamente, de modo que uma correção
ou uma nova skill adicionada sob `skills/` fique disponível a Claude e Codex
na mesma release.

Os manifestos podem ter campos específicos de cada plataforma, mas `name` e
`version` representam o mesmo produto e devem permanecer iguais. A versão é
alterada conjuntamente em toda publicação (hoje: `0.2.1`).

## Documentação e validação

O README passará a apresentar o plugin como multi-harness: a seção
"Instalação" vira "Instalação por harness", com `### Claude Code` (mantendo
`make marketplace-add`/`make install` atuais, inalterados) e `### Codex`
(abrir o app Codex → Plugins → localizar "Analizza Skills" após publicação
no marketplace Codex; para desenvolvimento local, usar o manifesto
`.codex-plugin/plugin.json` com o fluxo de instalação local que o Codex
suporta). A seção "Publicando uma versão" passa a exigir subir a mesma
versão nos dois manifestos e rodar `make validate && make check` antes de
`make tag`. A seção "Estrutura" ganha as duas linhas de manifesto e a linha
de `tools/`.

Este repositório não tem hoje nenhuma infraestrutura Python. Será
introduzida:

- `tools/validate_plugin_manifests.py`: valida que `name` e `version` são
  idênticos entre os manifestos Claude e Codex; que `skills` do Codex é
  exatamente `"./skills/"`; que o diretório `plugins/analizza-skills/skills/`
  existe; que todos os campos obrigatórios de `interface` estão presentes
  (`displayName`, `shortDescription`, `longDescription`, `developerName`,
  `category`, `capabilities`); e que o número de arquivos `SKILL.md` sob
  `plugins/analizza-skills/` é igual ao número de subpastas em `skills/`
  (adaptação da checagem "1 skill" do design de referência para um plugin
  com múltiplas skills — pega tanto uma skill sem `SKILL.md` quanto uma
  pasta esquecida).
- `tools/tests/test_validate_plugin_manifests.py`: testa cada erro
  isoladamente (nome divergente, versão divergente, caminho de skills
  errado, diretório ausente, campo de interface ausente, contagem de
  `SKILL.md` divergente), valida os manifestos reais do repositório, e
  garante que o README documenta `### Claude Code` e `### Codex`.
- `requirements-dev.txt` na raiz, contendo apenas `pytest`, documentado no
  README (`pip install -r requirements-dev.txt`) como pré-requisito de
  `make check`.

O `Makefile` ganha:

1. `make check`: roda `python3 -m pytest tools/tests -q`.
2. `make validate`: passa a rodar, além dos comandos `claude plugin
   validate` já existentes, `python3 tools/validate_plugin_manifests.py`.
3. `make tag`: passa a depender de `validate`, garantindo que a tag nunca é
   criada com manifestos divergentes.

Uma falha de empacotamento, campo ausente ou divergência de versão é detectada
localmente antes de uma tag. Não há falhas de rede nem estado externo no fluxo
de validação.

## Fora de escopo

- Publicar o plugin no marketplace oficial do Codex; esta entrega prepara o
  artefato para isso, mas a publicação requer credenciais e revisão externa.
- Alterar o conteúdo ou o comportamento das 3 skills existentes.
- Criar MCP server, hooks ou interface gráfica.
- Separar o conteúdo de skills em um novo repositório.
- Adicionar validação de catálogo de conhecimento (o `analizza-skills` não
  tem catálogo de riscos como o `analizza-leiloes`; `tools/` deste repo
  conterá apenas o validador de manifestos).

## Critérios de aceite

1. O repositório contém manifestos válidos para Claude Code e Codex no mesmo
   diretório `plugins/analizza-skills/`.
2. O manifesto Codex aponta para `./skills/`, sem duplicar o conteúdo das
   skills.
3. Nome e versão são idênticos nos dois manifestos.
4. A documentação explica como instalar e atualizar o plugin em cada
   harness.
5. `make validate` e `make check` passam, cobrindo os dois manifestos, o
   diretório de skills e a contagem de `SKILL.md`.
