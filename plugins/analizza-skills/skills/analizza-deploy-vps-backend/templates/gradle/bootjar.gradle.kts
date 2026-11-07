
// Nome fixo do jar executavel: o Dockerfile copia este arquivo. A versao
// (gradle.properties) vai no manifesto, nao no nome.
tasks.named<org.springframework.boot.gradle.tasks.bundling.BootJar>("bootJar") {
    archiveFileName.set("${project.name}.jar")
    manifest {
        attributes("Implementation-Version" to project.version)
    }
}
