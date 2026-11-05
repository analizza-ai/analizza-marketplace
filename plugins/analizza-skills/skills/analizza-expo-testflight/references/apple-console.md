# Guia das telas da Apple

Conferido em **2026-11-05**, no navegador embutido do app Claude, com uma conta
de time pago, numa primeira configuração real de ponta a ponta (App ID, app,
grupo, tester e primeiro build no TestFlight). A Apple muda as telas sem aviso: se uma tela não bater com este
guia, siga pelo que está vendo, diga à pessoa o que mudou e anote a diferença
no relatório final para atualizar este arquivo.

## O que já se sabe do navegador

- O navegador embutido abre developer.apple.com e appstoreconnect.apple.com.
  O login (usuário, senha, dois fatores) é feito pela pessoa no painel; a
  sessão vale para os dois sites sem novo login.
- **developer.apple.com aparece em inglês; o App Store Connect, em português**
  (segue o idioma da conta). Procure os rótulos nos dois idiomas.
- No App Store Connect, `get_page_text` volta **vazio** (a página é montada por
  script). Leia com `read_page` (`filter: "interactive"`) ou com screenshot, e
  ache botões com `find` pelo nome acessível.
- O botão `+` da lista de Apps tem o nome acessível **"Novo app"** (não
  "Adicionar apps", que é o texto visível só quando a lista está vazia).
- **Screenshot vencido engana.** Depois de um clique que troca de tela, o
  screenshot seguinte pode ainda mostrar a tela anterior. Na sequência do App
  ID, o **Register** aparece exatamente onde estava o **Continue**: um segundo
  clique "no Continue" registra sem confirmação. Depois de cada clique, espere
  e tire um screenshot novo antes do próximo, e nunca clique duas vezes no
  mesmo lugar sem conferir o que está ali.
- No developer.apple.com, o formulário do App ID não aparece no `read_page` nem
  no `find`: use screenshot, clique por coordenada e `type`. O botão Continue
  só habilita depois que o campo do bundle perde o foco (Tab).
- No App Store Connect, `form_input` em lista (`select`) troca o valor mas o
  screenshot logo depois pode não mostrar; confira com `read_page` do modal.
- Se o SMS de dois fatores não chegar: "Reenviar código" com opção de ligação,
  ou código gerado num aparelho logado na conta (Ajustes → nome → Iniciar
  Sessão e Segurança → Obter Código de Verificação). Não há o que a skill faça
  por esse passo: espere a pessoa.

## Bloqueios que param tudo

- **Contrato de licença atualizado.** Banner "Contrato de licença atualizado do
  Apple Developer Program" na lista de Apps: enquanto o **titular da conta** não
  aceitar em developer.apple.com/account, a Apple recusa app novo e build novo.
  Pare e peça ao titular; um Administrador não consegue aceitar.
- **Termos de serviço do App Store Connect** (primeiro acesso): caixa "Eu li e
  concordo com os termos apresentados acima." e **Concordar**. Aceitar é da
  pessoa.
- **"Review the updated Paid Applications Schedule"** (em inglês, mesmo com a
  conta em português): segundo contrato, só do titular, em Negócios. Não
  bloqueou criar app nem enviar build ao TestFlight interno; bloqueia apps
  pagos, compras dentro do app e envio à App Store. Avise e siga.
- **Limite de certificados de distribuição.** Se o time já estiver no limite,
  pare: revogar um certificado derruba o deploy de outro app.

## developer.apple.com (inglês)

**Conferir o time.** O canto superior direito mostra `<NOME DA EMPRESA> -
<TEAM ID>`. Compare com o Team ID da spec antes de qualquer cadastro.

**App ID.** `https://developer.apple.com/account/resources/identifiers/list`
1. `+` ao lado de "Identifiers" (ou "Register an App ID" quando a lista está vazia).
2. "Register a new identifier": rádio **App IDs** → Continue.
3. "Select a type": **App** (não App Clip) → Continue.
4. "Register an App ID": Description, Bundle ID **Explicit** com o bundle.
   Capabilities: deixe como vêm (todas desmarcadas é normal).
5. Continue → tela "Confirm your App ID" → **Register**.
6. A lista de Identifiers passa a mostrar o nome e o bundle.

Já existe? Procure o bundle na lista antes do passo 1.

**Certificado Apple Distribution.** `https://developer.apple.com/account/resources/certificates/list`
1. Conte os certificados do tipo Distribution na lista.
2. `+` → "Create a New Certificate" → **Apple Distribution** (a segunda opção;
   "iOS Distribution (App Store Connect and Ad Hoc)" é a legada) → Continue.
3. Envie o `.csr` (seletor de arquivo do sistema: é a pessoa quem escolhe).
4. "Download your certificate" → **Download** (`distribution.cer`).

## appstoreconnect.apple.com (português)

**Novo app.** `https://appstoreconnect.apple.com/apps`
1. `+` (nome acessível "Novo app").
2. Modal "Novo app":
   - Plataformas: iOS
   - Nome da empresa: só aparece no primeiro app do time
   - Nome: até 30 caracteres, único na App Store
   - Idioma principal
   - ID do pacote: lista que só mostra App IDs já registrados
   - SKU
   - Acesso de usuário: "Acesso total" ou "Acesso limitado"
3. **Criar**. A lista de Apps mostra o app com "iOS 1.0 Preparar para envio".

Ao criar, a Apple pode mostrar "Não foi possível salvar seus ajustes de acesso
de usuário" mesmo com o app criado: o texto diz que "todos os usuários têm
acesso ao app". Para usuários que já tinham acesso só a apps específicos, isso
**não** vale: eles continuam sem o app novo (ver Testers).

Nome já usado na App Store: o modal recusa; pergunte uma variação à pessoa (o
nome no ícone vem do `.properties`, não daqui).

**Chave da App Store Connect API.** Usuários e acesso → Integrações → (menu
Chaves) API do App Store Connect.
1. Primeira vez no time: **Solicitar acesso** → a página mostra "Sua solicitação
   de acesso à API do App Store Connect foi aprovada".
2. **Gerar chave de API** → modal: Nome, Acesso (chips; padrão sugerido:
   **Administrador**) → **Gerar**.
3. Na linha da chave: **Baixar** (só uma vez). A tabela mostra o ID DA CHAVE;
   o **Issuer ID** fica acima da tabela, com botão Copiar.

Já existe uma chave ativa do CI? Reaproveite os arquivos guardados pela pessoa;
não gere outra.

**Grupo de testes interno.** App → aba **TestFlight** → barra lateral
**TESTES INTERNOS** → `+` → "Criar novo grupo interno": nome e **Ativar
distribuição automática** (o próprio modal avisa que não muda depois) → Criar.

**Testers.** O modal "Adicionar testers ao grupo" só lista quem já é usuário do
App Store Connect **e tem acesso ao app**. Usuário que já existe mas não aparece:
Usuários e acesso → a pessoa → Apps → **Gerenciar apps** → marcar o app novo →
Concluído → **Salvar**. Mudar acesso de usuário é ação da pessoa (peça o ok).
Se a seleção cobrir todos os apps do time, a Apple a troca por **"Todos os
apps"**, que inclui os apps futuros: mostre isso antes de Salvar.

Usuários com função acima de Desenvolvedor (Gerente de apps, Administrador)
servem como testers internos; não mude a função para isso.
1. Usuários e acesso → aba **Pessoas** → `+` → "Novo usuário": Nome, Sobrenome,
   E-mail, Funções (ex.: Desenvolvedor) → Próximo → convite por e-mail.
2. O usuário aparece com convite pendente ("Reenviar convite") até aceitar.
3. Depois de aceito: TestFlight → grupo → **Convidar testers** → marcar → Adicionar.
