import pytest
from app.tracker import ScrollTracker

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
