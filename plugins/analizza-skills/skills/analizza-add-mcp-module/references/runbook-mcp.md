---
type: api
---

# Servidor MCP de {base}

As tools do `{base}-mcp` chamam os handlers de leitura direto, no mesmo
processo do `{api-module}`, e a identidade de quem chamou vem do
`Authorization` que chega em `/mcp`.

Pré-requisito: a aplicação rodando e um token válido.

## 1. O que precisa bater

Registre um servidor MCP HTTP apontando para `http://localhost:8080/mcp` com o
cabeçalho `Authorization: Bearer <token>`. Numa conversa nova, peça algo que
force a tool `{tool-name}`. Confira:

- a IA mostra que chamou `{tool-name}` antes de responder
- a resposta cita dado real do sistema, não algo inventado

## 2. O que tentar para ver se quebra

- **Token errado.** Troque o token por qualquer string. Esperado: recusa de
  autenticação antes de a tool rodar — nunca stack trace, nunca dado.
- **Sem o cabeçalho.** Remova o `Authorization`. Mesmo resultado.
- **Papel sem acesso** (se a tool exigir papel): token de alguém sem o papel.
  Esperado: a tool recusa com a mensagem de papel insuficiente, sem devolver
  dado nenhum.

## 3. O que não está na lista

**Confira campo a campo o que a tool devolveu.** É aqui que se decide o que um
modelo de IA pode ver, e nenhuma automação decide isso por você. Procure em
especial: URLs assinadas, tokens, caminhos internos, dados pessoais que a tela
equivalente não mostra, e qualquer campo que exista "porque o Result já
tinha". Na implementação de referência, um campo `url` com link assinado de 3
anos só não foi parar no modelo porque uma pessoa reparou nele nesta seção.

Estranhe também resposta da IA citando dado sem ter chamado tool nenhuma.

## 4. O que este checkpoint já pegou

(preencher depois de rodar, com data e achado real)
