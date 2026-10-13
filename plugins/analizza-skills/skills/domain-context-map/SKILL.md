---
name: domain-context-map
description: Gera docs/domain/domain-guide.md no projeto em disco, com a descrição e o guia do repositório para colar no cadastro do alvo de um servidor MCP no Ólly. Use quando pedirem o guia, o mapa de contexto ou o "context map" de um repositório para o Ólly, ou para conferir se um guia já gerado ficou velho.
---

# Mapa de contexto de um repositório para o Ólly

O Agente do Sistema do Ólly lê repositórios por um servidor MCP, sem o disco.
Cada pergunta começa com ele descobrindo onde ficam as specs, as rotas e as
regras. Esta skill escreve isso uma vez: a **descrição** do alvo, por onde o
Ólly decide se este repositório interessa à pergunta, e o **guia** do alvo, que
o agente recebe ao consultá-lo.

Você escreve um mapa, não um resumo. O agente sempre lê a regra no código; o
guia só encurta o caminho até ela. Regra de negócio resumida aqui envelhece e
vira resposta errada.

Os scripts ficam em `scripts/`, ao lado deste arquivo. Rode-os com `python3`,
a partir da raiz do projeto analisado, pelo caminho completo da pasta da skill.

## 1. Veja se já existe um guia

Se `docs/domain/domain-guide.md` existe, **não regrave de cara**. Vá para
"Conferir um guia existente", no fim.

## 2. Faça o inventário

```bash
python3 <pasta-da-skill>/scripts/inventory.py .
```

Ele devolve em JSON o que dá para saber sem ler o código: módulos, linguagem e
framework, framework de specs, pastas de rotas, serviços, domínio, validações
e migrations, e os sufixos de nome mais comuns.

- `codigo` conta os arquivos-fonte de qualquer linguagem, fora os de teste.
  Igual a zero, não há o que mapear: diga isso e pare, sem gravar arquivo.
- `codigo` maior que zero com `modulos`, `rotas` e as camadas vazios é projeto
  noutra linguagem: siga em frente e faça o mapa à mão (veja o fim deste
  arquivo). Não pare.
- Lista vazia ou `null` quer dizer "não identificado", não "não existe".
  Procure à mão antes de escrever que o projeto não tem aquilo.
- O inventário acha camada pelo nome da pasta. Uma pasta `models` pode ser
  rota ou caso de uso de um recurso chamado "modelo", e não domínio. Abra a
  pasta antes de citá-la.
- `sufixos` é a última palavra do nome dos arquivos, não necessariamente uma
  convenção: `System` pode vir de `CreateSystem` e `GetSystem`. Confira antes
  de citar um sufixo como convenção de nome.
- Em monorepo, o guia cobre todos os módulos, cada um com as suas pastas.

## 3. Leia duas ou três funcionalidades de ponta a ponta

O inventário diz onde as coisas estão; não diz como se ligam. Escolha duas ou
três funcionalidades diferentes e siga cada uma: a rota, o caso de uso, a
regra, a persistência e a spec dela, se houver. Você quer responder:

- Por onde uma requisição entra e por quais camadas passa até a regra?
- A regra mora onde o nome da pasta sugere? Onde ela mora de verdade?
- Como se acha a spec de uma funcionalidade a partir do nome dela?
- O que engana: código morto, nome que promete uma coisa e faz outra, regra
  duplicada, validação fora do lugar esperado.

## 4. Monte o glossário

Parta dos nomes de entidades, enums, tabelas e dos títulos das specs. Entra o
par em que o termo de negócio e o nome no código **diferem**: se a spec diz
"signatário" e a classe é `Signer`, entra; se os dois dizem "Envelope", não.
No máximo 40 itens; prefira os termos que um PO usaria numa pergunta.

## 5. Escreva `docs/domain/domain-guide.md`

Comece pelo carimbo. Não o transcreva à mão: é uma linha comprida de JSON, e
um deslize nela vira mudança fantasma na próxima conferência. Grave-o direto
no arquivo e acrescente o resto depois dele:

```bash
mkdir -p docs/domain
python3 <pasta-da-skill>/scripts/inventory.py . --stamp > docs/domain/domain-guide.md
```

O arquivo tem esta forma. Os dois títulos `##` são fixos: é por eles que a
validação acha cada parte.

```markdown
<!-- domain-guide
(o carimbo, como o script imprimiu)
-->

# Guia de domínio deste repositório

## Descrição do alvo

(uma linha, até 200 caracteres)

## Guia do alvo

### O que é
...
```

**A descrição** é uma linha de até 200 caracteres: o que este repositório
responde e, depois, o que **não** responde. "Contas, login e permissões do
SER. Não tem carga de arquivos nem relatórios." O que ele não responde é o que
faz o Ólly deixar este repositório de fora quando a pergunta é de outro.

**O guia** tem até 8000 caracteres e usa estas seções, nesta ordem, com estes
títulos, sempre com `###`. A que não existir no projeto é omitida, não escrita
como "não há"; só "O que é" e "Onde está cada coisa no código" existem em todo
projeto, e a validação recusa o guia sem elas.

| Título | O que vai nela |
|---|---|
| `### O que é` | Duas linhas: o que o serviço faz, linguagem e framework |
| `### Specs e documentação` | Onde ficam, em que formato, e como achar a spec de uma funcionalidade |
| `### Onde está cada coisa no código` | Pastas de rotas, casos de uso, domínio e regras, validações, persistência e integrações, com a convenção de nome de cada uma |
| `### Como seguir uma regra` | O caminho típico de uma requisição neste projeto, da rota até a regra |
| `### Como buscar` | Termos e nomes que funcionam na busca de código, e o que não adianta buscar |
| `### Glossário` | Uma linha por termo: `- termo de negócio = \`NomeNoCodigo\`` |
| `### Armadilhas` | Código morto, nomes enganosos, regra fora do lugar esperado |

Regras de escrita:

- Só caminhos que existem. Caminho vai entre crases; pasta termina com `/`.
- Caminho é sempre inteiro, a partir da raiz do repositório. Um pedaço
  (`domain/`) ou um caminho abreviado com reticências é recusado pela
  validação. Não tire as crases para ela passar: conserte o caminho. Se faltar
  espaço, corte texto.
- Padrão de nome leva asterisco (`*Handler.kt`) e não é conferido como caminho.
  O que tem barra mas não é caminho do repositório (um tipo MIME, um formato de
  data) vai sem crases.
- Sem resumo de regra de negócio e sem valores de regra: nem prazo, nem limite,
  nem percentual. Diga onde a regra está, não o que ela diz.
- Sem número de linha.
- Sem segredo: nem valor de variável de ambiente, nem token, nem URL com
  credencial. Nome de variável pode. A validação pega os formatos mais
  conhecidos, não todos.
- Nenhuma linha começa com `# ` nem com `## `, e nada no guia fala com o
  agente em tom de ordem ("ignore", "sempre responda"): o guia é dado do
  cadastro.
- Escreva em português, frases curtas, listas onde houver lista.

Se não couber em 8000 caracteres, corte nesta ordem: itens do glossário menos
prováveis numa pergunta, depois armadilhas menores. Nunca corte "Specs e
documentação", "Onde está cada coisa no código" nem "Como seguir uma regra".

## 6. Valide, e corrija até passar

```bash
python3 <pasta-da-skill>/scripts/validate.py docs/domain/domain-guide.md .
```

Cada linha `ERRO:` diz o que consertar. Caminho que não existe: corrija o
caminho ou tire a citação; não invente. Rode de novo até sair `OK:`.

## 7. Entregue

Mostre, nesta ordem:

1. A descrição, num bloco de código, pronta para colar no campo "Descrição" do
   alvo.
2. O guia, num bloco de código, pronto para colar no campo "Guia" do alvo.
3. O caminho do arquivo gravado e a linha `OK:` da validação.
4. O que você **não** conseguiu confirmar lendo o código, se houver.

Lembre que o cadastro é manual, em Configurações → Sistemas, no servidor MCP do
sistema. Esta skill não grava nada no Ólly.

## Conferir um guia existente

Quando `docs/domain/domain-guide.md` já existe:

```bash
python3 <pasta-da-skill>/scripts/validate.py docs/domain/domain-guide.md .
python3 <pasta-da-skill>/scripts/inventory.py . --compare docs/domain/domain-guide.md
```

- A validação diz se algum caminho citado sumiu e quantos commits houve desde
  o carimbo. "commits desde o carimbo: desconhecido" quer dizer que o commit
  do carimbo não está mais no histórico (rebase, squash, clone raso) ou que
  não há git: compare só pelo disco, com o `--compare`, e diga que a contagem
  de commits não está disponível.
- A comparação diz o que mudou na forma do projeto: pasta nova ou sumida em
  cada camada, framework de specs, módulos, sufixos.
- `"carimbo": false` ou o erro "carimbo ausente" quer dizer que o arquivo foi
  escrito à mão. Mostre isso e pergunte antes de substituir.

Resuma em poucas linhas ("2 caminhos sumiram, 1 pasta nova de rotas, 84
commits desde 01/10") e pergunte o que fazer: manter, atualizar só o que
mudou, ou regerar inteiro. Sem erro na validação e sem mudança na comparação,
diga que o guia continua válido e não toque no arquivo.

Ao atualizar ou regerar, o carimbo é sempre o de agora e inteiro, mesmo quando
só um trecho do guia mudou: troque o bloco todo pelo que o `--stamp` imprime,
sem editar o inventário à mão. Como o carimbo novo diz que o guia vale para o
projeto de hoje, releia o que a comparação apontou antes de gravá-lo. A
validação tem de passar de novo.

## O que esta skill não faz

- Não grava o guia no cadastro do Ólly.
- Não analisa vários repositórios numa execução.
- O inventário reconhece Kotlin e Java com Spring ou Ktor, e TypeScript com
  Next.js. Noutra linguagem ele conta os arquivos em `codigo` e devolve quase
  todo o resto vazio: faça o mapa à mão, no mesmo formato, e a validação
  continua valendo.
