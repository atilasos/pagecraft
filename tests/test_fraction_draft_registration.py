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


async def test_complete_revision_can_publish_in_isolation_without_changing_old_work(tmp_path, monkeypatch):
    import shutil
    import jsonschema
    slug = 'fracoes-banda-desenhada-2ano'
    root = tmp_path / 'repo'
    (root / 'drafts').mkdir(parents=True)
    shutil.copytree(ROOT / 'server/static', root / 'server/static')
    shutil.copytree(ROOT / 'activities/fracoes-2-minecraft', root / 'activities/fracoes-2-minecraft')
    for suffix in ['.html','.md','-docspec.json','-design-spec.json']:
        shutil.copyfile(ROOT / 'drafts' / (slug+suffix),root / 'drafts' / (slug+suffix))
    spec = json.loads((ROOT / 'drafts' / (slug+'-docspec.json')).read_text())
    design = json.loads((ROOT / 'drafts' / (slug+'-design-spec.json')).read_text())
    jsonschema.validate(spec,json.loads((ROOT / 'server/pipeline/schemas/docspec.schema.json').read_text()))
    jsonschema.validate(design,json.loads((ROOT / 'server/pipeline/schemas/design-spec.schema.json').read_text()))
    assert sum(unit['duration'] for unit in spec['units']) == spec['duration'] == 45
    registration = json.loads((ROOT / 'drafts' / (slug+'-registration.json')).read_text())
    assert registration['criteria'] == spec['criteria']
    for key,path in [('PAGECRAFT_REPO_ROOT',root),('PAGECRAFT_DATA_DIR',root/'data'),('PAGECRAFT_ACTIVITIES_DIR',root/'activities'),('PAGECRAFT_CATALOG_PATH',root/'catalog.json')]:
        monkeypatch.setenv(key,str(path))
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            old = (await teacher.post('/api/learning/activities',json={**registration,'slug':'fracoes-2-minecraft','requires_completion':False})).json()
            assert (await teacher.post(f"/api/learning/activities/{old['code']}/publish")).status_code == 200
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,client=('192.0.2.44',1234)),base_url='http://test') as pupil:
                previous = (await pupil.post(f"/api/learning/activities/{old['code']}/start",json={'name':'Trabalho anterior'})).json()
                response = await pupil.post('/api/learning/me/events',json={'events':[{'id':'old-answer','type':'attempt','unitId':'u1','payload':{'correct':False}}]})
                assert response.status_code == 200
                original = (await pupil.get(f"/api/learning/activities/{old['code']}/content")).text
                draft = (await teacher.post('/api/learning/activities',json=registration)).json()
                assert (await pupil.get(f"/api/learning/activities/{draft['code']}/content")).status_code == 404
                published = await teacher.post(f"/api/learning/activities/{draft['code']}/publish")
                assert published.status_code == 200, published.text
                assert published.json()['code'] == draft['code']
                assert published.json()['requires_completion'] is True
                assert (await pupil.get(f"/api/learning/activities/{draft['code']}/content")).status_code == 200
                assert (await pupil.get(f"/api/learning/activities/{old['code']}/content")).text == original
                restored = (await pupil.get('/api/learning/me')).json()
                assert restored['id'] == previous['id']
                assert restored['events'][0]['payload']['correct'] is False
