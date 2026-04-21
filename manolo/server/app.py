"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from manolo.server.lifecycle import lifespan
from manolo.server.routers import calendar, chat, conversations, fx, health


def create_app() -> FastAPI:
    """Build FastAPI app with routers and static UI."""
    app = FastAPI(title="Manolo AI Helper", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(conversations.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(calendar.router, prefix="/v1")
    app.include_router(fx.router, prefix="/v1")

    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
