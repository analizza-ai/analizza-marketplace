# A camada de LLM sobre o módulo de testes de integração

A `analizza-integration-test` entrega `{project-name}-integration-tests` com
`BaseIntegrationTest`, banco em container e a regra ArchUnit. Ela não sabe que
a aplicação depende de um LLM. Sem esta camada, o contexto do
`ApplicationContextIT` nem sobe: `LLM_BASE_URL`, `LLM_API_TOKEN` e `LLM_MODEL`
não têm default (de propósito).

## 1. Dependência do módulo de IT

No `build.gradle{dsl-ext}` de `{project-name}-integration-tests`, junto dos
outros módulos do Testcontainers:

```kotlin
    testImplementation("org.testcontainers:testcontainers-ollama")   // kts
```

```groovy
    testImplementation 'org.testcontainers:testcontainers-ollama'    // groovy
```

## 2. `OllamaTestContainer` e `ChatRouteIT`

Copie de `templates/source/{language}/it/` para o módulo de IT, pela regra de
espelhamento: `support/OllamaTestContainer` e
`presenter/routes/chat/ChatRouteIT`. **Não** copie o `support/BaseIntegrationTest`
do template — ele é do layout `it-no-modulo`; aqui a base é a que a
`analizza-integration-test` gerou.

## 3. Ligar o LLM na base que já existe

Em `support/BaseIntegrationTest`, acrescente o método abaixo ao lado do
container de banco, e os dois imports.

Kotlin — dentro do `companion object`:

```kotlin
        @JvmStatic
        @DynamicPropertySource
        fun llm(registry: DynamicPropertyRegistry) {
            OllamaTestContainer.registerLlm(registry, "{mcp-name}")
        }
```

Java — método estático da classe:

```java
    @DynamicPropertySource
    static void llm(DynamicPropertyRegistry registry) {
        OllamaTestContainer.registerLlm(registry, "{mcp-name}");
    }
```

Imports: `org.springframework.test.context.DynamicPropertyRegistry` e
`org.springframework.test.context.DynamicPropertySource`.

`{mcp-name}` nos dois trechos é placeholder: troque pelo nome do servidor MCP
do projeto (o mesmo prefixo do `application.yaml`, `tools-mcp` se nenhum foi
informado). É por ele que a base desliga o cliente MCP nos ITs.

## 4. Conferir

```bash
./gradlew :{project-name}-integration-tests:integrationTest --console=plain > /tmp/agent-it.log 2>&1; echo "EXIT=$?"
```

`EXIT=0`, com `ChatRouteIT`, `ApplicationContextIT` e
`EntrypointHasIntegrationTestIT` no XML de resultado. A regra ArchUnit passa
porque a `ChatRoute` — o único `@RestController` — tem o `ChatRouteIT`.

A primeira execução baixa a imagem do Ollama e o modelo (~2 GB) e grava a
imagem local `tc-ollama-<modelo>`; as seguintes sobem direto dela.
