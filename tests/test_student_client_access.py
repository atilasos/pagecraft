from pathlib import Path


STUDENT_JAVASCRIPT = (
    Path(__file__).parent.parent
    / "server"
    / "static"
    / "student"
    / "app.js"
)


def test_student_client_shows_http_detail_on_join_and_claim_errors():
    javascript = STUDENT_JAVASCRIPT.read_text("utf-8")

    assert (
        'status.textContent = err.message;'
        in javascript
    )
    assert (
        'if (!resp.ok) {\n'
        '    status.textContent = (await resp.json()).detail || "não foi possível";'
        in javascript
    )
    assert javascript.count("(await resp.json()).detail") == 2
