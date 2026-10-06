---
name: analizza-new-agent
description: >-
  Cria um agente conversacional de IA em Spring Boot (Java ou Kotlin): do zero,
  como monorepo sem -core, com {project-name}-agent carregando presenter,
  application, domain e infrastructure num módulo só, mais buildingBlocks e,
  se pedido, {project-name}-web com tela de chat, Postgres e memória de
  conversa; ou acrescentando o módulo {base}-agent, como aplicação própria, a
  um projeto Gradle multi-módulo existente. Entrega endpoint de chat (JSON e
  SSE), LLM OpenAI-compatível via LangChain4j atrás de uma interface, cliente
  MCP preguiçoso, observabilidade (OpenTelemetry, LangWatch local,
  Prometheus) e testes com Ollama em Testcontainers. Use quando o usuário
  pedir "novo agente", "criar agent", "agente de IA", "adicionar módulo
  agent", "chat com LLM", "agente com MCP" ou invocar /analizza-new-agent.
  Para monorepo com -api e -core sem agente, use analizza-new-project.
argument-hint: "Sem argumentos — o modo (do zero ou projeto existente) é detectado; linguagem, módulo, web, Postgres, memória e servidor MCP são perguntados com defaults"
---

# Novo agente conversacional

Procedimento em construção — ver o plano
`docs/superpowers/plans/2026-10-06-analizza-new-agent-skill.md`.
