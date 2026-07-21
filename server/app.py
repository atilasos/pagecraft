"""App FastAPI do PageCraft Studio (servidor local do professor)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
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
    wiki = WikiClient(config.vault_path, api_url=config.wiki_api_url)
    ae = AEClient(config.vault_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from .classroom import ClassroomService
        from .classroom.feedback import FeedbackService
        from .security import load_or_create_teacher_token

        app.state.config = config
        app.state.storage = storage
        app.state.hub = hub
        app.state.wiki = wiki
        app.state.ae = ae
        app.state.teacher_token = load_or_create_teacher_token(config.data_dir)
        app.state.runner = PipelineRunner(
            config, storage, hub, build_generation_provider(config), wiki, ae
        )
        app.state.classroom = ClassroomService(config, storage, hub)
        app.state.feedback = FeedbackService(
            config, storage, app.state.classroom, build_feedback_provider(config)
        )
        app.state.feedback.start()
        await app.state.runner.start()
        yield
        await app.state.feedback.stop()
        await app.state.runner.stop()

    app = FastAPI(title="PageCraft Studio", lifespan=lifespan)

    ACTIVITY_CSP = (
        "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
        "img-src data:; media-src data:; font-src data:; connect-src 'none'; "
        "form-action 'none'; base-uri 'none'"
    )

    @app.middleware("http")
    async def activity_csp(request, call_next):
        response = await call_next(request)
        # defesa em profundidade: mesmo que uma atividade gerada tente usar
        # rede, o browser bloqueia (o invariante offline deixa de depender
        # só da validação estática)
        if request.url.path.startswith(("/activities/", "/outputs/")):
            response.headers["content-security-policy"] = ACTIVITY_CSP
        return response

    @app.get("/api/teacher-token")
    async def teacher_token(request: Request):
        from .security import is_loopback_direct

        if not is_loopback_direct(request):
            raise HTTPException(403, "só disponível na máquina do professor")
        return {"token": app.state.teacher_token}

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "app": "pagecraft-studio",
            "vault": ae.available,
            "wiki": await wiki.probe(),
        }

    @app.get("/api/meta")
    async def meta():
        from .api.catalog import list_activities

        return {
            "subjects": ["Português", "Matemática", "Estudo do Meio", "Educação Física", "Inglês"],
            "ae_subjects": ae.list_subjects(),
            "years": [1, 2, 3, 4],
            "makers": ["minecraft", "lego", "3d-print", "robotics", "whiteboard", "unplugged"],
            "activities": list_activities(config.activities_dir),
        }

    from .api import catalog as catalog_api
    from .api import classroom as classroom_api
    from .api import jobs

    app.include_router(jobs.router)
    app.include_router(classroom_api.router)
    app.include_router(catalog_api.router)

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
