# Onde gravar as convenções de arquitetura

Esta skill não gera código de domínio. A arquitetura-alvo é registrada como
**instrução**, no arquivo canônico do framework de Spec-Driven Development que o
projeto já usa. Quem for implementar a primeira fatia lê de lá.

O conteúdo a gravar é o
[architecture-conventions.md.template](../templates/architecture-conventions.md.template),
com os placeholders substituídos.

## Detecção

Verifique nesta ordem e **pare no primeiro que casar**. A ordem importa: um repo
pode ter mais de um sinal, e o primeiro da lista é o mais específico.

| Sinal no repo | Destino |
|---|---|
| diretório `openspec/` | `openspec/PROJECT.md` + resumo na chave `context:` do `openspec/config.yaml` |
| diretório `specs/` ou `.specify/` | `specs/CONSTITUTION.md` |
| diretório `docs/superpowers/` | `docs/superpowers/INSTRUCTIONS.md` |
| nenhum | pergunte ao usuário qual usar; se ele não quiser nenhum, `docs/ARCHITECTURE.md` |

```bash
if   [ -d openspec ];        then echo openspec
elif [ -d specs ] || [ -d .specify ]; then echo speckit
elif [ -d docs/superpowers ]; then echo superpowers
else echo nenhum; fi
```

## Regra que vale para todos

**Se o arquivo de destino já existe, acrescente uma seção. Nunca sobrescreva.**
Esses arquivos costumam ter conteúdo escrito à mão que não está em lugar nenhum.

Use um título de seção fixo, `## Arquitetura`, para que uma segunda execução da
skill consiga encontrar e substituir a própria seção em vez de duplicá-la:

```bash
grep -q '^## Arquitetura' "$destino" \
  && echo "seção já existe — substitua o conteúdo dela" \
  || echo "seção nova — acrescente no fim"
```

## OpenSpec

As convenções vão inteiras para `openspec/PROJECT.md`, sob `## Arquitetura`.

O `openspec/config.yaml` recebe apenas um resumo de duas ou três linhas na chave
`context:`, apontando para o PROJECT.md. Esse `context` é injetado em todo
artefato que o OpenSpec gera, então ele precisa ser curto — o documento inteiro
ali dentro polui todo prompt do projeto.

O arquivo padrão traz o `context:` comentado. Descomente e preencha:

```yaml
context: |
  Monorepo de quatro módulos: {project-name}-api (controllers Spring Boot),
  {project-name}-core (Clean Architecture + CQRS), {project-name}-web (Next.js)
  e {project-name}-mobile (Expo). Convenções completas em openspec/PROJECT.md.
```

Preserve o resto do arquivo, incluindo os comentários de exemplo do bloco
`rules:`.

## Speckit

`specs/CONSTITUTION.md`, sob `## Arquitetura`. Se o arquivo não existir, crie-o
com um título `# Constituição do projeto` antes da seção.

## Superpowers

`docs/superpowers/INSTRUCTIONS.md`, sob `## Arquitetura`. Se não existir, crie
com o título `# Instruções do projeto`.

Não confunda com `docs/superpowers/specs/` e `docs/superpowers/plans/`, que
guardam artefatos datados de trabalhos específicos. O `INSTRUCTIONS.md` é
permanente e vale para o projeto inteiro.

## Nenhum framework

Pergunte. Se o usuário escolher um, crie a estrutura mínima dele e siga a regra
correspondente. Se recusar, grave em `docs/ARCHITECTURE.md` e diga no relatório
final onde ficou — senão a convenção some.
