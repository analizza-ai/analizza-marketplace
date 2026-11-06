const { aplicarAssinaturaRelease } = require("../plugins/android-release-signing") as {
  aplicarAssinaturaRelease: (gradle: string) => string;
};
const { definirAppName } = require("../plugins/android-display-name") as {
  definirAppName: (strings: any, nome: string) => any;
};

// Trecho de signingConfigs/buildTypes de um android/app/build.gradle gerado pelo Expo.
// O jest roda a partir da raiz do app.
const GRADLE: string = require("fs").readFileSync("__tests__/fixtures/app-build.gradle", "utf8");

test("aplicaBlocoReleaseLendoAmbiente", () => {
  const r = aplicarAssinaturaRelease(GRADLE);
  expect(r).toContain('System.getenv("ANDROID_KEYSTORE_FILE")');
  expect(r).toContain('keyAlias System.getenv("ANDROID_KEY_ALIAS")');
  expect(r).toContain('storePassword System.getenv("ANDROID_STORE_PASSWORD")');
  expect(r).toContain('keyPassword System.getenv("ANDROID_KEY_PASSWORD")');
});

test("releaseUsaDebugSemKeystore", () => {
  const r = aplicarAssinaturaRelease(GRADLE);
  expect(r).toContain(
    'signingConfig System.getenv("ANDROID_KEYSTORE_FILE") ? signingConfigs.release : signingConfigs.debug',
  );
  // buildTypes.debug continua assinando com a chave de debug
  expect(r).toMatch(/debug \{\s*signingConfig signingConfigs\.debug\s*\}/);
  // o bloco debug de signingConfigs não muda
  expect(r).toContain("storeFile file('debug.keystore')");
});

test("idempotente", () => {
  const uma = aplicarAssinaturaRelease(GRADLE);
  expect(aplicarAssinaturaRelease(uma)).toBe(uma);
});

test("gradleSemSigningConfigsFalhaAlto", () => {
  expect(() => aplicarAssinaturaRelease("android {}")).toThrow(/signingConfigs/);
});

test("definirAppNameTrocaSoAppName", () => {
  const strings = {
    resources: {
      string: [
        { $: { name: "app_name" }, _: "meu-app" },
        { $: { name: "expo_splash_screen_resize_mode", translatable: "false" }, _: "contain" },
      ],
    },
  };
  const r = definirAppName(strings, "Meu App Dev");
  expect(r.resources.string).toEqual([
    { $: { name: "app_name" }, _: "Meu App Dev" },
    { $: { name: "expo_splash_screen_resize_mode", translatable: "false" }, _: "contain" },
  ]);
});

test("semAppNameFalhaAlto", () => {
  expect(() => definirAppName({ resources: { string: [] } }, "X")).toThrow(/app_name/);
});
