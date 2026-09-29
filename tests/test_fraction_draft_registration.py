"""The revised lesson is a private draft with its own identity."""
import json
from pathlib import Path

import httpx

from server.app import create_app

ROOT = Path(__file__).resolve().parents[1]


async def test_fraction_revision_registers_as_private_preview(tmp_path, monkeypatch):
    registration = json.loads((ROOT / 'drafts/fracoes-banda-desenhada-2ano-registration.json').read_text())
    original = (ROOT / 'activities/fracoes-2-minecraft/index.html').read_bytes()
    monkeypatch.setenv('PAGECRAFT_DATA_DIR', str(tmp_path / 'data'))
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            response = await teacher.post('/api/learning/activities', json=registration)
            assert response.status_code == 201, response.text
            draft = response.json()
            assert draft['slug'] != 'fracoes-2-minecraft'
            assert draft['published'] is False
            code = draft['code']
            assert (await teacher.get(f'/api/learning/activities/{code}/content')).status_code == 200
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.8', 1234)), base_url='http://test') as pupil:
                assert (await pupil.get(f'/api/learning/activities/{code}/content')).status_code == 404
            classroom = (await teacher.post('/api/classes', json={'name':'Revisão', 'year':2})).json()
            session = (await teacher.post('/api/sessions', json={'class_id':classroom['id'], 'activity_slug':draft['slug']})).json()
            board_path = f"/api/board/sessions/{session['id']}/content"
            assert (await teacher.get(board_path)).status_code == 401
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.9', 1234)), base_url='http://test') as board:
                assert (await board.get(board_path)).status_code == 401
                pairing = (await board.post('/api/board/pairings')).json()
                await teacher.post('/api/board/pairings/confirm', json={'code':pairing['code']})
                await board.post('/api/board/pairings/complete', json={'pairing_id':pairing['pairing_id']})
                content = await board.get(board_path)
                assert content.status_code == 200
                assert content.text == (ROOT / 'drafts/fracoes-banda-desenhada-2ano.html').read_text()
                assert "connect-src 'none'" in content.headers['content-security-policy']
                assert (await board.get('/api/board/sessions/another-session/content')).status_code == 404
                await teacher.post(f"/api/sessions/{session['id']}/close")
                assert (await board.get(board_path)).status_code == 404
                await teacher.delete('/api/board/pairing')
                assert (await board.get(board_path)).status_code == 401
            preview = await teacher.post(f'/api/learning/activities/{code}/start', json={'name':'Ensaio do professor'})
            assert preview.status_code == 201
            assert preview.json()['preview'] is True
            assert (await teacher.get('/api/learning/reports')).json() == []
    assert (ROOT / 'activities/fracoes-2-minecraft/index.html').read_bytes() == original
