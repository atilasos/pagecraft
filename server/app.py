"""App FastAPI do PageCraft Studio (servidor local do professor)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .storage import Storage


def create_app() -> FastAPI:
    config = load_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        app.state.storage = Storage(config.data_dir)
        yield

    app = FastAPI(title="PageCraft Studio", lifespan=lifespan)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "app": "pagecraft-studio"}

    app.mount(
        "/activities",
        StaticFiles(directory=config.activities_dir, html=True),
        name="activities",
    )
    app.mount(
        "/",
        StaticFiles(directory=config.repo_root / "server" / "static", html=True),
        name="static",
    )
    return app


app = create_app()
