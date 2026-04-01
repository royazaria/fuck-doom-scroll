// F*CK Doom Scroll — content script
// Strategy:
//   YouTube Shorts  → count TIME on /shorts/ URL (watching = doom scrolling)
//   Facebook/Instagram → count SCROLL VELOCITY (only block if actively scrolling)

const SERVER = "http://localhost:7331";
const REPORT_INTERVAL_MS = 2000;

const host = location.hostname.replace("www.", "");
const isYouTube = host === "youtube.com" || host === "m.youtube.com";

// ── YouTube Shorts: time-based ──────────────────────────────────────────────

function isOnShorts() {
  return isYouTube && location.pathname.startsWith("/shorts");
}

if (isYouTube) {
  setInterval(() => {
    if (!isOnShorts()) return;
    if (document.hidden) return; // tab not focused — don't count
    fetch(`${SERVER}/scroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site: "youtube.com", active_seconds: REPORT_INTERVAL_MS / 1000 }),
    }).catch(() => {});
  }, REPORT_INTERVAL_MS);

  // Handle YouTube SPA navigation
  window.addEventListener("yt-navigate-finish", () => { /* no-op, isOnShorts() re-checks */ });
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
      fetch(`${SERVER}/scroll`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site: host, active_seconds: REPORT_INTERVAL_MS / 1000 }),
      }).catch(() => {});
    }
  }, REPORT_INTERVAL_MS);
}
