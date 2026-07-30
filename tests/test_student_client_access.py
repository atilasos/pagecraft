from pathlib import Path


STUDENT_JAVASCRIPT = (
    Path(__file__).parent.parent
    / "server"
    / "static"
    / "student"
    / "app.js"
)
STUDENT_HTML = (
    Path(__file__).parent.parent
    / "server"
    / "static"
    / "student"
    / "index.html"
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


def test_student_client_loads_own_history_after_the_session_closes():
    javascript = STUDENT_JAVASCRIPT.read_text("utf-8")
    html = STUDENT_HTML.read_text("utf-8")

    assert "loadOwnHistory();" in javascript
    assert (
        "/students/${state.studentId}/history`"
        in javascript
    )
    assert 'id="history-panel"' in html
    assert 'id="history-list"' in html
