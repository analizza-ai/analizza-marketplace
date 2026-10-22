"""Testes do yeroon-key.sh contra um servidor local que finge o signup."""
import json
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[2]
          / "plugins/analizza-skills/skills/yeroon-play-plug/scripts/yeroon-key.sh")
KEY = "yk_" + "abcd1234efgh5678"
SECRET = "whsec_" + "zyxw9876vuts5432"
OK_BODY = {"tenantId": "t1", "name": "Acme", "apiKey": KEY, "webhookSecret": SECRET,
           "sessionToken": "sess-token-123", "sessionExpiresAt": "2030-01-01T00:00:00Z"}
INPUT = 'Acme "Ltda"\nnome@dominio.com\nsenha"secreta\ns\n'


@pytest.fixture
def fake():
    state = {"status": 201, "body": OK_BODY, "requests": []}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            state["requests"].append((self.path, json.loads(self.rfile.read(n))))
            if state.get("on_request"):
                state["on_request"]()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(state["body"]).encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{srv.server_port}"
    yield state
    srv.shutdown()


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env\n")
    return tmp_path


def run(repo, api, stdin=INPUT, *args):
    return subprocess.run(["bash", str(SCRIPT), "--api", api, *args], cwd=repo,
                          input=stdin, capture_output=True, text=True, timeout=60)


def test_grava_chave_e_segredo(repo, fake):
    r = run(repo, fake["url"])
    assert r.returncode == 0, r.stderr
    env = (repo / ".env").read_text()
    assert f"YEROON_API_KEY={KEY}" in env
    assert f"YEROON_WEBHOOK_SECRET={SECRET}" in env
    out = r.stdout + r.stderr
    for s in (KEY, SECRET, "sess-token-123", 'senha"secreta'):
        assert s not in out
    assert KEY[:7] + "…" in r.stdout
    assert (os.stat(repo / ".env").st_mode & 0o777) == 0o600


def test_env_fora_do_gitignore_para_sem_chamar_api(repo, fake):
    (repo / ".gitignore").write_text("outro\n")
    r = run(repo, fake["url"])
    assert r.returncode == 2
    assert fake["requests"] == []


def test_email_ja_cadastrado(repo, fake):
    fake["status"], fake["body"] = 409, {"title": "Já existe"}
    (repo / ".env").write_text("A=1\n")
    r = run(repo, fake["url"])
    assert r.returncode == 3
    assert "nome+projeto@" in r.stdout + r.stderr
    assert (repo / ".env").read_text() == "A=1\n"


def test_422_lista_codigos(repo, fake):
    fake["status"] = 422
    fake["body"] = {"errors": [{"code": "tenant.allowed-origins", "detail": "ruim"}]}
    r = run(repo, fake["url"])
    assert r.returncode == 4
    assert "tenant.allowed-origins" in r.stderr


def test_chave_existente_nao_e_sobrescrita(repo, fake):
    (repo / ".env").write_text("YEROON_API_KEY=antiga\n")
    r = run(repo, fake["url"])
    assert r.returncode == 5
    assert (repo / ".env").read_text() == "YEROON_API_KEY=antiga\n"
    assert fake["requests"] == []


def test_force_substitui_sem_duplicar(repo, fake):
    (repo / ".env").write_text("A=1\nYEROON_API_KEY=antiga\nB=2\n")
    r = run(repo, fake["url"], INPUT, "--force")
    assert r.returncode == 0, r.stderr
    lines = (repo / ".env").read_text().splitlines()
    assert lines.count(f"YEROON_API_KEY={KEY}") == 1
    assert sum(l.startswith("YEROON_API_KEY=") for l in lines) == 1
    assert "A=1" in lines and "B=2" in lines


def test_corpo_enviado(repo, fake):
    r = run(repo, fake["url"], INPUT, "--origin", "http://localhost:4000")
    assert r.returncode == 0, r.stderr
    path, body = fake["requests"][0]
    assert path == "/account/signup"
    assert body["origin"] == "http://localhost:4000"
    assert body["acceptedTerms"] is True
    assert body["name"] == 'Acme "Ltda"' and body["password"] == 'senha"secreta'
    assert body.get("webhookUrl") is None


def test_termos_recusados(repo, fake):
    r = run(repo, fake["url"], 'Acme\na@b.com\nx\nn\n')
    assert r.returncode == 1
    assert fake["requests"] == []


def test_falha_de_rede(repo):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    r = run(repo, f"http://127.0.0.1:{port}")
    assert r.returncode == 6


@pytest.mark.parametrize("linha", ["export YEROON_API_KEY=antiga", "YEROON_API_KEY = antiga",
                                   "  export  YEROON_WEBHOOK_SECRET =x"])
def test_chave_existente_com_export_nao_e_sobrescrita(repo, fake, linha):
    (repo / ".env").write_text(linha + "\n")
    r = run(repo, fake["url"])
    assert r.returncode == 5
    assert fake["requests"] == []


def test_force_substitui_linha_com_export(repo, fake):
    (repo / ".env").write_text("A=1\nexport YEROON_API_KEY=antiga\nYEROON_WEBHOOK_SECRET = velho\n")
    r = run(repo, fake["url"], INPUT, "--force")
    assert r.returncode == 0, r.stderr
    lines = (repo / ".env").read_text().splitlines()
    assert sum("YEROON_API_KEY" in l for l in lines) == 1
    assert sum("YEROON_WEBHOOK_SECRET" in l for l in lines) == 1
    assert f"YEROON_API_KEY={KEY}" in lines and "A=1" in lines


def test_env_somente_leitura_para_antes_da_api(repo, fake):
    (repo / ".env").write_text("A=1\n")
    os.chmod(repo / ".env", 0o400)
    r = run(repo, fake["url"])
    assert r.returncode == 1
    assert fake["requests"] == []


def test_env_diretorio_para_antes_da_api(repo, fake):
    (repo / ".env").mkdir()
    r = run(repo, fake["url"])
    assert r.returncode == 1
    assert fake["requests"] == []


def test_201_sem_chave_mensagem_propria(repo, fake):
    fake["body"] = {"tenantId": "t1"}
    r = run(repo, fake["url"])
    assert r.returncode == 7
    assert "apiKey" in r.stderr


def test_falha_na_gravacao_salva_fallback_fora_do_repo(repo, fake, tmp_path_factory):
    # Simula a corrida: o .env fica nao gravavel so depois da checagem (servidor o tranca).
    env = repo / ".env"
    env.write_text("A=1\n")
    home = tmp_path_factory.mktemp("home")
    def lock(*_):
        os.chmod(env, 0o400)
    # a primeira requisicao tranca o .env antes de a resposta ser gravada
    fake["on_request"] = lock
    r = subprocess.run(["bash", str(SCRIPT), "--api", fake["url"]], cwd=repo, input=INPUT,
                       capture_output=True, text=True, timeout=60,
                       env={**os.environ, "HOME": str(home), "XDG_STATE_HOME": ""})
    assert r.returncode == 7, r.stderr
    files = list((home / ".local/state/yeroon-play").glob("chave-*.env"))
    assert len(files) == 1 and (os.stat(files[0]).st_mode & 0o777) == 0o600
    assert f"YEROON_API_KEY={KEY}" in files[0].read_text()
    assert str(files[0]) in r.stderr and KEY not in r.stdout + r.stderr
    assert (os.stat(files[0].parent).st_mode & 0o777) == 0o700


@pytest.mark.parametrize("vazia", ["YEROON_API_KEY=", "YEROON_API_KEY=   ", 'YEROON_API_KEY=""',
                                   "export YEROON_API_KEY="])
def test_linha_vazia_e_preenchida_sem_force(repo, fake, vazia):
    (repo / ".env").write_text(f"A=1\n{vazia}\nYEROON_WEBHOOK_SECRET=\nB=2\n")
    r = run(repo, fake["url"])
    assert r.returncode == 0, r.stderr
    lines = (repo / ".env").read_text().splitlines()
    assert sum("YEROON_API_KEY=" in l for l in lines) == 1
    assert sum("YEROON_WEBHOOK_SECRET=" in l for l in lines) == 1
    assert f"YEROON_API_KEY={KEY}" in lines
    assert f"YEROON_WEBHOOK_SECRET={SECRET}" in lines
    assert "A=1" in lines and "B=2" in lines


def test_uma_preenchida_outra_vazia_para_com_5(repo, fake):
    (repo / ".env").write_text("YEROON_API_KEY=antiga\nYEROON_WEBHOOK_SECRET=\n")
    r = run(repo, fake["url"])
    assert r.returncode == 5
    assert fake["requests"] == []
