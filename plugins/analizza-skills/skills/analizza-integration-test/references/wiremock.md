# WireMock no `BaseIntegrationTest`

Só quando o projeto depende de HTTP externo e o usuário confirmar. Um servidor
para a suíte inteira, na mesma forma do container de banco: campo estático,
iniciado na mão, porta dinâmica e `resetAll()` antes de cada teste.

## Dependência

```kotlin
testImplementation("org.wiremock:wiremock-standalone:3.13.1")   // build.gradle.kts
```

```groovy
testImplementation 'org.wiremock:wiremock-standalone:3.13.1'    // build.gradle
```

## Kotlin

```kotlin
import com.github.tomakehurst.wiremock.WireMockServer
import com.github.tomakehurst.wiremock.core.WireMockConfiguration.options
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource

// dentro do BaseIntegrationTest
@BeforeEach
fun limparWireMock() {
    wireMock.resetAll()
}

companion object {
    @JvmStatic
    val wireMock: WireMockServer = WireMockServer(options().dynamicPort()).also { it.start() }

    @JvmStatic
    @DynamicPropertySource
    fun propriedadesDoHttpExterno(registry: DynamicPropertyRegistry) {
        // Troque pela propriedade real da URL base do cliente HTTP.
        registry.add("<cliente.base-url>") { "http://localhost:${wireMock.port()}" }
    }
}
```

## Java

```java
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.options;

import com.github.tomakehurst.wiremock.WireMockServer;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

// dentro do BaseIntegrationTest
protected static final WireMockServer WIRE_MOCK = new WireMockServer(options().dynamicPort());

static {
    WIRE_MOCK.start();
}

@BeforeEach
void limparWireMock() {
    WIRE_MOCK.resetAll();
}

@DynamicPropertySource
static void propriedadesDoHttpExterno(DynamicPropertyRegistry registry) {
    // Troque pela propriedade real da URL base do cliente HTTP.
    registry.add("<cliente.base-url>", () -> "http://localhost:" + WIRE_MOCK.port());
}
```

Um `companion object`/bloco `static` só por classe: mescle com o do container
de banco em vez de declarar um segundo.
