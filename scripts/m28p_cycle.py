"""Dados cumulativos do ciclo M28P, independentes da lista editorial do piloto."""
import hashlib
from itertools import combinations
import re
import unicodedata

CYCLE_GAMES = {
    'listen-build': ('Ouvir e montar', 'Ouve e junta as sílabas.', 'Monto uma palavra a partir do áudio.'),
    'read-choose': ('Ler e escolher', 'Lê e escolhe a imagem.', 'Escolho a imagem da palavra escrita.'),
    'sentence': ('Montar frases', 'Ordena as palavras da frase.', 'Ordeno palavras para formar uma frase.'),
    'discover': ('Descobrir palavras', 'Junta sílabas. Descobre as palavras escondidas.', 'Experimento combinações e descubro palavras.'),
}


def asset_id(text, sentence=False):
    if sentence:
        return 'frase-' + hashlib.sha256(text.encode()).hexdigest()[:12]
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)).replace(' ', '-') + ('-circ' if 'ô' in text else '')


def validate_cycle(cycle, words):
    """Recusa grafias, segmentações e tokens fora do repertório disponível."""
    ordered = sorted(words, key=lambda w: w['order'])
    unknown = set(cycle['keywords']) - {w['slug'] for w in ordered}
    if unknown:
        raise ValueError(f'Palavras-chave desconhecidas: {sorted(unknown)}')
    conflicts = cycle.get('visualConflicts', [])
    labels = {w['label'] for w in words} | {
        w['label'] for section in cycle['keywords'].values() for w in section['newWords']}
    if not isinstance(conflicts, list) or any(
        not isinstance(group, list) or any(not isinstance(label, str) or label not in labels for label in group)
        for group in conflicts
    ):
        raise ValueError('visualConflicts deve conter grupos de palavras existentes.')
    consonants, known, sentences, result = set(), [], [], {}
    vowels = set(cycle['repertoire']['vowels'])
    if not vowels or any(len(v) != 1 or v not in 'aeiouáéíóúâêôãõà' for v in vowels):
        raise ValueError('Vogais inválidas no repertório.')
    introduced = ''
    for keyword in ordered:
        slug = keyword['slug']
        introduced += ' ' + keyword['label']
        consonants.update(cycle['repertoire']['consonantsByKeyword'].get(slug, []))
        families = vowels | {c + v for c in consonants for v in vowels}
        # Grupos só podem entrar por palavras-chave já trabalhadas.
        groups = [g for g in ('nh','lh','ch','rr','ss','qu','gu','ai','ei','oi','ui','au','eu','ou','ão','ãe','õe') if g in introduced]
        families |= {g + v for g in groups if g[-1] not in vowels for v in vowels}
        families |= set(groups)
        known.append(dict(keyword, picturable=True))
        if slug not in cycle['keywords']:
            continue
        section = cycle['keywords'][slug]
        for item in section['newWords']:
            label = item['label']
            if ''.join(item['syllables']) != label:
                raise ValueError(f'{slug}: concatenação das sílabas diferente da grafia: {label}')
            if not item['syllables'] or any(s not in families for s in item['syllables']):
                raise ValueError(f'{slug}: sílabas fora do repertório: {label}')
            if any(g in label and g not in groups for g in ('nh','lh','ch','rr','ss','ai','ei','oi','ui','au','eu','ou','ão','ãe','õe')):
                raise ValueError(f'{slug}: dígrafo ou ditongo ainda não introduzido: {label}')
            if label in {w['label'] for w in known}:
                raise ValueError(f'{slug}: palavra repetida: {label}')
            if not isinstance(item['picturable'], bool):
                raise ValueError(f'{slug}: picturable deve ser booleano: {label}')
            known.append(dict(item, slug=asset_id(label)))
        for function in cycle['functionWords']:
            text=function['word']
            reachable={0}
            for start in range(len(text)):
                if start in reachable:
                    reachable.update(start+len(part) for part in families if text.startswith(part,start))
            if len(text) not in reachable:
                raise ValueError(f'{slug}: palavra funcional fora do repertório: {function["word"]}')
        allowed = {w['label'] for w in known} | {w['word'] for w in cycle['functionWords']}
        for sentence in section['sentences']:
            tokens = sentence['tokens']
            if re.findall(r"[^\W\d_]+", sentence['text'].lower()) != [t.lower() for t in tokens]:
                raise ValueError(f'{slug}: tokens não reproduzem a frase: {sentence["text"]}')
            for token in tokens:
                if token.lower() not in allowed | families:
                    raise ValueError(f'{slug}: token fora do repertório: {token}')
            sentences.append(dict(sentence, slug=asset_id(sentence['text'], True)))
        if len({s['text'] for s in sentences}) != len(sentences):
            raise ValueError(f'{slug}: frases repetidas.')
        result[slug] = dict(words=list(known), sentences=list(sentences), families=sorted(families), visualConflicts=conflicts)
    return result


def image_choices(target, items, conflicts):
    """Escolhe duas imagens distinguíveis entre si e do alvo."""
    for pair in combinations((w for w in items if w['slug'] != target['slug']), 2):
        labels = {w['label'] for w in (target, *pair)}
        if all(len(labels.intersection(group)) <= 1 for group in conflicts):
            return [target, *pair]
    return []


def _plain(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)) == text


def formable(label, pieces, limit=3):
    """Indica se a palavra se forma juntando até `limit` peças diferentes do tabuleiro."""
    def search(rest, used, depth):
        if not rest:
            return True
        if depth == limit:
            return False
        return any(rest.startswith(piece) and search(rest[len(piece):], used | {i}, depth + 1)
                   for i, piece in enumerate(pieces) if i not in used)
    return search(label, frozenset(), 0)


def discover_rounds(current, vocabulary, families, rng, size=2, max_rounds=4):
    """Agrupa as palavras escondidas por ronda e escolhe sílabas suficientes, sem excesso.

    Cada ronda mostra as sílabas das suas palavras e uma sílaba a mais. As palavras
    escondidas são todas as do vocabulário que se formam com essas peças, para que o
    contador que a criança vê corresponda ao que é possível descobrir.
    """
    usable = [w for w in vocabulary if 2 <= len(w['syllables']) <= 3]
    start = next((i for i, w in enumerate(usable) if w['slug'] == current), len(usable))
    priority = usable[start:] + usable[:start]
    rounds = min(max_rounds, len(priority) // size)
    if not rounds:
        return []
    groups = [priority[i * size:(i + 1) * size] for i in range(rounds)]
    leftover = priority[rounds * size:]
    if len(leftover) == 1 and rounds < max_rounds:
        groups[-1].append(leftover[0])
    result = []
    for group in groups:
        counts = {}
        for word in group:
            for syllable in dict.fromkeys(word['syllables']):
                counts[syllable] = max(counts.get(syllable, 0), word['syllables'].count(syllable))
        pieces = [s for s, n in counts.items() for _ in range(n)]
        extra = sorted(s for s in families if len(s) >= 2 and _plain(s) and s not in counts)
        if extra:
            pieces.append(rng.choice(extra))
        hidden = list(group) + [w for w in usable if w not in group and formable(w['label'], pieces)]
        result.append(dict(pieces=pieces, hidden=hidden))
    return result
