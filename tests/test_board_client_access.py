from pathlib import Path


BOARD_STATIC = Path(__file__).parent.parent / "server" / "static" / "board"


def test_board_client_pairs_then_waits_for_a_live_session():
    html = (BOARD_STATIC / "index.html").read_text("utf-8")
    javascript = (BOARD_STATIC / "app.js").read_text("utf-8")

    assert 'id="pairing-code"' in html
    assert 'id="waiting"' in html
    assert 'id="board"' in html
    assert 'src="/board/app.js"' in html
    assert 'fetch("/api/board/pairings", { method: "POST" })' in javascript
    assert 'fetch("/api/board/pairings/complete"' in javascript
    assert 'fetch("/api/board/session")' in javascript
    assert "response.status === 204" in javascript


def test_board_client_streams_only_collective_state_without_role_credentials():
    html = (BOARD_STATIC / "index.html").read_text("utf-8")
    javascript = (BOARD_STATIC / "app.js").read_text("utf-8")
    client = f"{html}\n{javascript}"

    assert "new EventSource(`/api/sessions/${session.id}/stream`)" in javascript
    assert "if (data.student_id != null) return;" in javascript
    assert "board.contentWindow?.postMessage" in javascript
    assert "common.js" not in client
    assert "localStorage" not in client
    assert "teacher_token" not in client
    assert "pagecraft_teacher_token" not in client
    assert "?role=" not in client
    assert "/control" not in client
    assert "/message" not in client
    assert "/release" not in client


def test_board_client_only_posts_during_pairing():
    javascript = (BOARD_STATIC / "app.js").read_text("utf-8")

    assert javascript.count('method: "POST"') == 2
