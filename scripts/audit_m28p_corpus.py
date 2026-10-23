#!/usr/bin/env python3
"""Confere reservas e exposições escritas M28P; não avalia descodificação.

Uso: python3 scripts/audit_m28p_corpus.py [--root CAMINHO] [--json]
AdultPrompt e guias são notas privadas, não exposição infantil. Os cartões
realmente apresentados são declarados no manifesto e entram na cronologia.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*", re.UNICODE)
# Incluir também pistas, títulos e desafios: uma instrução vista já é exposição.
CHILD_FIELDS = ('text', 'prompt', 'options', 'answer', 'pieces', 'title',
                'hints', 'challenge', 'placeholder', 'criterion')


def normalize(value: str) -> str:
    return unicodedata.normalize('NFC', value).casefold()


def tokens(value: str) -> set[str]:
    found = set(WORD.findall(normalize(value)))
    # Uma palavra inteira mostrada por sílabas com hífen também foi exposta.
    return found | {word.replace('-', '') for word in found if '-' in word}


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def page_exposures(page: dict):
    for field in CHILD_FIELDS:
        for value in strings(page.get(field)):
            yield field, tokens(value)
        if field in ('pieces', 'answer') and page.get('type') == 'order':
            # A resposta ordenada recompõe a palavra mesmo com peças baralhadas.
            values = page.get(field, [])
            if isinstance(values, list) and all(isinstance(v, str) for v in values):
                yield field + '.juntas', tokens(''.join(values))


def audit(root: Path) -> dict:
    errors = []
    files = sorted((root / 'drafts/m28p-v2').glob('*/content.json'))
    contents = [json.loads(path.read_text()) for path in files]
    rows = json.loads((root / 'docs/m28p-corpus-reservado.json').read_text())
    by_slug = {data['slug']: data for data in contents}
    if len(contents) != 28 or len(by_slug) != 28:
        errors.append(f'Esperados 28 conteúdos distintos; encontrados {len(contents)}.')
    if len(rows) != 28 or {r['percurso'] for r in rows} != set(by_slug):
        errors.append('O manifesto deve conter exatamente uma linha por cada um dos 28 percursos.')
    if sorted(r['ordem'] for r in rows) != list(range(1, 29)):
        errors.append('As ordens do manifesto devem ser exatamente 1–28.')
    reservations = [normalize(row[k]['item']) for row in rows for k in ('inicial', 'diferido')]
    duplicates = sorted(item for item, count in Counter(reservations).items() if count > 1)
    if len(reservations) != 56 or duplicates:
        errors.append(f'Esperadas 56 reservas distintas; duplicados: {duplicates}.')

    # (ordem do percurso, página) estabelece a cronologia global.
    exposures = []
    for data in contents:
        if not 12 <= len(data['pages']) <= 16:
            errors.append(f"{data['slug']}: esperadas 12–16 páginas, há {len(data['pages'])}.")
        for n, page in enumerate(data['pages'], 1):
            exposures.extend(((data['order'], n), f"{data['slug']}:{n}:{field}", words)
                             for field, words in page_exposures(page))
    for row in rows:
        data = by_slug.get(row['percurso'])
        if not data:
            continue
        if (row['ordem'], row['palavra']) != (data['order'], data['word']):
            errors.append(f"{row['percurso']}: ordem/palavra diverge do conteúdo.")
        if not row.get('correspondencias') or not row.get('preEnsino') or not row.get('ensino'):
            errors.append(f"{row['percurso']}: faltam correspondências, pré-ensino ou fontes de ensino.")
        for card in row.get('cartoes', []):
            n = card['pagina']
            if not 1 <= n <= len(data['pages']):
                errors.append(f"{row['percurso']}: página de cartão inválida: {n}.")
                continue
            page = data['pages'][n - 1]
            if page['id'] != card['id'] or page['type'] != 'oral' or page['phase'] not in ('transfer', 'review'):
                errors.append(f"{row['percurso']}:{n}: referência de cartão divergente.")
            for item in card['itens']:
                if normalize(item) not in tokens(page.get('adultPrompt', '')):
                    errors.append(f"{row['percurso']}:{n}: cartão {item!r} ausente da instrução privada.")
                exposures.append(((data['order'], n), f"{row['percurso']}:{n}:cartao", tokens(item)))

    for row in rows:
        data = by_slug.get(row['percurso'])
        if not data:
            continue
        for kind, phase in [('inicial', 'transfer'), ('diferido', 'review')]:
            reserve = row[kind]
            item, n = normalize(reserve['item']), reserve['pagina']
            where = (data['order'], n)
            label = f"{row['percurso']}:{n} ({kind}, {reserve['item']})"
            if not 1 <= n <= len(data['pages']):
                errors.append(label + ': página inexistente.')
                continue
            page = data['pages'][n - 1]
            if page['phase'] != phase or page['id'] != reserve['id']:
                errors.append(label + ': fase/id não corresponde à reserva.')
            if reserve['suporte'] == 'cartao-adulto':
                matches = [c for c in row.get('cartoes', [])
                           if c['pagina'] == n and item in map(normalize, c['itens'])]
                if page['type'] != 'oral' or not matches:
                    errors.append(label + ': falta cartão oral declarado.')
            elif reserve['suporte'] == 'opcoes':
                if page['type'] != 'choice' or item not in map(normalize, page.get('options', [])):
                    errors.append(label + ': falta item nas opções.')
            else:
                errors.append(label + ': suporte desconhecido.')
            if not page.get('adultPrompt'):
                errors.append(label + ': falta observação adulta.')
            if kind == 'diferido' and page['session'] <= data['pages'][row['inicial']['pagina'] - 1]['session']:
                errors.append(label + ': revisão sem sessão posterior à transferência.')
            earlier = sorted({location for position, location, words in exposures
                              if position < where and item in words})
            if earlier:
                errors.append(label + ': exposição anterior em ' + ', '.join(earlier))
            for source in row.get('ensino', []):
                source_data = by_slug.get(source['percurso'])
                source_n = source['pagina']
                if not source_data or not 1 <= source_n <= len(source_data['pages']):
                    errors.append(label + ': fonte de ensino inexistente.')
                    continue
                source_page = source_data['pages'][source_n - 1]
                if source_page['id'] != source['id'] or source_page['phase'] != 'code':
                    errors.append(label + ': fonte não corresponde à página de código declarada.')
                if (source_data['order'], source_n) >= where:
                    errors.append(label + ': ensino declarado posterior à tentativa.')
    return {'percursos': len(contents), 'reservas': len(reservations),
            'reservas_distintas': len(set(reservations)), 'erros': errors,
            'limite': 'Auditoria documental de exposição e referências de ensino. Não verifica pronúncia, qualidade da descodificação, ensino efetivo com a criança, intervalo real ou autonomia.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true', help='Emitir relatório legível por ferramentas.')
    args = parser.parse_args()
    try:
        report = audit(args.root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Erro ao ler corpus/manifesto: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['percursos']} percursos; {report['reservas']} reservas; {report['reservas_distintas']} distintas.")
        for error in report['erros']:
            print('ERRO:', error)
        print(report['limite'])
        print('Exposição e referências: ' + ('FALHOU' if report['erros'] else 'sem conflitos documentados.'))
    return int(bool(report['erros']))


if __name__ == '__main__':
    raise SystemExit(main())
