(() => {
  'use strict';

  const adKeys = new Set([
    'adPlacements', 'playerAds', 'adSlots', 'adBreakHeartbeatParams',
    'adEngagementPanels', 'adSafetyReason', 'adTracking'
  ]);

  const shouldCleanUrl = (url) => {
    url = String(url || '');
    return /\/youtubei\/v1\/(player|next|browse|get_watch)|\/player(?:\?|$)|\/watch\?/.test(url);
  };

  const cleanJson = (root) => {
    if (!root || typeof root !== 'object') return root;

    const stack = [root];
    const seen = new WeakSet();
    while (stack.length) {
      const obj = stack.pop();
      if (!obj || typeof obj !== 'object' || seen.has(obj)) continue;
      seen.add(obj);

      if (obj.playerConfig?.adConfig) obj.playerConfig.adConfig = {};
      if (obj.playbackTracking?.adTracking) delete obj.playbackTracking.adTracking;

      if (Array.isArray(obj)) {
        for (let i = obj.length - 1; i >= 0; i--) {
          const v = obj[i];
          if (v && typeof v === 'object' && (
            v.adSlotRenderer || v.displayAdRenderer || v.promotedSparklesWebRenderer ||
            v.companionAdRenderer || v.playerLegacyDesktopWatchAdsRenderer ||
            v.instreamVideoAdRenderer || v.videoAdRenderer ||
            v.command?.reelWatchEndpoint?.adClientParams?.isAd
          )) obj.splice(i, 1);
          else stack.push(v);
        }
        continue;
      }

      for (const key of Object.keys(obj)) {
        if (adKeys.has(key)) delete obj[key];
        else if (key === 'playerResponse' && obj[key] && typeof obj[key] === 'object') {
          cleanJson(obj[key]);
          stack.push(obj[key]);
        } else stack.push(obj[key]);
      }
    }
    return root;
  };

  const cleanText = (text, url = '') => {
    if (typeof text !== 'string') return text;
    if (!shouldCleanUrl(url) && !/(adPlacements|playerAds|adSlots)/.test(text)) return text;
    try { return JSON.stringify(cleanJson(JSON.parse(text))); }
    catch {
      return text
        .replace(/,"adPlacements":\[[\s\S]*?\](?=,)/g, '')
        .replace(/,"playerAds":\[[\s\S]*?\](?=,)/g, '')
        .replace(/,"adSlots":\[[\s\S]*?\](?=,)/g, '')
        .replace(/,"adBreakHeartbeatParams":\{[\s\S]*?\}(?=,)/g, '')
        .replace(/"adPlacements"/g, '"no_ads"')
        .replace(/"adSlots"/g, '"no_ads"');
    }
  };

  const defineCleanWindowProp = (name) => {
    let value;
    try {
      Object.defineProperty(window, name, {
        configurable: true,
        get() { return value; },
        set(v) { value = cleanJson(v); }
      });
    } catch {}
  };

  defineCleanWindowProp('ytInitialPlayerResponse');
  defineCleanWindowProp('playerResponse');

  const nativeParse = JSON.parse;
  JSON.parse = new Proxy(nativeParse, {
    apply(target, thisArg, args) {
      const out = Reflect.apply(target, thisArg, args);
      if (typeof args[0] === 'string' && /(adPlacements|playerAds|adSlots)/.test(args[0])) return cleanJson(out);
      return out;
    }
  });

  const nativeFetch = window.fetch;
  window.fetch = async function(input, init) {
    const response = await nativeFetch.apply(this, arguments);
    const url = typeof input === 'string' ? input : input?.url || response.url;
    if (!shouldCleanUrl(url)) return response;
    const text = await response.clone().text();
    const cleaned = cleanText(text, url);
    if (cleaned === text) return response;
    const headers = new Headers(response.headers);
    headers.set('content-length', String(new Blob([cleaned]).size));
    return new Response(cleaned, { status: response.status, statusText: response.statusText, headers });
  };

  const nativeResponseJson = Response.prototype.json;
  Response.prototype.json = async function() {
    const data = await nativeResponseJson.apply(this, arguments);
    return shouldCleanUrl(this.url) ? cleanJson(data) : data;
  };

  const nativeOpen = XMLHttpRequest.prototype.open;
  const nativeSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method, url) {
    this.__braveLikeUrl = url;
    return nativeOpen.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function() {
    this.addEventListener('readystatechange', function() {
      if (this.readyState !== 4) return;
      const url = this.__braveLikeUrl || this.responseURL;
      if (!shouldCleanUrl(url)) return;
      const cleaned = cleanText(this.responseText, url);
      if (cleaned === this.responseText) return;
      try {
        Object.defineProperty(this, 'responseText', { value: cleaned });
        Object.defineProperty(this, 'response', { value: cleaned });
      } catch {}
    });
    return nativeSend.apply(this, arguments);
  };

  const fallbackSkip = () => {
    const player = document.querySelector('.html5-video-player.ad-showing');
    if (!player || document.activeElement?.closest?.('ytd-searchbox, input, textarea')) return;
    document.querySelector('.ytp-ad-skip-button,.ytp-ad-skip-button-modern,.ytp-skip-ad-button,button[aria-label*="Saltar"],button[aria-label*="Omitir"],button[aria-label*="Skip"]')?.click();
  };
  setInterval(fallbackSkip, 500);
})();
