"""Valida e compila percursos M28P a partir dos conteúdos revistos por palavra."""
from __future__ import annotations

import argparse
from collections import Counter
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator, ValidationError
from server.activity_support import embed_activity_support
from server.bridge_snippet import ensure_bridge_lite
from server.typography import embed_activity_typography

PHASES = {'context', 'recognition', 'syllables', 'code', 'transfer', 'comprehension', 'writing', 'communication', 'review'}
TYPES = {'choice', 'order', 'write', 'oral'}
SLUG = re.compile(r'^[a-z][a-z0-9-]*$')


def validate_content(data: dict) -> None:
    """Erros de autoria na fronteira; não tentar adivinhar fonologia ou repertório."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(isinstance(data, dict), 'O conteúdo deve ser um objeto JSON.')
    for field in ['slug', 'word', 'phonologyNotes', 'assistedReading']:
        require(isinstance(data.get(field), str) and data[field].strip(), f'Falta {field}.')
    require(bool(SLUG.fullmatch(data['slug'])), 'slug inválido.')
    require(type(data.get('order')) is int and 1 <= data['order'] <= 28, 'order deve ser 1–28.')
    for field, minimum, maximum in [('syllables', 1, 8), ('prerequisites', 1, 20), ('objectives', 2, 4), ('criteria', 2, 4)]:
        values = data.get(field)
        require(isinstance(values, list) and minimum <= len(values) <= maximum and all(isinstance(v, str) and v.strip() for v in values), f'{field}: lista de {minimum}–{maximum} textos.')
    require(''.join(data['syllables']).casefold() == data['word'].casefold(), 'As sílabas devem recompor a palavra, sem divisão automática.')
    sessions = data.get('sessions')
    require(isinstance(sessions, list) and 3 <= len(sessions) <= 4, 'São necessárias 3–4 sessões.')
    for session in sessions:
        require(isinstance(session, dict) and isinstance(session.get('title'), str) and type(session.get('minutes')) is int and 6 <= session['minutes'] <= 12, 'Sessão precisa de title e minutes entre 6 e 12.')
    pages = data.get('pages')
    require(isinstance(pages, list) and 12 <= len(pages) <= 16, 'São necessárias 12–16 páginas.')
    ids, phases, page_sessions = set(), set(), []
    for index, page in enumerate(pages, 1):
        label = f'Página {index}'
        require(isinstance(page, dict), f'{label}: objeto esperado.')
        for field in ['id', 'title', 'prompt']:
            require(isinstance(page.get(field), str) and page[field].strip(), f'{label}: falta {field}.')
        require(bool(SLUG.fullmatch(page['id'])) and page['id'] not in ids, f'{label}: id inválido ou repetido.')
        ids.add(page['id'])
        require(page.get('phase') in PHASES, f'{label}: phase desconhecida.')
        phases.add(page['phase'])
        require(page.get('type') in TYPES, f'{label}: type desconhecido.')
        require(type(page.get('session')) is int and 1 <= page['session'] <= len(sessions), f'{label}: session inválida.')
        page_sessions.append(page['session'])
        for field in ['text', 'challenge', 'adultPrompt', 'placeholder', 'criterion']:
            require(field not in page or isinstance(page[field], str), f'{label}: {field} tem de ser texto.')
        hints = page.get('hints')
        require(isinstance(hints, list) and 2 <= len(hints) <= 3, f'{label}: 2–3 pistas obrigatórias.')
        for mode in ['individual', 'group']:
            require(all(isinstance(hint, dict) and isinstance(hint.get(mode), str) and 1 <= len(hint[mode]) <= 400 for hint in hints), f'{label}: pistas precisam de {mode} com 1–400 caracteres.')
            require(len({hint[mode].strip().casefold() for hint in hints}) == len(hints), f'{label}: as pistas devem oferecer abordagens distintas.')
        kind = page['type']
        if kind == 'choice':
            options = page.get('options')
            require(isinstance(options, list) and 2 <= len(options) <= 5 and all(isinstance(v, str) and v.strip() for v in options) and len(set(options)) == len(options), f'{label}: options precisa de 2–5 textos distintos.')
            require(page.get('answer') in options, f'{label}: answer não pertence a options.')
        elif kind == 'order':
            pieces, answer = page.get('pieces'), page.get('answer')
            require(isinstance(pieces, list) and 2 <= len(pieces) <= 8 and all(isinstance(v, str) and v.strip() for v in pieces), f'{label}: pieces precisa de 2–8 textos.')
            require(isinstance(answer, list) and all(isinstance(v, str) for v in answer) and Counter(pieces) == Counter(answer), f'{label}: answer deve ordenar exatamente as mesmas peças.')
        else:
            require('answer' not in page, f'{label}: texto livre e oralidade não têm resposta correta automática.')
        if kind == 'oral':
            require(bool(page.get('adultPrompt')), f'{label}: oral exige adultPrompt.')
        if page['phase'] == 'code':
            require(bool(page.get('adultPrompt')), f'{label}: modelação som/grafema exige adultPrompt.')
    require(phases == PHASES, f'Fases em falta: {sorted(PHASES - phases)}.')
    require(page_sessions == sorted(page_sessions) and set(page_sessions) == set(range(1, len(sessions) + 1)), 'Sessões devem estar em ordem e ter páginas.')
    phase_list = [page['phase'] for page in pages]
    require(phase_list[0] == 'context' and phase_list[-1] == 'review', 'O percurso começa no contexto e termina na revisão.')
    require(any(page['phase'] == 'review' and page['type'] in {'oral', 'write'} for page in pages), 'A revisão exige observação oral adulta ou escrita, além de escolhas.')
    require(any(page['phase'] == 'writing' and page['type'] == 'write' for page in pages), 'A produção escrita precisa de campo aberto.')
    # O host limita checkpoints a 4096 bytes. A escrita admite 180 unidades
    # UTF-16; o runtime retira controlos C0 não textuais e surrogates isolados.
    # Texto válido ocupa até três bytes por unidade, incluindo escapes JSON.
    answers = {}
    for page in pages:
        if page['type'] == 'choice':
            answers[page['id']] = max(page['options'], key=lambda value: len(json.dumps(value, ensure_ascii=False).encode()))
        elif page['type'] == 'order':
            answers[page['id']] = list(range(len(page['pieces'])))
        else:
            answers[page['id']] = True if page['type'] == 'oral' else '€' * 180
    payload = {'activity': 'm28p-v2-' + data['slug'], 'version': 1, 'readyForReflection': False,
               'state': {'version': 1, 'page': len(pages) - 1, 'level': 'intermediate',
                         'answers': answers, 'confirmed': dict.fromkeys(answers, True)}}
    require(len(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()) <= 4096,
            'O checkpoint pode exceder 4096 bytes; reduzir a extensão das opções/identificadores ou pedidos escritos simultâneos.')


def docspec_for(data: dict) -> dict:
    units = []
    session_counts = Counter(page['session'] for page in data['pages'])
    session_positions = Counter()
    for page in data['pages']:
        criterion = page.get('criterion', page['prompt'])
        minutes = data['sessions'][page['session'] - 1]['minutes']
        quotient, remainder = divmod(minutes, session_counts[page['session']])
        duration = quotient + int(session_positions[page['session']] < remainder)
        session_positions[page['session']] += 1
        units.append({
            'summary': page['title'], 'textDescription': page['prompt'] + ' ' + page.get('adultPrompt', ''),
            'duration': duration,
            'interaction': {
                'state': [{'name': 'resposta', 'type': 'quiz' if page['type'] == 'choice' else 'sorting' if page['type'] == 'order' else 'derived', 'default': None}],
                'render': page.get('text', '') + ' ' + page['prompt'],
                'transition': 'Responder, confirmar, rever e avançar. Uma resposta incorreta não bloqueia.',
                'constraint': 'Manter o significado e relacionar a escrita com a linguagem oral, sem inferir domínio pela conclusão.',
                'assessment': criterion + (' Critério fechado verificável.' if page['type'] in {'choice', 'order'} else ' Produção ou declaração sem veredicto automático.')},
            'differentiation': {
                'support': 'Primeira pista local visível após pedido, leitura mediada e ação acompanhada.',
                'standard': 'Critério e pedido visíveis, pistas progressivas por pedido.',
                'challenge': page.get('challenge', 'Explica a tua estratégia a um colega ou adulto.')},
            'support': {
                'objective': page['prompt'][:400], 'criteria': [criterion[:250]],
                'obstacles': [{'id': page['id'], 'label': {'pt': 'Quero uma pista para este trabalho'},
                    'hints': [{'id': f'pista-{n}', 'text': {'pt': hint}} for n, hint in enumerate(page['hints'], 1)]}]}})
    spec = {
        'slug': 'm28p-v2-' + data['slug'], 'topic': 'Percurso da palavra ' + data['word'],
        'years': [1], 'order': data['order'],
        'tags': ['m28p', 'm28p-v2', 'leitura', 'escrita', '1ano'],
        'ageRange': '6-7 anos', 'duration': sum(s['minutes'] for s in data['sessions']),
        'objectives': data['objectives'],
        'curriculum': {'ae': [], 'competencies': ['PA-A: Linguagens e textos', 'PA-E: Relacionamento interpessoal', 'PA-F: Desenvolvimento pessoal e autonomia']},
        'curriculumNote': 'Proposta de trabalho de leitura e escrita; conferir alinhamento no documento pedagógico da coleção.',
        'memAlignment': {'modules': ['TEA (Trabalho de Estudo Autónomo)', 'Trabalho curricular comparticipado', 'Circuitos de comunicação'], 'instruments': ['Plano individual de trabalho', 'Registo de observação e autoavaliação'], 'socialOrganization': 'Mediação adulta, trabalho individual ou a pares, comunicação a um destinatário.'},
        'materials': ['Adulto disponível para leitura e modelação de sons', 'Papel e lápis', 'Texto ou objeto ligado à experiência da criança'],
        'sessionFlow': ' / '.join(s['title'] for s in data['sessions']),
        'support': {'version': 'm28p-v2-1', 'languages': ['pt'], 'automaticAfterFailures': 3},
        'units': units}
    Draft202012Validator(json.loads((ROOT / 'server/pipeline/schemas/docspec.schema.json').read_text())).validate(spec)
    return spec


def canonical_bridge() -> str:
    template = (ROOT / 'server/pipeline/prompts/template-base.html').read_text()
    start = template.index('    window.PageCraftBridge = (function () {')
    end = template.index('    /* Ouvir o embutidor', start)
    return template[start:end]


def render_html(data: dict, spec: dict) -> str:
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    content = (ROOT / 'scripts/templates/m28p-journey.html').read_text()
    content = content.replace('@@TITLE@@', html.escape('Percurso da palavra ' + data['word'])).replace('@@CONTENT@@', encoded).replace('@@BRIDGE@@', canonical_bridge())
    content = embed_activity_support(content, spec, 'm28p-v2-' + data['slug'])
    return embed_activity_typography(ensure_bridge_lite(content))


def build(content_path: Path, validate_only: bool = False) -> dict:
    data = json.loads(content_path.read_text())
    validate_content(data)
    if content_path.parent.name != data['slug']:
        raise ValueError('O slug deve coincidir com a pasta do conteúdo.')
    spec = docspec_for(data)
    rendered = render_html(data, spec)
    stem = 'm28p-v2-' + data['slug']
    artifacts = {
        stem + '.html': rendered,
        stem + '-docspec.json': spec,
        stem + '-design-spec.json': {'version': 1, 'visualDirection': 'Papel, tinta e caderno de palavras; uma ação por ecrã.', 'font': 'Century Gothic / Didact Gothic incorporada', 'bodyPx': 22, 'touchTargetPx': 56, 'layout': 'Coluna fluida até 50ch, sem arrastar, navegação por teclado.', 'levels': ['Com pistas', 'Passo a passo', 'Mais desafios'], 'feedback': 'Âmbar com pista concreta; avançar após resposta, incluindo incorreta.', 'representation': 'Textos do autor e peças manipuláveis. Sem imagens ou modelos na transferência e revisão.'},
        stem + '-activity.json': {'slug': stem, 'title': 'Percurso da palavra ' + data['word'], 'year': 1, 'duration': spec['duration'], 'group': 'm28p-v2', 'languages': ['pt'], 'requires_completion': True, 'criteria': [{'id': f'criterio-{i}', 'pt': value} for i, value in enumerate(data['criteria'], 1)]},
        stem + '-run-manifest.json': {'slug': stem, 'status': 'draft-generated', 'content': str(content_path.relative_to(ROOT)) if content_path.is_relative_to(ROOT) else str(content_path), 'html': stem + '.html', 'docspec': stem + '-docspec.json', 'design': stem + '-design-spec.json', 'teacherGuide': 'guia-docente.md', 'checks': {'contentContract': 'passed', 'docspecSchema': 'passed', 'contextualSupport': 'embedded', 'offlineFont': 'embedded', 'browserEvaluation': 'pending', 'teacherReview': 'pending'}, 'publication': 'not-published'}}
    if not validate_only:
        for name, value in artifacts.items():
            (content_path.parent / name).write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        # O registo canónico procura drafts/<slug>.html. Os dados de autoria
        # continuam agrupados por palavra, sem duplicar versões do mesmo HTML.
        if content_path.is_relative_to(ROOT / 'drafts/m28p-v2'):
            aliases = {name: name for name in artifacts}
            aliases[stem + '.md'] = 'guia-docente.md'
            for alias, target in aliases.items():
                link = ROOT / 'drafts' / alias
                relative = Path('m28p-v2') / data['slug'] / target
                if link.is_symlink():
                    if link.readlink() == relative:
                        continue
                    raise ValueError(f'O alias {link} aponta para outro destino.')
                if link.exists():
                    raise ValueError(f'O alias {link} já existe como ficheiro; preservar e rever manualmente.')
                link.symlink_to(relative)
    return {'word': data['word'], 'slug': data['slug'], 'pages': len(data['pages']), 'artifacts': list(artifacts), 'validation': 'passed'}


def build_index(base: Path, results: list[dict]) -> None:
    rows = []
    ordered = sorted(results, key=lambda result: json.loads((base / result['slug'] / 'content.json').read_text())['order'])
    for result in ordered:
        data = json.loads((base / result['slug'] / 'content.json').read_text())
        slug = html.escape(data['slug'], quote=True)
        rows.append(f'<li><a href="{slug}/m28p-v2-{slug}.html">{data["order"]}. {html.escape(data["word"])}</a>'
                    f'<p>{len(data["sessions"])} sessões · {len(data["pages"])} páginas · {sum(s["minutes"] for s in data["sessions"])} minutos no total</p>'
                    f'<a class="guide" href="{slug}/guia-docente.md">Guia docente</a></li>')
    content = '''<!doctype html><html lang="pt-PT"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisão docente · 28 palavras</title><style>
body{max-width:1000px;margin:auto;padding:24px;background:#fbf8ee;color:#253b45;font:22px/1.5 "Century Gothic","Didact Gothic",sans-serif}h1{font-size:36px}a{color:#234f63;display:inline-flex;align-items:center;min-height:56px}a:focus-visible{outline:4px solid #315d9e;outline-offset:4px}li{padding:16px 0;border-top:1px solid #bcb4a0}p{max-width:50ch}.guide{font-size:22px}ol{padding-left:28px;list-style:none}li p{margin:4px 0}</style></head><body><h1>Percursos das 28 palavras</h1><p>Área privada de revisão docente. Estes percursos são rascunhos e ainda não estão publicados para os alunos. A integração em main conserva o trabalho para revisão; cada atividade precisa de avaliação e aprovação docente.</p><p>As páginas apoiam o trabalho com um adulto. A conclusão não comprova domínio da leitura.</p><ol>'''+''.join(rows)+'</ol></body></html>'
    (base / 'index.html').write_text(embed_activity_typography(content))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--word')
    selection.add_argument('--all', action='store_true')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    if args.word and not SLUG.fullmatch(args.word):
        parser.error('--word deve ser um slug simples.')
    base = ROOT / 'drafts/m28p-v2'
    paths = sorted(base.glob('*/content.json')) if args.all else [base / args.word / 'content.json']
    if not paths:
        parser.error('Ainda não existem conteúdos para gerar.')
    failures, results = [], []
    for path in paths:
        try:
            result = build(path, args.validate_only)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
        except (ValueError, KeyError, TypeError, OSError, ValidationError) as error:
            failures.append(f'{path}: {error}')
    if args.all and not args.validate_only and not failures:
        build_index(base, results)
    for failure in failures:
        print(failure, file=sys.stderr)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
