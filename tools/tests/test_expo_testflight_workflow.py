"""Workflows do TestFlight (Dev e Prod) gerados pela analizza-expo-testflight."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.tests.expo_testflight_render import MARCADOR, renderizar

SKILL = Path("plugins/analizza-skills/skills/analizza-expo-testflight")
MOLDE = SKILL / "templates/github/workflows/mobile-ios-testflight.yml.template"

VALORES = {
    "app-dir": "apps/mobile",
    "github-environment": "exemplo-dev",
    "properties-file": ".github/apps/exemplo-dev.properties",
    "default-branch": "main",
    "xcode-workspace": "exemplomobile",
    "xcode-scheme": "exemplomobile",
    "node-cache": "npm",
    "lockfile": "apps/mobile/package-lock.json",
    "install-dir": "apps/mobile",
    "install-command": "npm ci",
}

GERENCIADORES = {
    "npm": {"node-cache": "npm", "lockfile": "apps/mobile/package-lock.json",
            "install-dir": "apps/mobile", "install-command": "npm ci"},
    "yarn": {"node-cache": "yarn", "lockfile": "yarn.lock",
             "install-dir": ".", "install-command": "yarn install --frozen-lockfile"},
    "pnpm": {"node-cache": "pnpm", "lockfile": "pnpm-lock.yaml",
             "install-dir": ".", "install-command": "pnpm install --frozen-lockfile"},
}


def texto(env: str, pm: str = "npm") -> str:
    blocos = {env} | ({"pnpm"} if pm == "pnpm" else set())
    return renderizar(MOLDE.read_text(encoding="utf-8"), {**VALORES, **GERENCIADORES[pm], "env": env}, blocos)


def wf(env: str) -> dict:
    # BaseLoader mantém a chave "on" como texto (o loader padrão a vira True).
    return yaml.load(texto(env), Loader=yaml.BaseLoader)


def passos(env: str) -> list[dict]:
    return wf(env)["jobs"]["build-and-upload"]["steps"]


def test_dev_dispara_so_manual():
    assert set(wf("dev")["on"]) == {"workflow_dispatch"}


def test_prod_dispara_por_tag():
    assert wf("prod")["on"]["push"]["tags"] == ["v*"]


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_guarda_antes_dos_secrets(env):
    lista = [json.dumps(p) for p in passos(env)]
    guardas = [
        i for i, p in enumerate(lista)
        if "ios-identity.sh" in p and any(g in p for g in ("guard-branch", "guard-tag", "on-default"))
    ]
    com_secret = [i for i, p in enumerate(lista) if "secrets." in p]
    assert guardas, "nenhum passo de guarda"
    if env == "prod":
        assert len(guardas) >= 2, "prod precisa de guard-tag e on-default"
    assert max(guardas) < min(com_secret)


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_ref_nao_interpolado_em_run(env):
    for p in passos(env):
        assert "${{ github.ref" not in p.get("run", ""), p.get("name")


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_publicas_vao_para_github_env(env):
    runs = [p.get("run", "") for p in passos(env)]
    assert any("public-env" in r and '>> "$GITHUB_ENV"' in r for r in runs)


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_sem_marcador_sobrando(env):
    assert not MARCADOR.findall(texto(env))


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_acoes_fixadas_por_sha(env):
    for p in passos(env):
        if "uses" in p:
            assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", p["uses"]), p["uses"]


@pytest.mark.parametrize("pm", ["npm", "yarn", "pnpm"])
def test_instalacao_segue_o_gerenciador(pm):
    lista = yaml.load(texto("dev", pm), Loader=yaml.BaseLoader)["jobs"]["build-and-upload"]["steps"]
    node = next(i for i, p in enumerate(lista) if p.get("uses", "").startswith("actions/setup-node@"))
    assert lista[node]["with"]["cache"] == GERENCIADORES[pm]["node-cache"]
    assert lista[node]["with"]["cache-dependency-path"] == GERENCIADORES[pm]["lockfile"]
    instala = next(p for p in lista if p.get("run") == GERENCIADORES[pm]["install-command"])
    assert instala["working-directory"] == GERENCIADORES[pm]["install-dir"]
    tem_pnpm = [i for i, p in enumerate(lista) if p.get("uses", "").startswith("pnpm/action-setup@")]
    assert (tem_pnpm and tem_pnpm[0] < node) if pm == "pnpm" else not tem_pnpm


@pytest.mark.parametrize("env,pm", [("dev", "npm"), ("prod", "npm"), ("dev", "yarn"), ("dev", "pnpm")])
def test_actionlint_limpo(env, pm, tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("sem docker para rodar o actionlint")
    destino = tmp_path / ".github/workflows/mobile-ios-testflight.yml"
    destino.parent.mkdir(parents=True)
    destino.write_text(texto(env, pm), encoding="utf-8")
    r = subprocess.run(
        ["docker", "run", "--rm", "-v", f"{tmp_path}:/repo", "--workdir", "/repo",
         "rhysd/actionlint:latest", "-no-color", ".github/workflows/mobile-ios-testflight.yml"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


RUNBOOK = SKILL / "templates/docs/testflight-ios.md.template"
VALORES_RUNBOOK = {
    "app-name": "Exemplo Dev",
    "bundle-id": "com.exemplo.app.dev",
    "team-id": "ABCDE12345",
    "sku": "exemplo-dev",
    "github-environment": "exemplo-dev",
    "github-repo": "dono/repo",
    "default-branch": "main",
    "testers-group": "Equipe",
    "properties-file": ".github/apps/exemplo-dev.properties",
    "public-urls": "- `EXPO_PUBLIC_API_URL`: https://api.dev.exemplo.com",
}
SECOES = [
    "## 1. O que precisa bater",
    "## 2. O que tentar para ver se quebra",
    "## 3. O que não está na lista",
    "## 4. O que este checkpoint já pegou",
]


@pytest.mark.parametrize("blocos", [
    {"dev", "primeiro-do-time"}, {"prod", "reaproveita"},
    {"prod", "primeiro-do-time"}, {"dev", "reaproveita"},
])
def test_runbook_renderizado_dev_e_prod(blocos):
    env = "dev" if "dev" in blocos else "prod"
    texto = renderizar(RUNBOOK.read_text(encoding="utf-8"), {**VALORES_RUNBOOK, "env": env}, blocos)
    assert not MARCADOR.findall(texto)
    assert texto.startswith("---\ntype: screen-mobile\n---")
    posicoes = [texto.index(s) for s in SECOES]
    assert posicoes == sorted(posicoes)
    if env == "prod":
        assert "v<versão>" in texto
        assert "workflow_dispatch" not in texto
    if "primeiro-do-time" in blocos:
        assert "Solicitar acesso" in texto and "Apple Distribution" in texto
        assert "Já existem no time" not in texto
    else:
        assert "Solicitar acesso" not in texto
        assert "Já existem no time" in texto
    numeros = re.findall(r"^(\d+)\. \*\*", texto, re.MULTILINE)
    assert len(numeros) == len(set(numeros)), f"passos com número repetido: {numeros}"
