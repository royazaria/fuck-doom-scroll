// F*CK Doom Scroll — content script
// Sends scroll/time data via chrome.runtime.sendMessage to background.js
// (background service worker makes the actual fetch — bypasses mixed-content block)

const REPORT_INTERVAL_MS = 2000;
const host = location.hostname.replace("www.", "");
const isYouTube = host === "youtube.com" || host === "m.youtube.com";

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
