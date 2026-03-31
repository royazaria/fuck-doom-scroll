import threading
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class SiteState:
    accumulated: float = 0.0
    blocked: bool = False

class ScrollTracker:
    def __init__(self, threshold: float, cooldown: float):
        self.threshold = threshold
        self.cooldown = cooldown
        self._sites: Dict[str, SiteState] = {}
        self._lock = threading.Lock()

    def _get(self, site: str) -> SiteState:
        if site not in self._sites:
            self._sites[site] = SiteState()
        return self._sites[site]

    def record_scroll(self, site: str, active_seconds: float):
        with self._lock:
            state = self._get(site)
            if not state.blocked:
                state.accumulated += active_seconds
                if state.accumulated >= self.threshold:
                    state.blocked = True

    def is_blocked(self, site: str) -> bool:
        with self._lock:
            return self._get(site).blocked

    def unblock(self, site: str):
        with self._lock:
            self._sites[site] = SiteState()

    def get_accumulated(self, site: str) -> float:
        with self._lock:
            return self._get(site).accumulated
