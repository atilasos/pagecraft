"""Frases ditadas pela turma e avisos sobre o repertório cumulativo."""
import json
import re
from functools import lru_cache
from pathlib import Path

from scripts.m28p_cycle import validate_cycle


@lru_cache(maxsize=1)
def repertoire():
    base = Path(__file__).resolve().parents[2] / 'drafts/m28p-v3'
    words = sorted(json.loads((base / 'words.json').read_text()), key=lambda w: w['order'])
    cycle = json.loads((base / 'cycle.json').read_text())
    for word in words:
        cycle['keywords'].setdefault(word['slug'], {'newWords': [], 'sentences': []})
    return words, cycle, validate_cycle(cycle, words)


def session_keyword(session):
    slug = session.get('activity_slug', '')
    return next((w['slug'] for w in repertoire()[0] if slug.startswith(f"m28p-ciclo-{w['slug']}-")), None)


def prepare_sentence(text, keyword):
    _, cycle, pools = repertoire()
    if keyword not in pools:
        raise ValueError('Escolhe uma palavra-chave disponível.')
    text = ' '.join(text.split())
    tokens = re.findall(r'[^\W\d_]+', text)
    if not 2 <= len(tokens) <= 12:
        raise ValueError('Escreve uma frase com 2 a 12 palavras.')
    if text[-1] not in '.!?…':
        text += '.'
    pool = pools[keyword]
    known = {w['label'].lower() for w in pool['words']} | {w['word'].lower() for w in cycle['functionWords']}
    families = pool['families']
    letters = set(''.join(families))
    warnings = []
    for token in dict.fromkeys(tokens):
        word = token.lower()
        if word in known:
            continue
        reachable = {0}
        for start in range(len(word)):
            if start in reachable:
                reachable.update(start + len(part) for part in families if word.startswith(part, start))
        if len(word) in reachable:
            continue
        missing = sorted(set(word) - letters)
        warnings.append(f'“{token}” tem letras ainda não trabalhadas: {", ".join(missing)}' if missing else f'“{token}” tem sílabas ainda não trabalhadas.')
    return text, tokens, warnings
