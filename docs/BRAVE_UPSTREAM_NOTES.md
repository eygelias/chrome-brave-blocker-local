# Brave upstream study / Estudio de Brave upstream

Research snapshot: **2026-10-21**. Only official Brave, Mozilla, Chrome, EasyList, uBlock Origin, and AdGuard sources were used.

Corte de investigación: **2026-10-21**. Solo se usaron fuentes oficiales de Brave, Mozilla, Chrome, EasyList, uBlock Origin y AdGuard.

## Findings / Hallazgos

| Brave change | Official evidence | WebExtension decision |
|---|---|---|
| `adblock-rust` 0.13.3 and `brave-core` adblock update | [`adblock-rust` releases](https://github.com/brave/adblock-rust/releases), [adblock-resources update](https://github.com/brave/adblock-resources/commit/deab9cc5a6) | Upgraded catalog and compilation metadata to match latest Brave core v0.13.3 and component versions from installed Brave 155.1.97.59. |
| Brave Query Filter & Clean URLs (stripping tracking query parameters) | Installed Brave component `cemdlagocoimleflkfkjoihojfainiho` (Query Filter v1.0.191) & `afalakplffnnnlkncjhbmahjfjhmlkal` (Clean URLs v1.0.1545) | Extracted tracking parameter dictionaries and compiled a dedicated DNR ruleset (`ruleset_7`) using declarativeNetRequest `redirect` with `transform: { removeParams: [...] }`. Strips 60+ universal trackers (`fbclid`, `gclid`, `wbraid`, `srsltid`, `twclid`, `ttclid`, `mc_eid`, `msclkid`, etc.) and platform-specific trackers (Instagram `igsh`, YouTube `si`, Twitter/X `ref_src`, Amazon tracking tags, Facebook referral tokens) natively in Chrome and Firefox. |
| Brave YouTube Shields Suite additions | [`adblock-resources` resources/](https://github.com/brave/adblock-resources/tree/master/resources), installed Brave component `mfddibmblmbccpadfndgakiopmmhebop` (Resources v1.0.155) | Vendored and injected official Brave scripts: `brave-youtube-navigation-fix.js` (ensures strictly monotonic `performance.now` preventing player navigation freezes), `brave-youtube-theater-fix.js` (preserves `wide` theater mode cookie), `brave-youtube-playback-speed-fix.js` (persists custom speed buttons in sessionStorage), and `brave-video-bg-play-update.js` (prevents tab-switch pausing and suppresses "Are you still watching?" prompts). |
| Brave YouTube SABR Delay Fix updates | [adblock-resources `brave-yt-sabr-fix.js`](https://github.com/brave/adblock-resources/blob/master/resources/brave-yt-sabr-fix.js) | Vendored the latest updated version of Brave's mobile YouTube SABR backoff fix under MPL-2.0, active on `m.youtube.com`. |
| Brave Twitch Video Ad-Free Integration | [adblock-resources `vaft-ublock-origin.js`](https://github.com/brave/adblock-resources/blob/master/resources/vaft-ublock-origin.js), [brave-lists `brave-twitch.txt`](https://raw.githubusercontent.com/brave/adblock-lists/master/brave-lists/brave-twitch.txt) | Vendored `vaft-ublock-origin.js` and injected it in MAIN world on `twitch.tv` to bypass video ads without lag or stream drops, alongside Brave's Twitch network filter rules. |
| Brave CNAME First-Party Uncloaking Rules | [brave-lists `brave-firstparty-cname.txt`](https://raw.githubusercontent.com/brave/adblock-lists/master/brave-lists/brave-firstparty-cname.txt) | Incorporated Brave's extensive first-party CNAME tracking subdomains blocklist into Group 3, boosting Chrome network rules to 147,906. |
| Brave Invideo and Adblock Lists Updates | [Brave adblock-lists commits](https://github.com/brave/adblock-lists/commits/master) up to commit `ff303c3097cb0f195d535186b40287c2b3e8e7a6` | Sourced up-to-date filter lists across all groups with October 2026 data. |

## What is replicated / Qué se replica

- Sincronización completa con los catálogos y listas oficiales de Brave hasta octubre de 2026.
- **Protección contra rastreo en URL (Brave Query Filter & Clean URLs)**: eliminación nativa de parámetros de rastreo (`fbclid`, `gclid`, `wbraid`, `srsltid`, `twclid`, `si`, `igsh`, etc.) mediante reglas DNR `removeParams` sin retrasos ni rotura de navegación.
- **Suite completa de YouTube Shields de Brave**:
  - `brave-yt-sabr-fix.js`: eliminación del spinner de retardo SABR en móvil.
  - `brave-youtube-navigation-fix.js`: solución a cuelgues de navegación y Polymer en YouTube.
  - `brave-youtube-theater-fix.js`: preservación del modo cine (`wide` cookie).
  - `brave-youtube-playback-speed-fix.js`: persistencia de velocidad de reproducción personalizada.
  - `brave-video-bg-play-update.js`: reproducción en segundo plano sin pausa y supresión de avisos "¿Sigues ahí?".
  - `yt-main.js`: poda reforzada de JSON de anuncios en player, Shorts y recomendaciones.
- **Bloqueo de anuncios en vídeo de Twitch**: integración del scriptlet oficial `vaft-ublock-origin.js` de Brave.
- **Bloqueo first-party y CNAME uncloaking**: inclusión de `brave-firstparty-cname.txt`.
- Compilación auditable con `build-info.json` registrando SHA-256 y conteos exactos.

## What cannot be replicated / Qué no puede replicarse

- Brave's browser-native `adblock-rust` request interception, DAT cache, Rust memory layout, internal debug UI, DNS-level CNAME uncloaking heuristics, response-body stream rewriting in C++, or trusted scriptlet permission system.
- Full procedural cosmetic filtering and every uBO/Brave scriptlet that requires internal browser hooks not exposed by WebExtensions.
- Permanent unsigned installation in normal Firefox. Mozilla signing is required.

Chrome and Firefox extensions therefore provide the maximum practical **WebExtension approximation**, bringing Brave Shields' capabilities to other browsers safely.
