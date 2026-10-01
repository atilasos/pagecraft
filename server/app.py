"""App FastAPI do PageCraft Studio (servidor local do professor)."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager
from datetime import tzinfo

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .access import (
    RATE_LIMIT_DETAIL,
    RequestRateLimiter,
    Role,
    RoutePolicy,
    TrustChannel,
    access_policy,
    declare_teacher_loopback_bootstrap,
    declare_route_policy,
    issue_teacher_cookie,
    match_route,
    policy_allows,
    resolve_access,
    route_bootstraps_teacher,
    route_policy,
    route_rate_limit,
    teacher_loopback_bootstrap,
    validate_route_policies,
)
from .config import load_config
from .events import EventHub, utcnow
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


def create_app(
    *,
    route_extensions: Iterable[Callable[[FastAPI], None]] = (),
    rate_limit_clock: Callable[[], float] = time.monotonic,
    classroom_clock: Callable[[], str] = utcnow,
    school_timezone: tzinfo | None = None,
) -> FastAPI:
    config = load_config()
    storage = Storage(config.data_dir)
    hub = EventHub(storage)
    wiki = WikiClient(config.vault_path, api_url=config.wiki_api_url)
    ae = AEClient(config.vault_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from .board_pairing import BoardPairings
        from .classroom import ClassroomService
        from .classroom.feedback import FeedbackService
        from .security import load_or_create_teacher_token

        from .cloudflare_access import CloudflareAccess
        app.state.cloudflare_access = CloudflareAccess(config)
        app.state.config = config
        app.state.storage = storage
        app.state.hub = hub
        app.state.wiki = wiki
        app.state.ae = ae
        app.state.teacher_token = load_or_create_teacher_token(config.data_dir)
        from .learning import Learning
        app.state.learning = Learning(storage, config)
        app.state.board_pairings = BoardPairings(
            storage,
            clock=classroom_clock,
        )
        app.state.runner = PipelineRunner(
            config, storage, hub, build_generation_provider(config), wiki, ae
        )
        app.state.classroom = ClassroomService(
            config,
            storage,
            hub,
            clock=classroom_clock,
            school_timezone=school_timezone,
        )
        app.state.feedback = FeedbackService(
            config, storage, app.state.classroom, build_feedback_provider(config)
        )
        app.state.feedback.start()
        await app.state.runner.start()
        yield
        await app.state.classroom.stop()
        await app.state.feedback.stop()
        await app.state.runner.stop()

    app = FastAPI(
        title="PageCraft Studio",
        lifespan=lifespan,
    )
    app.state.access_rate_limiter = RequestRateLimiter(rate_limit_clock)
    for framework_route in app.routes:
        declare_route_policy(framework_route, RoutePolicy.TEACHER)

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

    @app.middleware("http")
    async def enforce_access(request: Request, call_next):
        learning_request = request.url.path.startswith(('/api/learning/', '/api/teacher-'))
        if learning_request and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            from urllib.parse import urlsplit
            origin = request.headers.get('origin')
            if origin and urlsplit(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Origem não autorizada.'}, status_code=403)
        route, child_scope = match_route(request, app.routes)
        if route is None:
            return await call_next(request)
        policy = route_policy(route)
        if policy is None:
            return JSONResponse(
                {"detail": "rota sem política de Acesso"},
                status_code=403,
            )

        access = await resolve_access(request, policy)
        bootstraps_teacher = route_bootstraps_teacher(route)
        request.state.access = access
        if (access.role is Role.TEACHER and config.teacher_origin
            and access.channel is not TrustChannel.LOOPBACK
            and request.method not in {"GET", "HEAD", "OPTIONS"}
            and request.headers.get("origin") not in {None, config.teacher_origin}):
            return JSONResponse({"detail": "Origem não autorizada."}, status_code=403)
        requested_session_id = child_scope.get("path_params", {}).get(
            "session_id"
        )
        if (
            RoutePolicy.PUBLIC not in policy
            and access.role is Role.STUDENT
            and requested_session_id
            and access.student_session_id != requested_session_id
        ):
            return JSONResponse(
                {"detail": "este Aluno da sessão pertence a outra sessão"},
                status_code=403,
            )
        rate_limit_operation = route_rate_limit(route)
        if (
            rate_limit_operation
            and not app.state.access_rate_limiter.allows(
                rate_limit_operation,
                access.client_ip,
            )
        ):
            return JSONResponse(
                {"detail": RATE_LIMIT_DETAIL},
                status_code=429,
            )
        if not policy_allows(
            policy,
            access,
            teacher_bootstrap=bootstraps_teacher,
        ):
            if (config.teacher_origin and request.method == "GET"
                and request.url.path.startswith("/teacher")
                and request.url.hostname != app.state.cloudflare_access.hostname):
                return RedirectResponse(config.teacher_origin + request.url.path, status_code=303,
                                        headers={"Cache-Control": "no-store"})
            status = 401 if access.role is None else 403
            detail = (
                "este pedido precisa de um Papel"
                if status == 401
                else "este Papel não pode usar esta rota"
            )
            return JSONResponse({"detail": detail}, status_code=status)
        response = await call_next(request)
        if learning_request or RoutePolicy.TEACHER in policy:
            response.headers['Cache-Control'] = 'no-store'
        if (
            bootstraps_teacher
            and access.channel is TrustChannel.LOOPBACK
        ):
            issue_teacher_cookie(response, app.state.teacher_token)
        return response

    @app.get("/api/teacher-bootstrap", status_code=204)
    @access_policy(RoutePolicy.TEACHER)
    @teacher_loopback_bootstrap
    async def teacher_bootstrap():
        pass

    @app.get("/api/health")
    @access_policy(RoutePolicy.PUBLIC)
    async def health():
        return {
            "status": "ok",
            "app": "pagecraft-studio",
            "vault": ae.available,
            "wiki": await wiki.probe(),
        }

    @app.get("/api/meta")
    @access_policy(RoutePolicy.TEACHER)
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
    from .api import board as board_api
    from .api import classroom as classroom_api
    from .api import jobs
    from .api import learning as learning_api

    app.include_router(jobs.router)
    app.include_router(board_api.router)
    app.include_router(classroom_api.router)
    app.include_router(catalog_api.router)
    app.include_router(learning_api.router)

    for extend_routes in route_extensions:
        extend_routes(app)

    static_dir = config.repo_root / "server" / "static"

    @app.get("/")
    @app.get("/index.html")
    @access_policy(RoutePolicy.PUBLIC)
    async def studio_home(request: Request):
        if config.teacher_origin and request.url.hostname == app.state.cloudflare_access.hostname:
            return RedirectResponse("/teacher/activities.html", status_code=303, headers={"Cache-Control": "no-store"})
        return FileResponse(static_dir / "index.html")

    @app.get("/studio.css")
    @access_policy(RoutePolicy.PUBLIC)
    async def studio_styles():
        return FileResponse(static_dir / "studio.css")

    config.outputs_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=config.outputs_dir), name="outputs")
    declare_route_policy(app.routes[-1], RoutePolicy.PUBLIC)
    app.mount(
        "/activities",
        StaticFiles(directory=config.activities_dir, html=True),
        name="activities",
    )
    declare_route_policy(app.routes[-1], RoutePolicy.PUBLIC)
    app.mount(
        "/student",
        StaticFiles(directory=static_dir / "student", html=True),
        name="student-static",
    )
    declare_route_policy(app.routes[-1], RoutePolicy.PUBLIC)
    app.mount(
        "/board",
        StaticFiles(directory=static_dir / "board", html=True),
        name="board-static",
    )
    declare_route_policy(app.routes[-1], RoutePolicy.PUBLIC)
    app.mount(
        "/teacher",
        StaticFiles(
            directory=static_dir / "teacher",
            html=True,
        ),
        name="teacher-static",
    )
    declare_route_policy(app.routes[-1], RoutePolicy.TEACHER)
    declare_teacher_loopback_bootstrap(app.routes[-1])

    app.mount('/learning-assets', StaticFiles(directory=static_dir / 'learning'), name='learning-static')
    declare_route_policy(app.routes[-1], RoutePolicy.PUBLIC)

    @app.get('/api/access-info')
    @access_policy(RoutePolicy.PUBLIC)
    async def access_info():
        return {'public_origin': config.public_origin,
                'teacher_origin': config.teacher_origin}

    @app.get('/login')
    @access_policy(RoutePolicy.PUBLIC)
    async def learning_login(request: Request):
        target = config.teacher_origin + "/teacher/activities.html" if config.teacher_origin else "/teacher/activities.html"
        return RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store"})

    @app.get("/logout")
    @access_policy(RoutePolicy.PUBLIC)
    async def learning_logout(request: Request):
        from .access import TEACHER_COOKIE_NAME
        remote = request.state.access.channel is not TrustChannel.LOOPBACK
        target = config.teacher_origin + "/cdn-cgi/access/logout" if remote and config.teacher_origin else "/"
        response = RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store"})
        response.delete_cookie(TEACHER_COOKIE_NAME, path="/")
        return response

    @app.get('/{code}')
    @access_policy(RoutePolicy.PUBLIC)
    async def permanent_activity(code: str, request: Request):
        from .api.learning import visible_activity
        await visible_activity(request, code)
        return FileResponse(static_dir / 'learning' / 'activity.html')

    validate_route_policies(app.routes)
    return app


app = create_app()
