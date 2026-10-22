# Chrome Web Store Metadata & Publishing Reference

> Single source of truth for Chrome Web Store listing, permissions justification, privacy policy disclosures, and version history for `chrome-brave-blocker-local`.

---

## Listing Metadata

- **Extension Name**: Brave-like Blocker Local
- **Version**: 3.1.0
- **Summary / Description**:
  Bloqueador local inspirado en Brave | Local ad/tracker blocker inspired by Brave.
- **Detailed Description**:
  Brave-like Blocker Local brings the ad blocking, tracker protection, and media optimization of Brave Shields to Chrome and Chromium browsers.

  Key Features:
  - Native network request blocking powered by Declarative Net Request (DNR) with over 147,000 rules.
  - Sourced from current Brave Shields, EasyList, EasyPrivacy, uBlock Origin, and AdGuard catalogs.
  - URL Tracking Protection (Clean URLs): Automatically strips tracking parameters (fbclid, gclid, wbraid, srsltid, twclid, si, igsh) upon navigation.
  - YouTube Shields Suite: Resolves player navigation freezes, preserves theater mode, saves playback speed settings, eliminates mobile SABR delays, and enables background playback.
  - Twitch Video Ad-Free: Bundles Brave's official VAFT scriptlet for uninterrupted video streams.
  - Zero Telemetry: Completely silent, local-only, no server connections, no user accounts, no analytics.

---

## Permissions Justification

| Permission | Justification |
|---|---|
| `declarativeNetRequest` | Required to perform native, efficient browser-level blocking of advertising and tracking network requests using bundled local rule sets. |
| `host_permissions: ["<all_urls>"]` | Required by Declarative Net Request to evaluate network blocking and redirect actions (including tracking query parameter stripping) across visited websites, and to apply cosmetic CSS hiding and YouTube/Twitch player fix scriptlets locally. |

---

## Privacy & Data Use Disclosure

- **Data Collection**: No data collected (`none`).
- **Data Transmission**: None. All rules and scripts are packaged locally within the extension.
- **Third-Party Services**: None. No analytics, tracking, or remote endpoints are contacted.
- **Single Purpose Compliance**: The extension's single purpose is blocking unwanted ads, trackers, and playback disruptions across websites using local rules.

---

## Version History

### v3.1.0 (2026-10-21)
- Upgraded to latest Brave upstream components and filter catalogs (October 2026).
- Added Brave Query Filter & Clean URLs: native stripping of tracking query tokens via DNR `removeParams`.
- Added complete YouTube Shields Suite: navigation fix (`performance.now` strictly monotonic), theater mode cookie persistence, playback speed persistence, and video background play.
- Added Twitch Video Ad-Free (`vaft-ublock-origin.js`).
- Added Brave first-party CNAME uncloaking rules (`brave-firstparty-cname.txt`), expanding Chrome network rules to 147,906.
- Firefox build optimized to 30,000 static rules with 100% essential rule retention.

### v3.0.1 (2026-07-29)
- Hotfix release discarding unrepresentable DNR modifiers and unscoped block patterns.
- Added Firefox extension build.
- Added Brave YouTube SABR backoff fix for mobile YouTube.
- Added Spanish and Portuguese regional filters.
