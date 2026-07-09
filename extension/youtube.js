(() => {
  'use strict';

  const skipSelectors = [
    '.ytp-ad-skip-button',
    '.ytp-ad-skip-button-modern',
    '.ytp-skip-ad-button',
    'button[aria-label*="Skip"]',
    'button[aria-label*="Saltar"]',
    'button[aria-label*="Omitir"]'
  ];

  let typingUntil = 0;

  const markTyping = () => { typingUntil = Date.now() + 5000; };
  const visible = (el) => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));

  const userTyping = () => {
    if (Date.now() < typingUntil) return true;
    const el = document.activeElement;
    if (!el) return false;
    return el.tagName === 'INPUT'
      || el.tagName === 'TEXTAREA'
      || el.isContentEditable
      || !!el.closest?.('ytd-searchbox, #search, form#search-form');
  };

  const clickSkip = () => {
    for (const selector of skipSelectors) {
      const button = [...document.querySelectorAll(selector)].find(visible);
      if (button) button.click();
    }
  };

  const adShowing = () => {
    const player = document.querySelector('.html5-video-player');
    return !!(player && player.classList.contains('ad-showing'));
  };

  const tick = () => {
    if (userTyping()) return;

    clickSkip();
    if (!adShowing()) return;

    const video = document.querySelector('video');
    if (!video) return;

    // ponytail: only touches video while YouTube player is in ad mode and user is not typing.
    video.muted = true;
    video.playbackRate = 16;
    if (Number.isFinite(video.duration) && video.duration > 1) {
      video.currentTime = Math.max(video.currentTime, video.duration - 0.05);
    }
    video.play().catch(() => {});
    clickSkip();
  };

  document.addEventListener('focusin', (e) => {
    if (e.target?.closest?.('ytd-searchbox, #search, form#search-form') || e.target?.tagName === 'INPUT') markTyping();
  }, true);
  document.addEventListener('keydown', (e) => {
    if (e.target?.closest?.('ytd-searchbox, #search, form#search-form') || e.target?.tagName === 'INPUT') markTyping();
  }, true);

  setInterval(tick, 250);
  window.addEventListener('yt-navigate-finish', tick, true);
})();
