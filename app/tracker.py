import threading
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional

SECONDS_IN_24H = 86400
STATE_FILE = os.path.join(os.path.expanduser("~"), ".fuck-doom-scroll-state.json")

@dataclass
class SiteState:
    accumulated: float = 0.0
    blocked: bool = False
    block_count_today: int = 0
    first_block_time: Optional[float] = None

class ScrollTracker:
    def __init__(self, threshold: float, cooldown: float):
        self.threshold = threshold
        self.cooldown = cooldown
        self._sites: Dict[str, SiteState] = {}
        self._lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            for site, s in data.items():
                self._sites[site] = SiteState(**s)
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {site: asdict(state) for site, state in self._sites.items()}
            with open(STATE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _get(self, site: str) -> SiteState:
        if site not in self._sites:
            self._sites[site] = SiteState()
        return self._sites[site]

    def _maybe_reset_daily_count(self, state: SiteState):
        if state.first_block_time is not None:
            if time.time() - state.first_block_time >= SECONDS_IN_24H:
                state.block_count_today = 0
                state.first_block_time = None

    def record_scroll(self, site: str, active_seconds: float):
        with self._lock:
            state = self._get(site)
            if not state.blocked:
                state.accumulated += active_seconds
                if state.accumulated >= self.threshold:
                    state.blocked = True
                    self._maybe_reset_daily_count(state)
                    state.block_count_today += 1
                    if state.first_block_time is None:
                        state.first_block_time = time.time()
                    self._save_state()

    def is_blocked(self, site: str) -> bool:
        with self._lock:
            return self._get(site).blocked

    def get_countdown_seconds(self, site: str, base_seconds: int) -> int:
        with self._lock:
            state = self._get(site)
            extra = max(0, state.block_count_today - 1) * 60
            return base_seconds + extra

    def unblock(self, site: str):
        with self._lock:
            state = self._get(site)
            state.accumulated = 0.0
            state.blocked = False
            self._save_state()

    def get_accumulated(self, site: str) -> float:
        with self._lock:
            return self._get(site).accumulated
