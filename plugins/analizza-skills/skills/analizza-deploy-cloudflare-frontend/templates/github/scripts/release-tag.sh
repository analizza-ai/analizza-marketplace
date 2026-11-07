#!/usr/bin/env bash
# Tag de versao dos deploys de dev (backend, web, apps).
#
#   release-tag.sh check <ref> <gerar> <branch-padrao>   gerar=true so na branch padrao;
#                                                        roda antes de qualquer credencial
#   release-tag.sh create <versao>                       cria e envia v<versao> no commit atual
#
# A tag e v<versao>, a versao unica do produto (version.sh). Ela so marca o
# commit: criada com o GITHUB_TOKEN, nao dispara nenhum outro workflow. Todos os
# deploys dividem a mesma tag; se ela ja existe no mesmo commit (outro deploy
# criou), nao e erro. Em outro commit, e: a versao precisa subir
# (make version V=X.Y.Z).
# Testes: .github/scripts/release-tag.test.sh
set -euo pipefail

erro() { echo "::error::$*" >&2; exit 1; }

check() {
  local ref="${1:-}" gerar="${2:-}" padrao="${3:-}"
  [[ -n "$padrao" ]] || erro "check precisa da branch padrao."
  case "$gerar" in
    true) [[ "$ref" == "refs/heads/${padrao}" ]] || erro "So a ${padrao} gera tag. Dispare da ${padrao} ou desmarque 'gerar_tag'. Recebido: '${ref}'." ;;
    false) ;;
    *) erro "gerar_tag precisa ser true ou false. Recebido: '${gerar}'." ;;
  esac
}

# Commit para onde a tag aponta no origin (vazio se ela nao existe).
remota() { git ls-remote --tags origin "refs/tags/$1" | cut -f1; }

create() {
  local versao="${1:-}" tag atual existente
  [[ "$versao" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || erro "Versao invalida: '${versao}' (esperado X.Y.Z)."
  tag="v${versao}"
  atual="$(git rev-parse HEAD)"
  existente="$(remota "$tag")"
  if [[ -z "$existente" ]]; then
    git tag "$tag" "$atual"
    # Se outro deploy enviou a mesma tag nesse meio-tempo, o push falha: confere de novo.
    if git push -q origin "refs/tags/${tag}"; then
      echo "Tag ${tag} criada em ${atual}."
      return 0
    fi
    existente="$(remota "$tag")"
  fi
  [[ "$existente" == "$atual" ]] || erro "A tag ${tag} ja existe em outro commit (${existente}). Suba a \"version\" com make version V=X.Y.Z antes de gerar outra tag."
  echo "Tag ${tag} ja existe neste commit (${atual}); nada a fazer."
}

case "${1:-}" in
  check) check "${2:-}" "${3:-}" "${4:-}" ;;
  create) create "${2:-}" ;;
  *) erro "uso: $0 check <ref> <gerar> <branch-padrao> | create <versao>" ;;
esac
