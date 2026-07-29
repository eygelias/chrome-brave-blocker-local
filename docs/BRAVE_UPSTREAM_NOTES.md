# Brave upstream study / Estudio de Brave upstream

Research snapshot: **2026-07-29**. Only official Brave, Mozilla, Chrome, EasyList, uBlock Origin, and AdGuard sources were used.

Corte de investigación: **2026-07-29**. Solo se usaron fuentes oficiales de Brave, Mozilla, Chrome, EasyList, uBlock Origin y AdGuard.

## Findings / Hallazgos

| Brave change | Official evidence | WebExtension decision |
|---|---|---|
| `adblock-rust` 0.13.0 added `$method`, iterative list parsing, structured debug data, and memory/performance work | [`adblock-rust` 0.13.0 changelog](https://github.com/brave/adblock-rust/blob/4d9176b7e7cee8731d76a1b07a58ba3952039a6b/CHANGELOG.md#0130---2026-07-09), [Brave Core update](https://github.com/brave/brave-core/commit/f1f2026057e678b1ab54ef5e994cbac5c92cb2af) | `$method` is preserved through `@adguard/dnr-converter` 1.1.0 as DNR `requestMethods`. Parser/debug/memory changes belong to Brave's native Rust engine and cannot be copied into Chrome/Firefox DNR. |
| `adblock-rust` 0.12.4 and 0.12.5 reject `url(` and `image-set(` in cosmetic styles | [`adblock-rust` changelog](https://github.com/brave/adblock-rust/blob/00b19a06508ddd4f3453779f8618983421ddf32b/CHANGELOG.md) | Cosmetic generator rejects `url(`, `image-set(`, declaration braces, comments, and remote-code patterns before producing CSS. |
| Brave moved to current default, privacy, first-party, cookie, mobile-promo, and regional catalogs | [Brave list catalog snapshot](https://github.com/brave/adblock-resources/blob/b77c5758b9c752b24a1d2184b978ffce1f8f4611/filter_lists/list_catalog.json) | Build uses desktop-compatible network/cosmetic material plus Spanish/Portuguese regional lists. Android-only and SugarCoat resource rules are intentionally omitted because plain DNR cannot execute Brave native redirect/scriptlet resources. |
| Brave added and repeatedly hardened a YouTube SABR backoff fix | [Current SABR resource](https://github.com/brave/adblock-resources/blob/b77c5758b9c752b24a1d2184b978ffce1f8f4611/resources/brave-yt-sabr-fix.js), [uBO coexistence fix](https://github.com/brave/adblock-resources/pull/336) | Exact MPL-2.0 Brave script is vendored with notice and loaded in MAIN world only on `m.youtube.com`, matching Brave's cautious current rollout. Existing player-response pruning remains for desktop YouTube. |
| Brave enabled the SABR fix on mobile YouTube after automated/manual tests | [Brave list PR #2967](https://github.com/brave/adblock-lists/pull/2967), [commit `8729bd9`](https://github.com/brave/adblock-lists/commit/8729bd97b810af36df3912291e184d64e84d1152) | Firefox and Chrome manifests load the vendored SABR fix on mobile YouTube only. Desktop enablement is deliberately avoided because Brave documented an extension-coexistence refresh-loop risk. |
| Brave added adblock debug mode and richer internal diagnostics | [Brave Core commit `541900e`](https://github.com/brave/brave-core/commit/541900ea90dd048f364d3416ca84c6ee0358a598) | Native-only UI is not copied. Builds instead include `build-info.json` with source URLs, SHA-256 hashes, versions, and rule counts for auditability. |
| Brave switched request matching to the request initiator | [Brave Core commit `04d22c8`](https://github.com/brave/brave-core/commit/04d22c890676332d280dcb3f86d12905577f1480) | Browser DNR already exposes initiator/domain conditions. Latest converter is used rather than adding a custom request interceptor forbidden by Chrome MV3. |
| Brave caches DAT files and shares parsed resource storage | [DAT cache commit](https://github.com/brave/brave-core/commit/75ddc804041b1e0c6877a5a1836e7c1bccd4ea04), [resource sharing commit](https://github.com/brave/brave-core/commit/aa8d7fab8c5e80c4ddebb01b57500806d2164d39) | Native-only optimization. Static DNR rules are compiled once at build time and evaluated by each browser's native DNR engine, which is the closest extension-safe equivalent. |

## What is replicated / Qué se replica

- Current Brave-compatible default/privacy/first-party network sources.
- Spanish and Portuguese regional blocking.
- Cookie-notice and mobile-promotion lists enabled in Brave's catalog.
- `$method`, `$urltransform`, `$removeparam`, headers, and other modifiers when DNR can express them.
- Generic cosmetic selectors with Brave-inspired CSS injection hardening.
- YouTube player JSON ad-field pruning in MAIN world.
- Brave's current mobile YouTube SABR backoff script, under MPL-2.0.
- Bundled local rules: no runtime filter download, telemetry, or remote JavaScript.

## What cannot be replicated / Qué no puede replicarse

- Brave's browser-native `adblock-rust` request interception, DAT cache, Rust memory layout, internal debug UI, CNAME/native first-party heuristics, response-body rewriting, or trusted scriptlet permission system.
- Full procedural cosmetic filtering and every uBO/Brave scriptlet.
- Guaranteed YouTube blocking: YouTube can change first-party payloads and SABR behavior server-side.
- Permanent unsigned installation in normal Firefox. Mozilla signing is required.

Chrome and Firefox extensions therefore provide the maximum practical **WebExtension approximation**, not 100% Brave Shields parity.

Las extensiones ofrecen la mejor **aproximación práctica mediante WebExtensions**, no paridad total con Brave Shields.

## Firefox static-rule limit / Límite estático de Firefox

Firefox currently sets `GUARANTEED_MINIMUM_STATIC_RULES` to **30,000** and still carries a TODO to allow extensions to exceed it. Evidence: [`ExtensionDNRLimits.sys.mjs`](https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/extensions/ExtensionDNRLimits.sys.mjs). The Firefox build is therefore capped at exactly 30,000 rules: all exceptions and high-priority rules are retained first, then domain and generic blocking rules are sampled evenly within semantic budgets. Selection details are written to `firefox/build-info.json`.

Firefox fija actualmente `GUARANTEED_MINIMUM_STATIC_RULES` en **30.000** y aún mantiene pendiente permitir que una extensión exceda ese límite. Por eso la compilación Firefox queda limitada a 30.000 reglas: primero conserva excepciones y reglas prioritarias; luego selecciona uniformemente reglas de dominio y genéricas dentro de presupuestos semánticos. El desglose queda en `firefox/build-info.json`.

## DNR conversion safety / Seguridad de conversión DNR

v3.0.0 was withdrawn after real Chrome testing exposed over-broad generated rules. Some upstream rules used modifiers such as `ipaddress`, `from`, `strict1p`, or `strict3p` that DNR cannot represent. The converter silently omitted those constraints while retaining the blocking action; several results matched every `main_frame` request.

v3.0.1 fails closed: rules containing unrepresentable modifiers are discarded before conversion. This explicitly includes known silently ignored modifiers such as `$app` and `$referrerpolicy`. A second structural guard rejects anchor-only universal URL filters (`|*`, `*|`, `|*|`, and equivalents), protocol-only universal filters, and every unscoped regex block. `scripts/test_converter_safety.mjs` reproduces these failure patterns, including Windows CRLF inputs, and runs through `npm test`. Sanitization and pruning totals are recorded in each `build-info.json`.

v3.0.0 fue retirada después de que una prueba real en Chrome revelara reglas generadas demasiado amplias. Algunos filtros upstream usaban modificadores como `ipaddress`, `from`, `strict1p` o `strict3p`, imposibles de representar mediante DNR. El conversor omitía silenciosamente esas condiciones pero conservaba el bloqueo; varias reglas resultantes coincidían con toda navegación `main_frame`.

v3.0.1 aplica cierre seguro: descarta antes de convertir reglas con modificadores no representables, incluidos los modificadores conocidos que el conversor ignora silenciosamente, como `$app` y `$referrerpolicy`. Una segunda guarda rechaza filtros URL universales formados solo por anclas (`|*`, `*|`, `|*|` y equivalentes), filtros universales basados solo en protocolo y cualquier regex sin alcance de dominio. `scripts/test_converter_safety.mjs` reproduce estos patrones, incluso con entradas CRLF de Windows, y se ejecuta mediante `npm test`. Los totales descartados quedan registrados en cada `build-info.json`.

## Browser references / Referencias de navegadores

- [Chrome Declarative Net Request](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest)
- [Mozilla `declarative_net_request` manifest key](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/manifest.json/declarative_net_request)
- [Mozilla content-script `world: MAIN`](https://developer.mozilla.org/docs/Mozilla/Add-ons/WebExtensions/manifest.json/content_scripts#world)
- [Mozilla temporary installation](https://extensionworkshop.com/documentation/develop/temporary-installation-in-firefox/)
- [Mozilla signing and distribution](https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/)
