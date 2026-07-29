(() => {
  'use strict';

  if (globalThis.__braveLikeBlockerLocalLoaded) return;
  Object.defineProperty(globalThis, '__braveLikeBlockerLocalLoaded', { value: true });

  const adKeys = new Set([
    'adPlacements', 'playerAds', 'adSlots', 'adBreakHeartbeatParams',
    'adEngagementPanels', 'adSafetyReason', 'adTracking'
  ]);

  const shouldCleanUrl = (url) => {
    url = String(url || '');
    return /\/youtubei\/v1\/(?:player|next|browse|get_watch|reel\/reel_item_watch|reel\/reel_watch_sequence)(?:[/?]|$)|\/player(?:\?|$)|\/watch\?/.test(url);
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
          const value = obj[i];
          if (value && typeof value === 'object' && (
            value.adSlotRenderer || value.displayAdRenderer || value.promotedSparklesWebRenderer ||
            value.companionAdRenderer || value.playerLegacyDesktopWatchAdsRenderer ||
            value.instreamVideoAdRenderer || value.videoAdRenderer || value.adSurveyRenderer ||
            value.command?.reelWatchEndpoint?.adClientParams?.isAd
          )) obj.splice(i, 1);
          else stack.push(value);
        }
        continue;
      }

      for (const key of Object.keys(obj)) {
        if (adKeys.has(key)) delete obj[key];
        else stack.push(obj[key]);
      }
    }
    return root;
  };

  const cleanText = (text, url = '') => {
    if (typeof text !== 'string') return text;
    if (!shouldCleanUrl(url) && !/(adPlacements|playerAds|adSlots)/.test(text)) return text;
    try { return JSON.stringify(cleanJson(JSON.parse(text))); }
    catch { return text; }
  };

  const defineCleanWindowProp = (name) => {
    let value = cleanJson(globalThis[name]);
    try {
      Object.defineProperty(globalThis, name, {
        configurable: true,
        get() { return value; },
        set(next) { value = cleanJson(next); }
      });
    } catch {}
  };

  defineCleanWindowProp('ytInitialPlayerResponse');
  defineCleanWindowProp('playerResponse');

  const nativeParse = JSON.parse;
  JSON.parse = new Proxy(nativeParse, {
    apply(target, thisArg, args) {
      const output = Reflect.apply(target, thisArg, args);
      return typeof args[0] === 'string' && /(adPlacements|playerAds|adSlots)/.test(args[0])
        ? cleanJson(output)
        : output;
    }
  });

  const nativeFetch = globalThis.fetch;
  globalThis.fetch = async function(input) {
    const response = await nativeFetch.apply(this, arguments);
    const url = typeof input === 'string' ? input : input?.url || response.url;
    if (!shouldCleanUrl(url)) return response;

    let text;
    try { text = await response.clone().text(); }
    catch { return response; }
    const cleaned = cleanText(text, url);
    if (cleaned === text) return response;

    const headers = new Headers(response.headers);
    headers.delete('content-length');
    const output = new Response(cleaned, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
    try {
      Object.defineProperty(output, 'url', { value: response.url, configurable: true });
      Object.defineProperty(output, 'redirected', { value: response.redirected, configurable: true });
      Object.defineProperty(output, 'type', { value: response.type, configurable: true });
    } catch {}
    return output;
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
    const cleanResponse = function() {
      if (this.readyState !== 4) return;
      this.removeEventListener('readystatechange', cleanResponse);
      if (this.responseType && this.responseType !== 'text') return;
      const url = this.__braveLikeUrl || this.responseURL;
      if (!shouldCleanUrl(url)) return;
      let original;
      try { original = this.responseText; }
      catch { return; }
      const cleaned = cleanText(original, url);
      if (cleaned === original) return;
      try {
        Object.defineProperty(this, 'responseText', { value: cleaned });
        Object.defineProperty(this, 'response', { value: cleaned });
      } catch {}
    };
    this.addEventListener('readystatechange', cleanResponse);
    return nativeSend.apply(this, arguments);
  };

  const fallbackSkip = () => {
    const player = document.querySelector('.html5-video-player.ad-showing');
    const active = document.activeElement;
    if (!player || active?.closest?.('ytd-searchbox, input, textarea, [contenteditable="true"]')) return;
    document.querySelector(
      '.ytp-ad-skip-button,.ytp-ad-skip-button-modern,.ytp-skip-ad-button,' +
      'button[aria-label*="Saltar"],button[aria-label*="Omitir"],button[aria-label*="Skip"]'
    )?.click();
  };
  setInterval(fallbackSkip, 750);
})();
