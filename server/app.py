"""App FastAPI do PageCraft Studio (servidor local do professor)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .events import EventHub
from .knowledge import AEClient, WikiClient
from .pipeline.runner import PipelineRunner
from .providers import AnthropicProvider, CodexProvider
from .storage import Storage


def build_generation_provider(config):
    if config.generation_provider == "anthropic":
        return AnthropicProvider(model=config.anthropic_model)
    return CodexProvider(codex_bin=config.codex_bin)


def build_feedback_provider(config):
    if config.feedback_provider == "anthropic":
        return AnthropicProvider(model=config.anthropic_model)
    if config.feedback_provider == "codex":
        return CodexProvider(codex_bin=config.codex_bin)
    anthropic = AnthropicProvider(model=config.anthropic_model)
    return anthropic if anthropic.available else CodexProvider(codex_bin=config.codex_bin)


def create_app() -> FastAPI:
    config = load_config()
    storage = Storage(config.data_dir)
    hub = EventHub(storage)
    wiki = WikiClient(config.vault_path)
    ae = AEClient(config.vault_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        app.state.storage = storage
        app.state.hub = hub
        app.state.wiki = wiki
        app.state.ae = ae
        app.state.runner = PipelineRunner(
            config, storage, hub, build_generation_provider(config), wiki, ae
        )
        app.state.feedback_provider = build_feedback_provider(config)
        yield

    app = FastAPI(title="PageCraft Studio", lifespan=lifespan)

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "app": "pagecraft-studio",
            "vault": ae.available,
            "wiki": wiki.available,
        }

    from .api import jobs

    app.include_router(jobs.router)

    config.outputs_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=config.outputs_dir), name="outputs")
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
