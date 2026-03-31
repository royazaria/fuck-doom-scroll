// Detects active scrolling and reports to local Python server
const SERVER = "http://localhost:7331";
const VELOCITY_THRESHOLD = 3;    // scroll events per second = "active"
const REPORT_INTERVAL_MS = 2000; // report every 2 seconds

let scrollEvents = 0;

window.addEventListener("scroll", () => { scrollEvents++; }, { passive: true });

const site = location.hostname.replace("www.", "");

setInterval(() => {
  const eventsPerSecond = scrollEvents / (REPORT_INTERVAL_MS / 1000);
  scrollEvents = 0;

  if (eventsPerSecond >= VELOCITY_THRESHOLD) {
    fetch(`${SERVER}/scroll`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ site, active_seconds: REPORT_INTERVAL_MS / 1000 }),
    }).catch(() => {});
  }
}, REPORT_INTERVAL_MS);
