"""Alvo `mobile-ios-secrets` gerado pela analizza-expo-testflight, rodado com um gh falso."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

from tools.tests.expo_testflight_render import MARCADOR, renderizar

MOLDE = Path(
    "plugins/analizza-skills/skills/analizza-expo-testflight/templates/makefile/mobile-ios-secrets.mk.template"
)

SECRETS = {
    "APPLE_API_KEY_ID": "KEY123",
    "APPLE_API_ISSUER_ID": "issuer-uuid",
    "APPLE_API_KEY_P8": "-----BEGIN PRIVATE KEY-----\nlinha 2 com $ e 'aspas'\n-----END PRIVATE KEY-----",
    "IOS_DISTRIBUTION_CERT_BASE64": "TUlJ+base64/==",
    "IOS_CERTIFICATE_PASSWORD": "s3nh@ com espaço",
}

# gh falso: registra cada chamada em $FAKE_GH_LOG; só lê o stdin em `secret set`,
# guardando o valor recebido em $FAKE_GH_DIR/<NOME>.
GH_FALSO = r"""#!/usr/bin/env bash
echo "$*" >> "$FAKE_GH_LOG"
if [[ "$1" == "api" ]]; then
  if [[ "$*" == *"-X PUT"* ]]; then exit 0; fi
  if [[ "${FAKE_GH_ENV_EXISTS:-0}" == "1" ]]; then exit 0; fi
  echo "gh: Not Found (HTTP 404)" >&2; exit 1
fi
if [[ "$1 $2" == "secret set" ]]; then
  nome="$3"
  cat > "$FAKE_GH_DIR/$nome"
  if [[ "${FAKE_GH_FAIL_ON:-}" == "$nome" ]]; then exit 1; fi
  exit 0
fi
exit 0
"""


@pytest.fixture
def projeto(tmp_path: Path):
    texto = renderizar(MOLDE.read_text(encoding="utf-8"), {"github-repo": "dono/repo"}, set())
    assert not MARCADOR.findall(texto)
    (tmp_path / "Makefile").write_text(texto, encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(GH_FALSO, encoding="utf-8")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    (tmp_path / "recebido").mkdir()
    return tmp_path


def rodar(projeto: Path, segredos: dict, args=("ENV=exemplo-dev",), **extra):
    env = {
        "PATH": f"{projeto / 'bin'}:/usr/bin:/bin",
        "HOME": str(projeto),
        "FAKE_GH_LOG": str(projeto / "gh.log"),
        "FAKE_GH_DIR": str(projeto / "recebido"),
        **segredos,
        **extra,
    }
    return subprocess.run(
        ["make", "-s", "mobile-ios-secrets", *args],
        cwd=projeto, env=env, capture_output=True, text=True,
    )


def chamadas(projeto: Path) -> list[str]:
    log = projeto / "gh.log"
    return log.read_text().splitlines() if log.exists() else []


def test_sem_env_falha_sem_chamar_gh(projeto):
    r = rodar(projeto, SECRETS, args=())
    assert r.returncode != 0
    assert "ENV=<environment> obrigatório" in r.stdout + r.stderr
    assert chamadas(projeto) == []


def test_lista_todas_as_variaveis_faltando(projeto):
    r = rodar(projeto, {})
    assert r.returncode != 0
    for nome in SECRETS:
        assert nome in r.stdout + r.stderr
    assert chamadas(projeto) == []


def test_environment_existente_nao_recebe_put(projeto):
    r = rodar(projeto, SECRETS, FAKE_GH_ENV_EXISTS="1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not any("PUT" in c for c in chamadas(projeto))
    assert sum(c.startswith("secret set") for c in chamadas(projeto)) == 5


def test_environment_ausente_e_criado(projeto):
    r = rodar(projeto, SECRETS, FAKE_GH_ENV_EXISTS="0")
    assert r.returncode == 0, r.stdout + r.stderr
    log = chamadas(projeto)
    puts = [i for i, c in enumerate(log) if "-X PUT" in c and "environments/exemplo-dev" in c]
    sets = [i for i, c in enumerate(log) if c.startswith("secret set")]
    assert len(puts) == 1 and puts[0] < sets[0]
    assert all("--env exemplo-dev" in log[i] and "--repo dono/repo" in log[i] for i in sets)


def test_valor_multilinha_chega_inteiro(projeto):
    r = rodar(projeto, SECRETS, FAKE_GH_ENV_EXISTS="1")
    assert r.returncode == 0, r.stdout + r.stderr
    for nome, valor in SECRETS.items():
        assert (projeto / "recebido" / nome).read_text() == valor


def test_falha_num_secret_para(projeto):
    r = rodar(projeto, SECRETS, FAKE_GH_ENV_EXISTS="1", FAKE_GH_FAIL_ON="APPLE_API_KEY_P8")
    assert r.returncode != 0
    gravados = [c.split()[2] for c in chamadas(projeto) if c.startswith("secret set")]
    assert gravados[-1] == "APPLE_API_KEY_P8"
    assert "IOS_DISTRIBUTION_CERT_BASE64" not in gravados


def test_get_com_erro_que_nao_e_404_nao_cria(projeto, tmp_path):
    # gh sem login (erro diferente de 404) não pode virar PUT num environment talvez existente.
    gh = projeto / "bin" / "gh"
    gh.write_text(
        '#!/usr/bin/env bash\necho "$*" >> "$FAKE_GH_LOG"\necho "gh: authentication required (HTTP 401)" >&2\nexit 1\n'
    )
    r = rodar(projeto, SECRETS)
    assert r.returncode != 0
    assert not any("PUT" in c for c in chamadas(projeto))
