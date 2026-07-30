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


def test_student_client_keeps_only_non_secret_identity_metadata():
    javascript = STUDENT_JAVASCRIPT.read_text("utf-8")

    assert "student_token" not in javascript
    assert "state.token" not in javascript
    assert "saved.token" not in javascript
    assert "?role=student" not in javascript
    assert "me.session.status !== \"live\"" not in javascript
    assert (
        "sessionId: state.session.id,\n"
        "        studentId: state.studentId,\n"
        "        displayName: state.displayName,"
    ) in javascript
