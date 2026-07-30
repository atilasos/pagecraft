"""Políticas de Acesso declaradas pelas rotas do Studio."""

from __future__ import annotations

import hmac
from collections import deque
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from fastapi import Request, Response
from starlette.routing import Match
from starlette.routing import BaseRoute


class Role(StrEnum):
    TEACHER = "teacher"
    STUDENT = "student"
    BOARD = "board"


class TrustChannel(StrEnum):
    LOOPBACK = "loopback_direct"
    CLOUDFLARE = "cloudflare_tunnel"
    LAN = "lan"


class RoutePolicy(StrEnum):
    PUBLIC = "public"
    TEACHER = Role.TEACHER
    STUDENT = Role.STUDENT
    BOARD = Role.BOARD


class RateLimitOperation(StrEnum):
    JOIN = "join"
    CLAIM = "claim"


_POLICY_ATTRIBUTE = "__pagecraft_access_policy__"
_TEACHER_BOOTSTRAP_ATTRIBUTE = "__pagecraft_teacher_loopback_bootstrap__"
_RATE_LIMIT_ATTRIBUTE = "__pagecraft_access_rate_limit__"
_PROXY_HEADERS = ("x-forwarded-for", "x-real-ip", "forwarded", "cf-connecting-ip")
TEACHER_COOKIE_NAME = "pagecraft_teacher_session"
STUDENT_COOKIE_NAME = "pagecraft_student_session"
RATE_LIMIT_DETAIL = "muitas tentativas — espera um bocadinho"


@dataclass(frozen=True)
class AccessContext:
    role: Role | None
    channel: TrustChannel
    client_ip: str
    student_id: str | None = None
    student_session_id: str | None = None
    student_credential: str = ""


class RequestRateLimiter:
    """Janela deslizante in-process, isolada por operação e IP resolvido."""

    def __init__(
        self,
        clock: Callable[[], float],
        *,
        limit: int = 20,
        window_seconds: float = 60,
    ):
        self._clock = clock
        self._limit = limit
        self._window_seconds = window_seconds
        self._attempts: dict[
            tuple[RateLimitOperation, str],
            deque[float],
        ] = {}

    def allows(self, operation: RateLimitOperation, client_ip: str) -> bool:
        now = self._clock()
        attempts = self._attempts.setdefault((operation, client_ip), deque())
        cutoff = now - self._window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if len(attempts) >= self._limit:
            return False
        attempts.append(now)
        return True


def access_policy(policy: RoutePolicy, *additional: RoutePolicy):
    """Declara a política no endpoint antes de o router o registar."""

    policies = frozenset((policy, *additional))
    if RoutePolicy.PUBLIC in policies and len(policies) != 1:
        raise ValueError("a política pública não pode ser combinada com Papéis")

    def decorate(endpoint: Callable) -> Callable:
        setattr(endpoint, _POLICY_ATTRIBUTE, policies)
        return endpoint

    return decorate


def rate_limited(operation: RateLimitOperation):
    """Declara um orçamento de pedidos por IP para uma rota pública."""

    def decorate(endpoint: Callable) -> Callable:
        setattr(endpoint, _RATE_LIMIT_ATTRIBUTE, operation)
        return endpoint

    return decorate


def declare_route_policy(route: BaseRoute, policy: RoutePolicy) -> None:
    """Declara a política de uma rota sem endpoint, como um ``Mount``."""

    setattr(route, _POLICY_ATTRIBUTE, frozenset((policy,)))


def teacher_loopback_bootstrap(endpoint: Callable) -> Callable:
    """Declara que loopback direto pode criar o Papel Professor nesta rota."""

    setattr(endpoint, _TEACHER_BOOTSTRAP_ATTRIBUTE, True)
    return endpoint


def declare_teacher_loopback_bootstrap(route: BaseRoute) -> None:
    """Declara o bootstrap numa rota sem endpoint, como um ``Mount``."""

    setattr(route, _TEACHER_BOOTSTRAP_ATTRIBUTE, True)


def route_bootstraps_teacher(route: BaseRoute) -> bool:
    declared = getattr(route, _TEACHER_BOOTSTRAP_ATTRIBUTE, None)
    if declared is None:
        declared = getattr(
            getattr(route, "endpoint", None),
            _TEACHER_BOOTSTRAP_ATTRIBUTE,
            False,
        )
    return bool(declared)


def route_policy(route: BaseRoute) -> frozenset[RoutePolicy] | None:
    declared = getattr(route, _POLICY_ATTRIBUTE, None)
    if declared is None:
        declared = getattr(getattr(route, "endpoint", None), _POLICY_ATTRIBUTE, None)
    return declared


def route_rate_limit(route: BaseRoute) -> RateLimitOperation | None:
    declared = getattr(route, _RATE_LIMIT_ATTRIBUTE, None)
    if declared is None:
        declared = getattr(
            getattr(route, "endpoint", None),
            _RATE_LIMIT_ATTRIBUTE,
            None,
        )
    return declared


def iter_effective_routes(routes: Iterable[BaseRoute]) -> Iterator[BaseRoute]:
    """Expande routers incluídos, que o FastAPI recente mantém preguiçosos."""

    for route in routes:
        candidates = getattr(route, "effective_candidates", None)
        if candidates is not None:
            yield from candidates()
        else:
            yield route


def validate_route_policies(routes: Iterable[BaseRoute]) -> None:
    missing = [route for route in iter_effective_routes(routes) if route_policy(route) is None]
    if not missing:
        return

    route = missing[0]
    methods = " ".join(sorted(getattr(route, "methods", ()) or ())) or "MOUNT"
    name = getattr(route, "name", None) or getattr(
        getattr(route, "endpoint", None), "__name__", "<sem nome>"
    )
    path = getattr(route, "path", "<sem caminho>")
    raise RuntimeError(
        f"rota sem política de Acesso: {methods} {path} ({name})"
    )


def match_route(
    request: Request,
    routes: Iterable[BaseRoute],
) -> tuple[BaseRoute | None, MutableMapping[str, Any]]:
    partial: tuple[BaseRoute, MutableMapping[str, Any]] | None = None
    for route in iter_effective_routes(routes):
        match, child_scope = route.matches(request.scope)
        if match is Match.FULL:
            return route, child_scope
        if match is Match.PARTIAL and partial is None:
            partial = (route, child_scope)
    return partial or (None, {})


def _trust_channel(request: Request) -> tuple[TrustChannel, str]:
    socket_ip = request.client.host if request.client else ""
    if socket_ip in {"127.0.0.1", "::1", "localhost"}:
        if not any(header in request.headers for header in _PROXY_HEADERS):
            return TrustChannel.LOOPBACK, socket_ip
        if request.headers.get("cf-connecting-ip"):
            return TrustChannel.CLOUDFLARE, request.headers["cf-connecting-ip"]
    return TrustChannel.LAN, socket_ip


async def resolve_access(request: Request, path_params: dict) -> AccessContext:
    """Resolve Papel e canal uma única vez, antes de executar o handler."""

    channel, client_ip = _trust_channel(request)
    expected = getattr(request.app.state, "teacher_token", "")
    teacher_token = request.cookies.get(TEACHER_COOKIE_NAME, "")
    if teacher_token and expected and hmac.compare_digest(teacher_token, expected):
        return AccessContext(Role.TEACHER, channel, client_ip)

    student_cookie = request.cookies.get(STUDENT_COOKIE_NAME, "")
    student_session_id, separator, student_credential = student_cookie.partition(".")
    classroom = getattr(request.app.state, "classroom", None)
    if separator and student_session_id and student_credential and classroom is not None:
        student_id = await classroom.student_for_token(
            student_session_id,
            student_credential,
            require_live=False,
        )
        if student_id:
            return AccessContext(
                Role.STUDENT,
                channel,
                client_ip,
                student_id=student_id,
                student_session_id=student_session_id,
                student_credential=student_credential,
            )

    return AccessContext(None, channel, client_ip)


def policy_allows(
    policy: frozenset[RoutePolicy],
    access: AccessContext,
    *,
    teacher_bootstrap: bool = False,
) -> bool:
    if RoutePolicy.PUBLIC in policy:
        return True
    if teacher_bootstrap:
        return (
            access.role is Role.TEACHER
            or access.channel is TrustChannel.LOOPBACK
        )
    return (
        access.role is not None
        and RoutePolicy(access.role.value) in policy
    )


def issue_teacher_cookie(response: Response, credential: str) -> None:
    """Emite a credencial sem a expor ao handler nem ao JavaScript."""

    response.set_cookie(
        TEACHER_COOKIE_NAME,
        credential,
        httponly=True,
        samesite="strict",
        path="/",
    )


def issue_student_cookie(
    response: Response,
    session_id: str,
    credential: str,
    issued_at: str | datetime,
    expires_at: str,
) -> None:
    """Emite o Papel Aluno da sessão até à meia-noite local seguinte."""

    expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    issued = (
        issued_at
        if isinstance(issued_at, datetime)
        else datetime.fromisoformat(str(issued_at).replace("Z", "+00:00"))
    )
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)
    response.set_cookie(
        STUDENT_COOKIE_NAME,
        f"{session_id}.{credential}",
        expires=expires.astimezone(timezone.utc),
        max_age=max(
            0,
            int(
                (
                    expires.astimezone(timezone.utc)
                    - issued.astimezone(timezone.utc)
                ).total_seconds()
            ),
        ),
        httponly=True,
        samesite="strict",
        path="/",
    )
