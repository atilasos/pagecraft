from server.pipeline.validators import validate_activity_html

GOOD = (
    "<!doctype html>\n"
    '<html lang="pt-PT"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<style>:focus-visible{outline:3px solid blue} "
    "@media (prefers-reduced-motion: reduce){*{animation:none}}</style></head>"
    '<body><main aria-live="polite">' + ("conteúdo pedagógico " * 200) + "</main></body></html>"
)


def test_good_html_passes():
    report = validate_activity_html(GOOD)
    assert report.passed, report.errors
    assert report.warnings == []


def test_external_script_fails():
    bad = GOOD.replace("<body>", '<body><script src="https://cdn.example.com/x.js"></script>')
    report = validate_activity_html(bad)
    assert not report.passed


def test_fetch_fails():
    bad = GOOD.replace("<body>", "<body><script>fetch('/api')</script>")
    report = validate_activity_html(bad)
    assert not report.passed


def test_missing_lang_fails():
    bad = GOOD.replace(' lang="pt-PT"', "")
    assert not validate_activity_html(bad).passed


def test_short_html_fails():
    assert not validate_activity_html("<!doctype html><html lang='pt'>oi</html>").passed


def test_post_message_allowed():
    ok = GOOD.replace("<body>", "<body><script>parent.postMessage({pagecraft:1},'*')</script>")
    report = validate_activity_html(ok)
    assert report.passed, report.errors


def test_local_script_src_fails():
    bad = GOOD.replace("<body>", '<body><script src="/api/sessions"></script>')
    assert not validate_activity_html(bad).passed


def test_css_remote_url_fails():
    bad = GOOD.replace("</style>", "body{background:url(https://x.pt/a.png)}</style>")
    assert not validate_activity_html(bad).passed


def test_send_beacon_fails():
    bad = GOOD.replace("<body>", "<body><script>navigator.sendBeacon('/x')</script>")
    assert not validate_activity_html(bad).passed


def test_form_action_external_fails():
    bad = GOOD.replace("<body>", '<body><form action="https://mau.pt/roubo">')
    assert not validate_activity_html(bad).passed


def test_bracket_fetch_fails():
    bad = GOOD.replace("<body>", "<body><script>window[\"fetch\"]('/x')</script>")
    assert not validate_activity_html(bad).passed


def test_data_url_allowed():
    ok = GOOD.replace("</style>", "body{background:url(data:image/png;base64,AAA)}</style>")
    report = validate_activity_html(ok)
    assert report.passed, report.errors
