"""Gera exemplos técnicos do apoio comum, sem publicar atividades ou contactar IA."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.activity_support import embed_activity_support
from server.typography import embed_activity_typography


def render(spec):
    html = f'''<!doctype html><html lang="pt-PT"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(spec['topic'])} · Ensaio do apoio</title><style>
body{{margin:auto;max-width:900px;padding:24px;background:#f5f3ea;color:#233c32;font:20px/1.45 'Didact Gothic',sans-serif}}
textarea{{font:inherit;width:100%;box-sizing:border-box}}:focus-visible{{outline:3px solid #285cc0}}
h1{{font-size:30px}}.note{{font-size:18px}}</style></head><body>
<p class="note">Ensaio técnico do componente. Estes exemplos não são atividades completas de aula.</p>
<section id="u1"><h1>{escape(spec['topic'])}</h1><p>{escape(spec['units'][0]['support']['objective'])}</p>
<label for="attempt">Tentativa para o ensaio</label><textarea id="attempt" rows="2"></textarea>
<aside data-pagecraft-support="u1"></aside></section><script>
function sync(){{if(window.PageCraftSupport)PageCraftSupport.update({{unit_id:'u1',answer:document.getElementById('attempt').value,level:'intermediate'}})}}
document.addEventListener('pagecraft-support-ready',sync);
document.getElementById('attempt').addEventListener('input',sync);
</script></body></html>'''
    return embed_activity_typography(embed_activity_support(html, spec))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    examples=json.loads((ROOT/'tests/fixtures/support-examples.json').read_text())
    for example in examples:
        target=args.output/(example['slug']+'.html')
        target.write_text(render(example));print(target)


if __name__=='__main__':main()
