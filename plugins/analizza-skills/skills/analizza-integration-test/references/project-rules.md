# Regras de projeto

Seções acrescentadas pelo Passo 9 ao arquivo de convenções do projeto. Cada
uma entra **só se o arquivo ainda não tiver uma seção com o mesmo título**
(`grep -qE '^#{1,4} <título>$'`); nunca sobrescreva uma existente. Uma seção
com o mesmo título em qualquer nível de heading conta como já existente —
projetos aninham estas seções sob `## Arquitetura` como `###`. O parágrafo de
*Testes* vai para dentro da seção *Testes* que já existir, ou para uma nova.

## Variáveis de ambiente

**Toda variável lida pela configuração da aplicação (`${NOME}` ou
`${NOME:padrao}`) está em dois lugares além dela, no mesmo commit que a
introduz:**

1. **`README.md`, seção *Variáveis de ambiente*, sem valor** — sempre `NOME=`,
   mesmo quando há padrão e mesmo quando o valor não é segredo. O padrão mora
   só na configuração: copiá-lo para o README é criar um segundo lugar para
   ele envelhecer.
2. **`.env.local` da raiz, se o arquivo existir na máquina** — com o padrão da
   configuração preenchido, ou vazio (`NOME=`) quando não há padrão. O arquivo
   não é versionado, então isto é um passo na máquina de quem mexeu, não uma
   linha do diff: não crie o arquivo se ele não existe.

Renomear ou remover uma variável mexe nas mesmas duas listas.

O porquê: o `.env.local` não vai para o repositório, e o README é a única
lista versionada do que a aplicação precisa para subir. Sem ela, uma variável
nova sem padrão faz a aplicação parar de subir em toda máquina, e ninguém sabe
que ela existe até o boot recusar.

## Checkpoints de conferência

Um checkpoint é uma parada onde **uma pessoa olha o resultado rodando** antes
de o trabalho seguir. Ele não substitui teste: existe para o que teste nenhum
pega.

**Proponha um checkpoint sem esperar que peçam** sempre que o critério de
aceite mora fora da suíte de testes:

- **Aparência.** Uma tela nova ou redesenhada, comparada com um print, um
  protótipo ou uma descrição.
- **Contrato com serviço externo.** A primeira chamada real a um storage, a um
  SMTP, a uma API de terceiro. Container e emulador provam a forma, não provam
  a conta de produção, o CORS nem a credencial.
- **Migration que muda dado que já existe.** Rodar contra uma cópia e conferir
  as linhas antes de rodar contra o ambiente de verdade.
- **Qualquer coisa irreversível ou de fora**: apagar dado, publicar, mandar
  mensagem para gente de verdade, mexer em configuração compartilhada.

**Não proponha checkpoint** para o que a suíte já cobre: regra de domínio,
handler, contrato HTTP entre os próprios módulos, refactor com teste verde
antes e depois. Um checkpoint a cada tarefa treina quem revisa a carimbar sem
olhar.

**Como propor.** Diga o que olhar e como olhar, não "confira por favor", e
aponte o runbook da funcionalidade em `docs/checkpoints/`. Diga também, sem
que perguntem, **o que você não conseguiu verificar** — é isso que a pessoa
confere primeiro.

**Quem executa é uma pessoa, na mão.** Não rode o fluxo e apresente a saída
como se fosse a conferência. Num plano de implementação, o checkpoint é uma
seção própria entre as fases, e a fase seguinte não começa sem o aval.

## Débitos técnicos

Coisas já implementadas que funcionam mas carregam uma dívida conhecida. Cada
item diz o que está errado, por que foi aceito e o que o fecha. Nenhum bloqueia
o uso em desenvolvimento; quem mexer na área decide se fecha junto.

Um item entra no mesmo commit que cria a dívida, não depois. Um débito que só
existe na cabeça de quem o criou é um defeito esperando para ser redescoberto.

## Testes — parágrafo

**Um exemplo escrito à mão do formato de saída de outro sistema não é
evidência sobre o que aquele sistema produz.** Teste de adapter que monta à
mão uma URL, um JSON ou uma mensagem "como o SDK devolveria" prova só que o
código entende o exemplo. O teste que protege a integração usa a saída real —
do SDK, do container, do serviço — ao menos uma vez.

**O inverso também vale: o teste de integração não substitui o unitário.**
Subir container e contexto Spring a cada ramo de erro é caro demais para
cobrir todos eles a cada mudança — é o teste unitário do handler, com dublê
da dependência externa, que cobre os ramos de erro exaustivamente e roda em
segundos. Todo entrypoint tem os dois: o unitário prova os ramos, o
`<Nome>IT` prova que o sistema de verdade se comporta como o dublê promete.
Nenhum dos dois é opcional por causa do outro.
