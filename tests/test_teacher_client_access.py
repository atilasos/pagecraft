from pathlib import Path


TEACHER_STATIC = Path(__file__).parent.parent / "server" / "static" / "teacher"


def test_teacher_client_keeps_the_credential_out_of_javascript_and_urls():
    javascript = "\n".join(
        path.read_text("utf-8")
        for path in (
            TEACHER_STATIC / "common.js",
            TEACHER_STATIC / "app.js",
            TEACHER_STATIC / "class.js",
            TEACHER_STATIC / "present.html",
        )
    )

    assert "/api/teacher-bootstrap" not in javascript
    assert "pagecraft_teacher_token" not in javascript
    assert "/api/teacher-token" not in javascript
    assert "x-teacher-token" not in javascript
    assert "teacher_token" not in javascript
    assert "localStorage" not in javascript
