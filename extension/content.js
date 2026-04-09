// F*CK Doom Scroll — content script
// Sends scroll/time data via chrome.runtime.sendMessage to background.js
// (background service worker makes the actual fetch — bypasses mixed-content block)

const REPORT_INTERVAL_MS = 2000;
const host = location.hostname.replace("www.", "");
const isYouTube = host === "youtube.com" || host === "m.youtube.com";
const isFacebook = host === "facebook.com" || host === "m.facebook.com";

function ping(site, active_seconds) {
  chrome.runtime.sendMessage({ type: "scroll", site, active_seconds });
}

// ── YouTube Shorts: time-based ──────────────────────────────────────────────
if (isYouTube) {
  setInterval(() => {
    if (!location.pathname.startsWith("/shorts")) return;
    if (document.hidden) return;
    ping("youtube.com", REPORT_INTERVAL_MS / 1000);
  }, REPORT_INTERVAL_MS);
}

// ── Facebook Reels: MutationObserver for video autoplay ────────────────────
// FB Reels doesn't always fire scroll events — detect reel navigation by
// watching for new <video> elements that autoplay (the real signal).
if (isFacebook) {
  let _fbReelActive = false;
  let _fbReelTimer = null;

  function _onFBVideoStarted() {
    // Only count if we're in the Reels section
    const url = location.href;
    if (!url.includes("/reels") && !url.includes("reel")) return;

    if (!_fbReelActive) {
      _fbReelActive = true;
      _fbReelTimer = setInterval(() => {
        if (document.hidden) return;
        ping("facebook.com", REPORT_INTERVAL_MS / 1000);
      }, REPORT_INTERVAL_MS);
    }
  }

  function _stopFBReelTimer() {
    _fbReelActive = false;
    if (_fbReelTimer) { clearInterval(_fbReelTimer); _fbReelTimer = null; }
  }

  // Watch for new video elements being added/played
  const _fbObserver = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== 1) continue;
        const videos = node.tagName === "VIDEO" ? [node] : [...node.querySelectorAll("video")];
        for (const video of videos) {
          video.addEventListener("play", _onFBVideoStarted, { once: false });
          video.addEventListener("pause", _stopFBReelTimer, { once: false });
        }
      }
    }
  });
  _fbObserver.observe(document.body, { childList: true, subtree: true });

  // Also attach to any videos already in the DOM
  document.querySelectorAll("video").forEach(v => {
    v.addEventListener("play", _onFBVideoStarted);
    v.addEventListener("pause", _stopFBReelTimer);
  });
}

// ── Facebook / Instagram: scroll-velocity-based ─────────────────────────────
if (!isYouTube) {
  let scrollCount = 0;
  window.addEventListener("scroll",    () => scrollCount++, { passive: true, capture: true });
  window.addEventListener("wheel",     () => scrollCount++, { passive: true, capture: true });
  window.addEventListener("touchmove", () => scrollCount++, { passive: true, capture: true });
  document.addEventListener("scroll",  () => scrollCount++, { passive: true, capture: true });

  setInterval(() => {
    const eventsPerSecond = scrollCount / (REPORT_INTERVAL_MS / 1000);
    scrollCount = 0;
    if (eventsPerSecond >= 1) {
      ping(host, REPORT_INTERVAL_MS / 1000);
    }
  }, REPORT_INTERVAL_MS);
}
