# WireMock no BaseIntegrationTest (Java)

Bloco para adicionar ao `BaseIntegrationTest` quando o projeto depender de HTTP externo e precisar
de mock nos testes de integracao. Aplicar apenas se o usuario confirmar.

## Dependencia (build.gradle do modulo de integracao)

```groovy
testImplementation 'org.wiremock:wiremock-standalone:3.9.1'
```

## BaseIntegrationTest

Adicionar os imports necessarios e os blocos abaixo:

```java
import com.github.tomakehurst.wiremock.WireMockServer;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.options;

public abstract class BaseIntegrationTest {

    protected static final WireMockServer WIRE_MOCK_SERVER = startWireMockServer();

    @BeforeEach
    void resetWireMock() {
        WIRE_MOCK_SERVER.resetAll();
    }

    @DynamicPropertySource
    static void overrideProperties(DynamicPropertyRegistry registry) {
        // Ajustar a chave para a propriedade real de base URL do cliente HTTP do projeto.
        registry.add("<client.base-url>", () -> "http://localhost:" + WIRE_MOCK_SERVER.port());
    }

    private static WireMockServer startWireMockServer() {
        WireMockServer server = new WireMockServer(options().dynamicPort());
        server.start();
        return server;
    }
}
```

> Usar porta dinamica (`dynamicPort()`) para evitar conflitos em execucao paralela e `resetAll()` em
> `@BeforeEach` para isolar os testes. Ao mesclar com outros blocos estaticos /
> `@DynamicPropertySource`, unificar as chaves em um unico metodo `overrideProperties` — o Spring
> aceita varios metodos `@DynamicPropertySource`, mas manter um so evita chaves duplicadas.
