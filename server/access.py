"""Políticas de Acesso declaradas pelas rotas do Studio."""

from __future__ import annotations

import hmac
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from fastapi import Request
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


_POLICY_ATTRIBUTE = "__pagecraft_access_policy__"
_PROXY_HEADERS = ("x-forwarded-for", "x-real-ip", "forwarded", "cf-connecting-ip")
TEACHER_COOKIE_NAME = "pagecraft_teacher_session"


@dataclass(frozen=True)
class AccessContext:
    role: Role | None
    channel: TrustChannel
    client_ip: str
    student_id: str | None = None
    student_token: str = ""


def access_policy(policy: RoutePolicy, *additional: RoutePolicy):
    """Declara a política no endpoint antes de o router o registar."""

    policies = frozenset((policy, *additional))
    if RoutePolicy.PUBLIC in policies and len(policies) != 1:
        raise ValueError("a política pública não pode ser combinada com Papéis")

    def decorate(endpoint: Callable) -> Callable:
        setattr(endpoint, _POLICY_ATTRIBUTE, policies)
        return endpoint

    return decorate


def declare_route_policy(route: BaseRoute, policy: RoutePolicy) -> None:
    """Declara a política de uma rota sem endpoint, como um ``Mount``."""

    setattr(route, _POLICY_ATTRIBUTE, frozenset((policy,)))


def route_policy(route: BaseRoute) -> frozenset[RoutePolicy] | None:
    declared = getattr(route, _POLICY_ATTRIBUTE, None)
    if declared is None:
        declared = getattr(getattr(route, "endpoint", None), _POLICY_ATTRIBUTE, None)
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


async def _student_token(request: Request) -> str:
    token = request.query_params.get("student_token", "")
    if token or request.method not in {"POST", "PUT", "PATCH"}:
        return token
    try:
        body = await request.json()
    except (ValueError, RuntimeError):
        return ""
    return str(body.get("student_token", "")) if isinstance(body, dict) else ""


async def resolve_access(request: Request, path_params: dict) -> AccessContext:
    """Resolve Papel e canal uma única vez, antes de executar o handler."""

    channel, client_ip = _trust_channel(request)
    expected = getattr(request.app.state, "teacher_token", "")
    teacher_token = request.cookies.get(TEACHER_COOKIE_NAME, "")
    if teacher_token and expected and hmac.compare_digest(teacher_token, expected):
        return AccessContext(Role.TEACHER, channel, client_ip)

    student_token = await _student_token(request)
    session_id = path_params.get("session_id", "")
    classroom = getattr(request.app.state, "classroom", None)
    if student_token and session_id and classroom is not None:
        student_id = await classroom.student_for_token(
            session_id,
            student_token,
            require_live=False,
        )
        if student_id:
            return AccessContext(
                Role.STUDENT,
                channel,
                client_ip,
                student_id=student_id,
                student_token=student_token,
            )

    return AccessContext(None, channel, client_ip)


def policy_allows(
    policy: frozenset[RoutePolicy],
    role: Role | None,
) -> bool:
    if RoutePolicy.PUBLIC in policy:
        return True
    return role is not None and RoutePolicy(role.value) in policy
