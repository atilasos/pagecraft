"""Browser checks attach only to a session opened by Agent Browser Hub."""
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DRAFT = Path(__file__).resolve().parents[2] / 'drafts' / 'fracoes-banda-desenhada-2ano.html'


@pytest.fixture(scope='module')
def lesson_origin():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split('?')[0] != '/lesson' or not DRAFT.exists():
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(DRAFT.read_bytes())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/lesson'
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def page():
    cdp = os.environ.get('PAGECRAFT_TEST_CDP')
    if not cdp:
        pytest.skip('Open an Agent Browser Hub session and set PAGECRAFT_TEST_CDP')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(cdp)
        # Separate cookies/storage: a teacher preview must not authenticate the
        # next test's student requests as the teacher. The browser stays in Hub.
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(3000)
        try:
            yield page
        finally:
            context.close()


@pytest.fixture(scope='module')
def studio_origin(tmp_path_factory):
    """Real Studio with disposable data and a copy of the lesson, never production."""
    import shutil
    import socket
    import subprocess
    import sys
    import time
    import urllib.request

    root = tmp_path_factory.mktemp('fraction-studio')
    (root / 'drafts').mkdir()
    shutil.copytree(DRAFT.parent.parent / 'server' / 'static', root / 'server' / 'static')
    shutil.copyfile(DRAFT, root / 'drafts' / DRAFT.name)
    activity = root / 'activities' / 'fraction-test'
    activity.mkdir(parents=True)
    shutil.copyfile(DRAFT, activity / 'index.html')
    for slug in ['bota', 'arvore', 'canva-4ano-estudio-de-slides', 'classificar-objetos-1ano', '2026-03-17-dobro-ate-10', 'dedo']:
        shutil.copytree(DRAFT.parent.parent / 'activities' / slug, root / 'activities' / slug)
    # The unpublished Canva draft is copied only into this disposable test server.
    canva = root / 'activities' / 'canva-animais-4ano'
    canva.mkdir()
    shutil.copyfile(DRAFT.parent / 'canva-animais-4ano.html', canva / 'index.html')
    (canva / 'meta.json').write_text('{"title":"Dois animais, três formas de comunicar","year":"4","subject":"TIC"}')
    with socket.socket() as socket_:
        socket_.bind(('127.0.0.1', 0))
        port = socket_.getsockname()[1]
    env = dict(os.environ, PAGECRAFT_REPO_ROOT=str(root), PAGECRAFT_DATA_DIR=str(root / 'data'),
               PAGECRAFT_ACTIVITIES_DIR=str(root / 'activities'), PAGECRAFT_CATALOG_PATH=str(root / 'catalog.json'),
               PAGECRAFT_PUBLIC_ORIGIN='', PAGECRAFT_TEACHER_ORIGIN='', PAGECRAFT_ACCESS_AUD='',
               PAGECRAFT_ACCESS_TEAM_DOMAIN='', PAGECRAFT_ACCESS_EMAIL='')
    origin = f'http://127.0.0.1:{port}'
    with (root / 'server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server.app:app', '--host', '127.0.0.1', '--port', str(port)],
                                   cwd=DRAFT.parent.parent, env=env, stdout=log, stderr=log)
        try:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail((root / 'server.log').read_text())
                try:
                    urllib.request.urlopen(origin + '/api/health', timeout=.2).close()
                    break
                except OSError:
                    time.sleep(.1)
            else:
                pytest.fail('Isolated Studio did not start')
            yield origin
        finally:
            process.terminate()
            process.wait(timeout=10)
