from pathlib import Path


TEACHER_STATIC = Path(__file__).parent.parent / "server" / "static" / "teacher"


def test_teacher_client_keeps_the_credential_out_of_javascript_and_urls():
    javascript = "\n".join(
        path.read_text("utf-8")
        for path in (
            TEACHER_STATIC / "common.js",
            TEACHER_STATIC / "app.js",
            TEACHER_STATIC / "class.js",
        )
    )

    assert "/api/teacher-bootstrap" not in javascript
    assert "pagecraft_teacher_token" not in javascript
    assert "/api/teacher-token" not in javascript
    assert "x-teacher-token" not in javascript
    assert "teacher_token" not in javascript
    assert "localStorage" not in javascript


def test_teacher_panel_manages_board_pairing_without_teacher_credentials():
    html = (TEACHER_STATIC / "class.html").read_text("utf-8")
    javascript = (TEACHER_STATIC / "class.js").read_text("utf-8")

    assert 'id="board-pairing-form"' in html
    assert 'id="board-pairing-code"' in html
    assert 'id="board-unpair"' in html
    assert 'tfetch("/api/board/pairing")' in javascript
    assert 'tfetch("/api/board/pairings/confirm"' in javascript
    assert 'method: "DELETE"' in javascript
    assert "present.html?session" not in javascript
    assert "?role=teacher" not in javascript
    assert not (TEACHER_STATIC / "present.html").exists()
