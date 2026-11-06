// Nome exibido no Android (app_name do strings.xml) vindo do ambiente, como o
// CFBundleDisplayName no iOS. O `name` do Expo não muda: ele gera o projeto nativo.
const { withStringsXml } = require("expo/config-plugins");

function definirAppName(strings, nome) {
  const lista = strings.resources?.string ?? [];
  // Sem app_name o app sairia com o nome errado sem ninguém perceber: falha alto.
  if (!lista.some((s) => s.$?.name === "app_name")) {
    throw new Error("android-display-name: string app_name não encontrada no strings.xml");
  }
  return {
    ...strings,
    resources: {
      ...strings.resources,
      string: lista.map((s) => (s.$?.name === "app_name" ? { ...s, _: nome } : s)),
    },
  };
}

function withAndroidDisplayName(config, { nome }) {
  return withStringsXml(config, (c) => {
    c.modResults = definirAppName(c.modResults, nome);
    return c;
  });
}

module.exports = withAndroidDisplayName;
module.exports.definirAppName = definirAppName;
