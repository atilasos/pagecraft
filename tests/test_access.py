import pytest

from server import app as app_module


def test_app_refuses_to_start_with_a_route_without_an_access_policy():
    def add_unprotected_route(app):
        @app.get("/api/forgotten")
        async def forgotten_route():
            return {"should": "never be public by accident"}

    with pytest.raises(
        RuntimeError,
        match=r"GET /api/forgotten.*forgotten_route",
    ):
        app_module.create_app(route_extensions=[add_unprotected_route])
