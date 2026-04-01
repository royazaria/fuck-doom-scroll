const SERVER = "http://localhost:7331";

const BLOCKED_PATTERNS = [/facebook\.com/, /instagram\.com/, /youtube\.com/];

function isBlockedSite(url) {
  return url && BLOCKED_PATTERNS.some(p => p.test(url));
}

function getSite(url) {
  try { return new URL(url).hostname.replace("www.", ""); } catch { return ""; }
}

// ── Keep service worker alive ────────────────────────────────────────────────
chrome.alarms.create("keepAlive", { periodInMinutes: 0.4 }); // every ~24s
chrome.alarms.create("checkBlock", { periodInMinutes: 0.033 }); // every ~2s

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "checkBlock") checkAndBlock();
  // keepAlive just wakes the service worker
});

// ── Inject content script into existing open tabs on extension load ──────────
chrome.runtime.onInstalled.addListener(async () => {
  const tabs = await chrome.tabs.query({
    url: [
      "https://*.facebook.com/*",
      "https://*.instagram.com/*",
      "https://*.youtube.com/*",
    ]
  });
  for (const tab of tabs) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    }).catch(() => {});
  }
});

// ── Receive scroll pings from content script ─────────────────────────────────
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type !== "scroll") return;
  fetch(`${SERVER}/scroll`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ site: msg.site, active_seconds: msg.active_seconds }),
  }).catch(() => {});
});

// ── Poll server and redirect blocked tabs ────────────────────────────────────
async function checkAndBlock() {
  let tabs;
  try { tabs = await chrome.tabs.query({ active: true }); } catch { return; }
  for (const tab of tabs) {
    if (!isBlockedSite(tab.url)) continue;
    if (tab.url.includes("blocked.html")) continue;
    const site = getSite(tab.url);
    try {
      const r = await fetch(`${SERVER}/status?site=${site}`);
      const { blocked } = await r.json();
      if (blocked) {
        chrome.tabs.update(tab.id, { url: chrome.runtime.getURL("blocked.html") });
      }
    } catch (_) {}
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;
  if (!isBlockedSite(tab.url) || tab.url.includes("blocked.html")) return;
  const site = getSite(tab.url);
  fetch(`${SERVER}/status?site=${site}`)
    .then(r => r.json())
    .then(({ blocked }) => {
      if (blocked) chrome.tabs.update(tabId, { url: chrome.runtime.getURL("blocked.html") });
    })
    .catch(() => {});
});
