# Third-party notices / Avisos de terceros

This project is unofficial and is not affiliated with, endorsed by, or sponsored by Brave Software, Google, Mozilla, EasyList, uBlock Origin, or AdGuard.

Este proyecto no es oficial ni está afiliado, respaldado o patrocinado por Brave Software, Google, Mozilla, EasyList, uBlock Origin o AdGuard.

## Project code / Código del proyecto

Project-authored code is distributed under **GPL-3.0-only**. See [`LICENSE`](LICENSE).

El código propio del proyecto se distribuye bajo **GPL-3.0-only**. Consulta [`LICENSE`](LICENSE).

## Brave sources / Fuentes de Brave

- Brave filter catalog and lists: [brave/adblock-resources](https://github.com/brave/adblock-resources) (commit `6da9b247c32b55f1ff4d1b8764e5256e6ca08969`) and [brave/adblock-lists](https://github.com/brave/adblock-lists) (commit `ff303c3097cb0f195d535186b40287c2b3e8e7a6`), **MPL-2.0**.
- Vendored YouTube SABR delay fix (`brave-yt-sabr-fix.js`), **MPL-2.0**.
- Vendored YouTube navigation fix (`brave-youtube-navigation-fix.js`), **MPL-2.0**.
- Vendored YouTube theater mode cookie persistence fix (`brave-youtube-theater-fix.js`), **MPL-2.0**.
- Vendored YouTube playback speed persistence fix (`brave-youtube-playback-speed-fix.js`), **MPL-2.0**.
- Vendored Video background play fix (`brave-video-bg-play-update.js`): based on Mozilla video-bg-play, **MIT**.
- Vendored Twitch video ad-free solution (`vaft-ublock-origin.js`): based on TwitchAdSolutions / Brave adblock-resources, **GPL-3.0** / **MPL-2.0**.
- Brave Query Filter and Clean URLs tracking parameters specifications: derived from Brave Shields components `cemdlagocoimleflkfkjoihojfainiho` (Query Filter) and `afalakplffnnnlkncjhbmahjfjhmlkal` (Local Data Files / Clean URLs), **MPL-2.0**.
- Full MPL-2.0 text: [`LICENSES/MPL-2.0.txt`](LICENSES/MPL-2.0.txt).
- Full MIT text: [`LICENSES/MIT.txt`](LICENSES/MIT.txt).

Brave trademarks and logos are not licensed by MPL-2.0 and are not used to imply endorsement.

## Filter lists and build tools / Listas y herramientas

Generated DNR and cosmetic artifacts include converted material from these sources. Their original terms continue to apply:

- [uBlock Origin uAssets](https://github.com/uBlockOrigin/uAssets): **GPL-3.0**.
- [EasyList, EasyPrivacy, EasyList Spanish, and Fanboy lists](https://easylist.to/pages/licence.html): dual-licensed under **GPL-3.0-or-later** or **CC-BY-SA-3.0-or-later**. Attribution: **The EasyList authors — https://easylist.to/**.
- [AdGuard Filters](https://github.com/AdguardTeam/AdguardFilters): **GPL-3.0**.
- [Brave adblock lists](https://github.com/brave/adblock-lists): **MPL-2.0**.
- [URLhaus filter](https://gitlab.com/malware-filter/urlhaus-filter): **MIT**, Copyright (c) 2023 Ming Di Leom.
- [`@adguard/dnr-converter`](https://github.com/AdguardTeam/tsurlfilter/tree/master/packages/dnr-converter): build-time tool, **GPL-3.0-only**.
- [`web-ext`](https://github.com/mozilla/web-ext): validation and packaging tool, **MPL-2.0**.

Exact source URLs and SHA-256 hashes used for a build are recorded in each browser folder's `build-info.json`.

Las URL exactas y hashes SHA-256 usados en cada compilación quedan registrados en `build-info.json` dentro de cada carpeta del navegador.

## URLhaus MIT notice

```text
MIT License

Copyright (c) 2023 Ming Di Leom

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
