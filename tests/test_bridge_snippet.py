from server.bridge_snippet import MARKER, ensure_bridge_lite

BASE = "<!doctype html><html lang='pt-PT'><head></head><body><main><section>a</section></main></body></html>"


def test_injects_before_body_close():
    out = ensure_bridge_lite(BASE)
    assert MARKER in out
    assert out.index(MARKER) < out.lower().rindex("</body>")


def test_idempotent():
    once = ensure_bridge_lite(BASE)
    twice = ensure_bridge_lite(once)
    assert once == twice


def test_skips_full_bridge_template():
    html = BASE.replace("<main>", "<script>if (d.type === 'highlight' && d.unitId) {}</script><main>")
    assert ensure_bridge_lite(html) == html


def test_no_body_appends():
    out = ensure_bridge_lite("<p>fragmento sem body")
    assert MARKER in out
