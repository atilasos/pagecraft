"""Políticas de Acesso declaradas pelas rotas do Studio."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from enum import StrEnum

from fastapi import FastAPI
from starlette.routing import BaseRoute


class Role(StrEnum):
    TEACHER = "teacher"
    STUDENT = "student"
    BOARD = "board"


class RoutePolicy(StrEnum):
    PUBLIC = "public"
    TEACHER = Role.TEACHER
    STUDENT = Role.STUDENT
    BOARD = Role.BOARD
    TEACHER_OR_STUDENT = "teacher_or_student"


_POLICY_ATTRIBUTE = "__pagecraft_access_policy__"


def access_policy(policy: RoutePolicy):
    """Declara a política no endpoint antes de o router o registar."""

    def decorate(endpoint: Callable) -> Callable:
        setattr(endpoint, _POLICY_ATTRIBUTE, policy)
        return endpoint

    return decorate


def declare_route_policy(route: BaseRoute, policy: RoutePolicy) -> None:
    """Declara a política de uma rota sem endpoint, como um ``Mount``."""

    setattr(route, _POLICY_ATTRIBUTE, policy)


def route_policy(route: BaseRoute) -> RoutePolicy | None:
    declared = getattr(route, _POLICY_ATTRIBUTE, None)
    if declared is None:
        declared = getattr(getattr(route, "endpoint", None), _POLICY_ATTRIBUTE, None)
    return declared


def declare_framework_routes(app: FastAPI) -> None:
    """Torna explícita a política das rotas de documentação criadas pelo FastAPI."""

    for route in app.routes:
        if getattr(route, "name", None) in {
            "openapi",
            "swagger_ui_html",
            "swagger_ui_redirect",
            "redoc_html",
        }:
            declare_route_policy(route, RoutePolicy.PUBLIC)


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
    raise RuntimeError(
        f"rota sem política de Acesso: {methods} {route.path} ({name})"
    )
