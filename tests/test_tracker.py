import pytest
import tempfile
import os
import app.tracker as tracker_module
from app.tracker import ScrollTracker

@pytest.fixture(autouse=True)
def tmp_state_file(tmp_path):
    original = tracker_module.STATE_FILE
    tracker_module.STATE_FILE = str(tmp_path / "state.json")
    yield
    tracker_module.STATE_FILE = original

def test_fresh_tracker_not_blocked():
    t = ScrollTracker(threshold=10, cooldown=5)
    assert t.is_blocked("youtube.com") is False

def test_accumulates_active_scroll_time():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=6)
    t.record_scroll("youtube.com", active_seconds=5)
    assert t.get_accumulated("youtube.com") == 11

def test_triggers_block_at_threshold():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.is_blocked("youtube.com") is True

def test_different_sites_independent():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.is_blocked("facebook.com") is False

def test_unblock_resets_accumulator():
    t = ScrollTracker(threshold=10, cooldown=5)
    t.record_scroll("youtube.com", active_seconds=11)
    t.unblock("youtube.com")
    assert t.is_blocked("youtube.com") is False
    assert t.get_accumulated("youtube.com") == 0

def test_progressive_countdown():
    t = ScrollTracker(threshold=10, cooldown=5)
    # First block: base seconds
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.get_countdown_seconds("youtube.com", 60) == 60
    t.unblock("youtube.com")
    # Second block: base + 60
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.get_countdown_seconds("youtube.com", 60) == 120
    t.unblock("youtube.com")
    # Third block: base + 120
    t.record_scroll("youtube.com", active_seconds=11)
    assert t.get_countdown_seconds("youtube.com", 60) == 180
