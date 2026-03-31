from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.tracker import ScrollTracker

class ScrollPing(BaseModel):
    site: str
    active_seconds: float

def create_app(tracker: ScrollTracker) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/status")
    def status(site: str):
        return {"blocked": tracker.is_blocked(site)}

    @app.post("/scroll")
    def scroll(ping: ScrollPing):
        tracker.record_scroll(ping.site, ping.active_seconds)
        return {"ok": True, "accumulated": tracker.get_accumulated(ping.site)}

    @app.post("/unblock")
    def unblock(site: str):
        tracker.unblock(site)
        return {"ok": True}

    return app
