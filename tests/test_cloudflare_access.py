import asyncio
import time
from types import SimpleNamespace

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from server.app import create_app


@pytest.fixture
async def access_app(tmp_path, monkeypatch):
    for key, value in {
        'DATA_DIR': str(tmp_path/'data'), 'ACCESS_TEAM_DOMAIN':'school.cloudflareaccess.com',
        'ACCESS_AUD':'pagecraft-only', 'ACCESS_EMAIL':'teacher@example.com',
        'TEACHER_ORIGIN':'https://studio.example',
    }.items():
        monkeypatch.setenv('PAGECRAFT_'+key, value)
    app = create_app()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    async with app.router.lifespan_context(app):
        # Real RSA signing/verification, only remote key retrieval substituted.
        monkeypatch.setattr(app.state.cloudflare_access.keys, 'get_signing_key_from_jwt',
                            lambda token: SimpleNamespace(key=key.public_key()))
        yield app, key


def sign(key, **overrides):
    claims = dict(iss='https://school.cloudflareaccess.com', aud=['pagecraft-only'],
                  sub='teacher-id', email='teacher@example.com', iat=int(time.time()),
                  exp=int(time.time())+600)
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm='RS256', headers={'kid':'test'})


async def test_signed_teacher_gets_panel_api_and_no_reusable_local_cookie(access_app):
    app, key = access_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://studio.example',
                                headers={'cf-connecting-ip':'203.0.113.1', 'cf-access-jwt-assertion':sign(key)}) as client:
        for path in ['/teacher/activities.html','/api/teacher-bootstrap','/api/learning/reports']:
            response = await client.get(path)
            assert response.status_code in {200,204}
            assert 'set-cookie' not in response.headers
        logout = await client.get('/logout')
        assert logout.status_code == 303
        assert logout.headers['location'] == 'https://studio.example/cdn-cgi/access/logout'


async def test_paired_board_keeps_collective_access_with_signed_teacher_identity(access_app):
    app, key = access_app
    transport = httpx.ASGITransport(app=app)
    headers = {
        'cf-connecting-ip': '203.0.113.1',
        'cf-access-jwt-assertion': sign(key),
    }
    async with (
        httpx.AsyncClient(transport=transport, base_url='https://studio.example',
                          headers=headers) as teacher,
        httpx.AsyncClient(transport=transport, base_url='https://studio.example',
                          headers=headers) as board,
    ):
        challenge = (await board.post('/api/board/pairings')).json()
        confirmation = await teacher.post('/api/board/pairings/confirm',
                                           json={'code': challenge['code']})
        assert confirmation.status_code == 200
        completed = await board.post('/api/board/pairings/complete',
                                     json={'pairing_id': challenge['pairing_id']})
        assert completed.status_code == 200
        assert (await board.get('/api/board/session')).status_code == 204

        classroom = (await teacher.post('/api/classes', json={
            'name': 'Turma de teste', 'year': 2, 'students': ['Lia'],
        })).json()
        session = (await teacher.post('/api/sessions', json={
            'class_id': classroom['id'], 'activity_slug': 'demo',
            'activity_title': 'Dobros',
        })).json()
        student_id = next(iter(session['roster']))
        live = await board.get('/api/board/session')
        assert live.status_code == 200
        assert live.json()['id'] == session['id']

        stream = asyncio.create_task(
            board.get(f"/api/board/sessions/{session['id']}/stream")
        )
        try:
            for _ in range(200):
                if session['id'] in app.state.classroom.live_session_ids():
                    break
                await asyncio.sleep(0.001)
            assert session['id'] in app.state.classroom.live_session_ids()
            await teacher.post(f"/api/sessions/{session['id']}/control", json={
                'action': 'highlight', 'unit_id': 'privada', 'student_id': student_id,
            })
            await teacher.post(f"/api/sessions/{session['id']}/control", json={
                'action': 'highlight', 'unit_id': 'global',
            })
            await teacher.post(f"/api/sessions/{session['id']}/close")
            response = await asyncio.wait_for(stream, timeout=2)
        finally:
            if not stream.done():
                stream.cancel()
                await asyncio.gather(stream, return_exceptions=True)
        assert response.status_code == 200
        assert 'event: session_state_snapshot' in response.text
        assert 'global' in response.text
        assert 'privada' not in response.text
        assert student_id not in response.text
        assert '"students"' not in response.text

        # O login remoto mantém o painel, mas não substitui o emparelhamento.
        assert (await teacher.get('/api/learning/reports')).status_code == 200
        await teacher.delete('/api/board/pairing')
        assert (await board.get('/api/board/session')).status_code == 401
        assert (
            await board.get(f"/api/board/sessions/{session['id']}/stream")
        ).status_code == 401


@pytest.mark.parametrize('claims', [
    {'email':'another@example.com'}, {'aud':['other-app']}, {'exp':1},
    {'iss':'https://evil.example'}, {'iat':int(time.time())+3600}, {'sub':''},
])
async def test_wrong_identity_application_or_validity_denied(access_app, claims):
    app, key = access_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://studio.example') as client:
        r = await client.get('/api/learning/reports', headers={
            'cf-connecting-ip':'203.0.113.1','cf-access-jwt-assertion':sign(key, **claims),
            'cf-access-authenticated-user-email':'teacher@example.com'})
        assert r.status_code == 401


async def test_spoofed_header_signature_public_host_and_old_cookie_denied(access_app):
    app, key = access_app
    rogue = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    for host, socket, token in [
        ('studio.example','127.0.0.1',''),
        ('studio.example','127.0.0.1',sign(rogue)),
        ('public.example','127.0.0.1',sign(key)),
        ('studio.example','10.0.0.9',sign(key)),
    ]:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(socket,1234)),
            base_url='https://'+host, cookies={'pagecraft_teacher_session':app.state.teacher_token}) as client:
            r = await client.get('/api/learning/reports',headers={
                'cf-connecting-ip':'203.0.113.1','cf-access-jwt-assertion':token,
                'cf-access-authenticated-user-email':'teacher@example.com'})
            assert r.status_code == 401
            assert (await client.get('/api/health')).status_code == 200


async def test_login_redirects_to_protected_origin_and_jwks_outage_fails_closed(access_app, monkeypatch):
    app, key = access_app
    def fail(token):
        raise jwt.PyJWKClientConnectionError('offline')
    monkeypatch.setattr(app.state.cloudflare_access.keys,'get_signing_key_from_jwt',fail)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://public.example',
        headers={'cf-connecting-ip':'203.0.113.1'}) as client:
        for path in ['/login','/teacher/activities.html']:
            r=await client.get(path)
            assert r.status_code == 303
            assert r.headers['location'] == 'https://studio.example/teacher/activities.html'
        r=await client.get('https://studio.example/api/learning/reports',headers={'cf-access-jwt-assertion':sign(key)})
        assert r.status_code == 401
