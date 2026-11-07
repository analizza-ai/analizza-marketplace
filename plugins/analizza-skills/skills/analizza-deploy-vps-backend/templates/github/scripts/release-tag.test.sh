#!/usr/bin/env bash
# Testes do release-tag.sh (quem pode gerar a tag e como ela e criada).
# Rodar da raiz do repositorio: bash .github/scripts/release-tag.test.sh
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$RAIZ/.github/scripts/release-tag.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

casos=0
falha() { echo "FALHOU: $1" >&2; exit 1; }
espera() {
  local nome="$1" codigo="$2"; shift 2
  casos=$((casos + 1))
  "$@" >"$TMP/out" 2>"$TMP/err"
  local obtido=$?
  [[ "$obtido" == "$codigo" ]] || falha "$nome: exit $obtido, esperado $codigo (stderr: $(cat "$TMP/err"))"
}
cita() { grep -qF -- "$2" "$TMP/$1" || falha "$3: $1 nao cita '$2' (tem: $(cat "$TMP/$1"))"; }

# --- check: so a branch padrao gera tag
espera "padrao sem tag passa" 0 bash "$SCRIPT" check refs/heads/trunk false trunk
espera "padrao com tag passa" 0 bash "$SCRIPT" check refs/heads/trunk true trunk
espera "outra branch sem tag passa" 0 bash "$SCRIPT" check refs/heads/feat/x false trunk
espera "outra branch com tag e recusada" 1 bash "$SCRIPT" check refs/heads/feat/x true trunk
cita err "::error::" "outra branch com tag"
cita err "trunk" "outra branch com tag"
espera "main nao e a padrao aqui" 1 bash "$SCRIPT" check refs/heads/main true trunk
espera "valor estranho em gerar" 1 bash "$SCRIPT" check refs/heads/trunk sim trunk
espera "sem branch padrao" 1 bash "$SCRIPT" check refs/heads/trunk true

# --- create: num clone com origin de verdade (repositorio nu local)
git init -q --bare "$TMP/origin.git"
git clone -q "$TMP/origin.git" "$TMP/clone" 2>/dev/null
cd "$TMP/clone"
git -c user.name=t -c user.email=t@t commit -q --allow-empty -m um
git push -q origin HEAD:trunk
primeiro="$(git rev-parse HEAD)"

espera "versao invalida" 1 bash "$SCRIPT" create "1.0"
espera "cria a tag nova" 0 bash "$SCRIPT" create "1.0.0"
[[ "$(git ls-remote --tags origin refs/tags/v1.0.0 | cut -f1)" == "$primeiro" ]] || falha "v1.0.0 nao chegou ao origin no commit certo"
cita out "v1.0.0" "cria a tag nova"
espera "mesma tag no mesmo commit" 0 bash "$SCRIPT" create "1.0.0"
cita out "ja existe" "mesma tag no mesmo commit"

git -c user.name=t -c user.email=t@t commit -q --allow-empty -m dois
git push -q origin HEAD:trunk
espera "mesma tag em outro commit" 1 bash "$SCRIPT" create "1.0.0"
cita err "make version" "mesma tag em outro commit"
[[ "$(git ls-remote --tags origin refs/tags/v1.0.0 | cut -f1)" == "$primeiro" ]] || falha "v1.0.0 foi movida"

espera "uso errado" 1 bash "$SCRIPT" outra

echo "ok: $casos casos"
