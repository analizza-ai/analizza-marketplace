# Design: skill `analizza-expo-testflight`

Data: 2026-11-05
Repositório: `analizza-ai/analizza-marketplace`
Status: em brainstorming, aguardando aprovação

## Intenção

Hoje, levar um app Expo ao TestFlight custa um dia de cliques no portal da
Apple, um pipeline escrito à mão e um runbook que só fica certo depois de
errar uma vez. Isso aconteceu duas vezes: no bjjdream (Flutter, com um gist
de 30 prints) e no yeroon-play (Expo, PR `yeroon-tech/yeroon-play#44`). Na
comparação entre os dois, o runbook do yeroon-play errou rótulos e caminhos
da Apple e pulou passos inteiros: os termos do App Store Connect, o
"Solicitar acesso" da API e a criação do usuário antes de adicioná-lo como
tester.

A skill faz esse trabalho em qualquer app Expo, de qualquer empresa. Ela
implementa o pipeline no repositório e depois configura a Apple pelo
navegador embutido, com a pessoa assistindo. A pessoa faz login, decide e
cuida dos segredos. A skill preenche o que a spec já define.

## Objetivos

- Um app Expo sai da skill com um botão (Dev) ou uma tag (Prod) que builda,
  assina e envia ao TestFlight.
- A configuração na Apple Developer e no App Store Connect é feita pela skill
  no navegador, com a pessoa vendo cada tela.
- Nada específico de empresa ou app fica escrito na skill. Tudo vem da spec
  do projeto ou de uma entrevista.
- Cada ambiente sai com o seu runbook em `docs/checkpoints/`, conferível pelo
  `/test-runbook`.
- Funciona em Claude Code, Codex e Antigravity. Esses dois últimos não têm
  navegador embutido e recebem os passos para seguir à mão.

## Não-objetivos

- Flutter, Swift nativo ou React Native sem Expo.
- Expo com a pasta `ios/` versionada (bare workflow) ou com build pelo EAS.
- Android e Play Store.
- Publicar na App Store. A promoção do TestFlight para a loja continua manual.
- Push notifications, Firebase e outras capabilities além das padrão.
- CI fora do GitHub Actions.

## Anti-objetivos

Falhar em qualquer item abaixo é falhar, mesmo que o build chegue ao
TestFlight. *Lista proposta por mim; a pessoa não tinha uma pronta.*

- **Mexer no que já existe na conta Apple:** revogar certificado, apagar App
  ID, trocar o papel de um usuário. Um app novo não pode derrubar o deploy de
  outro. Se algo existente impede o avanço, a skill para e pergunta.
- **Segredo fora do lugar.** O `.p8`, o `.p12`, a chave privada do CSR ou uma
  senha aparecendo no repositório, num commit, no chat, num arquivo da skill
  ou no log do Actions.
- **Ação sem volta sem o ok da pessoa no momento.** Aceitar termos, convidar
  pessoas, gerar chave, registrar App ID, criar app ou grupo.
- **Terminar calada pela metade.** O relatório final sempre separa o que
  ficou pronto do que ficou pendente (por exemplo, o convite ainda não
  aceito) e diz quem tem de fazer o quê.
- **Prender a skill a um cliente.** Nome, time, URL ou caminho de uma empresa
  escritos no texto da skill ou nos templates.
- **Fatia sem runbook.** Toda fatia entrega o seu.

## Decisões da pessoa

1. **Só Expo.**
2. **Os dois ambientes, Dev e Prod**, perguntados no início. Cada ambiente é
   uma fatia completa. Normalmente se começa por Dev, mas dá para ir direto
   para Prod.
3. **Dev** é um app próprio na Apple (ex.: "Yeroon Play Dev"), aponta para o
   backend de desenvolvimento e é disparado manualmente de qualquer branch,
   menos a padrão. **Prod** é outro app (ex.: "Yeroon Play"), aponta para o
   backend de produção, é disparado por tag e vai para o TestFlight. A
   promoção para a loja é manual.
4. **A spec pode vir de um brainstorming anterior. Se faltar ou estiver
   incompleta, a skill entrevista** e escreve a spec antes de implementar.
5. **Dado faltando: a skill pergunta. Passo manual: a skill diz exatamente o
   que digitar ou clicar no navegador** e espera a pessoa avisar.
6. **Mora no `analizza-marketplace`**, no plugin `analizza-skills`, e é
   instalada pelo plugin do Claude Code ou de outro harness, como as demais.
7. **A chave da API sai com acesso Administrador por padrão**, o mesmo nível
   que já funciona no bjjdream com `-allowProvisioningUpdates`. A skill avisa
   que essa chave vale para o time inteiro, e por isso o environment precisa
   de aprovação obrigatória. A pessoa ainda confirma o nível na tela.
8. **A validação de ponta a ponta é a fatia Prod do yeroon-play.** O Dev já
   existe lá (PR `yeroon-tech/yeroon-play#44`). Na validação, a skill
   reconhece essa fatia, monta o app "Yeroon Play" de produção, reaproveita a
   chave e o certificado e leva o primeiro build por tag ao TestFlight. A fatia
   Dev do zero é conferida por leitura dos templates e pelo teste em modo
   manual, sem criar um app descartável na Apple.

## Como funciona

### Fase 0: ler, entrevistar, decidir o ambiente

1. **Confere se é um projeto Expo.** Procura `app.json` ou `app.config.*` com
   `expo`, e `expo` no `package.json`. Se for um monorepo, pergunta qual pasta
   é o app quando houver mais de uma. Se não for Expo, para e diz por quê.
2. **Lê o que já existe.** Specs em `docs/superpowers/specs/`, arquivos de
   identidade em `.github/apps/*.properties`, workflows
   `mobile-ios-testflight-*.yml` e runbooks `docs/checkpoints/testflight-ios-*`.
   Uma fatia que já existe é retomada, não refeita.
3. **Pergunta o ambiente:** Dev, Prod ou os dois, com Dev sugerido.
4. **Junta os dados.** O que a spec não traz é perguntado de uma vez, no
   começo, para não interromper a pessoa no meio da Apple (*minha decisão*).
   Ver "Dados de entrada".
5. **Grava a spec** em `docs/superpowers/specs/AAAA-MM-DD-testflight-ios-<env>-design.md`
   quando ela veio da entrevista, para a próxima fatia e a próxima pessoa
   lerem.

### Fase 1: implementar no repositório

Generaliza o que o yeroon-play já tem e já foi revisado:

| Artefato | Papel |
|---|---|
| `.github/apps/<app-slug>.properties` | Identidade não secreta do ambiente: nome, bundle, time e as URLs públicas. |
| `.github/scripts/ios-identity.sh` e `.test.sh` | Guarda de ref (branch para Dev, tag para Prod) e leitura e validação do `.properties`. |
| `.github/workflows/mobile-ios-testflight-<env>.yml` | Dev: `workflow_dispatch`. Prod: push de tag. Mesmo build (prebuild, archive sem assinatura, export assinado pela chave da API, upload). |
| `app.config.ts` do app | Lê do ambiente o nome exibido, o bundle, o time e o build number. Declara `ITSAppUsesNonExemptEncryption: false`. Sem as variáveis, nada muda. Tem teste. |
| alvo `mobile-ios-secrets` no `Makefile` | Grava as cinco credenciais no environment do GitHub escolhido (`ENV=`), sem apagar a proteção. Cria o environment só se ele não existir. |
| `docs/checkpoints/testflight-ios-<env>.md` | Runbook do ambiente no formato de `docs/checkpoints/README.md`. A preparação usa os rótulos reais da Apple (ver "Guia da Apple"). |

Regras herdadas do yeroon-play:

- **O `name` e o `scheme` do Expo não mudam.** Eles definem o projeto Xcode,
  e o scheme costuma estar fixo no retorno de OAuth. Só muda o
  `CFBundleDisplayName`.
- **As variáveis públicas do app vêm do `.properties`.** São as
  `EXPO_PUBLIC_*` que o app de fato lê, levantadas com um `grep` no código.
  Elas são repassadas ao prebuild e ao archive. A skill não inventa nomes.
- **O build number é o `run_number` do workflow.** Como Dev e Prod são apps
  diferentes, cada um tem o seu contador.
- **O workflow só aparece para disparo depois de estar na branch padrão.** A
  skill diz isso e entrega a fatia como PR. Ela não faz merge.
- **Testes antes do código** para o `app.config.ts` e para o script de
  identidade, como no yeroon-play.

Tudo fica numa branch, com commits e um PR. Push e PR só com o ok da pessoa.

### Fase 2: configurar a Apple pelo navegador

**Ferramenta, em ordem de preferência.**
1. Navegador embutido do app Claude (`mcp__Claude_Browser__*`).
2. Claude in Chrome, se a pessoa pedir.
3. Sem navegador (Codex, Antigravity, terminal): a skill entrega os passos do
   runbook, um bloco por vez, e espera a confirmação de cada um. É o mesmo
   modo manual da `test-runbook`.

**Painel visível antes do primeiro passo.** A pessoa acompanha cada tela.

**Sequência para o primeiro ambiente do time.** Os detalhes de tela estão no
Guia da Apple.

1. **Login** em developer.apple.com com a conta da empresa.
   *Pessoa:* digita usuário, senha e 2FA.
   *Skill:* confere o time no canto da tela contra o Team ID da spec. Se não
   bater, para.
2. **App ID explícito** com o bundle do ambiente.
   *Skill:* preenche e mostra o resumo.
   *Pessoa:* dá o ok, e a skill clica em Register.
3. **App Store Connect:** termos, se aparecerem.
   *Pessoa:* marca a caixa e clica em Concordar.
4. **Novo app:** plataforma iOS, nome da empresa (só no primeiro app do
   time), nome, idioma, ID do pacote, SKU e acesso de usuário.
   *Skill:* preenche.
   *Pessoa:* dá o ok, e a skill clica em Criar.
   *Se o nome estiver tomado* (é único no mundo), a skill pergunta uma
   variação.
5. **Chave da API**, uma por time: "Solicitar acesso" na primeira vez, depois
   "Gerar chave de API" com o nome e o nível de acesso da spec.
   *Skill:* preenche o nome.
   *Pessoa:* confirma o nível de acesso e clica em Baixar o `.p8`, salvando
   fora do repositório.
   *Skill:* lê da tela o Key ID e o Issuer ID.
6. **Certificado Apple Distribution**, um por time.
   *Skill:* conta antes os certificados de distribuição. Se o limite estiver
   cheio, para; não revoga nada.
   *Skill:* gera a chave e o CSR com `openssl` numa pasta fora do repositório,
   que a pessoa escolhe, e sem imprimir a chave.
   *Pessoa:* envia o CSR e baixa o `.cer`, porque escolher arquivo é um
   seletor do sistema.
   *Pessoa:* gera o `.p12` no próprio terminal com `openssl pkcs12 -export`,
   digitando a senha. A skill entrega o comando.
7. **Grupo de testes interno** com distribuição automática.
   *Skill:* avisa que a distribuição automática não muda depois de criado o
   grupo e pede o ok.
8. **Testers.** Quem ainda não é usuário do App Store Connect é criado em
   Usuários e acesso → Pessoas, com a função da spec.
   *Pessoa:* autoriza cada convite.
   *Convidado:* aceita por e-mail. A skill registra o convite como pendente e
   segue.
   Quem já aceitou é adicionado ao grupo.

No segundo ambiente do mesmo time, os passos 5 e 6 são pulados e as
credenciais são reaproveitadas.

### Fase 3: GitHub

1. **Credenciais.** A pessoa roda o `make mobile-ios-secrets ENV=<environment>`
   no próprio terminal. A skill entrega o bloco de `export` com os caminhos
   dos arquivos e nunca vê os valores. No segundo ambiente, os mesmos
   arquivos vão para o segundo environment.
2. **Aprovação obrigatória no environment.** A skill orienta a configuração
   pelo navegador em Settings → Environments, ou monta o `gh api`. A pessoa dá
   o ok porque é uma mudança de configuração do repositório. O motivo vai no
   runbook: o workflow roda o arquivo da ref escolhida, e o certificado e a
   chave valem para o time inteiro.
3. **Merge do PR pela pessoa**, para o botão aparecer (Dev). Em Prod, o
   gatilho é a primeira tag.

### Fase 4: primeiro build e conferência

A skill pede para a pessoa disparar o workflow (Dev) ou criar a tag (Prod).
Depois acompanha o run com `gh run watch` e propõe o `/test-runbook` no
runbook do ambiente.

Fecha com um relatório:
- o que ficou pronto;
- o que está pendente e com quem (convite não aceito, PR por mergear,
  aprovação no environment);
- o que fazer para a próxima fatia.

### Retomada

Cada passo da Fase 2 começa olhando se já foi feito:
- o App ID já está na lista;
- o app já está no App Store Connect;
- a chave já está ativa, ou o acesso já foi pedido e está esperando aprovação;
- o grupo já existe;
- o tester já está no grupo.

O mesmo vale para a Fase 3: o environment já existe e os secrets já estão
listados no `gh secret list --env`, que mostra só os nomes.

A skill pula o que já está feito e continua do próximo passo. Ela nunca cria
uma segunda cópia.

## Dados de entrada

**Do time.** Valem para todos os apps da empresa.

| Dado | Exemplo | Onde se usa |
|---|---|---|
| Team ID | `XF98CA5PDT` | `.properties`, conferência do login |
| Nome da empresa no App Store Connect | `Yeroon` | Novo app, só no primeiro app do time |
| Nível de acesso da chave da API | Administrador (padrão sugerido) | Gerar chave |
| Repositório do GitHub | `yeroon-tech/yeroon-play` | `make mobile-ios-secrets` |

**Do ambiente.** Um conjunto por ambiente.

| Dado | Exemplo (Dev) |
|---|---|
| Nome do app (até 30 caracteres; *a confirmar*: na tela do bjjdream o contador mostrava 20) | `Yeroon Play Dev` |
| Bundle ID | `video.yeroon.play.dev` |
| SKU | `yeroon-play-dev` |
| Idioma principal | Português (Brasil) |
| Acesso de usuário ao app | Acesso total |
| URLs públicas: cada `EXPO_PUBLIC_*` que o app lê | `https://api.dev...` |
| Environment do GitHub | `yeroon-play-dev` |
| Gatilho | Dev: manual, qualquer branch menos a padrão. Prod: tag `v*` (*minha decisão*) |
| Grupo de testes | `Yeroon` |
| Testers (nome, e-mail, função) | pessoas do time |

Na conversa entra só o que não é segredo. Senhas, o `.p8`, o `.p12` e os
códigos de 2FA nunca passam pela skill.

## Guia da Apple

Um arquivo de referência da skill (`references/apple-console.md`) guarda a
sequência real de telas, com os rótulos nos dois idiomas. Na comparação com o
gist, o developer.apple.com apareceu em inglês e o App Store Connect em
português. O guia registra:

- Identifiers → `+` → App IDs → Continue → App → Continue. O formulário tem
  Description e Bundle ID Explicit. Capabilities ficam como vêm. Depois
  Continue e Register.
- Termos de serviço / Terms of Service: caixa e Concordar / Agree.
- Apps → Adicionar apps / `+` → Novo app, com os campos:
  - Plataformas
  - Nome da empresa (só no primeiro app do time)
  - Nome
  - Idioma principal
  - ID do pacote, numa lista que só mostra App IDs já registrados
  - SKU
  - Acesso de usuário

  Depois Criar.
- Usuários e acesso → Integrações → API do App Store Connect → Solicitar
  acesso → aguardar aprovação → Gerar chave de API (nome e acesso) → Gerar →
  Baixar (só uma vez). O Issuer ID fica acima da tabela.
- Certificates → `+` → Apple Distribution (não a iOS Distribution legada) →
  enviar o CSR → Download.
- TestFlight → TESTES INTERNOS → `+` → Criar novo grupo interno, com nome e
  Ativar distribuição automática (não muda depois).
- Usuários e acesso → Pessoas → `+` → Novo usuário (nome, sobrenome, e-mail,
  funções) → convite por e-mail. Depois TestFlight → grupo → Convidar testers.

O guia leva a data da última conferência. Se uma tela não bater, a skill
avisa, segue pelo que está vendo e anota a diferença para atualizar o guia.

## Restrições de segurança

- A skill nunca digita senha, código 2FA, conteúdo de chave ou senha de
  `.p12`, nem lê esses valores de arquivo.
- Arquivos secretos ficam numa pasta fora do repositório, escolhida pela
  pessoa. A skill confere que o `.gitignore` não é a única proteção: a pasta
  não pode estar dentro do repositório.
- Os cliques sem volta (Register, Criar, Gerar, Concordar, convidar) só
  acontecem depois do ok da pessoa naquele passo. Um ok não vale para o
  passo seguinte.
- Nada existente é revogado, apagado ou rebaixado.
- O workflow gerado passa `github.ref` e `github.ref_name` por `env:`, sem
  interpolar no script. Isso corrige o ponto adiado M1 do yeroon-play.

## Distribuição

- Pasta `plugins/analizza-skills/skills/analizza-expo-testflight/`, com:
  - `SKILL.md`;
  - `references/` com o guia da Apple e o guia de dados de entrada;
  - `templates/` com o workflow, o script de identidade e o teste dele, o
    `.properties`, o trecho do `app.config.ts` e o teste dele, o alvo do
    Makefile e o runbook.
- Entra nas descrições de `marketplace.json`, `.claude-plugin/plugin.json` e
  `.codex-plugin/plugin.json`, e no README.
- Versão do plugin: `0.12.0`.
- Instalação: pelo plugin do harness (`claude plugin install`, Codex,
  Antigravity) ou por `npx skills add analizza-ai/analizza-marketplace --skill analizza-expo-testflight`.
- O nome `analizza-expo-testflight` é *minha decisão*.

## Decisões minhas (a pessoa pode trocar)

- **Só Expo com geração nativa.** A pasta `ios/` fica no `.gitignore` e é
  recriada pelo `expo prebuild --clean`. Se a `ios/` estiver versionada (bare
  workflow) ou o projeto já usar EAS (`eas.json`), a skill para e explica:
  o prebuild apagaria as customizações nativas, e o EAS já é outro caminho de
  build. Os dois casos entram nos não-objetivos.
- **Versão em Prod.** A tag é `v<versão>` e precisa ser igual ao `version`
  do `app.json`. Se não bater, a guarda falha antes de ler qualquer
  credencial. O build number continua sendo o `run_number` do workflow de
  Prod. A guarda de Prod também exige que o commit da tag esteja na branch
  padrão. Uma tag criada em branch de feature não vai para produção.
- **Fatia existente com outro formato.** A skill nunca reescreve uma fatia que
  já funciona. Ao acrescentar Prod, ela cria os arquivos no formato dela e
  deixa os do Dev como estão. No relatório, ela aponta as diferenças e oferece
  a migração como um passo separado, que só acontece com o ok da pessoa. Uma
  fatia existente é reconhecida pelo
  `.github/workflows/mobile-ios-testflight-*.yml` e pelo `.properties` que ele
  lê.
- **Formato canônico.** Script `ios-identity.sh <guard-branch|guard-tag|load>`.
  O `.properties` traz uma linha para cada `EXPO_PUBLIC_*` que o app lê, em
  vez de `API_URL` e `WEB_URL` fixos. O alvo do Makefile recebe `ENV=`.
- **O navegador antes de tudo.** O primeiro passo do plano é um teste
  descartável: abrir developer.apple.com e appstoreconnect.apple.com no
  navegador embutido e conferir se o login com 2FA funciona e se a sessão
  continua de uma tela para outra. Se não funcionar, o modo manual vira o
  caminho principal e o navegador fica como opção.
- **Runbook.** Os runbooks que contam são os que a skill gera no projeto de
  destino. O marketplace não tem a regra de runbook por funcionalidade, então
  a skill não ganha um runbook próprio.

## Fica para quem implementar

- O texto exato do `SKILL.md` e a divisão entre o `SKILL.md` e as references.
- Como detectar no código as `EXPO_PUBLIC_*` usadas.
- O formato do bloco de `export` entregue para o `make mobile-ios-secrets`.
- Como um projeto com `app.config.js` em vez de `app.config.ts` recebe a
  leitura do ambiente.

## Pronto quando

- **Validação real**, no yeroon-play: a skill reconhece a fatia Dev existente
  e entrega a fatia Prod de ponta a ponta. São o PR, o app "Yeroon Play" na
  Apple, o environment de Prod com secrets e aprovação obrigatória, e o
  primeiro build por tag no TestFlight, conferido pelo `/test-runbook`.
- Num projeto Expo sem nada de iOS (conferido sem tocar na Apple), a skill
  entregaria a fatia Dev:
  - PR com o workflow, a identidade, o `app.config.ts` testado, o alvo do
    Makefile e o runbook;
  - Apple configurada pelo navegador, com a pessoa assistindo;
  - secrets gravados;
  - primeiro build no TestFlight.
- Rodada no Codex, a skill entrega os passos à mão, sem tentar abrir
  navegador.
- `grep` nos arquivos da skill não encontra Yeroon, XF98CA5PDT nem bjjdream.
