# Mobile no simulador, no emulador e no aparelho

O `{project-name}-mobile` nasce pronto para rodar fora do Expo Go: os alvos
`mobile-*` do Makefile buildam e instalam o app de um Mac, sem loja, sem conta
paga da Apple e sem EAS. Este arquivo explica o caminho, o que a máquina e o
aparelho precisam e por que cada contorno do Makefile existe. Cada contorno
custou depuração real; não o "simplifique" sem ler o motivo.

## O caminho: prebuild + run, sem loja

```
expo prebuild --platform <ios|android>        gera ios/ ou android/ (fora do git)
expo run:ios                                  Debug + Metro, no simulador
expo run:ios --device --configuration Release Release, no iPhone no cabo
expo run:android                              Debug + Metro, no emulador
expo run:android --device --variant release   Release, no Android no cabo
```

| Alvo | Onde | Build | Precisa de Metro? | Fala com |
|---|---|---|---|---|
| `mobile-ios-sim` | simulador iOS | Debug | sim (o próprio `run` sobe) | api e web locais |
| `mobile-android-emu` | emulador Android | Debug | sim (via `adb reverse`) | api e web locais |
| `mobile-ios-device` | iPhone no cabo | Release | não | o que `EXPO_PUBLIC_*` apontar |
| `mobile-android-device` | Android no cabo | Release | não | o que `EXPO_PUBLIC_*` apontar |

O build **Release embute o JS** no binário: o aparelho não precisa de Expo Go
nem de um Metro de pé, e o app continua abrindo depois de desconectar o cabo.
É o que se quer para conferir o app como o usuário vai vê-lo.

`ios/` e `android/` são **gerados** pelo prebuild e ficam fora do git (o
`gitignore-extra.template` já os ignora). Toda configuração nativa mora no
`app.json`/`app.config.ts` e em config plugins, nunca em edição à mão dessas
pastas — os alvos de aparelho rodam `prebuild --clean`, que as apaga e refaz.

Os alvos de simulador e emulador passam `EXPO_PUBLIC_API_URL` e
`EXPO_PUBLIC_WEB_URL` apontando para `localhost`. São os nomes que o app deve
ler quando começar a falar com o backend; o scaffold não escreve esse código.
Nos alvos de aparelho o Makefile não passa nada: o app usa o que estiver no
ambiente ou o default que ele mesmo definir (um ambiente publicado, tipicamente),
porque `localhost` no aparelho é o próprio aparelho.

## Falhar cedo

Todo alvo confere o que precisa **antes** do prebuild, que leva minutos:

- `doctor-mobile-ios`: `xcodebuild -version` (Xcode instalado e selecionado) e
  `pod` no PATH (o prebuild do iOS roda `pod install`).
- `doctor-mobile-android`: `adb` no PATH e `ANDROID_HOME` definido.
- `mobile-ios-device`: `APPLE_TEAM_ID` definido, `expo.ios.bundleIdentifier`
  no `app.json` e um iPhone **pareado e no cabo** segundo
  `xcrun devicectl list devices` (o mesmo que o Expo usa; ver "Achar o
  iPhone"). O UDID é conferido de novo logo antes do `expo run:ios`, porque o
  aparelho pode cair durante os minutos do prebuild.
- `mobile-android-*`: `adb devices` filtrado por `$2=="device"` — `unauthorized`
  e `offline` não contam. Sem `ANDROID_SERIAL`, exige **um** aparelho só; com
  ele, exige aquele serial.

Cada mensagem diz o que fazer, não só o que faltou.

## iPhone com Apple ID gratuito

1. Xcode > Settings > Accounts: adicione o Apple ID e anote o **Team ID** do
   "Personal Team".
2. `export APPLE_TEAM_ID=...` — **só por variável de ambiente**. O
   `app.config.ts` (do [template](../templates/mobile/app.config.ts.template))
   o injeta em `ios.appleTeamId`; o ID nunca entra no repositório.
3. No iPhone: Ajustes > Privacidade e Segurança > **Modo Desenvolvedor** ligado
   (pede reinício).
4. Cabo, iPhone destravado, aceite **"Confiar neste computador?"** e digite a
   senha do aparelho. Sem isso o Mac não o lista como conectado.
5. `make mobile-ios-device`, com o iPhone **destravado** durante o build.
6. Na primeira instalação: Ajustes > Geral > VPN e Gerenciamento de
   Dispositivos > toque no perfil do Apple ID > **Confiar**. Até lá o `make`
   instala o app mas termina com "Unable to launch ... profile has not been
   explicitly trusted by the user", e o iPhone mostra "Desenvolvedor não
   confiável". Depois de confiar, abra o app pelo ícone.

Com Apple ID gratuito o perfil vence em **7 dias**: o app para de abrir e basta
rodar o `make` de novo, que renova o perfil sozinho (próxima seção). É limite
da Apple, não defeito do build.

### Achar o iPhone: `devicectl`, não `xctrace`

`xcrun xctrace list devices` joga o iPhone em "Devices Offline" sempre que a
tela bloqueia, **mesmo no cabo** — o alvo falharia a cada descanso de tela. O
Makefile lê o JSON do `xcrun devicectl list devices --json-output /dev/stdout`
(direto no pipe, sem arquivo temporário) e pega o primeiro aparelho com
`platform == "iOS"`, `pairingState == "paired"` e `transportType == "wired"`;
o UDID dele está em `hardwareProperties.udid`. `IOS_DEVICE=<udid>` fixa um
aparelho quando houver mais de um.

### Passe o UDID ao `expo run:ios`, sempre

- `--device` sem valor abre um seletor (o próprio Mac aparece como destino) e
  falha sem terminal interativo.
- `--device ""` — o que sai quando a busca do UDID não acha nada — **cai em
  silêncio no simulador ligado**: o build "funciona" e o app vai para o lugar
  errado.

Por isso a receita confere `[ -n "$udid" ]` imediatamente antes do run e roda
`expo run:ios --device "$udid" --configuration Release`.

### Perfil de provisionamento: "No profiles for '<bundle>' were found"

O Expo só passa `-allowProvisioningUpdates` ao `xcodebuild` quando é ele quem
escolhe o time. Com o `appleTeamId` fixado pelo `APPLE_TEAM_ID`, não passa, e
sem um perfil já baixado o build falha com `No profiles for '<bundle>' were
found`.

O alvo procura em `~/Library/Developer/Xcode/UserData/Provisioning Profiles`
um perfil cujo `Entitlements.application-identifier` seja
`$APPLE_TEAM_ID.<bundle>` (lido com `security cms -D` + `plutil -extract`) e
cujo `ExpirationDate` ainda não passou. O bundle vem de
`expo.ios.bundleIdentifier` no `app.json`. Sem perfil válido, roda **uma vez**:

```bash
xcodebuild -workspace <app>.xcworkspace -scheme <app> -configuration Release \
  -destination "id=$udid" -allowProvisioningUpdates -allowProvisioningDeviceRegistration \
  DEVELOPMENT_TEAM="$APPLE_TEAM_ID" build
```

que pede o perfil à Apple (o Apple ID precisa estar em Xcode > Settings >
Accounts), e confere de novo. O `expo run:ios` que vem depois só reaproveita o
perfil. É o mesmo passo que renova o perfil de 7 dias do Apple ID gratuito.

### "ddiServicesAvailable: false"

O Expo diz que não acha o aparelho, e o `devicectl` mostra
`ddiServicesAvailable: false`: a imagem de desenvolvedor não está montada no
iPhone. Monte uma vez com:

```bash
xcrun devicectl device info ddiServices --device <identifier do devicectl>
```

## Repositório dentro do iCloud: o CodeSign falha

Se o repositório estiver em `~/Documents` ou `~/Desktop` com "Pastas Desktop e
Documentos" do iCloud ligado, o File Provider marca o
`ExpoModulesJSI.framework` recém-buildado com xattrs (FinderInfo) e o CodeSign
falha com:

```
resource fork, Finder information, or similar detritus not allowed
```

`xattr -cr` antes do build não resolve (o iCloud remarca), e nem uma pasta
`*.nosync` escapa. O contorno do Makefile:

1. `EXPO_CUSTOM_BUILD_ROOT` aponta para fora do iCloud
   (`~/Library/Caches/{project-name}-mobile/expo-modules-jsi-<versão>`). O
   script de build do pacote `expo-modules-jsi` lê essa variável. A pasta é
   **chaveada pela versão** do `expo-modules-jsi` instalado: subir o `expo`
   gera um cache novo em vez de reaproveitar um xcframework de outra versão.
2. `mobile-ios-nosync` copia o xcframework pronto de volta para
   `node_modules/expo-modules-jsi/apple/Products` com `rsync` (o podspec lê dali;
   link simbólico não serve, o CocoaPods deixa de ver o xcframework), limpa os
   xattrs e refaz o `pod install`.
3. **Na primeira vez numa máquina o cache está vazio**: o primeiro
   `expo run:ios` gera o xcframework no cache e falha no CodeSign. O alvo então
   roda o `nosync` e tenta de novo, uma vez. A repetição **só** acontece quando
   o cache estava vazio antes da primeira tentativa — com o cache pronto, uma
   falha é falha de verdade e o `make` para na primeira, sem esconder erro.

Fora do iCloud o contorno é inofensivo: o build só usa outro diretório.

## Locale UTF-8

O Ruby do CocoaPods morre em `Encoding::CompatibilityError` quando o shell não
está em UTF-8 (comum em terminais de IDE e em shells não interativos). Os
alvos exportam `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8` no prebuild, no
`run:ios` e no `pod install`. Rodando qualquer um deles na mão, exporte você.

## Emulador Android: `adb reverse`, não `10.0.2.2`

O emulador chega ao Mac por `10.0.2.2`, mas trocar `localhost` por esse
endereço quebra tudo que compara URL: o `redirect_uri` de OAuth deixa de bater
com o cadastrado, URLs de mídia que o backend devolve com `localhost` não
abrem. Em vez disso, `mobile-android-emu` faz `adb reverse` das portas da api,
do web e do Metro (`8081`): dentro do emulador, `localhost:<porta>` passa a ser
o Mac, e o app usa os mesmos endereços do simulador iOS.

Com emulador e aparelho conectados ao mesmo tempo, `adb reverse` falha com
`more than one device/emulator`. O Makefile para antes, pedindo
`ANDROID_SERIAL=<serial>` (o que `adb devices` mostra, por exemplo
`emulator-5554`); com ele, passa `-s <serial>` ao `adb` e `--device <serial>` ao
`expo run:android`.

## Requisitos da máquina, num clone novo

- **iOS:** Xcode (e `sudo xcode-select -s /Applications/Xcode.app`), CocoaPods
  (`brew install cocoapods`). Para o simulador, o runtime do iOS: a partir do
  Xcode 26 ele não vem junto (Xcode > Settings > Components).
- **Android:** Android Studio com SDK, Platform-Tools e um AVD;
  `ANDROID_HOME=$HOME/Library/Android/sdk` e `$ANDROID_HOME/platform-tools` no
  PATH. Se o Gradle do React Native recusar o JDK do sistema, use o do Android
  Studio: `JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"`.
- **Typecheck:** num clone novo, rode `npx expo start` uma vez e saia antes do
  primeiro `tsc` (ver [armadilhas](./pitfalls.md), "Frontends").
- O Expo abre o simulador por `osascript`; na primeira vez o macOS pede
  permissão de Automação para o terminal. Negada, o build termina mas o app não
  abre sozinho.

## O app instala e fecha ao abrir

Quase sempre é módulo pré-compilado do Expo fora de versão: o Expo distribui
alguns módulos (`expo-video`, por exemplo) já compilados contra uma versão
exata do `expo-modules-core`, e versões de **patch** dentro do mesmo SDK podem
não casar. O sintoma é `dyld: Symbol not found` no crash report
(`~/Library/Logs/DiagnosticReports/<app>-*.ips`), não erro de build.

`npx expo install --check` (no `make doctor-mobile`) acusa o desencontro e
`npx expo install --fix` o corrige. Desligar os pré-compilados não é saída
confiável: compilar o `expo-modules-core` do fonte pode travar o compilador
Swift do Xcode.

### Crash de JS no Release: pegue a mensagem pelo console

Se o app abre e cai depois (num toque, logo após o login), o mais provável é
erro de JavaScript: no Release ele vira `RCTFatal` e mata o app. O `.ips` do
crash report **não traz** a mensagem do erro JS. Para vê-la, lance o app pelo
`devicectl` com o console ligado e repita o caminho:

```bash
xcrun devicectl device process launch --console --terminate-existing \
  --device <identifier do devicectl> <bundle id>
```

A razão da `RCTFatalException` (por exemplo `undefined is not a function`)
aparece no terminal. Um caso real: a lista vinha do backend como
`{ "videos": [...] }`, o app tratava como array, e os testes não pegaram
porque mockavam o array cru (ver [armadilhas](./pitfalls.md), "Mocks no formato
real da resposta").
