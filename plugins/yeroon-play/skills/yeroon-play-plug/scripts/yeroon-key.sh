#!/usr/bin/env bash
# Cria uma conta de teste no yeroon play e grava YEROON_API_KEY e
# YEROON_WEBHOOK_SECRET no .env do back-end. Rode VOCE, no seu terminal:
# a senha, a chave e o segredo nao passam pelo agente.
#
# Uso: yeroon-key.sh [--env ./.env] [--api URL] [--origin URL] [--webhook URL] [--force]
# Saidas: 0 ok | 1 uso/termos recusados | 2 .env fora do .gitignore | 3 e-mail ja
#         tem conta | 4 regra quebrada (422) | 5 chave ja existe (sem --force)
#         6 falha de rede | 7 resposta inesperada
set -euo pipefail

ENV_FILE="./.env"
API="${YEROON_API_URL:-https://api.dev.play.yeroon.video}"
ORIGIN="http://localhost:3000"
WEBHOOK=""
FORCE=0

die() { printf '%s\n' "$2" >&2; exit "$1"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --env) [ $# -ge 2 ] || die 1 "--env precisa de um valor"; ENV_FILE="$2"; shift 2 ;;
    --api) [ $# -ge 2 ] || die 1 "--api precisa de um valor"; API="$2"; shift 2 ;;
    --origin) [ $# -ge 2 ] || die 1 "--origin precisa de um valor"; ORIGIN="$2"; shift 2 ;;
    --webhook) [ $# -ge 2 ] || die 1 "--webhook precisa de um valor"; WEBHOOK="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) die 1 "Argumento desconhecido: $1" ;;
  esac
done

command -v python3 >/dev/null 2>&1 || die 1 "python3 e necessario."
command -v curl >/dev/null 2>&1 || die 1 "curl e necessario."

ENV_DIR="$(dirname "$ENV_FILE")"
ENV_BASE="$(basename "$ENV_FILE")"

# 1. O .env precisa estar fora do git, antes de qualquer chamada.
ignored=0
if git -C "$ENV_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ENV_DIR" check-ignore -q "$ENV_BASE" && ignored=1
elif [ -f "$ENV_DIR/.gitignore" ] \
  && grep -qxF -e "$ENV_BASE" -e "/$ENV_BASE" "$ENV_DIR/.gitignore"; then
  ignored=1
fi
[ "$ignored" -eq 1 ] || die 2 "O arquivo $ENV_FILE nao esta no .gitignore. Adicione '$ENV_BASE' ao .gitignore e rode de novo (a chave nao pode ir para o git)."

# 2. Nao criar conta nova se ja ha chave, a menos que --force.
if [ "$FORCE" -eq 0 ] && [ -f "$ENV_FILE" ] \
  && grep -Eq '^[[:space:]]*(export[[:space:]]+)?(YEROON_API_KEY|YEROON_WEBHOOK_SECRET)[[:space:]]*=' "$ENV_FILE"; then
  die 5 "$ENV_FILE ja tem YEROON_API_KEY/YEROON_WEBHOOK_SECRET. Use --force para substituir."
fi

# 2b. O .env precisa ser gravavel ANTES de criar a conta (a chave so aparece uma vez).
if [ -e "$ENV_FILE" ]; then
  [ -f "$ENV_FILE" ] || die 1 "$ENV_FILE existe mas nao e um arquivo comum."
  [ -w "$ENV_FILE" ] || die 1 "$ENV_FILE nao tem permissao de escrita. Ajuste e rode de novo."
else
  [ -d "$ENV_DIR" ] && [ -w "$ENV_DIR" ] || die 1 "Nao consigo criar $ENV_FILE: a pasta nao existe ou nao tem permissao de escrita."
fi
case "$API" in
  http://localhost*|http://127.0.0.1*|http://\[::1\]*) ;;
  http://*) printf 'Aviso: --api usa http:// puro para um host que nao e local; a senha e a chave trafegam sem criptografia.\n' >&2 ;;
esac

# 3. Perguntas (a senha nao aparece na tela).
printf 'Nome da conta: ' >&2; IFS= read -r NAME || NAME=""
printf 'E-mail: ' >&2; IFS= read -r EMAIL || EMAIL=""
printf 'Senha: ' >&2; IFS= read -rs PASSWORD || PASSWORD=""; printf '\n' >&2
printf 'Aceita os termos de uso do yeroon play? (s/n): ' >&2; IFS= read -r ACCEPT || ACCEPT=""
case "$ACCEPT" in
  s|S|sim|Sim|SIM|y|Y|yes) ;;
  *) die 1 "Termos nao aceitos: a conta nao foi criada." ;;
esac
[ -n "$NAME" ] && [ -n "$EMAIL" ] && [ -n "$PASSWORD" ] || die 1 "Nome, e-mail e senha sao obrigatorios."

# 4. Corpo JSON montado sem interpolar texto (aspas na senha, etc.).
umask 077
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
trap 'exit 130' INT TERM
Y_NAME="$NAME" Y_EMAIL="$EMAIL" Y_PASSWORD="$PASSWORD" Y_ORIGIN="$ORIGIN" Y_WEBHOOK="$WEBHOOK" \
python3 -c '
import json, os
e = os.environ
body = {"name": e["Y_NAME"], "email": e["Y_EMAIL"], "password": e["Y_PASSWORD"],
        "origin": e["Y_ORIGIN"], "acceptedTerms": True}
if e["Y_WEBHOOK"]:
    body["webhookUrl"] = e["Y_WEBHOOK"]
print(json.dumps(body))' > "$TMP/req.json"
unset PASSWORD

set +e
STATUS="$(curl -sS --max-time 20 -o "$TMP/resp.json" -w '%{http_code}' \
  -X POST -H 'Content-Type: application/json' --data @"$TMP/req.json" \
  "${API%/}/account/signup" 2>"$TMP/curl.err")"
CURL_RC=$?
set -e
if [ "$CURL_RC" -ne 0 ]; then
  die 6 "Falha de rede ao falar com $API (curl codigo $CURL_RC). Confira a URL e a conexao."
fi

case "$STATUS" in
  201) ;;
  409) die 3 "Ja existe uma conta yeroon com este e-mail e nao ha como recuperar a chave. Use um alias, por exemplo nome+projeto@dominio.com, ou cole a chave que voce ja tem no .env (YEROON_API_KEY e YEROON_WEBHOOK_SECRET)." ;;
  422)
    Y_BODY="$TMP/resp.json" python3 -c '
import json, os, sys
try:
    d = json.load(open(os.environ["Y_BODY"]))
except Exception:
    d = {}
errs = d.get("errors") or []
if not errs:
    print("422: regra quebrada (sem detalhes).", file=sys.stderr)
for x in errs:
    line = "422: " + str(x.get("code", "?"))
    if x.get("detail"):
        line += " - " + str(x["detail"])
    print(line, file=sys.stderr)' >&2
    exit 4 ;;
  *) die 7 "Resposta inesperada do yeroon (HTTP $STATUS)." ;;
esac

# 5. Grava no .env sem passar a chave por argumentos nem pelo terminal.
FALLBACK_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/yeroon-play"
FALLBACK="$FALLBACK_DIR/chave-$(date +%s).env"
rc=0
Y_BODY="$TMP/resp.json" Y_ENV="$ENV_FILE" Y_FB_DIR="$FALLBACK_DIR" Y_FB="$FALLBACK" python3 -c '
import json, os, sys
d = json.load(open(os.environ["Y_BODY"]))
key, sec = d.get("apiKey"), d.get("webhookSecret")
if not key or not sec:
    print("O yeroon respondeu 201 mas sem apiKey/webhookSecret; nada foi gravado.", file=sys.stderr); sys.exit(7)
path = os.environ["Y_ENV"]
new = {"YEROON_API_KEY": key, "YEROON_WEBHOOK_SECRET": sec}
lines = open(path).read().splitlines() if os.path.exists(path) else []
out, seen = [], set()
for l in lines:
    t = l.strip()
    if t.startswith("export") and t[6:7].isspace():
        t = t[6:].lstrip()
    name = t.split("=", 1)[0].strip() if "=" in t else ""
    if name in new:
        if name not in seen:
            out.append(name + "=" + new[name]); seen.add(name)
        continue
    out.append(l)
for name, v in new.items():
    if name not in seen:
        out.append(name + "=" + v)
data = "\n".join(out) + "\n"
try:
    if os.path.exists(path):
        with open(path, "w") as f:
            f.write(data)
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(data)
except OSError as err:
    os.makedirs(os.environ["Y_FB_DIR"], mode=0o700, exist_ok=True)
    os.chmod(os.environ["Y_FB_DIR"], 0o700)
    fd = os.open(os.environ["Y_FB"], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("".join(n + "=" + v + "\n" for n, v in new.items()))
    print("A conta foi criada mas nao consegui gravar em " + path + " (" + err.strerror + ").", file=sys.stderr)
    print("A chave e o segredo foram salvos em " + os.environ["Y_FB"] + " (modo 600, fora do repositorio).", file=sys.stderr)
    print("Mova as duas linhas desse arquivo para o .env do back-end e apague o arquivo.", file=sys.stderr)
    sys.exit(7)
print(key[:7] + "…")' > "$TMP/prefix.txt" || rc=$?
[ "$rc" -eq 0 ] || exit "$rc"

printf 'Conta criada. Chave gravada em %s (prefixo %s).\n' "$ENV_FILE" "$(cat "$TMP/prefix.txt")"
printf 'Lembrete: a chave e o segredo do webhook ficam so no .env do back-end; nunca no front, no app, em log ou no git.\n'
