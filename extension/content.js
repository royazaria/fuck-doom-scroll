// Detects active scrolling and reports to local Python server
const SERVER = "http://localhost:7331";
const REPORT_INTERVAL_MS = 2000;

let scrollCount = 0;

// Standard window scroll (most sites)
window.addEventListener("scroll", () => { scrollCount++; }, { passive: true, capture: true });

// Wheel events — catches Facebook Reels, Instagram, YouTube Shorts
// even when the page itself doesn't "scroll" (single-page swipe feeds)
window.addEventListener("wheel", () => { scrollCount++; }, { passive: true, capture: true });

// Touch swipe — catches mobile-style feeds on desktop
window.addEventListener("touchmove", () => { scrollCount++; }, { passive: true, capture: true });

// Catch scroll on any inner div (Facebook/Instagram scroll containers)
document.addEventListener("scroll", () => { scrollCount++; }, { passive: true, capture: true });

const site = location.hostname.replace("www.", "");

setInterval(() => {
  const eventsPerSecond = scrollCount / (REPORT_INTERVAL_MS / 1000);
  scrollCount = 0;

  // 1 event/sec threshold — a single reel swipe counts as active scrolling
  if (eventsPerSecond >= 1) {
    fetch(`${SERVER}/scroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site, active_seconds: REPORT_INTERVAL_MS / 1000 }),
    }).catch(() => {});
  }
}, REPORT_INTERVAL_MS);
