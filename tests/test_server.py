import pytest
from httpx import AsyncClient, ASGITransport
from app.server import create_app
from app.tracker import ScrollTracker

@pytest.fixture
def tracker():
    return ScrollTracker(threshold=10, cooldown=5)

@pytest.fixture
def app(tracker):
    return create_app(tracker)

@pytest.mark.asyncio
async def test_status_not_blocked(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/status?site=youtube.com")
    assert r.status_code == 200
    assert r.json() == {"blocked": False}

@pytest.mark.asyncio
async def test_scroll_ping_accumulates(app, tracker):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/scroll", json={"site": "youtube.com", "active_seconds": 5})
    assert r.status_code == 200
    assert tracker.get_accumulated("youtube.com") == 5

@pytest.mark.asyncio
async def test_status_blocked_after_threshold(app, tracker):
    tracker.record_scroll("youtube.com", active_seconds=11)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/status?site=youtube.com")
    assert r.json() == {"blocked": True}
