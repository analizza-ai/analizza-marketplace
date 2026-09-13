# Jest num scaffold Expo real (`-mobile`)

Depois de instalar `jest-expo jest @types/jest @testing-library/react-native`
(Passo 7) e antes de gravar `__tests__/tela-inicial-test.tsx`, siga os passos
abaixo, cada um só se a condição indicada valer para o projeto. Eles resolvem
gaps do ecossistema Expo SDK 57 / Reanimated 4 / Worklets / NativeWind que o
`jest-expo` sozinho não cobre — sem eles, `tsc --noEmit` e `jest` falham num
scaffold real, mesmo com o teste mínimo do template.

## 1 — `"types": ["jest"]` no `tsconfig.json`

Sem isto, `tsc --noEmit` não enxerga `@types/jest` mesmo instalado: erros como
`Cannot find name 'test'` / `Cannot find name 'expect'`.

Verifique se já existe um array `"types"` em `compilerOptions`:

```bash
grep -n '"types"' tsconfig.json
```

- **Sem saída (não existe):** acrescente `"types": ["jest"]` a
  `compilerOptions`.
- **Com saída (já existe):** acrescente `"jest"` ao array existente, sem
  remover o que já tem.

## 2 — ordem dos `paths` específicos antes dos genéricos

O `withTypescriptMapping` do `jest-expo` constrói o `moduleNameMapper` do Jest
na ordem das chaves de `compilerOptions.paths`. Se um alias genérico
(`"@/*"`) vem antes de um mais específico (`"@/assets/*"`), o genérico casa
primeiro e captura os imports que deveriam ir para o específico — em runtime
isso aparece como `Could not locate module @/assets/...`.

```bash
grep -n '"@/' tsconfig.json
```

Se um alias mais específico aparecer **depois** de um mais genérico que o
prefixa (ex.: `"@/*"` antes de `"@/assets/*"`), reordene `paths` para que os
mais específicos venham primeiro:

```json
"paths": {
  "@/assets/*": ["./assets/*"],
  "@/*": ["./src/*"]
}
```

## 3 — tipos do matcher `toHavePathname`

`expo-router/testing-library` registra `toHavePathname` (e os matchers
correlatos) em runtime, via `expect.extend(...)`, mas não publica o `.d.ts`
correspondente — `tsc --noEmit` acusa
`Property 'toHavePathname' does not exist on type 'JestMatchers<...>'` mesmo
com o teste correto. Este passo é sempre necessário quando o teste usa
`toHavePathname` (o template desta skill usa).

Grave `expo-router-testing-library.d.ts` na raiz do `{mobile-dir}`:

```ts
// expo-router/testing-library registra estes matchers em runtime
// (expect.extend em build/testing-library/expect.js) mas o pacote nao
// publica os tipos deles (build/testing-library/expect.d.ts so tem
// `export {}`). Sem isto, `tsc --noEmit` acusa erro no matcher que o
// template desta skill usa (toHavePathname).
declare global {
  namespace jest {
    interface Matchers<R> {
      toHavePathname(pathname: string): R;
      toHavePathnameWithParams(pathname: string): R;
      toHaveSegments(segments: string[]): R;
      toHaveSearchParams(params: Record<string, string | string[]>): R;
      toHaveRouterState(state: unknown): R;
    }
  }
}

export {};
```

## 4 — resolver do `react-native-worklets`, se presente

`react-native-worklets` (dependência do Reanimated 4) não inicializa sob
Jest sem o resolver próprio que o pacote publica; sem ele, a suite quebra ao
renderizar a árvore real do app com
`Cannot read properties of undefined (reading 'loadUnpackers')`.

```bash
grep -n '"react-native-worklets"' package.json
```

Se aparecer em `dependencies`, acrescente à configuração `"jest"` do
`package.json`:

```json
"jest": {
  "resolver": "react-native-worklets/jest/resolver.js"
}
```

Sem `react-native-worklets` no projeto, pule este passo.

## 5 — mock de CSS, se algum fonte importar `.css` (NativeWind)

`renderRouter` renderiza o `_layout.tsx` real; se algum arquivo importado por
ele (direto ou não) tiver `import "...css"` (típico de NativeWind com
`global.css`), o Jest quebra com `SyntaxError: Unexpected token ':'` — ele não
sabe transformar CSS.

```bash
grep -rlE "from ['\"].*\.css['\"]|import ['\"].*\.css['\"]" --include='*.ts' --include='*.tsx' app src 2>/dev/null
```

Com alguma saída, grave `__mocks__/styleMock.js`:

```js
// Jest nao sabe transformar CSS (src/global.css, importado pelo layout raiz
// para o NativeWind). Sem isto, `import '@/global.css'` quebra a suite com
// SyntaxError antes mesmo do primeiro teste rodar.
module.exports = {};
```

E acrescente `moduleNameMapper` à configuração `"jest"` do `package.json`
(mescle com o `resolver` do passo 4 se os dois se aplicarem):

```json
"jest": {
  "moduleNameMapper": {
    "\\.css$": "<rootDir>/__mocks__/styleMock.js"
  }
}
```

Sem nenhum import de `.css`, pule este passo.

## 6 — `jest`, `jest-expo`, `@types/jest` em `devDependencies`

`npx expo install ... -- --save-dev` pode, dependendo da versão do CLI, gravar
`jest`, `jest-expo` e `@types/jest` em `"dependencies"` em vez de
`"devDependencies"` — contradiz a intenção do `--save-dev` (cosmético, não
quebra a suite, mas corrija).

```bash
node -e "const p=require('./package.json'); ['jest','jest-expo','@types/jest'].forEach(n => { if (p.dependencies?.[n]) console.log(n) })"
```

Para cada nome impresso, mova a entrada de `dependencies` para
`devDependencies` no `package.json` e rode `npm install` de novo para
atualizar o lockfile.
