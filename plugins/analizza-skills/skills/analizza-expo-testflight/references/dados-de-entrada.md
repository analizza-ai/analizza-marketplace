# Dados de entrada

O que a skill precisa saber antes de gerar arquivos ou abrir a Apple. Procure
primeiro na spec do projeto (`docs/superpowers/specs/`), nos `.properties` de
`.github/apps/` e no `app.json`. O que faltar vira **uma pergunta só**, no
começo, com todos os itens juntos: a pessoa não deve ser interrompida no meio
da Apple por um dado que dava para pedir antes.

Nunca peça nem aceite na conversa: senha, código de dois fatores, conteúdo de
`.p8`, `.p12` ou chave privada.

## Do time (valem para todos os apps da empresa)

| Dado | Pergunta | Onde se usa |
|---|---|---|
| Team ID | "Qual o Team ID da empresa na Apple? (10 caracteres, no canto do developer.apple.com)" | `.properties`, conferência do login |
| Nome da empresa | "Que nome de empresa aparece na App Store?" | Novo app, só no primeiro app do time |
| Chave da API já existe? | "O time já tem uma chave da App Store Connect API e um certificado Apple Distribution para CI, com os arquivos guardados?" | pular ou fazer os passos de chave e certificado |
| Nível de acesso da chave | padrão **Administrador**; confirme | Gerar chave |
| Repositório no GitHub | lido do `git remote get-url origin`; confirme | `make mobile-ios-secrets` |
| Pasta segura dos arquivos | "Em que pasta, fora do repositório, ficam o `.p8` e o `.p12`?" | `openssl`, bloco de `export` |

## Do ambiente (um conjunto por ambiente)

| Dado | Pergunta | Exemplo (Dev) |
|---|---|---|
| Ambiente | "Qual ambiente montar agora: Dev, Prod ou os dois?" (sugira Dev) | Dev |
| Nome do app | "Que nome aparece no ícone e na App Store?" | Meu App Dev |
| Bundle ID | "Qual o bundle do app deste ambiente?" (sugira `<bundle do app.json>.dev` para Dev) | com.exemplo.app.dev |
| SKU | sugira o slug do nome; confirme | meu-app-dev |
| Idioma principal | "Idioma principal na App Store?" | Português (Brasil) |
| Acesso de usuário | "Acesso total ou limitado ao app no App Store Connect?" | Acesso total |
| Endereços públicos | para cada `EXPO_PUBLIC_*` que o app lê: "Qual o valor em <ambiente>?" | https://api.dev.exemplo.com |
| Environment do GitHub | sugira `<slug-do-app>-<env>` | meu-app-dev |
| Branch padrão | lida do `git symbolic-ref refs/remotes/origin/HEAD`; confirme | main |
| Grupo de testes | "Nome do grupo de testers internos?" | Equipe |
| Testers | "Quem testa? Nome, e-mail e função de cada um." | — |

## A spec que a skill grava

Quando os dados vieram da entrevista, grave
`docs/superpowers/specs/AAAA-MM-DD-testflight-ios-<env>-design.md` com:

```markdown
# TestFlight iOS — <env> (<nome do app>)

## Time
- Team ID: …
- Empresa: …
- Chave da API e certificado: <criados nesta fatia | reaproveitados>
- Repositório: …

## Ambiente
- Nome: … · Bundle: … · SKU: … · Idioma: … · Acesso de usuário: …
- Disparo: <manual de branch, menos <branch padrão> | tag v<versão> na <branch padrão>>
- Environment do GitHub: …
- Endereços: <EXPO_PUBLIC_X>: …
- Grupo de testes: … · Testers: <nome, e-mail, função>

## Pendências
- <convite não aceito, contrato por aceitar, PR por mergear…>
```

Nenhum segredo entra nesse arquivo. E-mails de testers entram só se a pessoa
concordar; senão, registre só os nomes.
