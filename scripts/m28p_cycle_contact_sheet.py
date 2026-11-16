"""Gera a folha de contacto do ciclo para revisão docente, sem alterar a v3."""
import html
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT/'assets/m28p-tic/manifest.json').read_text())
    entries = [dict(text=w, image=f'images/{w}.svg') for w in ('menina', 'menino', 'uva')]
    entries += [entry for entry in manifest['cycle'] if entry['image']]
    cards = ''.join(
        '<figure><img src="' + (ROOT/'assets/m28p-tic'/entry['image']).as_uri() +
        '"><figcaption>' + html.escape(entry['text']) + '</figcaption></figure>'
        for entry in entries)
    document = '''<!doctype html><meta charset="utf-8"><title>Imagens do ciclo M28P</title>
<style>body{margin:24px;font:18px Arial;background:#fff;color:#263e49}
h1{font-size:25px;margin:0 0 16px}main{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
figure{margin:0;border:1px solid #ccd6db;border-radius:8px;padding:8px;text-align:center}
img{width:168px;height:200px}figcaption{min-height:42px;font-size:18px}</style>
<h1>Ciclo M28P · imagens para revisão docente</h1><main>''' + cards + '</main>'
    output = ROOT/'drafts/m28p-v3/cycle-images-sheet.png'
    with tempfile.TemporaryDirectory(prefix='m28p-sheet-') as folder:
        page = Path(folder)/'sheet.html'
        page.write_text(document)
        subprocess.run(['google-chrome', '--headless=new', '--no-sandbox',
                        '--hide-scrollbars', '--screenshot='+str(output),
                        '--window-size=1320,1100', page.as_uri()], check=True,
                       capture_output=True)
    print(output)


if __name__ == '__main__':
    main()
