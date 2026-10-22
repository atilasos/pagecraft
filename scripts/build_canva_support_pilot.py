"""Reconstrói a variante Canva de revisão sem alterar a atividade publicada."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'canva-animais-autonomia-piloto'


def build(*, check=False):
    source = (ROOT / 'activities/canva-animais-4ano/index.html').read_text()
    source = source.replace('canva-animais-4ano', SLUG)
    source = source.replace('Dois animais, três formas de comunicar', 'Dois animais, três formas de comunicar · Piloto de apoio')
    source = source.replace("else if(d.type==='ai_feedback'&&typeof p.text==='string'&&(!p.unit_id||p.unit_id==='u'+(state.step+1)))$('pagecraft-feedback').textContent=p.text.slice(0,1500);", "else if(d.type==='ai_feedback')receiveHint(p);")
    old = "PageCraftBridge.helpNeeded('u'+(state.step+1),'O grupo pediu ajuda nesta etapa.');$('save-message').textContent=embedded?'Pedido de ajuda enviado. Chama também o professor se precisares.':'Chama o professor e mostra esta etapa.'"
    assert old in source
    source = source.replace(old, 'requestTeacherHelp()')
    anchor = "window.addEventListener('message',e=>{if(!embedded"
    assert source.count(anchor) == 1
    source = source.replace(anchor, (ROOT / 'pilots/canva-autonomia/support.js').read_text()+'\n'+anchor)
    source = source.replace('</style>', '''
.context-support{border:2px solid var(--primary);border-radius:12px;padding:20px;margin-top:20px;background:#edf0e7}
.support-controls{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.context-support select{width:100%;max-width:450px;margin:10px 0;padding:10px}
.hint-action:not(:empty){font-size:23px;padding:18px;background:var(--paper);border-radius:8px;margin:16px 0}
</style>''', 1)
    target = ROOT / 'drafts' / (SLUG+'.html')
    if check:
        assert target.read_text() == source, 'Piloto desatualizado: executa scripts/build_canva_support_pilot.py'
    else:
        target.write_text(source)
    data = json.loads(re.search(r'const DATA=(.*);\nconst SLUG', source)[1])
    registration = {'slug': SLUG, 'title': 'Piloto Canva · Um próximo passo', 'year': 4,
                    'duration': 45, 'languages': ['pt'], 'criteria': data['criteria'], 'requires_completion': True}
    spec = json.loads((ROOT / 'activities/canva-animais-4ano/docspec.json').read_text().replace('canva-animais-4ano', SLUG))
    for suffix, content in [('registration', registration), ('docspec', spec)]:
        artifact = ROOT / 'drafts' / (SLUG+'-'+suffix+'.json')
        encoded = json.dumps(content, ensure_ascii=False, indent=2)+'\n'
        if check:
            assert artifact.read_text() == encoded, f'{artifact.name} desatualizado'
        else:
            artifact.write_text(encoded)
    return target, data


if __name__ == '__main__':
    import sys
    path, data = build(check='--check' in sys.argv)
    print(path.relative_to(ROOT))
