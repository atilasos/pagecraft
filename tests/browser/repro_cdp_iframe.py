"""Isolate native input routing after revealing a sandboxed frame over Hub CDP.

Run with PAGECRAFT_TEST_CDP set to an owned Agent Browser Hub session.
Compare the default dynamic frame with --static-frame or --sync-pointer.
This diagnostic does not use PageCraft code or launch a browser.
"""
import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

STYLE = '''<style>body{margin:0}iframe{position:absolute;left:90px;top:305px;
width:1084px;height:561px;border:1px solid;border-radius:16px}</style>'''
HOST = '''<!doctype html>''' + STYLE + '''
<section id="work" hidden><iframe id="lesson" sandbox="allow-scripts"></iframe></section>
<script>fetch('/me').then(() => {
  lesson.onload = () => lesson.contentWindow.postMessage('ready', '*');
  lesson.src = '/child'; work.hidden = false;
})</script>'''
STATIC_HOST = '<!doctype html>' + STYLE + '<iframe id="lesson" sandbox="allow-scripts" src="/child"></iframe>'
CHILD = '''<!doctype html><style>body{margin:0}button{position:absolute;
left:592px;top:334px;width:111px;height:56px}
html:not([data-ready]) body{visibility:hidden}</style>
<script>addEventListener('message', () => document.documentElement.dataset.ready = 'true')</script>
<h1>Ready</h1><button onclick="document.querySelector('output').textContent='Clicked'">5. Grelha</button><output></output>'''
EVENTS = '''(() => {
  window.inputEvents = [];
  for (const type of ['pointermove', 'pointerdown', 'pointerup', 'click'])
    addEventListener(type, event => inputEvents.push({type,
      target:event.target.tagName, x:event.clientX, y:event.clientY}), true);
})()'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iterations', type=int, default=100)
    parser.add_argument('--sync-pointer', action='store_true')
    parser.add_argument('--static-frame', action='store_true')
    parser.add_argument('--failure-prefix', default='/tmp/pagecraft-cdp-iframe')
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('--iterations must be positive')
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(os.environ['PAGECRAFT_TEST_CDP'])
        context = browser.new_context()
        context.add_init_script(EVENTS)
        page = context.new_page()
        page.set_default_timeout(3000)
        host = STATIC_HOST if args.static_frame else HOST
        child = CHILD.replace('html:not([data-ready]) body', 'html[data-never] body') if args.static_frame else CHILD
        page.route('http://127.0.0.1:19999/**', lambda route: route.fulfill(
            content_type='text/html', body=child if route.request.url.endswith('/child') else host))
        iteration = -1
        try:
            page.goto('http://127.0.0.1:19999/host')
            for iteration in range(args.iterations):
                page.reload()
                lesson = page.frame_locator('#lesson')
                expect(lesson.get_by_role('heading', name='Ready')).to_be_visible()
                button = lesson.get_by_role('button', name='5. Grelha')
                if args.sync_pointer:
                    page.mouse.move(0, 0)
                    button.hover()
                    expect(lesson.locator('button:hover')).to_have_text('5. Grelha')
                button.click()
                expect(lesson.locator('output')).to_have_text('Clicked', timeout=3000)
            print(json.dumps({'browser':browser.version, 'passed':args.iterations,
                              'sync_pointer':args.sync_pointer, 'static_frame':args.static_frame}))
        except Exception:
            evidence = {'browser':browser.version, 'iteration':iteration, 'frames':[]}
            for frame in page.frames:
                evidence['frames'].append(frame.evaluate('''() => ({
                  events:window.inputEvents, output:document.querySelector('output')?.textContent,
                  button:[...document.querySelectorAll('button')].map(el => {
                    const rect=el.getBoundingClientRect();
                    return {rect:rect.toJSON(), inert:!!el.closest('[inert]'),
                      hit:document.elementFromPoint(rect.x+rect.width/2,rect.y+rect.height/2)?.tagName};
                  })})'''))
            Path(args.failure_prefix + '.json').write_text(json.dumps(evidence, indent=2))
            page.screenshot(path=args.failure_prefix + '.png')
            print(json.dumps(evidence))
            raise
        finally:
            context.close()


if __name__ == '__main__':
    main()
