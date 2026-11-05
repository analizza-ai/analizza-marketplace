#!/usr/bin/env bash
# Guardas de ref e identidade do app iOS para os workflows do TestFlight.
#
#   ios-identity.sh guard-branch <ref> <branch-padrao>  Dev: qualquer branch, menos a padrão
#   ios-identity.sh guard-tag <ref> <versao-do-app>     Prod: só a tag v<versao-do-app>
#   ios-identity.sh on-default <branch-padrao>          o HEAD está contido em origin/<branch-padrao>
#   ios-identity.sh load <arquivo.properties>           app_name=, ios_bundle_id=, apple_team_id= (para $GITHUB_OUTPUT)
#   ios-identity.sh public-env <arquivo.properties>     EXPO_PUBLIC_*=valor (para $GITHUB_ENV)
#
# O .properties é lido como texto: CHAVE=valor por linha, '#' comenta, aspas em
# volta do valor são tiradas, nada é expandido nem executado. Erros saem no
# stderr como ::error:: (anotação do GitHub Actions) e com exit 1.
set -euo pipefail

erro() { echo "::error::$*" >&2; exit 1; }

guard_branch() {
  local ref="$1" padrao="$2"
  [[ "$ref" == refs/heads/* ]] || erro "Este workflow dispara de uma branch, não de '$ref'."
  [[ "$ref" != "refs/heads/$padrao" ]] || erro "A branch '$padrao' fica para produção; dispare de uma branch de trabalho."
}

guard_tag() {
  local ref="$1" versao="$2"
  [[ "$ref" == refs/tags/* ]] || erro "Este workflow dispara de uma tag, não de '$ref'."
  local tag="${ref#refs/tags/}"
  [[ "$tag" == "v$versao" ]] || erro "A tag '$tag' não bate com a versão do app ($versao); esperado 'v$versao'."
}

on_default() {
  local padrao="$1"
  git merge-base --is-ancestor HEAD "origin/$padrao" 2>/dev/null \
    || erro "O commit desta tag não está na branch '$padrao'; produção só sai de commit da '$padrao'."
}

# Lê o arquivo e imprime "CHAVE<TAB>valor" por linha válida, já sem aspas.
ler() {
  local arquivo="$1" linha chave valor
  [[ -f "$arquivo" ]] || erro "Arquivo de identidade não encontrado: $arquivo"
  while IFS= read -r linha || [[ -n "$linha" ]]; do
    linha="${linha%$'\r'}"
    [[ -z "${linha//[[:space:]]/}" || "$linha" == \#* ]] && continue
    [[ "$linha" == *=* ]] || erro "Linha sem '=' em $arquivo: $linha"
    chave="${linha%%=*}"
    valor="${linha#*=}"
    if [[ ${#valor} -ge 2 && ( ( "$valor" == \"*\" ) || ( "$valor" == \'*\' ) ) ]]; then
      valor="${valor:1:${#valor}-2}"
    fi
    printf '%s\t%s\n' "$chave" "$valor"
  done <"$arquivo"
}

# Valida o arquivo inteiro e devolve o conteúdo lido (chave<TAB>valor).
validar() {
  local arquivo="$1" lido chave valor faltando="" app_name="" bundle="" team=""
  lido="$(ler "$arquivo")"
  while IFS=$'\t' read -r chave valor; do
    [[ -z "$chave" ]] && continue
    case "$chave" in
      APP_NAME) app_name="$valor" ;;
      IOS_BUNDLE_ID) bundle="$valor" ;;
      APPLE_TEAM_ID) team="$valor" ;;
      EXPO_PUBLIC_*)
        [[ "$chave" =~ ^EXPO_PUBLIC_[A-Z0-9_]+$ ]] || erro "Chave pública inválida em $arquivo: $chave"
        ;;
      *) erro "Chave desconhecida em $arquivo: $chave (só APP_NAME, IOS_BUNDLE_ID, APPLE_TEAM_ID e EXPO_PUBLIC_*)" ;;
    esac
  done <<<"$lido"
  [[ -n "$app_name" ]] || faltando="$faltando APP_NAME"
  [[ -n "$bundle" ]] || faltando="$faltando IOS_BUNDLE_ID"
  [[ -n "$team" ]] || faltando="$faltando APPLE_TEAM_ID"
  [[ -z "$faltando" ]] || erro "Faltando em $arquivo:$faltando"
  [[ "$team" =~ ^[A-Z0-9]{10}$ ]] || erro "APPLE_TEAM_ID inválido em $arquivo: '$team' (10 letras maiúsculas ou dígitos)"
  [[ "$bundle" =~ ^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$ ]] || erro "IOS_BUNDLE_ID inválido em $arquivo: '$bundle'"
  printf '%s\n' "$lido"
}

load() {
  local lido chave valor
  lido="$(validar "$1")"
  while IFS=$'\t' read -r chave valor; do
    case "$chave" in
      APP_NAME) echo "app_name=$valor" ;;
      IOS_BUNDLE_ID) echo "ios_bundle_id=$valor" ;;
      APPLE_TEAM_ID) echo "apple_team_id=$valor" ;;
    esac
  done <<<"$lido"
}

public_env() {
  local lido chave valor
  lido="$(validar "$1")"
  while IFS=$'\t' read -r chave valor; do
    [[ "$chave" == EXPO_PUBLIC_* ]] && echo "$chave=$valor"
  done <<<"$lido"
  return 0
}

uso() { erro "uso: $0 guard-branch <ref> <branch-padrao> | guard-tag <ref> <versao> | on-default <branch-padrao> | load <arquivo> | public-env <arquivo>"; }

[[ $# -ge 1 ]] || uso
comando="$1"; shift
case "$comando" in
  guard-branch) [[ $# -eq 2 ]] || uso; guard_branch "$1" "$2" ;;
  guard-tag) [[ $# -eq 2 ]] || uso; guard_tag "$1" "$2" ;;
  on-default) [[ $# -eq 1 ]] || uso; on_default "$1" ;;
  load) [[ $# -eq 1 ]] || uso; load "$1" ;;
  public-env) [[ $# -eq 1 ]] || uso; public_env "$1" ;;
  *) uso ;;
esac
