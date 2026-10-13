"""Projetos de mentira para os testes: cada um e um mapa de caminho para conteudo."""
from pathlib import Path


def write(root, files):
    for path, content in files.items():
        target = Path(root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


KOTLIN_OPENSPEC = {
    "build.gradle.kts": 'plugins { id("org.springframework.boot") version "4.0.0" }\n',
    "README.md": "# App\n",
    "openspec/specs/contas/spec.md": "# Contas\n",
    "openspec/changes/login/proposal.md": "# Login\n",
    "src/main/kotlin/app/presenter/routes/AccountRoute.kt": "@RestController\nclass AccountRoute\n",
    "src/main/kotlin/app/presenter/routes/LoginRoute.kt": '@RestController\nclass LoginRoute { @PostMapping("/login") fun login() {} }\n',
    "src/main/kotlin/app/application/CreateAccountHandler.kt": "class CreateAccountHandler\n",
    "src/main/kotlin/app/application/CloseAccountHandler.kt": "class CloseAccountHandler\n",
    "src/main/kotlin/app/application/LoginHandler.kt": "class LoginHandler\n",
    "src/main/kotlin/app/domain/Account.kt": "class Account\n",
    "src/main/kotlin/app/domain/rules/AccountMustBeOpen.kt": "class AccountMustBeOpen\n",
    "src/main/resources/db/migration/V1__init.sql": "create table account();\n",
    # Teste e pasta de build nao contam: nem como rota, nem como codigo.
    "src/test/kotlin/app/application/CreateAccountHandlerTest.kt": "@RestController class Fake\n",
    "build/classes/Ignored.kt": "@RestController class Ignored\n",
}

NEXT_SEM_SPECS = {
    "package.json": '{"dependencies": {"next": "16.0.0", "react": "19.0.0"}}\n',
    "docs/notas.md": "# Notas\n",
    "src/app/api/chat/route.ts": "export async function POST() {}\n",
    "src/app/page.tsx": "export default function Page() { return null }\n",
    "src/lib/chat-failures.ts": "export const x = 1\n",
    "src/lib/chat-failures.test.ts": "import { x } from './chat-failures'\n",
    "node_modules/next/index.js": "module.exports = {}\n",
}

MONOREPO = {
    "backend/build.gradle.kts": 'dependencies { implementation("org.springframework.boot:spring-boot-starter-web") }\n',
    "backend/src/main/kotlin/app/Application.kt": "class Application\n",
    "web/package.json": '{"dependencies": {"next": "16.0.0"}}\n',
    "web/src/app/page.tsx": "export default function Page() { return null }\n",
}

PYTHON_E_GO = {
    "README.md": "# App\n",
    "app/services/billing.py": "def charge(): pass\n",
    "main.go": "package main\n",
    "tests/test_billing.py": "def test_charge(): pass\n",
}

# Pastas com nome de camada que nao sao a camada: rota e caso de uso de um recurso chamado "model".
KOTLIN_COM_RECURSO_MODEL = {
    "build.gradle.kts": 'plugins { id("org.springframework.boot") version "4.0.0" }\n',
    "src/main/kotlin/app/presenter/routes/HealthRoute.kt": "@RestController\nclass HealthRoute\n",
    "src/main/kotlin/app/presenter/routes/models/ModelRoute.kt": "@RestController\nclass ModelRoute\n",
    "src/main/kotlin/app/application/models/CreateLlmModel.kt": "class CreateLlmModel\n",
    "src/main/kotlin/app/domain/models/LlmModel.kt": "class LlmModel\n",
    "src/main/kotlin/app/domain/rules/ModelMustBeValid.kt": "class ModelMustBeValid\n",
}

NEXT_COM_RECURSO_MODEL = {
    "web/package.json": '{"dependencies": {"next": "16.0.0"}}\n',
    "web/src/app/api/llm/providers/[id]/models/route.ts": "export async function GET() {}\n",
    "web/src/app/painel/models/page.tsx": "export default function Page() { return null }\n",
    "web/src/app/painel/models/helpers.ts": "export const x = 1\n",
    "web/src/telas/[id]/services/load.ts": "export const y = 1\n",
    "web/src/lib/models/llm.ts": "export type Llm = {}\n",
}

# Arquivo de rota na raiz do codigo, com as camadas abaixo dele.
KTOR_PLANO = {
    "build.gradle.kts": 'dependencies { implementation("io.ktor:ktor-server-core") }\n',
    "src/main/kotlin/Application.kt": "fun Application.module() { routing { } }\n",
    "src/main/kotlin/application/CreateAccount.kt": "class CreateAccount\n",
    "src/main/kotlin/domain/Account.kt": "class Account\n",
    "src/main/kotlin/models/AccountRow.kt": "class AccountRow\n",
}

SPRING_COM_ROTA_NO_PACOTE_BASE = {
    "build.gradle.kts": 'plugins { id("org.springframework.boot") version "4.0.0" }\n',
    "src/main/kotlin/com/acme/HealthController.kt": "@RestController\nclass HealthController\n",
    "src/main/kotlin/com/acme/domain/Account.kt": "class Account\n",
    "src/main/kotlin/com/acme/service/AccountService.kt": "class AccountService\n",
    "src/main/kotlin/com/acme/domain/rules/AccountMustBeOpen.kt": "class AccountMustBeOpen\n",
}
