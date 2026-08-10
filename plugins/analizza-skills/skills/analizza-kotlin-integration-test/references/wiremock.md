# WireMock no BaseIntegrationTest

Bloco para adicionar ao `BaseIntegrationTest` quando o projeto depender de HTTP externo e precisar
de mock nos testes de integracao. Aplicar apenas se o usuario confirmar.

## Dependencia (build.gradle.kts do modulo de integracao)

```kotlin
testImplementation("org.wiremock:wiremock-standalone:3.9.1")
```

## BaseIntegrationTest

Adicionar os imports necessarios e os blocos abaixo:

```kotlin
import com.github.tomakehurst.wiremock.WireMockServer
import com.github.tomakehurst.wiremock.core.WireMockConfiguration.options
import org.junit.jupiter.api.BeforeEach

abstract class BaseIntegrationTest {

    @BeforeEach
    fun resetWireMock() {
        wireMockServer.resetAll()
    }

    companion object {
        val wireMockServer: WireMockServer = WireMockServer(options().dynamicPort())
            .also { it.start() }

        @JvmStatic
        @DynamicPropertySource
        fun overrideProperties(registry: DynamicPropertyRegistry) {
            // Ajustar a chave para a propriedade real de base URL do cliente HTTP do projeto.
            registry.add("<client.base-url>") { "http://localhost:${wireMockServer.port()}" }
        }
    }
}
```

> Usar porta dinamica (`dynamicPort()`) para evitar conflitos em execucao paralela e `resetAll()` em
> `@BeforeEach` para isolar os testes. Ao mesclar com outros blocos `companion object` /
> `@DynamicPropertySource`, unificar as chaves em um unico metodo `overrideProperties`.
