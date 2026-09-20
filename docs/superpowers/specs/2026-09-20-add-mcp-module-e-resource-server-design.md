# `analizza-add-mcp-module` e o resource server como mecanismo — design

> Quatro entregas, 1 PR cada, em dois repositórios: `analizza-marketplace`
> (entregas 1 e 3) e `analizza-auction` (2 e 4).

## Contexto

O `documents-eaf-system` acabou de receber um servidor MCP servido por
Streamable HTTP em `/mcp`, no mesmo processo do `-api`, com as tools chamando
`QueryHandler` direto (spec `2026-09-19-mcp-transporte-http-design.md` daquele
repositório). Rodou em stage e foi verificado ponta a ponta com cliente MCP
real. É a implementação de referência desta skill.

Só que a referência é **uma** forma num **um** projeto: Kotlin, Gradle Groovy,
Spring Security com resource server OAuth2. Transformar isso em skill exige
saber o que é genérico e o que era daquele projeto. A comparação com o
`analizza-auction` — Java, Gradle Groovy, Spring Boot 4.1.0, Java 25, com
autenticação por filtro próprio e `jjwt` — já mostrou que parte do que parecia
genérico não era:

- o `CurrentMcpUser` da referência lê `authentication.principal as? Jwt`. No
  auction o principal é uma `String` (`new UsernamePasswordAuthenticationToken(userId, null, List.of())`),
  então esse código devolveria `null` e **toda** chamada morreria como "não
  autenticado";
- as authorities do auction chegam vazias (`List.of()`), então qualquer
  checagem de papel negaria tudo.

Uma skill escrita só a partir da referência entregaria, no projeto nº 2, algo
que não funciona. Daí testar a skill aplicando-a de verdade fazer parte desta
spec, e não ser um passo posterior.

## Objetivo

Uma skill `analizza-add-mcp-module` que acrescenta um servidor MCP a um projeto
Spring Boot em camadas já existente — Java ou Kotlin, Gradle Groovy ou Kotlin
DSL —, e a prova aplicando-a ao `analizza-auction`. No caminho, estreitar a
convenção de autenticação das skills e alinhar o auction a ela.

## Fora do escopo

- **Módulo com processo/pod próprio.** Continua o débito registrado na spec do
  `documents-eaf-system`; aqui o módulo é de biblioteca, mesmo processo.
- **Token de vida longa/revogável (PAT).** Mesma fatia futura de lá.
- **Gerar tools a partir do domínio.** A skill entrega uma tool de exemplo; as
  demais são escritas por quem conhece o domínio (ver D3).
- **A `analizza-new-project` passar a escrever código de segurança.** A
  fronteira dela — "a skill entrega a forma" — fica como está (ver D10).
- **Taxonomia de papéis do auction.** A entrega 2 leva o encanamento, não a
  decisão de produto (ver D12).

## Decisões

**D1 — O MCP entra como módulo Gradle de biblioteca, no mesmo processo.**
`{base}-mcp` aplica o plugin do Spring sem `bootJar`, não tem `main()` próprio,
e o `-api` ganha `implementation project(':{base}-mcp')`. Os beans entram no
mesmo contexto e o `/mcp` é servido pelo mesmo Tomcat. Descartados: pasta
dentro do `-api` (é o que a referência faz, mas então a skill não acrescenta
módulo nenhum e o nome mente) e módulo com pod próprio (exige Dockerfile,
manifest e pipeline, nada disso provado).

**D2 — `{base}-mcp` nunca depende do `-api`, e seu pacote fica sob o pacote
base da aplicação.** A dependência é só com o `-core`. Se uma tool precisar de
algo que hoje mora no `-api` — foi o caso do `ActorResolver` na referência —,
esse algo desce para o `-core`; o módulo não sobe. Por isso a tool de exemplo é
leitura pura, sem escrita de auditoria: não arrasta essa dependência na
primeira fatia. O pacote sob o pacote base (`br.com.ralvin.analizzaauction.mcp`)
faz o component scan do `@SpringBootApplication` alcançar as `@McpTool` sem
`@ComponentScan` extra.

**D3 — A skill gera a infraestrutura e UMA tool de exemplo, não uma tool por
handler.** Genérico é o encanamento: módulo, dependências, configuração
`STREAMABLE`/`SYNC`, a ponte de autenticação, o envelope de erro, a regra
ArchUnit, o IT com cliente MCP real e o runbook. A tool de exemplo sai de um
caso de uso de leitura que a skill pergunta qual é, e serve de modelo
compilável — e de alvo para o IT, que precisa de algo a chamar. Descartada a
introspecção automática (uma `@McpTool` por `QueryHandler` encontrado): cada
tool exposta é uma decisão de exposição de dado, e foi exatamente isso que
quase vazou um SAS de leitura de 3 anos na referência. Script não decide isso.

**D4 — A ponte de autenticação usa a `Authentication`, nunca o `Jwt`.**
`getName()` para identidade e `getAuthorities()` para papel. `getName()`
devolve o `sub` no resource server e o `userId` no filtro escrito à mão — as
duas formas que existem hoje nos projetos. Isso amarra a skill à **forma** que
a convenção de arquitetura fixa ("o `-api` é um resource server stateless") e
não ao **mecanismo** que ela deixa aberto de propósito.

**D5 — Autorização: detectar, perguntar, e dizer quando não há barreira.** A
skill procura modelo de papel no projeto (`hasRole`/`hasAnyRole`,
`GrantedAuthority` populada). Achou: pergunta quais papéis a tool exige e gera
a checagem. Não achou: gera só "precisa estar autenticado" e **relata** que não
há barreira de papel, em vez de fingir que há. Nunca gera checagem de papel num
projeto de authorities vazias — ela negaria tudo.

**D6 — Exposição de dado não é decidida pela skill.** Ela não conhece o
domínio. Gera o envelope de erro (mensagem genérica segura ao modelo e log da
exceção real no servidor, com `catch` específicos por conta do projeto) e
obriga a decisão no runbook, numa seção que manda conferir campo a campo o que
o Result carrega antes de liberar a tool.

**D7 — A skill confere que `/mcp` cai numa regra autenticada.** Lê o
`SecurityConfig` do projeto. Num projeto com `anyRequest().permitAll()`, ou sem
Spring Security, o endpoint nasceria aberto — nesse caso ela para e avisa, em
vez de gerar um MCP público em silêncio. Na referência isso veio de graça
(`anyRequest().authenticated()`), e é justamente o tipo de coisa que só aparece
quando a skill roda em outro projeto.

**D8 — A verificação usa um cliente MCP real, não chamada de método.** O
`McpEndpointIT` gerado fala o protocolo por HTTP com
`io.modelcontextprotocol.sdk:mcp-core`. Foi o único teste capaz de provar, na
referência, que o `SecurityContextHolder` sobrevive ao dispatch do Spring AI
até dentro do método `@McpTool` — um teste que chama a tool como método Kotlin
e popula o contexto à mão prova a lógica e nada sobre o transporte. Exige
quatro coisas: `initialize` responde; a tool devolve dado real de uma linha
semeada; chamada sem `Authorization` é recusada antes de a tool rodar; e, com
modelo de papel, token sem o papel volta `isError`.

**D9 — A regra ArchUnit passa a cobrir `@McpTool`, além de `@Tool`.** A regra
hoje na `main` guarda só `org.springframework.ai.tool.annotation.Tool`
(estilo tool-calling, exposto por `ToolCallbackProvider`). O scanner de
anotações do servidor MCP — o caminho que a referência usa e que esta skill
gera — é `org.springframework.ai.mcp.annotation.McpTool`. Sem as duas, um
projeto que siga a skill fica com um guardrail que nunca dispara para as tools
dele. Comparação por nome, como já se faz com `@KafkaListener`, para a regra
compilar sem `spring-ai` no classpath.

**D10 — A convenção estreita o mecanismo da validação, não o do login.** A
seção *Autenticação e autorização* do template da `analizza-new-project` passa
a fixar: a validação da credencial que chega é resource server OAuth2 do Spring
Security, com `JwtDecoder`. Continua aberto, como já está hoje, qual credencial
o usuário apresenta no login (senha, código, OAuth, certificado) — isso é
decisão de produto. A skill continua **não escrevendo** código de segurança: a
fronteira "a skill entrega a forma" fica intacta; o que muda é o que a forma
diz.

**D11 — A migração do auction preserva o formato do token.** O
`JwtTokenService` assina HS256 com `jjwt`; o `NimbusJwtDecoder` valida HS256
com a mesma chave. Então sai o `JwtAuthenticationFilter` escrito à mão e entra
a configuração do resource server, sem trocar o formato do token nem mexer no
login do `-web`. Token já emitido continua valendo. Trocar o formato exigiria
deploy coordenado de front e back — outra categoria de risco, evitada de
propósito.

**D12 — Papéis no auction: só o encanamento.** A configuração passa a ler uma
claim `roles` e mapeá-la para authorities `ROLE_*`; sem a claim, fica vazio
como hoje e nada quebra. Qual taxonomia de papéis o domínio de leilão precisa é
decisão de produto, e não se decide de carona numa fatia de MCP.

## As quatro entregas

**Entrega 1 — Estreitar a convenção** (`analizza-marketplace`). Edita a seção
*Autenticação e autorização* de `architecture-conventions.md.template` conforme
D10. Poucas linhas, sem código.

**Entrega 2 — Migrar o `analizza-auction` para resource server** (`analizza-auction`).
Sai `JwtAuthenticationFilter`; entra `spring-boot-starter-oauth2-resource-server`
com `NimbusJwtDecoder` HS256 sobre a mesma chave (D11) e o mapeamento de
`roles` para authorities (D12). O `JwtTokenService` (emissão) continua
funcionando. A rede desta entrega são os ITs de autenticação que já existem —
têm de continuar verdes **sem mudar de expectativa**, porque o comportamento
observável não muda — e o `McpEndpointIT` que a entrega 4 já deixou no
projeto, que quebra se a troca do mecanismo derrubar a ponte de D4.

**Entrega 3 — A skill `analizza-add-mcp-module`** (`analizza-marketplace`).
Estrutura irmã da `analizza-integration-test`: `SKILL.md` com *Vocabulário* e
*Procedimento* em passos, `references/` para os blocos que entram na
documentação do projeto, `templates/` por linguagem (`java`/`kotlin`) e por DSL
(`groovy`/`kts`). Inclui D9 (estender a regra ArchUnit). Argumentos em
português, como as irmãs: `linguagem=`, `modulo=`, `papeis=`.

**Entrega 4 — Aplicar no `analizza-auction`** (`analizza-auction`). Roda a
skill de verdade, com a verificação de D8 passando, e registra no relatório o
que ela detectou e o que não conseguiu verificar. É o teste da skill; um
problema encontrado aqui volta como correção na entrega 3.

A ordem é **1 → 3 → 4 → 2**, com as duas últimas invertidas de propósito.
Aplicar a skill (4) enquanto o auction ainda usa o filtro escrito à mão prova a
ponte de D4 no sabor que a motivou — `UsernamePasswordAuthenticationToken` com
principal `String`. Aplicá-la depois da migração testaria contra
`JwtAuthenticationToken`, o mesmo sabor da referência, que já está provado: o
caso fácil. E deixar a migração por último a entrega guardada — o
`McpEndpointIT` gerado na entrega 4 já está no lugar e quebra se a troca do
mecanismo mexer no contexto de segurança de um jeito que derrube as tools. A
entrega 3 não depende da 1: se a convenção atrasar, pode ser puxada para
frente.

## O que esta fatia deixa sem cobrir

- **O ramo "projeto COM modelo de papel" (D5) não roda em projeto real nesta
  fatia.** O auction não tem papéis antes da migração, e D12 leva só o
  encanamento — a claim `roles` continua sem quem a emita —, então também não
  tem depois dela. A entrega 4 exercita o ramo pobre; o rico fica coberto pelos
  testes da própria skill e pela referência, que tem `INTERNAL`/`ADMIN`.
  Aplicar a skill duas vezes no auction foi considerado e descartado: sem
  papéis em nenhum dos dois momentos, a segunda aplicação não provaria nada
  que a primeira já não prove.
- **Kotlin DSL (`.kts`) não é exercitado em projeto real.** Os dois projetos
  desta fatia usam Groovy. Os templates `.kts` saem da entrega 3 sem nunca
  terem rodado num build de verdade.
- **Nenhum dos dois projetos exercita a parada de D7** (projeto sem Spring
  Security, ou com `/mcp` aberto), porque os dois têm segurança configurada.
