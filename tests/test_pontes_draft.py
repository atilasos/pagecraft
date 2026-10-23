"""The bridge investigation stays private in a disposable Studio."""
import base64
import json
import re
import shutil
from pathlib import Path

import httpx
import jsonschema

from server.app import create_app

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'pontes-duas-vistas'


async def test_pontes_private_preview_never_enters_public_catalog_or_reports(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    (root / 'drafts').mkdir(parents=True)
    (root / 'activities').mkdir()
    shutil.copytree(ROOT / 'server/static', root / 'server/static')
    for suffix in ['.html', '.md', '-docspec.json', '-design-spec.json']:
        shutil.copyfile(ROOT / 'drafts' / (SLUG + suffix), root / 'drafts' / (SLUG + suffix))
    spec = json.loads((root / 'drafts' / (SLUG + '-docspec.json')).read_text())
    design = json.loads((root / 'drafts' / (SLUG + '-design-spec.json')).read_text())
    for name, artifact in [('docspec', spec), ('design-spec', design)]:
        jsonschema.validate(artifact, json.loads((ROOT / f'server/pipeline/schemas/{name}.schema.json').read_text()))
    assert sum(unit['duration'] for unit in spec['units']) == spec['duration'] == 15
    for key, value in {
        'REPO_ROOT': root, 'DATA_DIR': root / 'data', 'OUTPUTS_DIR': root / 'outputs',
        'ACTIVITIES_DIR': root / 'activities', 'CATALOG_PATH': root / 'catalog.json',
        'PUBLIC_ORIGIN': '', 'TEACHER_ORIGIN': '', 'ACCESS_AUD': '',
        'ACCESS_TEAM_DOMAIN': '', 'ACCESS_EMAIL': '',
    }.items():
        monkeypatch.setenv('PAGECRAFT_' + key, str(value))
    registration = {
        'slug': SLUG, 'title': 'Duas pontes iguais de cima', 'year': 3,
        'duration': 15, 'languages': ['pt'], 'criteria': spec['criteria'],
        'requires_completion': True,
    }
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as teacher:
            await teacher.get('/api/teacher-bootstrap')
            response = await teacher.post('/api/learning/activities', json=registration)
            assert response.status_code == 201, response.text
            draft = response.json()
            assert draft['published'] is False
            code = draft['code']
            content = await teacher.get(f'/api/learning/activities/{code}/content')
            assert content.status_code == 200
            assert content.text == (root / 'drafts' / (SLUG + '.html')).read_text()
            assert "connect-src 'none'" in content.headers['content-security-policy']
            fonts = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', content.text)
            assert len(fonts) == 1
            assert base64.b64decode(fonts[0]) == (ROOT / 'assets/fonts/didact-gothic/DidactGothic-Regular.woff2').read_bytes()
            assert (ROOT / 'assets/fonts/didact-gothic/OFL.txt').read_text().strip() in content.text
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.8', 1234)), base_url='http://test') as pupil:
                assert (await pupil.get(f'/api/learning/activities/{code}/content')).status_code == 404
                assert (await pupil.get(f'/{code}')).status_code == 404
                assert (await pupil.get(f'/drafts/{SLUG}.html')).status_code == 404
                assert (await pupil.post(f'/api/learning/activities/{code}/start', json={'name': 'Ensaio descartável'})).status_code == 404
            preview = await teacher.post(f'/api/learning/activities/{code}/start', json={'name': 'Ensaio descartável'})
            assert preview.status_code == 201
            assert preview.json()['preview'] is True
            assert (await teacher.get('/api/learning/reports')).json() == []
    assert list((root / 'activities').iterdir()) == []
    assert not (root / 'catalog.json').exists()
