// Detects active scrolling and reports to local Python server
// YouTube: only tracks /shorts/ URLs. Facebook/Instagram: always tracks.
const SERVER = "http://localhost:7331";
const REPORT_INTERVAL_MS = 2000;

let scrollCount = 0;
let tracking = false;

function shouldTrack() {
  const host = location.hostname.replace("www.", "");
  if (host === "youtube.com" || host === "m.youtube.com") {
    return location.pathname.startsWith("/shorts");
  }
  return true; // facebook.com, instagram.com — always track
}

function startTracking() {
  if (tracking) return;
  tracking = true;
  scrollCount = 0;
}

function stopTracking() {
  tracking = false;
  scrollCount = 0;
}

// Count all scroll-like events
const countScroll = () => { if (tracking) scrollCount++; };
window.addEventListener("scroll",    countScroll, { passive: true, capture: true });
window.addEventListener("wheel",     countScroll, { passive: true, capture: true });
window.addEventListener("touchmove", countScroll, { passive: true, capture: true });
document.addEventListener("scroll",  countScroll, { passive: true, capture: true });

// Handle YouTube SPA navigation (yt-navigate-finish fires on every page change)
window.addEventListener("yt-navigate-finish", () => {
  if (shouldTrack()) {
    startTracking();
  } else {
    stopTracking();
  }
});

// Also handle generic SPA navigation via popstate
window.addEventListener("popstate", () => {
  if (shouldTrack()) startTracking();
  else stopTracking();
});

// Initial check
if (shouldTrack()) startTracking();

const site = location.hostname.replace("www.", "");

setInterval(() => {
  if (!tracking) { scrollCount = 0; return; }

  const eventsPerSecond = scrollCount / (REPORT_INTERVAL_MS / 1000);
  scrollCount = 0;

  if (eventsPerSecond >= 1) {
    fetch(`${SERVER}/scroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site, active_seconds: REPORT_INTERVAL_MS / 1000 }),
    }).catch(() => {});
  }
}, REPORT_INTERVAL_MS);
