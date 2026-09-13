# Container de banco por banco escolhido

Valores que substituem os placeholders do `BaseIntegrationTest` e o
`{testcontainers-db-module}` do build. Todos os artefatos são gerenciados pelo
BOM do Spring Boot: nenhum leva versão.

| Banco | `{testcontainers-db-module}` | `{container-import}` | `{container-type}` |
|---|---|---|---|
| `postgres` | `org.testcontainers:testcontainers-postgresql` | `org.testcontainers.postgresql.PostgreSQLContainer` | `PostgreSQLContainer` |
| `oracle` | `org.testcontainers:testcontainers-oracle-free` | `org.testcontainers.oracle.OracleContainer` | `OracleContainer` |
| `mysql` | `org.testcontainers:testcontainers-mysql` | `org.testcontainers.mysql.MySQLContainer` | `MySQLContainer` |

## `{container-new}`

| Banco | Kotlin | Java |
|---|---|---|
| `postgres` | `PostgreSQLContainer("{image}")` | `new PostgreSQLContainer("{image}")` |
| `oracle` | `OracleContainer("{image}").withStartupTimeout(java.time.Duration.ofMinutes(6))` | `new OracleContainer("{image}").withStartupTimeout(java.time.Duration.ofMinutes(6))` |
| `mysql` | `MySQLContainer("{image}")` | `new MySQLContainer("{image}")` |

A primeira subida real da imagem do Oracle rotineiramente passa dos 60s que a
biblioteca espera por padrão, e o timeout do comando Gradle não estende a
espera própria do container — por isso `{container-new}` de `oracle` já leva
`.withStartupTimeout(...)`, com `java.time.Duration` por extenso para
`{container-import}` continuar sendo um único import.

`{image}`: a mesma imagem e tag que o `docker-compose.yml` do projeto usa para
aquele banco, se ele tiver uma — o teste roda contra a versão que o
desenvolvedor usa. Sem `docker-compose`, o padrão:

| Banco | Imagem padrão |
|---|---|
| `postgres` | `postgres:17-alpine` |
| `oracle` | `gvenzl/oracle-free:23-slim-faststart` |
| `mysql` | `mysql:8.4` |

## Oracle com `Dockerfile` próprio

Só quando o projeto **já tem** um `Dockerfile` (e `init.sql`) de Oracle para
testes. Ele fica em `src/test/resources/oracle/` do módulo que recebe os ITs —
nunca em `src/main/resources/` — e é carregado pelo classpath, sem caminho
relativo:

```kotlin
// {container-import} ganha tambem:
//   org.testcontainers.images.builder.ImageFromDockerfile
//   org.testcontainers.utility.DockerImageName
//   java.time.Duration
OracleContainer(
    DockerImageName.parse(
        ImageFromDockerfile()
            .withFileFromClasspath("Dockerfile", "oracle/Dockerfile")
            .withFileFromClasspath("init.sql", "oracle/init.sql")
            .get(),
    ).asCompatibleSubstituteFor("gvenzl/oracle-free"),
).withStartupTimeout(Duration.ofMinutes(6))
```

```java
new OracleContainer(
        DockerImageName.parse(new ImageFromDockerfile()
                .withFileFromClasspath("Dockerfile", "oracle/Dockerfile")
                .withFileFromClasspath("init.sql", "oracle/init.sql")
                .get())
                .asCompatibleSubstituteFor("gvenzl/oracle-free"))
        .withStartupTimeout(Duration.ofMinutes(6))
```

Se o arquivo estiver em `src/main/resources/`, mova-o com `git mv` antes.

## Outro banco

A skill não adivinha módulo do Testcontainers. Diga ao usuário que o banco não
está nesta tabela, peça o módulo (`org.testcontainers:testcontainers-<banco>`)
e a classe do container, e só siga com os dois confirmados.

## Kafka, Redis e outros serviços

Não fazem parte desta skill. Para acrescentar um, siga a mesma forma do banco:
um campo estático no `BaseIntegrationTest`, iniciado na mão, com
`@ServiceConnection` quando o Spring Boot conhecer o serviço e
`@DynamicPropertySource` quando não conhecer.
