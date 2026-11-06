// Assinatura do release Android pela upload key do Play, lida pelo Gradle na hora do build.
//
// O plugin so escreve no build.gradle os NOMES das variaveis; os valores (caminho do keystore,
// senhas, alias) vem do ambiente do runner (.github/workflows/mobile-android-play-<env>.yml).
// Nenhum segredo fica no android/ gerado. Sem ANDROID_KEYSTORE_FILE o release continua com a
// chave de debug, que e o que o build por cabo (make mobile-android-device) usa.
const { withAppBuildGradle } = require("expo/config-plugins");

const MARCA = "// yeroon: assinatura de release pelo ambiente";

const BLOCO_RELEASE = `
        ${MARCA}
        if (System.getenv("ANDROID_KEYSTORE_FILE")) {
            release {
                storeFile file(System.getenv("ANDROID_KEYSTORE_FILE"))
                storePassword System.getenv("ANDROID_STORE_PASSWORD")
                keyAlias System.getenv("ANDROID_KEY_ALIAS")
                keyPassword System.getenv("ANDROID_KEY_PASSWORD")
            }
        }`;

const ESCOLHA =
  'signingConfig System.getenv("ANDROID_KEYSTORE_FILE") ? signingConfigs.release : signingConfigs.debug';

function aplicarAssinaturaRelease(gradle) {
  if (gradle.includes(MARCA)) return gradle;
  // 1. bloco release dentro de signingConfigs, logo depois do debug
  const comBloco = gradle.replace(
    /(signingConfigs\s*\{\s*debug\s*\{[^}]*\})/,
    (debug) => debug + BLOCO_RELEASE,
  );
  if (comBloco === gradle) throw new Error("android-release-signing: signingConfigs.debug nao encontrado no build.gradle");
  // 2. buildTypes.release escolhe a chave pelo ambiente
  const comEscolha = comBloco.replace(
    /(buildTypes\s*\{[\s\S]*?release\s*\{[\s\S]*?)signingConfig signingConfigs\.debug/,
    (_, antes) => antes + ESCOLHA,
  );
  if (comEscolha === comBloco) throw new Error("android-release-signing: buildTypes.release nao encontrado no build.gradle");
  return comEscolha;
}

function withAndroidReleaseSigning(config) {
  return withAppBuildGradle(config, (c) => {
    c.modResults.contents = aplicarAssinaturaRelease(c.modResults.contents);
    return c;
  });
}

module.exports = withAndroidReleaseSigning;
module.exports.aplicarAssinaturaRelease = aplicarAssinaturaRelease;
