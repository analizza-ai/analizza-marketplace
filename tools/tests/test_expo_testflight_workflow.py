"""Workflows do TestFlight (Dev e Prod) gerados pela analizza-expo-testflight."""

import json
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
}


def texto(env: str) -> str:
    return renderizar(MOLDE.read_text(encoding="utf-8"), {**VALORES, "env": env}, {env})


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
def test_actionlint_limpo(env, tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("sem docker para rodar o actionlint")
    destino = tmp_path / ".github/workflows/mobile-ios-testflight.yml"
    destino.parent.mkdir(parents=True)
    destino.write_text(texto(env), encoding="utf-8")
    r = subprocess.run(
        ["docker", "run", "--rm", "-v", f"{tmp_path}:/repo", "--workdir", "/repo",
         "rhysd/actionlint:latest", "-no-color", ".github/workflows/mobile-ios-testflight.yml"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
