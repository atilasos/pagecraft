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
        page = browser.contexts[0].new_page()
        page.set_default_timeout(3000)
        yield page
        page.close()
