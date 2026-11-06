# Guia das telas do Play Console e do Google Cloud

Conferido em **2026-11-06**, no navegador embutido do app Claude, numa conta
de desenvolvedor **pessoal** já paga, com a interface em português. O Google muda
as telas sem aviso: se uma tela não bater com este guia, siga pelo que está
vendo, diga à pessoa o que mudou e anote a diferença no relatório final.

## O que já se sabe do navegador

- A home `google.play/business` mostra "Go to Play Console"; o link aponta para
  `accounts.google.com/ServiceLogin?service=androiddeveloper…`. Os links podem
  estar fora da tela: navegue direto para a URL do `href`.
- O login (e-mail, senha, dois fatores) é da pessoa. A sessão vale para o Play
  Console e para o console.cloud.google.com.
- Depois do login, a URL tem o ID da conta:
  `play.google.com/console/u/0/developers/<id-da-conta>/…`. O ID do app aparece
  em `…/app/<id-do-app>/…` depois de criado.
- Não ponha e-mail nem dado pessoal em parâmetro de URL (ex.: `authuser=`).
- `get_page_text` funciona no Play Console, mas a página demora a montar: espere
  2 a 3 s depois de navegar. Diálogos (permissões, listas) aparecem no fim do
  texto da página.
- **Campos de texto do Play Console:** `form_input` às vezes não fica. Prefira
  clicar no campo e usar `type`, e confira o valor com
  `document.querySelector('input[type=email]').value` antes do botão final.
- **Caixas de seleção:** os nomes acessíveis são "on". Para saber qual é qual,
  leia o texto do pai de cada `input[type=checkbox]` com `javascript_tool`, só
  para inspecionar.
- **Google Cloud:** o tema é escuro e as listas carregam devagar; recarregue a
  página se a conta recém-criada não aparecer.

## Conferir o papel

Abra `…/developers/<id>/users-and-permissions`. Se a lista de usuários aparece,
a pessoa é Proprietário ou Administrador. Anote as service accounts que já
existem: nenhuma delas é tocada.

## Criar app

`…/developers/<id>/create-new-app`:

- **Nome do app** (até 30) e **Nome do pacote**: o formulário pede o pacote na
  criação, e ele fica preso ao app. Clique em **Ver disponibilidade** e espere
  "Nome de pacote disponível".
- Idioma padrão (vem o da conta), **App** ou Jogo, **Grátis** ou Pago (gratuito
  não vira pago depois de publicado).
- Ao escolher Grátis aparece **"Você vai receber a proteção automática"**
  (verificação do instalador). Fica ligada: não afeta o build pelo cabo, que
  usa outro pacote.
- **Declarações**: duas caixas, Políticas do programa para desenvolvedores e
  Leis de exportação dos EUA. São aceites em nome da pessoa: ela marca, ou dá
  o ok explícito.
- **Criar app** leva ao Painel do app ("O que fazer antes de publicar o app"), e
  o teste interno já fica disponível.

## Google Cloud: projeto, API, service account e chave

- `console.cloud.google.com/projectselector2/home/dashboard` lista os
  projetos. Um projeto que já serve a outro app do Play costuma ter a API
  ativa: confira em
  `…/apis/api/androidpublisher.googleapis.com/metrics?project=<id>`, onde deve
  aparecer **Status: Ativado**.
- Contas de serviço: `…/iam-admin/serviceaccounts?project=<id>`. Criar:
  `…/iam-admin/serviceaccounts/create?project=<id>`. Os campos são nome, ID
  (preenchido a partir do nome) e descrição. **Criar e fechar** cria sem passar
  pela tela de papéis: é o que queremos (nenhum papel IAM).
- Chave: a conta → aba **Chaves** →
  `…/serviceaccounts/details/<id-numérico>/keys` → **Adicionar chave → Criar
  nova chave → JSON → Criar**. O aviso diz "Chave privada salva no seu
  computador: `<projeto>-<12 hex>.json`". O arquivo vai para `~/Downloads` da
  pessoa. Mova pelo nome exato, sem abrir (`mv` + `chmod 600`).
- Projeto "No organization": a criação de chave não é bloqueada. Numa
  organização com a política `iam.disableServiceAccountKeyCreation`, ela é
  bloqueada: pare e diga à pessoa.

## Convidar a service account

`…/developers/<id>/users-and-permissions/invite`:

- **Endereço de e-mail** (o placeholder é `user@example.com`): digite o e-mail da
  service account.
- **Permissões do app → Adicionar app**: um menu com caixas, uma por app, mais
  "Selecionar tudo". Marque só o app → **Aplicar**.
- O diálogo **"Permissões para <app>"** já vem com duas de leitura marcadas:
  "Ver informações do app (somente leitura)" e "Acessar informações de
  qualidade do app (somente leitura)". Marque também **"Liberar apps para as
  faixas de teste"**, que já inclui o upload em app rascunho. Deixe desmarcado:
  Administrador, "Enviar para produção…", dados financeiros e presença na loja.
  **Aplicar**.
- A tabela mostra o app com "3" permissões. **Permissões da conta**: nenhuma.
- **Convidar usuário** abre o diálogo **"Enviar convite?"** → **Enviar convite**.
  Service account não precisa aceitar: aparece como **Ativo** na lista.

## Teste interno e testers

`…/app/<id-do-app>/tracks/internal-testing?tab=testers`:

- A faixa começa "Inativo", com as etapas Selecionar testadores → Criar uma
  nova versão → Visualizar e confirmar.
- **As listas de e-mail são da conta inteira**: as que outros apps já usam
  aparecem aqui. Abrir uma lista ("Editar a lista de e-mails") mostra os
  e-mails; feche no X sem salvar. Marque a lista certa → **Salvar** ("Changes
  updated").
- "Como os testadores podem participar": "O link será exibido aqui quando você
  publicar o app", ou seja, só depois do primeiro lançamento.

## Bloqueios e avisos conhecidos

- **"Declare seu status de comerciante"** (banner do topo, prazo em 2027): não
  bloqueia o teste interno. Só a pessoa resolve.
- **Conta pessoal nova** precisa de um teste fechado com pelo menos 12 testers
  por 14 dias antes do acesso à produção. Não afeta o teste interno.
- **App em rascunho:** a API só aceita release `draft` até o primeiro
  lançamento pela tela.
