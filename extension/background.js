const SERVER = "http://localhost:7331";
const POLL_MS = 2000;

const BLOCKED_PATTERNS = [
  /facebook\.com/,
  /instagram\.com/,
  /youtube\.com/,
];

function isBlockedSite(url) {
  return BLOCKED_PATTERNS.some(p => p.test(url));
}

function getSite(url) {
  try {
    return new URL(url).hostname.replace("www.", "");
  } catch { return ""; }
}

async function checkAndBlock() {
  const tabs = await chrome.tabs.query({ active: true });
  for (const tab of tabs) {
    if (!tab.url || !isBlockedSite(tab.url)) continue;
    const site = getSite(tab.url);
    try {
      const r = await fetch(`${SERVER}/status?site=${site}`);
      const { blocked } = await r.json();
      if (blocked && !tab.url.includes("blocked.html")) {
        chrome.tabs.update(tab.id, {
          url: chrome.runtime.getURL("blocked.html"),
        });
      }
    } catch (_) {}
  }
}

setInterval(checkAndBlock, POLL_MS);

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && isBlockedSite(tab.url)) {
    const site = getSite(tab.url);
    fetch(`${SERVER}/status?site=${site}`)
      .then(r => r.json())
      .then(({ blocked }) => {
        if (blocked) {
          chrome.tabs.update(tabId, {
            url: chrome.runtime.getURL("blocked.html"),
          });
        }
      })
      .catch(() => {});
  }
});
