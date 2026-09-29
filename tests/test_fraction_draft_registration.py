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
            preview = await teacher.post(f'/api/learning/activities/{code}/start', json={'name':'Ensaio do professor'})
            assert preview.status_code == 201
            assert preview.json()['preview'] is True
            assert (await teacher.get('/api/learning/reports')).json() == []
    assert (ROOT / 'activities/fracoes-2-minecraft/index.html').read_bytes() == original
