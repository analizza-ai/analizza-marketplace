#!/usr/bin/env bash
# Testes do android-identity.sh: guardas de branch e de tag, commit na branch
# padrão, e leitura da identidade do app (.properties) sem executar nada do arquivo.
# Rodar de qualquer lugar: bash <pasta>/android-identity.test.sh
set -uo pipefail

SCRIPT="$(cd "$(dirname "$0")" && pwd)/android-identity.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

casos=0
falha() { echo "FALHOU: $1" >&2; exit 1; }

# espera <nome> <exit esperado> <comando...>; guarda stdout/stderr em $TMP/out e $TMP/err
espera() {
  local nome="$1" codigo="$2"; shift 2
  casos=$((casos + 1))
  "$@" >"$TMP/out" 2>"$TMP/err"
  local obtido=$?
  [[ "$obtido" == "$codigo" ]] || falha "$nome: exit $obtido, esperado $codigo (stderr: $(cat "$TMP/err"))"
}
contem() { grep -qxF -- "$2" "$TMP/$1" || falha "$3: $1 nao contem a linha '$2' (tem: $(cat "$TMP/$1"))"; }
cita() { grep -qF -- "$2" "$TMP/$1" || falha "$3: $1 nao cita '$2' (tem: $(cat "$TMP/$1"))"; }
nao_cita() { ! grep -qF -- "$2" "$TMP/$1" || falha "$3: $1 nao deveria citar '$2'"; }

# --- guardas de ref ---------------------------------------------------------

espera branch_feature_aceita 0 bash "$SCRIPT" guard-branch refs/heads/feat/x main
espera branch_padrao_aceita 0 bash "$SCRIPT" guard-branch refs/heads/main main
espera branch_padrao_sem_tag 0 bash "$SCRIPT" guard-branch refs/heads/main main false
espera branch_padrao_gera_tag 0 bash "$SCRIPT" guard-branch refs/heads/main main true
espera tag_so_na_padrao 1 bash "$SCRIPT" guard-branch refs/heads/feat/x main true
cita err "::error::" tag_so_na_padrao
cita err "main" tag_so_na_padrao
espera gerar_tag_invalido 1 bash "$SCRIPT" guard-branch refs/heads/main main sim
espera branch_recusa_tag 1 bash "$SCRIPT" guard-branch refs/tags/v1.0.0 main
espera branch_recusa_ref_de_pr 1 bash "$SCRIPT" guard-branch refs/pull/3/merge main

espera tag_igual_a_versao 0 bash "$SCRIPT" guard-tag refs/tags/v1.2.3 1.2.3
espera tag_diferente_da_versao 1 bash "$SCRIPT" guard-tag refs/tags/v1.2.3 1.2.4
cita err "v1.2.3" tag_diferente_da_versao
cita err "1.2.4" tag_diferente_da_versao
espera tag_recusa_branch 1 bash "$SCRIPT" guard-tag refs/heads/v1.2.3 1.2.3

# --- commit da tag contido na branch padrão ---------------------------------

REPO="$TMP/repo"
git init -q -b main "$REPO"
git -C "$REPO" -c user.name=t -c user.email=t@t commit -q --allow-empty -m base
git -C "$REPO" update-ref refs/remotes/origin/main HEAD
espera commit_na_padrao 0 bash -c "cd '$REPO' && bash '$SCRIPT' on-default main"
git -C "$REPO" switch -q -c feat
git -C "$REPO" -c user.name=t -c user.email=t@t commit -q --allow-empty -m fora
espera commit_fora_da_padrao 1 bash -c "cd '$REPO' && bash '$SCRIPT' on-default main"
cita err "::error::" commit_fora_da_padrao

# --- criação da tag v<versão> (dev na branch padrão, com gerar_tag) ----------

ORIGEM="$TMP/origem.git"
CLONE="$TMP/clone"
git init -q --bare "$ORIGEM"
git clone -q "$ORIGEM" "$CLONE" 2>/dev/null
git -C "$CLONE" -c user.name=t -c user.email=t@t commit -q --allow-empty -m um
git -C "$CLONE" push -q origin HEAD:main
PRIMEIRO="$(git -C "$CLONE" rev-parse HEAD)"
tag_remota() { git -C "$CLONE" ls-remote --tags origin "refs/tags/$1" | cut -f1; }

espera tag_versao_invalida 1 bash -c "cd '$CLONE' && bash '$SCRIPT' create-tag 1.0"
espera tag_criada 0 bash -c "cd '$CLONE' && bash '$SCRIPT' create-tag 1.0.0"
[[ "$(tag_remota v1.0.0)" == "$PRIMEIRO" ]] || falha "tag_criada: v1.0.0 não chegou ao origin no commit certo"
espera tag_no_mesmo_commit 0 bash -c "cd '$CLONE' && bash '$SCRIPT' create-tag 1.0.0"
cita out "já existe" tag_no_mesmo_commit
git -C "$CLONE" -c user.name=t -c user.email=t@t commit -q --allow-empty -m dois
git -C "$CLONE" push -q origin HEAD:main
espera tag_em_outro_commit 1 bash -c "cd '$CLONE' && bash '$SCRIPT' create-tag 1.0.0"
cita err "::error::" tag_em_outro_commit
cita err "version" tag_em_outro_commit
[[ "$(tag_remota v1.0.0)" == "$PRIMEIRO" ]] || falha "tag_em_outro_commit: a tag v1.0.0 foi movida"

# --- identidade -------------------------------------------------------------

cat >"$TMP/ok.properties" <<'EOF'
# identidade de exemplo
APP_NAME="Meu App Dev"
ANDROID_PACKAGE=com.exemplo.app.dev
PLAY_TRACK=internal
EXPO_PUBLIC_API_URL=https://api.dev.exemplo.com
EOF
espera load_completo 0 bash "$SCRIPT" load "$TMP/ok.properties"
contem out "app_name=Meu App Dev" load_completo
contem out "android_package=com.exemplo.app.dev" load_completo
contem out "play_track=internal" load_completo

sed "s/^APP_NAME=.*/APP_NAME='A B'/" "$TMP/ok.properties" >"$TMP/aspas.properties"
espera aspas_e_espacos 0 bash "$SCRIPT" load "$TMP/aspas.properties"
contem out "app_name=A B" aspas_e_espacos

# O $(...) é literal de propósito: o teste prova que ele não executa.
# shellcheck disable=SC2016
{ cat "$TMP/ok.properties"; printf 'EXPO_PUBLIC_X=$(touch %s/pwn)\n' "$TMP"; } >"$TMP/sub.properties"
espera valor_com_subshell_nao_executa 0 bash "$SCRIPT" public-env "$TMP/sub.properties"
contem out "EXPO_PUBLIC_X=\$(touch $TMP/pwn)" valor_com_subshell_nao_executa
[[ ! -e "$TMP/pwn" ]] || falha "valor_com_subshell_nao_executa: o subshell rodou"

printf 'APP_NAME=So o nome\n' >"$TMP/falta.properties"
espera faltando_lista_todas 1 bash "$SCRIPT" load "$TMP/falta.properties"
cita err "ANDROID_PACKAGE" faltando_lista_todas
cita err "PLAY_TRACK" faltando_lista_todas

sed 's/^PLAY_TRACK=.*/PLAY_TRACK=production/' "$TMP/ok.properties" >"$TMP/faixa.properties"
espera faixa_diferente_de_internal 1 bash "$SCRIPT" load "$TMP/faixa.properties"
cita err "PLAY_TRACK" faixa_diferente_de_internal

sed 's/^ANDROID_PACKAGE=.*/ANDROID_PACKAGE=com.exemplo-app.dev/' "$TMP/ok.properties" >"$TMP/pacote.properties"
espera pacote_com_hifen 1 bash "$SCRIPT" load "$TMP/pacote.properties"
cita err "ANDROID_PACKAGE" pacote_com_hifen

sed 's/^ANDROID_PACKAGE=.*/ANDROID_PACKAGE=exemplo/' "$TMP/ok.properties" >"$TMP/segmento.properties"
espera pacote_com_um_segmento 1 bash "$SCRIPT" load "$TMP/segmento.properties"
cita err "ANDROID_PACKAGE" pacote_com_um_segmento

{ cat "$TMP/ok.properties"; echo "IOS_BUNDLE_ID=com.exemplo.app.dev"; } >"$TMP/desconhecida.properties"
espera chave_desconhecida 1 bash "$SCRIPT" load "$TMP/desconhecida.properties"
cita err "IOS_BUNDLE_ID" chave_desconhecida

espera public_env_so_publicas 0 bash "$SCRIPT" public-env "$TMP/ok.properties"
contem out "EXPO_PUBLIC_API_URL=https://api.dev.exemplo.com" public_env_so_publicas
nao_cita out "APP_NAME" public_env_so_publicas

espera arquivo_inexistente 1 bash "$SCRIPT" load "$TMP/nao-existe.properties"

echo "OK ($casos casos)"
