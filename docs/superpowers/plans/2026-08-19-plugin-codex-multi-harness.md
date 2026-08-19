# Plugin Codex Multi-Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Disponibilizar o plugin `analizza-skills` (3 skills) para Codex sem duplicar o conteúdo distribuído ao Claude Code.

**Architecture:** A árvore `plugins/analizza-skills/skills/` continua canônica. Um manifesto Codex aponta para ela; o manifesto Claude é preservado. Um validador Python novo (este repositório não tem nenhuma infraestrutura Python hoje) verifica o contrato entre manifestos, incluindo que o número de `SKILL.md` bate com o número de pastas de skill, e é executado pelo Makefile e pytest.

**Tech Stack:** JSON, Markdown, GNU Make, Python 3 padrão e pytest.

**Spec:** docs/superpowers/specs/2026-08-19-plugin-codex-multi-harness-design.md

## Global Constraints

- A fonte de todas as skills é `plugins/analizza-skills/skills/`; não duplicar conteúdo nem usar links simbólicos.
- O manifesto Codex declara exatamente `"skills": "./skills/"`.
- `name` e `version` são iguais nos manifestos Claude e Codex (hoje `analizza-skills` / `0.2.1`).
- Não adicionar hooks, MCP servers, aplicações ou assets.
- Não alterar conteúdo ou comportamento das 3 skills existentes (`analizza-kotlin-integration-test`, `analizza-java-integration-test`, `analizza-new-project`).
- Não adicionar validação de catálogo de conhecimento — este plugin não tem catálogo de riscos; `tools/` contém apenas o validador de manifestos.

---

## File Structure

| Arquivo | Responsabilidade |
| --- | --- |
| `requirements-dev.txt` | Declara `pytest` como dependência de desenvolvimento. |
| `tools/__init__.py` | Torna `tools` um pacote Python importável pelos testes. |
| `tools/validate_plugin_manifests.py` | Validação independente do contrato entre os dois manifestos. |
| `tools/tests/__init__.py` | Torna `tools.tests` um pacote Python. |
| `tools/tests/test_validate_plugin_manifests.py` | Contrato do validador e integração com os manifestos e README reais. |
| `plugins/analizza-skills/.codex-plugin/plugin.json` | Descoberta Codex e referência à árvore canônica de skills. |
| `Makefile` | Executa o validador em `make validate`, roda a suíte em `make check`, e faz `make tag` depender de `validate`. |
| `README.md` | Instalação e publicação por harness. |

### Task 1: Validador do contrato multi-harness e suíte de testes

**Files:**

- Create: `requirements-dev.txt`
- Create: `tools/__init__.py`
- Create: `tools/tests/__init__.py`
- Create: `tools/validate_plugin_manifests.py`
- Create: `tools/tests/test_validate_plugin_manifests.py`
- Modify: `Makefile:36-42`

**Interfaces:**

- Consumes: os dois `plugin.json` em `plugins/analizza-skills/` (ainda não existe o Codex — criado na Task 2).
- Produces: `validar_manifestos(claude: dict, codex: dict, plugin_dir: Path) -> list[str]`, `carregar_manifesto(caminho: Path) -> Optional[dict]`, e um CLI (`main() -> int`) que outras tasks e o Makefile consomem.

- [ ] **Step 1: Declarar a dependência de teste**

Crie `requirements-dev.txt`:

~~~text
pytest
~~~

- [ ] **Step 2: Instalar a dependência**

Run: `pip3 install -r requirements-dev.txt`

Expected: instalação concluída sem erro (ou "Requirement already satisfied" se já estiver instalado).

- [ ] **Step 3: Criar os pacotes Python**

Crie `tools/__init__.py` e `tools/tests/__init__.py`, ambos vazios.

- [ ] **Step 4: Escrever os testes em vermelho**

Crie `tools/tests/test_validate_plugin_manifests.py`:

~~~python
import json
from pathlib import Path

from tools.validate_plugin_manifests import carregar_manifesto, validar_manifestos


def manifestos_validos():
    claude = {"name": "analizza-skills", "version": "0.2.1"}
    codex = {
        "name": "analizza-skills",
        "version": "0.2.1",
        "skills": "./skills/",
        "interface": {
            "displayName": "Analizza Skills",
            "shortDescription": "Scaffolding e qualidade para projetos Kotlin/Java + Spring Boot",
            "longDescription": "Cria monorepos do zero e configura testes de integração.",
            "developerName": "Diego Lirio",
            "category": "Developer Tools",
            "capabilities": ["Read", "Write"],
        },
    }
    return claude, codex


def criar_skills(tmp_path: Path, nomes: list[str]) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    for nome in nomes:
        pasta = skills_dir / nome
        pasta.mkdir()
        (pasta / "SKILL.md").write_text("# skill\n", encoding="utf-8")


def test_manifestos_compativeis_nao_produzem_erros(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b", "c"])
    claude, codex = manifestos_validos()
    assert validar_manifestos(claude, codex, tmp_path) == []


def test_versao_divergente_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["version"] = "0.3.0"
    assert "version diverge" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_caminho_de_skills_diferente_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["skills"] = "./codex-skills/"
    assert "skills deve ser './skills/'" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_diretorio_de_skills_ausente_e_reportado(tmp_path: Path):
    claude, codex = manifestos_validos()
    assert "diretório de skills não existe" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_interface_incompleta_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["interface"]["category"]
    assert "interface.category ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_skill_md_faltando_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b"])
    (tmp_path / "skills" / "c").mkdir()
    claude, codex = manifestos_validos()
    erros = "\n".join(validar_manifestos(claude, codex, tmp_path))
    assert "número de SKILL.md" in erros


def test_name_ausente_no_codex_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["name"]
    assert "codex: name ausente" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_version_ausente_no_codex_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["version"]
    assert "codex: version ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_manifesto_ausente_e_reportado(tmp_path: Path, capsys):
    caminho = tmp_path / "plugin.json"
    resultado = carregar_manifesto(caminho)
    assert resultado is None
    assert f"manifesto ausente ou inválido: {caminho}" in capsys.readouterr().out
~~~

- [ ] **Step 5: Executar os testes e confirmar a falha**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py -q`

Expected: FAIL durante coleta com `ModuleNotFoundError: No module named 'tools.validate_plugin_manifests'`.

- [ ] **Step 6: Implementar o validador**

Crie `tools/validate_plugin_manifests.py`:

~~~python
import json
import sys
from pathlib import Path
from typing import Optional


CAMPOS_INTERFACE_OBRIGATORIOS = (
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
)


def validar_manifestos(claude: dict, codex: dict, plugin_dir: Path) -> list[str]:
    erros = []

    if codex.get("name") is None:
        erros.append("codex: name ausente")
    elif claude.get("name") != codex.get("name"):
        erros.append("name diverge entre os manifestos")
    if codex.get("version") is None:
        erros.append("codex: version ausente")
    elif claude.get("version") != codex.get("version"):
        erros.append("version diverge entre os manifestos")
    if codex.get("skills") != "./skills/":
        erros.append("skills deve ser './skills/'")

    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        erros.append("diretório de skills não existe")
    else:
        subpastas = [p for p in skills_dir.iterdir() if p.is_dir()]
        skill_mds = list(skills_dir.glob("*/SKILL.md"))
        if len(skill_mds) != len(subpastas):
            erros.append(
                f"número de SKILL.md ({len(skill_mds)}) diverge do número de "
                f"pastas de skill ({len(subpastas)})"
            )

    interface = codex.get("interface", {})
    if not isinstance(interface, dict):
        interface = {}
    for campo in CAMPOS_INTERFACE_OBRIGATORIOS:
        if campo not in interface:
            erros.append(f"interface.{campo} ausente")

    return erros


def carregar_manifesto(caminho: Path) -> Optional[dict]:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"JSON inválido: {caminho}")
        return None
    except OSError:
        print(f"manifesto ausente ou inválido: {caminho}")
        return None


def main() -> int:
    raiz = Path(__file__).resolve().parent.parent
    plugin_dir = raiz / "plugins" / "analizza-skills"
    caminho_claude = plugin_dir / ".claude-plugin" / "plugin.json"
    caminho_codex = plugin_dir / ".codex-plugin" / "plugin.json"

    claude = carregar_manifesto(caminho_claude)
    codex = carregar_manifesto(caminho_codex)
    if claude is None or codex is None:
        return 1

    erros = validar_manifestos(claude, codex, plugin_dir)
    if erros:
        print("\n".join(erros))
        return 1

    print("manifestos multi-harness válidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
~~~

- [ ] **Step 7: Executar os testes unitários**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py -q`

Expected: PASS, 9 testes (o teste de integração com os manifestos reais e o teste do README ainda não foram adicionados — chegam nas Tasks 2 e 3).

- [ ] **Step 8: Integrar ao Makefile**

Modifique `Makefile:36-42` (seção `##@ Release`) de:

~~~make
.PHONY: validate
validate: ## Valida os manifestos do marketplace e do plugin
	claude plugin validate . && claude plugin validate $(PLUGIN_DIR)

.PHONY: tag
tag: ## Cria a tag {plugin}--v{version} validando os manifestos
	claude plugin tag $(PLUGIN_DIR)
~~~

Para:

~~~make
.PHONY: validate
validate: ## Valida os manifestos do marketplace, Claude e Codex
	claude plugin validate . && claude plugin validate $(PLUGIN_DIR) && python3 tools/validate_plugin_manifests.py

.PHONY: tag
tag: validate ## Cria a tag {plugin}--v{version} validando os manifestos
	claude plugin tag $(PLUGIN_DIR)

##@ Qualidade

.PHONY: check
check: ## Roda a suíte de testes dos validadores
	python3 -m pytest tools/tests -q
~~~

- [ ] **Step 9: Rodar a suíte via Makefile**

Run: `make check`

Expected: PASS, 9 testes.

- [ ] **Step 10: Commit**

~~~bash
git add requirements-dev.txt tools/__init__.py tools/tests/__init__.py tools/validate_plugin_manifests.py tools/tests/test_validate_plugin_manifests.py Makefile
git commit -m "test: validate multi-harness plugin manifests"
~~~

### Task 2: Manifesto Codex para as skills canônicas

**Files:**

- Create: `plugins/analizza-skills/.codex-plugin/plugin.json`
- Modify: `tools/tests/test_validate_plugin_manifests.py`

**Interfaces:**

- Consumes: `validar_manifestos` da Task 1 e `plugins/analizza-skills/skills/` (3 pastas de skill já existentes).
- Produces: manifesto Codex de produção apontando para `./skills/`.

- [ ] **Step 1: Escrever o teste de integração em vermelho**

Adicione ao final de `tools/tests/test_validate_plugin_manifests.py`:

~~~python
def test_manifestos_reais_respeitam_o_contrato():
    raiz = Path(__file__).resolve().parents[2]
    plugin_dir = raiz / "plugins/analizza-skills"
    claude = json.loads((plugin_dir / ".claude-plugin/plugin.json").read_text())
    codex = json.loads((plugin_dir / ".codex-plugin/plugin.json").read_text())
    assert validar_manifestos(claude, codex, plugin_dir) == []

    skills_dir = plugin_dir / "skills"
    assert skills_dir.is_dir()
    assert not skills_dir.is_symlink()
    assert len(list(plugin_dir.rglob("SKILL.md"))) == 3
~~~

- [ ] **Step 2: Executar o teste e confirmar a falha**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py::test_manifestos_reais_respeitam_o_contrato -q`

Expected: FAIL com `FileNotFoundError` para `.codex-plugin/plugin.json`.

- [ ] **Step 3: Criar o manifesto Codex**

Crie `plugins/analizza-skills/.codex-plugin/plugin.json`:

~~~json
{
  "name": "analizza-skills",
  "version": "0.2.1",
  "description": "Skills da Analizza para scaffolding e qualidade de projetos",
  "author": {"name": "Diego Lirio", "email": "diegolirio.dl@gmail.com"},
  "homepage": "https://github.com/analizza-ai/analizza-marketplace",
  "repository": "https://github.com/analizza-ai/analizza-marketplace",
  "keywords": ["kotlin", "java", "spring-boot", "scaffolding", "testes de integração"],
  "skills": "./skills/",
  "hooks": {},
  "interface": {
    "displayName": "Analizza Skills",
    "shortDescription": "Scaffolding e qualidade para projetos Kotlin/Java + Spring Boot",
    "longDescription": "Cria monorepos do zero (api, core, web, mobile) e configura infraestrutura de testes de integração em projetos Kotlin ou Java com Spring Boot.",
    "developerName": "Diego Lirio",
    "category": "Developer Tools",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": ["Crie um novo projeto Kotlin com Spring Boot."]
  }
}
~~~

- [ ] **Step 4: Verificar o manifesto**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py -q && python3 tools/validate_plugin_manifests.py`

Expected: PASS, 10 testes; saída final `manifestos multi-harness válidos`.

- [ ] **Step 5: Commit**

~~~bash
git add plugins/analizza-skills/.codex-plugin/plugin.json tools/tests/test_validate_plugin_manifests.py
git commit -m "feat: add Codex plugin manifest"
~~~

### Task 3: Documentação da distribuição

**Files:**

- Modify: `README.md:1-47`
- Modify: `tools/tests/test_validate_plugin_manifests.py`

**Interfaces:**

- Consumes: manifesto Codex da Task 2 e comandos Claude existentes (`make marketplace-add`, `make install`, `make update`).
- Produces: instruções verdadeiras para os dois harnesses sem inventar um CLI Codex.

- [ ] **Step 1: Escrever o teste em vermelho**

Adicione ao final de `tools/tests/test_validate_plugin_manifests.py`:

~~~python
def test_readme_documenta_claude_e_codex_sem_comando_inventado():
    raiz = Path(__file__).resolve().parents[2]
    readme = (raiz / "README.md").read_text(encoding="utf-8")
    assert "### Claude Code" in readme
    assert "### Codex" in readme
    assert "Plugins" in readme
    assert "codex plugin install" not in readme
~~~

- [ ] **Step 2: Executar o teste e confirmar a falha**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py::test_readme_documenta_claude_e_codex_sem_comando_inventado -q`

Expected: FAIL porque o README não possui a seção `### Claude Code`.

- [ ] **Step 3: Atualizar README.md**

Substitua o `README.md` inteiro por:

~~~markdown
# analizza-marketplace

Marketplace de plugins do Claude Code da Analizza.

| Plugin | Descrição |
| --- | --- |
| `analizza-skills` | Skills para scaffolding e qualidade de projetos |

## Instalação por harness

### Claude Code

```bash
make marketplace-add   # claude plugin marketplace add analizza-ai/analizza-marketplace
make install           # claude plugin install analizza-skills@analizza-marketplace
```

Para atualizar depois:

```bash
make update
```

### Codex

O Codex não tem um comando de instalação de plugin via CLI. Abra o app Codex, vá em **Plugins**, localize **Analizza Skills** depois que o marketplace Codex publicar o plugin e siga o fluxo da interface para instalar.

Para desenvolvimento local, o plugin mantém o manifesto `plugins/analizza-skills/.codex-plugin/plugin.json` na mesma pasta do plugin; use o fluxo de instalação local que o app Codex suporta para plugins nesse formato.

## Skills do plugin `analizza-skills`

| Skill | O que faz |
| --- | --- |
| `analizza-kotlin-integration-test` | Configura a infraestrutura de testes de integração em projetos Kotlin + Spring Boot. Detecta o layout: em multi-módulo cria um módulo dedicado `{base}-integration-tests`; em single-module configura tudo dentro de `src/test/`. Centraliza o `BaseIntegrationTest`, isola libs pesadas de teste, configura jacoco, as tasks Gradle `test`/`integrationTest` e a regra ArchUnit de cobertura de entrypoints. O CI fica por conta do projeto que consome a skill. |
| `analizza-java-integration-test` | Mesma infraestrutura da skill acima, para projetos Java + Spring Boot com Gradle Groovy DSL (`settings.gradle`, templates `.java`). Detecta o layout multi-módulo ou single-module da mesma forma. |
| `analizza-new-project` | Cria do zero um monorepo de quatro módulos: backend Java Spring Boot separado em `{project}-api` (controllers) e `{project}-core` (Clean Architecture + CQRS), mais `{project}-web` em Next.js e `{project}-mobile` em Expo. O backend vem da API do Spring Initializr e é refatorado para multi-módulo Gradle, com Postgres em docker-compose e migrations Flyway no core. |

## Publicando uma versão

Suba a mesma `version` em `plugins/analizza-skills/.claude-plugin/plugin.json` e em `plugins/analizza-skills/.codex-plugin/plugin.json`, valide e crie a tag:

```bash
make validate
make check
make tag        # cria a tag analizza-skills--v{version}
```

## Estrutura

```
.claude-plugin/marketplace.json     # manifesto do marketplace
plugins/analizza-skills/
├── .claude-plugin/plugin.json      # manifesto do plugin (Claude Code)
├── .codex-plugin/plugin.json       # manifesto do plugin (Codex)
└── skills/                         # uma pasta por skill, fonte única para os dois harnesses
tools/                              # validador dos manifestos multi-harness
docs/superpowers/specs/             # decisões de design
docs/superpowers/plans/             # planos de implementação
```
~~~

- [ ] **Step 4: Executar os testes e verificar o conteúdo**

Run: `python3 -m pytest tools/tests/test_validate_plugin_manifests.py -q && rg -n '### Claude Code|### Codex|\.codex-plugin/plugin\.json' README.md`

Expected: PASS, 11 testes; `rg` encontra as duas seções e as duas menções ao manifesto Codex.

- [ ] **Step 5: Commit**

~~~bash
git add README.md tools/tests/test_validate_plugin_manifests.py
git commit -m "docs: document Codex plugin distribution"
~~~

### Task 4: Verificação final

**Files:**

- Verify: `plugins/analizza-skills/.claude-plugin/plugin.json`
- Verify: `plugins/analizza-skills/.codex-plugin/plugin.json`
- Verify: `tools/validate_plugin_manifests.py`
- Verify: `Makefile`
- Verify: `README.md`

**Interfaces:**

- Consumes: Tasks 1–3.
- Produces: evidência reproduzível da distribuição com uma única árvore de skills para os dois harnesses.

- [ ] **Step 1: Rodar a suíte local**

Run: `make check`

Expected: PASS, 11 testes, sem falhas.

- [ ] **Step 2: Rodar a validação de release**

Run: `make validate`

Expected: PASS; `claude plugin validate` valida os manifestos próprios e o script Python valida o contrato Codex, incluindo a contagem de `SKILL.md`.

- [ ] **Step 3: Verificar ausência de duplicação**

Run: `find plugins/analizza-skills -name 'SKILL.md' -type f -print | sort`

Expected: exatamente 3 linhas — `plugins/analizza-skills/skills/analizza-java-integration-test/SKILL.md`, `plugins/analizza-skills/skills/analizza-kotlin-integration-test/SKILL.md` e `plugins/analizza-skills/skills/analizza-new-project/SKILL.md`.

- [ ] **Step 4: Inspecionar o estado final**

Run: `git diff --check && git status --short`

Expected: nenhum erro de whitespace; nenhuma modificação fora dos commits desta implementação (o `git status --short` deve estar vazio, já que tudo foi commitado nas Tasks 1–3).

## Plan Self-Review

- **Cobertura:** Task 1 implementa `validar_manifestos`, `carregar_manifesto`, a checagem de contagem de `SKILL.md` e a suíte de testes; Task 2 cria o manifesto Codex real e o teste de integração; Task 3 cobre documentação e release; Task 4 verifica todos os critérios de aceite do spec (manifestos válidos, `skills` apontando para `./skills/` sem duplicação, `name`/`version` idênticos, documentação por harness, `make validate` e `make check` passando).
- **Placeholders:** cada passo contém arquivos, testes, comandos e conteúdo concreto; nenhum "TBD" ou "similar à Task N" sem o código completo.
- **Consistência de tipos:** `validar_manifestos(claude: dict, codex: dict, plugin_dir: Path) -> list[str]` e `carregar_manifesto(caminho: Path) -> Optional[dict]` são definidos na Task 1 e usados sem alteração de assinatura nas Tasks 2–4; a versão `0.2.1` e o nome `analizza-skills` coincidem em todos os arquivos (manifesto Claude existente, manifesto Codex novo, testes, README).
