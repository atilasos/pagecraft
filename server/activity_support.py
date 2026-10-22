"""Compila o plano de apoio de cada atividade para HTML autocontido."""
from __future__ import annotations

import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
START = '<!-- pagecraft-support:start -->'
END = '<!-- pagecraft-support:end -->'


def support_configuration(docspec: dict, activity_id: str | None = None) -> dict | None:
    header = docspec.get('support')
    if header is None:
        if any('support' in unit for unit in docspec.get('units', [])):
            raise ValueError('O plano de apoio precisa de support.version na atividade.')
        return None
    schema = json.loads((ROOT / 'pipeline/schemas/docspec.schema.json').read_text())
    def validate(value, definition):
        Draft202012Validator({'$defs':schema['$defs'], '$ref':'#/$defs/'+definition}).validate(value)
    validate(header, 'ActivitySupport')
    languages = header.get('languages', ['pt'])
    if header.get('externalWork') and any(lang not in header['externalWork'] for lang in languages):
        raise ValueError('Falta traduzir o nome do trabalho externo para as línguas pedidas.')
    units = {}
    for i, unit in enumerate(docspec['units'], 1):
        plan = unit.get('support')
        if plan is None:
            raise ValueError(f'Falta o plano de apoio em u{i}.')
        validate(plan, 'UnitSupport')
        seen_obstacles = set()
        for obstacle in plan['obstacles']:
            if obstacle['id'] in seen_obstacles:
                raise ValueError(f'Obstáculo repetido em u{i}: {obstacle["id"]}')
            seen_obstacles.add(obstacle['id'])
            for lang in languages:
                if lang not in obstacle['label']:
                    raise ValueError(f'Falta label.{lang} em u{i}.')
                seen_ids, seen_text = set(), set()
                for hint in obstacle['hints']:
                    if lang not in hint['text']:
                        raise ValueError(f'Falta a pista em {lang} em u{i}.')
                    if hint['id'] in seen_ids:
                        raise ValueError(f'Identificador de pista repetido em u{i}.')
                    seen_ids.add(hint['id'])
                    text = tuple(' '.join(hint['text'][lang][mode].lower().split()) for mode in ['individual','group'])
                    if text in seen_text:
                        raise ValueError(f'As pistas de u{i} precisam de abordagens diferentes.')
                    seen_text.add(text)
        units[f'u{i}'] = dict(plan, title=unit['summary'])
    return {'activity':activity_id or docspec.get('slug') or docspec['topic'], 'activity_version':header['version'],
            'objective':'; '.join(docspec.get('objectives', [])), 'languages':languages,
            'externalWork':header.get('externalWork'), 'units':units}


def embed_activity_support(html: str, docspec: dict, activity_id: str | None = None) -> str:
    config = support_configuration(docspec, activity_id)
    if config is None:
        return html
    if not re.search(r'</body\s*>', html, re.I):
        raise ValueError('Falta </body> para incorporar o apoio.')
    runtime = (ROOT / 'pipeline/prompts/activity-support.js').read_text()
    styles = (ROOT / 'pipeline/prompts/activity-support.css').read_text()
    encoded = json.dumps(config, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    block = START+f'\n<style>{styles}</style>\n<script>{runtime}\nPageCraftSupport.configure({encoded});</script>\n'+END
    if START in html:
        return re.sub(re.escape(START)+r'.*?'+re.escape(END), lambda m:block, html, count=1, flags=re.S)
    return re.sub(r'</body\s*>', lambda m: block+'\n'+m[0], html, count=1, flags=re.I)
