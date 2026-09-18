# Runbooks de checkpoint

Um arquivo por funcionalidade, descrevendo como **uma pessoa** confere que
aquilo funciona rodando. O arquivo de convenções do projeto diz quando um
checkpoint é devido; esta pasta é onde o roteiro dele mora.

## Não é suíte de teste

Teste é o que roda sozinho e falha sozinho. Checkpoint é o que alguém olha — e
existe justamente para o que teste nenhum pega: a tela que sumiu com a suíte
verde, o CORS que só quebra no navegador, a migration que não casou uma linha.

Por isso a pasta não se chama `tests` nem `e2e`. Nomear assim convida a
automatizar o conteúdo, e automatizar destrói a propriedade que o faz valer.

## Um arquivo por funcionalidade

O nome descreve a funcionalidade, sem data e sem número de fatia:

```
docs/checkpoints/cadastro-de-cliente.md
docs/checkpoints/emissao-de-boleto.md
```

Quando a funcionalidade muda, **é este arquivo que muda**. Dois arquivos
datados descrevendo a mesma tela é como um deles envelhece em silêncio e
alguém confere pelo roteiro errado.

## O tipo, no topo do arquivo

Todo runbook abre declarando onde a conferência acontece:

```markdown
---
type: screen-web
---
```

| valor | significa |
|---|---|
| `screen-web` | há uma tela do `-web` para olhar |
| `screen-mobile` | há uma tela do `-mobile` para olhar |
| `api` | terminal e HTTP; não há tela |
| `inbox` | a conferência é numa caixa de entrada |

**O tipo descreve onde a *conferência* acontece, não o setup.** Um runbook
que pede para subir um arquivo pela tela e depois confere tudo no terminal é
`api`: subir é preparação.

## A forma, e por que ela é essa

Quatro seções, nesta ordem. Quem lê de cima para baixo faz primeiro o que
confirma, depois o que tenta quebrar.

**1. O que precisa bater.** A lista de sempre, cada item com o comando ou o
clique e o valor esperado. É a parte que parece um checklist e é a menos
valiosa.

**2. O que tentar para ver se quebra.** Não é lista de conferência, é
provocação: o arquivo corrompido, o campo vazio, o identificador inventado. É
aqui que os defeitos aparecem.

**3. O que não está na lista.** Um parágrafo lembrando de estranhar qualquer
número que apareça sem ter sido pedido. Existe porque a lista é, por
construção, feita das coisas em que já se pensou.

**4. O que este checkpoint já pegou.** Preenchido *depois*, com data e com o
achado real.

A seção 4 transforma a pasta em memória em vez de burocracia: quem for
conferir da próxima vez sabe o que procurar, porque está escrito o que a
última pessoa não teria achado se tivesse só marcado caixinhas.

## O risco desta pasta existir

Um checkpoint a cada tarefa treina quem revisa a carimbar sem olhar, e um
roteiro pronto tem o mesmo defeito, mais forte: lista pronta vira lista
marcada. A defesa são as seções 2 e 3 — as partes que não dá para responder
sem olhar. Um runbook que virou só a seção 1 parou de servir; vale mais
apagá-lo do que mantê-lo.

## Quem executa

Uma pessoa, na mão. Um agente pode preparar o ambiente, atualizar o runbook e
dizer o que não conseguiu verificar; a conferência e a decisão de aprovar são
de quem olha.
