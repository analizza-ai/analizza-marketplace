#!/usr/bin/env bash
# Versao unica do produto: todo arquivo listado em .github/versao.fontes carrega a
# mesma versao X.Y.Z (backend, web, app).
#
#   version.sh get           imprime a versao; falha se alguma fonte divergir
#   version.sh check         so confere (para as guardas dos workflows)
#   version.sh set <X.Y.Z>   grava a mesma versao em todas as fontes
#
# Fontes reconhecidas pelo nome do arquivo:
#   gradle.properties  linha version=
#   app.json           expo.version (Expo)
#   package.json       version
# A tag v<versao> (release-tag.sh) marca essa versao para todos os deploys.
# VERSAO_RAIZ troca a raiz do repositorio (usado pelos testes).
# Testes: .github/scripts/version.test.sh
set -euo pipefail

RAIZ="${VERSAO_RAIZ:-$(cd "$(dirname "$0")/../.." && pwd)}"
LISTA="$RAIZ/.github/versao.fontes"

erro() { echo "::error::$*" >&2; exit 1; }
valida() { [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || erro "$2: versao invalida '$1' (esperado X.Y.Z)."; }

fontes() {
  [[ -f "$LISTA" ]] || erro "Falta .github/versao.fontes (um arquivo por linha)."
  local n=0 linha
  while IFS= read -r linha || [[ -n "$linha" ]]; do
    linha="${linha%%#*}"; linha="$(echo "$linha" | tr -d '[:space:]')"
    [[ -n "$linha" ]] || continue
    echo "$linha"; n=$((n + 1))
  done < "$LISTA"
  (( n > 0 )) || erro ".github/versao.fontes nao lista nenhum arquivo."
}

le() {
  local f="$RAIZ/$1"
  [[ -f "$f" ]] || erro "Fonte de versao inexistente: $1."
  case "$(basename "$1")" in
    gradle.properties) sed -n 's/^version[[:space:]]*=[[:space:]]*//p' "$f" | tr -d '[:space:]' ;;
    app.json) node -e 'console.log((JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).expo||{}).version||"")' "$f" ;;
    package.json) node -e 'console.log(JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")).version||"")' "$f" ;;
    *) erro "Fonte de versao nao reconhecida: $1 (use gradle.properties, app.json ou package.json)." ;;
  esac
}

grava() {
  local f="$RAIZ/$1" v="$2" tmp
  case "$(basename "$1")" in
    gradle.properties)
      tmp="$(mktemp)"
      if grep -q '^version[[:space:]]*=' "$f"; then
        sed "s/^version[[:space:]]*=.*/version=${v}/" "$f" > "$tmp"
      else
        { cat "$f"; echo "version=${v}"; } > "$tmp"
      fi
      cat "$tmp" > "$f"; rm -f "$tmp" ;;
    app.json)
      node -e 'const fs=require("fs"),p=process.argv[1];const s=fs.readFileSync(p,"utf8");const j=JSON.parse(s);j.expo.version=process.argv[2];fs.writeFileSync(p,JSON.stringify(j,null,2)+"\n")' "$f" "$v" ;;
    package.json)
      node -e 'const fs=require("fs"),p=process.argv[1];const j=JSON.parse(fs.readFileSync(p,"utf8"));j.version=process.argv[2];fs.writeFileSync(p,JSON.stringify(j,null,2)+"\n")' "$f" "$v" ;;
  esac
}

get() {
  local primeira="" primeira_fonte="" fonte v lista
  lista="$(fontes)"
  while IFS= read -r fonte; do
    v="$(le "$fonte")"
    valida "$v" "$fonte"
    if [[ -z "$primeira" ]]; then primeira="$v"; primeira_fonte="$fonte"
    elif [[ "$v" != "$primeira" ]]; then
      erro "Versao divergente: ${primeira_fonte}=${primeira}, ${fonte}=${v}. Iguale com 'make version V=X.Y.Z'."
    fi
  done <<< "$lista"
  echo "$primeira"
}

set_versao() {
  local v="${1:-}" fonte
  valida "$v" "argumento"
  local lista; lista="$(fontes)"
  while IFS= read -r fonte; do le "$fonte" >/dev/null; done <<< "$lista"
  while IFS= read -r fonte; do grava "$fonte" "$v"; done <<< "$lista"
  echo "Versao ${v} em: $(echo "$lista" | paste -sd ' ' -)."
}

case "${1:-}" in
  get) get ;;
  check) v="$(get)"; echo "Versao ${v} (todas as fontes iguais)." ;;
  set) set_versao "${2:-}" ;;
  *) erro "uso: $0 get | check | set <X.Y.Z>" ;;
esac
