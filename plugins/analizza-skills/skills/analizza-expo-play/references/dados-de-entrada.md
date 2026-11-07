# Dados de entrada

O que a skill precisa saber antes de gerar arquivos ou abrir o Play Console.
Procure primeiro na spec do projeto (`docs/superpowers/specs/`), nos
`.properties` de `.github/apps/` e no `app.json`. O que faltar vira **uma
pergunta só**, no começo, com todos os itens juntos.

Nunca peça nem aceite na conversa: senha, código de dois fatores, senha do
keystore, conteúdo do `.jks` ou do JSON da service account.

## Da conta (valem para todos os apps da empresa)

| Dado | Pergunta | Onde se usa |
|---|---|---|
| Conta do Play Console | "Qual conta Google é dona da conta de desenvolvedor do Play (já paga)?" | login, conferência do papel |
| Tipo da conta | lido na home do Play Console ("Conta pessoal" ou organização) | aviso de produção para conta pessoal |
| Service account já existe? | "Já existe uma service account de CI para este projeto, com a chave guardada? Ou criamos uma nova?" (sugira uma nova por produto; nunca reaproveite a de outro produto) | blocos `primeira-service-account` / `reaproveita-service-account` |
| Projeto do Google Cloud | lido do console; sugira um que já tenha a API ativa | criação da service account |
| Repositório no GitHub | lido do `git remote get-url origin`; confirme | `make mobile-android-secrets` |
| Pasta segura | "Em que pasta, fora de qualquer repositório, ficam o keystore e o JSON?" (sugira `~/<empresa>-segredos`) | keytool, chave JSON, script dos secrets |

## Do ambiente (um conjunto por ambiente)

| Dado | Pergunta | Exemplo (Dev) |
|---|---|---|
| Ambiente | "Qual ambiente montar agora: Dev, Prod ou os dois?" (sugira Dev) | Dev |
| Nome do app | "Que nome aparece no ícone e no Play?" | Meu App Dev |
| Pacote | "Qual o pacote do app deste ambiente?" (sugira o do iOS do mesmo ambiente, se houver; senão `<pacote do app.json>.dev`) | com.exemplo.app.dev |
| Alias da upload key | sugira `<slug-do-app>-<env>-upload` | meu-app-dev-upload |
| Endereços públicos | para cada `EXPO_PUBLIC_*` que o app lê: "Qual o valor em <ambiente>?" (copie do `.properties` do iOS do mesmo ambiente, se houver) | https://api.dev.exemplo.com |
| Environment do GitHub | o mesmo do iOS do ambiente, se houver; senão `<slug-do-app>-<env>` | meu-app-dev |
| Branch padrão | lida do `git symbolic-ref refs/remotes/origin/HEAD`; confirme | main |
| Testers | "Quem testa? E-mails das contas Google." (no Play, confira se uma lista existente já serve) | — |

## A spec que a skill grava

Quando os dados vieram da entrevista, grave
`docs/superpowers/specs/AAAA-MM-DD-play-android-<env>-design.md` com:

```markdown
# Google Play Android — <env> (<nome do app>)

## Conta
- Play Console: <conta> (<pessoal | organização>)
- Service account: <e-mail> (<criada nesta fatia | reaproveitada>), projeto <id>
- Repositório: …

## Ambiente
- Nome: … · Pacote: … · Alias da upload key: …
- Disparo: <manual de qualquer branch, <branch padrão> inclusive, com gerar_tag só nela | tag v<versão> na <branch padrão>, por push ou à mão>
- Faixa: internal (promoção manual)
- Environment do GitHub: …
- Endereços: <EXPO_PUBLIC_X>: …
- Lista de testers: …

## Pendências
- <PR por mergear, primeiro lançamento em draft, tarefas do Painel…>
```

Nenhum segredo entra nesse arquivo. E-mails de testers só entram com o ok da
pessoa; sem ele, registre só o nome da lista.
