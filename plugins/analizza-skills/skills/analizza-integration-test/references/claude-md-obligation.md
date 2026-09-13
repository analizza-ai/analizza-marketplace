# Obrigação de runbook no `CLAUDE.md`

Acrescente ao fim do `CLAUDE.md` da raiz (crie o arquivo com este bloco se ele
não existir). `{conventions-file}` é o arquivo de convenções em que o Passo 8
gravou as regras de projeto.

```markdown
## O que "pronto" inclui

**Toda funcionalidade criada ou alterada produz ou atualiza o runbook dela em
`docs/checkpoints/<funcionalidade>.md`.** Faz parte do trabalho, não é um passo
depois dele: uma fatia que entrega código sem o runbook está incompleta. Não
entregue assim, e não peça permissão para pular.

**Como** escrever o runbook — um arquivo por funcionalidade, o tipo no topo, as
quatro seções e por que elas são essas — está em
[docs/checkpoints/README.md](docs/checkpoints/README.md). **Quando** propor a
conferência está em [{conventions-file}]({conventions-file}), na seção
*Checkpoints de conferência*.

Esta obrigação mora aqui, e não só no arquivo de convenções, porque este
arquivo entra em contexto sozinho: uma definição de pronto que mora apenas no
arquivo que pode não ser lido se perde em silêncio — e o runbook é o que mais
se perde, porque a fatia *parece* terminada sem ele.
```
