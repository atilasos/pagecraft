"""Dados cumulativos do ciclo M28P, independentes da lista editorial do piloto.

O repertório é descrito por palavra-chave em unidades gráficas: ataques (consoante
ou dígrafo, com as vogais com que já foi trabalhado), núcleos (ditongos) e codas
(sílabas fechadas). Os contextos registam leituras que dependem da posição, como o
s entre vogais (/z/) ou o r brando.
"""
import hashlib
from itertools import combinations, permutations
import re
import unicodedata

CYCLE_GAMES = {
    'listen-build': ('Ouvir e montar', 'Ouve e junta as sílabas.', 'Monto uma palavra a partir do áudio.'),
    'read-choose': ('Ler e escolher', 'Lê e escolhe a imagem.', 'Escolho a imagem da palavra escrita.'),
    'sentence': ('Montar frases', 'Ordena as palavras da frase.', 'Ordeno palavras para formar uma frase.'),
    'discover': ('Descobrir palavras', 'Junta sílabas. Descobre as palavras escondidas.', 'Experimento combinações e descubro palavras.'),
}
VOWEL_BASES = {'a': 'aáâ', 'e': 'eéê', 'i': 'ií', 'o': 'oóô', 'u': 'uú'}
# Ditongos orais e nasais que só podem aparecer dentro de uma unidade já introduzida.
DIPHTHONGS = ('ai', 'au', 'ei', 'eu', 'iu', 'oi', 'ou', 'ui', 'ão', 'ãe', 'õe')
TOKEN = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
MIN_ROUNDS = {'listen-build': 3, 'read-choose': 3, 'sentence': 1, 'discover': 1}


def plain(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))


def asset_id(text, sentence=False):
    if sentence:
        return 'frase-' + hashlib.sha256(text.encode()).hexdigest()[:12]
    return plain(text).replace(' ', '-') + ('-circ' if 'ô' in text else '')


def tokens_of(text):
    return TOKEN.findall(text)


def units_until(repertoire, slugs, index):
    """Unidades gráficas disponíveis depois de trabalhar as palavras-chave 0..index."""
    vowels = set(repertoire['vowels'])
    onsets, nuclei, codas = {}, set(), set()
    for slug in slugs[:index + 1]:
        spec = repertoire['byKeyword'].get(slug, {})
        for onset, bases in spec.get('onsets', {}).items():
            onsets.setdefault(onset, set()).update(bases)
        nuclei.update(spec.get('nuclei', []))
        codas.update(spec.get('codas', []))
    units = set(vowels) | nuclei
    for onset, bases in onsets.items():
        units |= {onset + v for v in vowels if plain(v) in bases}
        units |= {onset + n for n in nuclei if n[0] in bases}
    units |= {u + c for u in list(units) for c in codas if u[-1] in vowels}
    return units


def _context_errors(label, index, repertoire, slugs):
    return [rule['reason'] for rule in repertoire.get('contexts', [])
            if re.search(rule['pattern'], label) and slugs.index(rule['from']) > index]


def _diphthong_errors(label, syllables):
    """Um ditongo que atravessa a fronteira silábica não foi trabalhado como unidade."""
    bounds, start = [], 0
    for syllable in syllables:
        bounds.append((start, start + len(syllable)))
        start += len(syllable)
    errors = []
    for d in DIPHTHONGS:
        for match in re.finditer(d, label):
            if not any(a <= match.start() and match.end() <= b for a, b in bounds):
                errors.append(d)
    return errors


def readable_at(label, syllables, index, repertoire, slugs):
    if not syllables or ''.join(syllables) != label:
        return False
    units = units_until(repertoire, slugs, index)
    return (all(s in units for s in syllables) and not _context_errors(label, index, repertoire, slugs)
            and not _diphthong_errors(label, syllables))


def _check_item(slug, item, index, repertoire, slugs, lexicon, first_rule=True):
    label, syllables = item['label'], item['syllables']
    if ''.join(syllables) != label:
        raise ValueError(f'{slug}: concatenação das sílabas diferente da grafia: {label}')
    units = units_until(repertoire, slugs, index)
    if not syllables or any(s not in units for s in syllables):
        raise ValueError(f'{slug}: sílabas fora do repertório: {label}')
    if errors := _context_errors(label, index, repertoire, slugs):
        raise ValueError(f'{slug}: leitura ainda não trabalhada em {label}: {errors[0]}')
    if errors := _diphthong_errors(label, syllables):
        raise ValueError(f'{slug}: dígrafo ou ditongo ainda não introduzido: {label} ({errors[0]})')
    if first_rule and index and readable_at(label, syllables, index - 1, repertoire, slugs):
        earlier = next(i for i in range(index) if readable_at(label, syllables, i, repertoire, slugs))
        raise ValueError(f'{slug}: {label} já é formável em {slugs[earlier]}; entra na primeira palavra-chave possível.')
    if lexicon is not None and not lexicon(label):
        raise ValueError(f'{slug}: {label} não consta do dicionário pt-PT.')


def validate_cycle(cycle, words, lexicon=None):
    """Recusa grafias, segmentações e tokens fora do repertório disponível."""
    ordered = sorted(words, key=lambda w: w['order'])
    slugs = [w['slug'] for w in ordered]
    unknown = set(cycle['keywords']) - set(slugs)
    repertoire = cycle['repertoire']
    if unknown:
        raise ValueError(f'Palavras-chave desconhecidas: {sorted(unknown)}')
    if set(repertoire['byKeyword']) - set(slugs):
        raise ValueError('O repertório refere palavras-chave desconhecidas.')
    vowels = set(repertoire['vowels'])
    if not vowels or any(len(v) != 1 or plain(v) not in VOWEL_BASES for v in vowels):
        raise ValueError('Vogais inválidas no repertório.')
    articles = cycle.get('keywordArticles', {})
    for index, keyword in enumerate(ordered):
        if not readable_at(keyword['label'], keyword['syllables'], index, repertoire, slugs):
            raise ValueError(f"O repertório não cobre a palavra-chave {keyword['label']}.")
        if keyword['slug'] in cycle['keywords'] and articles.get(keyword['slug']) not in ('a', 'o'):
            raise ValueError(f"Falta o artigo de {keyword['label']} em keywordArticles.")
    conflicts = cycle.get('visualConflicts', [])
    labels = {w['label'] for w in words} | {
        w['label'] for section in cycle['keywords'].values() for w in section['newWords']}
    if not isinstance(conflicts, list) or any(
        not isinstance(group, list) or any(not isinstance(label, str) or label not in labels for label in group)
        for group in conflicts
    ):
        raise ValueError('visualConflicts deve conter grupos de palavras existentes.')
    for function in cycle['functionWords']:
        if not readable_at(function['word'], function.get('syllables', [function['word']]), 0, repertoire, slugs):
            raise ValueError(f'Palavra funcional fora do repertório: {function["word"]}')
    function_words = {f['word'] for f in cycle['functionWords']}
    ids = {}
    known, extra, sentences, result = [], [], [], {}
    for index, keyword in enumerate(ordered):
        slug = keyword['slug']
        item = dict(keyword, picturable=True, keyword=True, newIn=slug)
        known.append(item)
        ids.setdefault(asset_id(keyword['label']), keyword['label'])
        if slug not in cycle['keywords']:
            continue
        section = cycle['keywords'][slug]
        current = []
        for entry in section['newWords']:
            label = entry['label']
            _check_item(slug, entry, index, repertoire, slugs, lexicon)
            if label in {w['label'] for w in known + extra}:
                raise ValueError(f'{slug}: palavra repetida: {label}')
            if not isinstance(entry['picturable'], bool):
                raise ValueError(f'{slug}: picturable deve ser booleano: {label}')
            ident = asset_id(label)
            if ids.get(ident, label) != label:
                raise ValueError(f'{slug}: {label} e {ids[ident]} partilhariam os mesmos recursos ({ident}).')
            ids[ident] = label
            word = dict(entry, slug=ident, newIn=slug)
            known.append(word)
            current.append(word)
        for entry in section.get('sentenceWords', []):
            _check_item(slug, entry, index, repertoire, slugs, lexicon)
            if entry['label'] in {w['label'] for w in known + extra}:
                raise ValueError(f'{slug}: palavra repetida: {entry["label"]}')
            extra.append(dict(entry, newIn=slug))
        allowed = {w['label'].lower() for w in known + extra} | function_words
        for sentence in section['sentences']:
            tokens = sentence['tokens']
            if [t.lower() for t in tokens_of(sentence['text'])] != [t.lower() for t in tokens]:
                raise ValueError(f'{slug}: tokens não reproduzem a frase: {sentence["text"]}')
            for token in tokens:
                if token.lower() not in allowed:
                    raise ValueError(f'{slug}: token fora do repertório: {token}')
            for alternative in sentence.get('alternatives', []):
                if sorted(alternative) != sorted(tokens) or alternative == tokens:
                    raise ValueError(f'{slug}: ordem alternativa inválida em {sentence["text"]}')
            lowered = [t.lower() for t in tokens]
            if (len(tokens) == 5 and lowered[2] in ('é', 'e') and lowered[0] == lowered[3]
                    and [tokens[0], tokens[4], tokens[2], tokens[3], tokens[1]] not in sentence.get('alternatives', [])):
                raise ValueError(f'{slug}: a frase admite a ordem inversa; registar alternatives: {sentence["text"]}')
            if not isinstance(sentence.get('scene'), list) or not sentence['scene']:
                raise ValueError(f'{slug}: falta a cena ilustrada de {sentence["text"]}')
            sentences.append(dict(sentence, slug=asset_id(sentence['text'], True), newIn=slug))
        if len({s['text'] for s in sentences}) != len(sentences):
            raise ValueError(f'{slug}: frases repetidas.')
        result[slug] = dict(
            keyword=dict(item, article=articles[slug]), words=list(known), newWords=list(current), sentenceWords=list(extra),
            sentences=list(sentences), families=sorted(units_until(repertoire, slugs, index)),
            visualConflicts=conflicts)
    return result


def newest_first(pool, predicate=lambda w: True):
    """Palavras novas desta palavra-chave primeiro; depois as anteriores, das mais recentes para as mais antigas."""
    current = pool['keyword']['slug']
    fresh = [w for w in pool['newWords'] if predicate(w)]
    rest = [w for w in reversed(pool['words']) if w['slug'] != current and w not in fresh and predicate(w)]
    return fresh + rest


def _compatible(labels, conflicts):
    return all(len(set(labels).intersection(group)) <= 1 for group in conflicts)


def image_choices(target, items, conflicts, rng=None, usage=None):
    """Escolhe duas imagens distinguíveis entre si e do alvo, rodando os distratores."""
    pairs = [pair for pair in combinations((w for w in items if w['slug'] != target['slug']), 2)
             if _compatible({w['label'] for w in (target, *pair)}, conflicts)]
    if not pairs:
        return []
    if rng is not None:
        rng.shuffle(pairs)
    if usage is not None:
        pairs.sort(key=lambda pair: sum(usage.get(w['slug'], 0) for w in pair))
    return [target, *pairs[0]]


def near_syllables(units, families, rng, count=3):
    """Distratores do mesmo tamanho e da mesma família (mesmo ataque ou mesma vogal)."""
    lengths = {len(u) for u in units}
    accented = any(plain(u) != u for u in units)
    pool = [f for f in families if len(f) in lengths and f not in units and (accented or plain(f) == f)]
    def closeness(candidate):
        score = 0
        for unit in units:
            if plain(candidate) == plain(unit):
                score = max(score, 3)
            elif candidate[:-1] == unit[:-1] and candidate[:-1]:
                score = max(score, 2)
            elif plain(candidate[-1]) == plain(unit[-1]):
                score = max(score, 1)
        return score
    rng.shuffle(pool)
    pool.sort(key=closeness, reverse=True)
    return pool[:count]


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


def _combined_words(pieces, must, limit=3):
    words = set()
    for size in range(2, limit + 1):
        for order in permutations(range(len(pieces)), size):
            if must in order:
                words.add(''.join(pieces[i] for i in order))
    return words


def discover_rounds(pool, rng, lexicon=None, max_rounds=4, max_hidden=3):
    """Agrupa as palavras escondidas por ronda e escolhe sílabas suficientes, sem excesso.

    Cada ronda mostra só as sílabas das suas palavras e uma sílaba a mais. As palavras
    escondidas são todas as do vocabulário que se formam com essas peças, para que o
    contador corresponda ao que é possível descobrir, e nunca passam de três. A sílaba a
    mais é escolhida para não formar palavras do vocabulário nem, havendo dicionário,
    outras palavras reais.
    """
    usable = newest_first(pool, lambda w: 2 <= len(w['syllables']) <= 3)
    remaining, rounds = list(usable), []
    def board(group):
        counts = {}
        for word in group:
            for syllable in dict.fromkeys(word['syllables']):
                counts[syllable] = max(counts.get(syllable, 0), word['syllables'].count(syllable))
        pieces = [s for s, n in counts.items() for _ in range(n)]
        hidden = list(group) + [w for w in usable if w not in group and formable(w['label'], pieces)]
        return pieces, hidden
    while len(remaining) >= 2 and len(rounds) < max_rounds:
        size = 3 if len(remaining) == 3 else 2
        found = None
        used = {w['label'] for r in rounds for w in r['hidden']}
        # Primeiro, tabuleiros que não voltam a esconder palavras de rondas anteriores.
        for strict in (True, False):
            for first in range(len(remaining)):
                for others in combinations(range(first + 1, len(remaining)), size - 1):
                    group = [remaining[first]] + [remaining[i] for i in others]
                    pieces, hidden = board(group)
                    if len(hidden) <= max_hidden and not (strict and used & {w['label'] for w in hidden}):
                        found = pieces, hidden
                        break
                if found:
                    break
            if found:
                break
        if not found:
            break
        pieces, hidden = found
        labels = {w['label'] for w in hidden}
        vocabulary = {w['label'] for w in pool['words']}
        candidates = sorted(s for s in pool['families'] if len(s) >= 2 and plain(s) == s and s not in pieces)
        rng.shuffle(candidates)
        best = None
        for candidate in candidates:
            board_pieces = pieces + [candidate]
            if any(w not in hidden and formable(w['label'], board_pieces) for w in usable):
                continue
            made = _combined_words(board_pieces, len(pieces)) - labels
            clash = len(made & vocabulary) * 10 + (sum(1 for word in made if lexicon(word)) if lexicon else 0)
            if best is None or clash < best[0]:
                best = (clash, candidate)
            if clash == 0:
                break
        if best:
            pieces = pieces + [best[1]]
        rounds.append(dict(pieces=pieces, hidden=hidden))
        remaining = [w for w in remaining if w['label'] not in labels]
    return rounds
