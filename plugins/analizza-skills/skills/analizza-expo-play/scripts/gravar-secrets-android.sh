#!/usr/bin/env bash
# Grava os cinco secrets do Android no environment do GitHub, pelo alvo
# `make mobile-android-secrets`. Feito para a PESSOA rodar no terminal dela: as
# senhas são lidas sem eco, ficam só neste processo e somem quando ele termina.
# Antes de enviar qualquer coisa, confere a senha contra o keystore.
#
#   bash gravar-secrets-android.sh <environment> <keystore.jks> <alias> <service-account.json> <raiz-do-repo> [keytool]
set -euo pipefail

[[ $# -ge 5 ]] || { echo "uso: $0 <environment> <keystore.jks> <alias> <service-account.json> <raiz-do-repo> [keytool]"; exit 1; }
AMBIENTE="$1" KEYSTORE="$2" ALIAS="$3" JSON="$4" RAIZ="$5" KEYTOOL="${6:-keytool}"

[[ -f "$KEYSTORE" ]] || { echo "Keystore não encontrado: $KEYSTORE"; exit 1; }
[[ -f "$JSON" ]] || { echo "Chave da service account não encontrada: $JSON"; exit 1; }
command -v "$KEYTOOL" >/dev/null 2>&1 || [[ -x "$KEYTOOL" ]] || { echo "keytool não encontrado: passe o caminho como 6º argumento"; exit 1; }

read -r -s -p "Senha do keystore: " ANDROID_STORE_PASSWORD; echo
read -r -s -p "Senha da chave (Enter = mesma do keystore): " ANDROID_KEY_PASSWORD; echo
ANDROID_KEY_PASSWORD="${ANDROID_KEY_PASSWORD:-$ANDROID_STORE_PASSWORD}"
# -storepass:env lê do ambiente: exporta antes de conferir.
export ANDROID_STORE_PASSWORD ANDROID_KEY_PASSWORD

# Senha errada só apareceria no build do CI: confere aqui e para sem enviar nada.
"$KEYTOOL" -list -keystore "$KEYSTORE" -alias "$ALIAS" -storepass:env ANDROID_STORE_PASSWORD >/dev/null 2>&1 \
  || { echo "Senha do keystore não confere (ou o alias não é '$ALIAS'). Nada foi enviado."; exit 1; }

export ANDROID_KEY_ALIAS="$ALIAS"
ANDROID_KEYSTORE_BASE64="$(base64 -i "$KEYSTORE" 2>/dev/null || base64 -w0 "$KEYSTORE")"
export ANDROID_KEYSTORE_BASE64
GOOGLE_PLAY_SERVICE_ACCOUNT="$(cat "$JSON")"
export GOOGLE_PLAY_SERVICE_ACCOUNT

cd "$RAIZ"
make mobile-android-secrets ENV="$AMBIENTE"
