#!/usr/bin/env bash
# Testes do version.sh (versao unica entre as fontes de .github/versao.fontes).
# Rodar da raiz do repositorio: bash .github/scripts/version.test.sh
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$RAIZ/.github/scripts/version.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

casos=0
falha() { echo "FALHOU: $1" >&2; exit 1; }
espera() {
  local nome="$1" codigo="$2"; shift 2
  casos=$((casos + 1))
  VERSAO_RAIZ="$TMP/r" "$@" >"$TMP/out" 2>"$TMP/err"
  local obtido=$?
  [[ "$obtido" == "$codigo" ]] || falha "$nome: exit $obtido, esperado $codigo (stderr: $(cat "$TMP/err"))"
}
cita() { grep -qF -- "$2" "$TMP/$1" || falha "$3: $1 nao cita '$2' (tem: $(cat "$TMP/$1"))"; }

# repo falso com as tres fontes; $1 gradle, $2 app.json, $3 package.json
prepara() {
  rm -rf "$TMP/r"; mkdir -p "$TMP/r/.github" "$TMP/r/app" "$TMP/r/web"
  printf '# comentario\nversion=%s\norg.gradle.jvmargs=-Xmx1g\n' "$1" > "$TMP/r/gradle.properties"
  printf '{\n  "expo": {\n    "name": "app",\n    "version": "%s"\n  }\n}\n' "$2" > "$TMP/r/app/app.json"
  printf '{\n  "name": "web",\n  "version": "%s",\n  "private": true\n}\n' "$3" > "$TMP/r/web/package.json"
  printf '# fontes\ngradle.properties\napp/app.json\nweb/package.json\n' > "$TMP/r/.github/versao.fontes"
}

prepara 1.0.0 1.0.0 1.0.0
espera "iguais: get" 0 bash "$SCRIPT" get
[[ "$(cat "$TMP/out")" == "1.0.0" ]] || falha "get imprimiu '$(cat "$TMP/out")'"
espera "iguais: check" 0 bash "$SCRIPT" check

prepara 1.0.0 1.0.0 1.1.0
espera "uma fonte divergente: get falha" 1 bash "$SCRIPT" get
cita err "web/package.json=1.1.0" "divergente"
espera "uma fonte divergente: check falha" 1 bash "$SCRIPT" check

prepara 1.0 1.0 1.0
espera "fora de X.Y.Z falha" 1 bash "$SCRIPT" get

prepara 1.0.0 1.0.0 1.0.0
echo "outra/coisa.txt" >> "$TMP/r/.github/versao.fontes"
espera "fonte nao reconhecida falha" 1 bash "$SCRIPT" get

prepara 1.0.0 1.0.0 1.0.0
rm "$TMP/r/.github/versao.fontes"
espera "sem lista falha" 1 bash "$SCRIPT" get

prepara 1.0.0 1.0.0 1.0.0
printf 'gradle.properties\n' > "$TMP/r/.github/versao.fontes"
espera "uma fonte so vale" 0 bash "$SCRIPT" get

prepara 1.0.0 1.0.0 1.0.0
espera "set grava nas tres" 0 bash "$SCRIPT" set 2.3.4
espera "depois do set" 0 bash "$SCRIPT" get
[[ "$(cat "$TMP/out")" == "2.3.4" ]] || falha "depois do set: '$(cat "$TMP/out")'"
grep -q '^org.gradle.jvmargs=-Xmx1g$' "$TMP/r/gradle.properties" || falha "set apagou propriedade"
grep -q '"private": true' "$TMP/r/web/package.json" || falha "set perdeu campo do package.json"

prepara 1.0.0 1.0.0 1.0.0
printf 'org.gradle.jvmargs=-Xmx1g\n' > "$TMP/r/gradle.properties"
printf 'gradle.properties\n' > "$TMP/r/.github/versao.fontes"
espera "set acrescenta version= que falta" 0 bash "$SCRIPT" set 1.0.0
grep -q '^version=1.0.0$' "$TMP/r/gradle.properties" || falha "set nao acrescentou version="

prepara 1.0.0 1.0.0 1.0.0
espera "set recusa invalida" 1 bash "$SCRIPT" set 2.0
grep -q '^version=1.0.0$' "$TMP/r/gradle.properties" || falha "set invalido mexeu"

espera "uso errado" 1 bash "$SCRIPT" outra

echo "ok: $casos casos"
