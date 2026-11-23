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
    'listen-build': ('Ouvir e montar', 'Ouve e junta as sílabas.', 'Monto a palavra que ouvi.'),
    'read-choose': ('Ler e escolher', 'Lê a palavra. Escolhe a imagem certa.', 'Escolho a imagem da palavra que li.'),
    'sentence': ('Montar frases', 'Ordena as palavras da frase.', 'Ordeno palavras para formar uma frase.'),
    'discover': ('Descobrir palavras', 'Junta as sílabas. Descobre as palavras escondidas.', 'Junto sílabas e descubro palavras.'),
}
VOWEL_BASES = {'a': 'aáâ', 'e': 'eéê', 'i': 'ií', 'o': 'oóô', 'u': 'uú'}
# Ditongos orais e nasais que só podem aparecer dentro de uma unidade já introduzida.
DIPHTHONGS = ('ai', 'ao', 'au', 'ei', 'eu', 'iu', 'oi', 'ou', 'ui', 'ão', 'ãe', 'õe',
              'ái', 'áu', 'éi', 'éu', 'êi', 'êu', 'ói', 'ôu', 'óu')
# Só estes podem ser hiatos declarados («ra-i-nha»); «ão», «ãe», «õe» nunca se separam.
ORAL_DIPHTHONGS = tuple(d for d in DIPHTHONGS if d not in ('ão', 'ãe', 'õe'))
# Dígrafos que só se leem dentro de uma unidade já trabalhada («ss» de passarinho, não «s» de escada + «s»).
DIGRAPHS = ('ch', 'lh', 'nh', 'rr', 'ss', 'qu', 'gu')
VOWELS = set('aeiouáéíóúâêôãõà')
TOKEN = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
MIN_ROUNDS = {'listen-build': 3, 'read-choose': 3, 'sentence': 1, 'discover': 1}


def plain(text):
    """Sem acentos; o «ç» mantém-se, porque é outra letra e não um acento."""
    return unicodedata.normalize('NFC', ''.join(c for c in unicodedata.normalize('NFD', text)
                                                if not unicodedata.combining(c) or c == '\u0327'))


def asset_id(text, sentence=False):
    if sentence:
        return 'frase-' + hashlib.sha256(text.encode()).hexdigest()[:12]
    # Os IDs dos recursos retiram todos os diacríticos, incluindo o «ç», para se manterem estáveis.
    bare = ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))
    return bare.replace(' ', '-') + ('-circ' if 'ô' in text else '')


def leftover(text):
    """O que a frase tem fora das palavras e da pontuação (números, símbolos): não cabe nos cartões."""
    return TOKEN.sub('', text).strip(' ,.;:!?…«»"\'-—')


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
        units |= {onset + n for n in nuclei if plain(n[0]) in bases}
    # Sílabas fechadas só depois de vogal simples (não depois de ditongo: «roul» não é uma sílaba do repertório).
    units |= {u + c for u in list(units) for c in codas if u[-1] in vowels and not any(u.endswith(n) for n in nuclei)}
    return units


def _context_errors(label, index, repertoire, slugs):
    return [rule['reason'] for rule in repertoire.get('contexts', [])
            if re.search(rule['pattern'], label) and slugs.index(rule['from']) > index]


def _boundary_errors(label, syllables, hiatus=False):
    """Fronteiras silábicas inválidas: uma consoante entre vogais vai para a sílaba seguinte («sa-la», não «sal-a»),
    e nenhum ditongo ou dígrafo se parte entre duas sílabas."""
    errors, start = [], 0
    for current, following in zip(syllables, syllables[1:]):
        start += len(current)
        if current[-1] not in VOWELS and following[0] in VOWELS:
            errors.append(f'{current}-{following}')
        # «gu»/«qu» seguidos de vogal leem-se juntos («fo-guei-ra», não «fo-gu-ei-ra»; «á-gua» não é «á-gu-a»).
        if current.endswith(('gu', 'qu')) and following[0] in VOWELS:
            errors.append(f'{current}-{following}')
        pair = label[start - 1:start + 1]
        # Um hiato declarado só dispensa a fronteira entre duas vogais («ra-i-nha»), nunca as restantes regras.
        if (pair in DIPHTHONGS and not (hiatus and pair in ORAL_DIPHTHONGS)) or pair in DIGRAPHS:
            errors.append(pair)
    return errors


def _diphthong_errors(label, syllables, hiatus=False):
    """Um ditongo ou dígrafo que atravessa a fronteira silábica não foi trabalhado como unidade."""
    bounds, start = [], 0
    for syllable in syllables:
        bounds.append((start, start + len(syllable)))
        start += len(syllable)
    errors = []
    for d in DIPHTHONGS + DIGRAPHS:
        for match in re.finditer(d, label):
            if not any(a <= match.start() and match.end() <= b for a, b in bounds):
                if hiatus and d in ORAL_DIPHTHONGS and any(b == match.start() + 1 for _, b in bounds):
                    continue
                errors.append(d)
    return errors


def readable_at(label, syllables, index, repertoire, slugs, hiatus=False):
    if not syllables or ''.join(syllables) != label:
        return False
    units = units_until(repertoire, slugs, index)
    return (all(s in units for s in syllables) and not _context_errors(label, index, repertoire, slugs)
            and not _diphthong_errors(label, syllables, hiatus) and not _boundary_errors(label, syllables, hiatus))


def segmentations(label, units):
    """Todas as divisões da palavra em unidades do repertório."""
    result = []
    def search(start, parts):
        if start == len(label):
            result.append(parts)
            return
        for end in range(start + 1, len(label) + 1):
            if label[start:end] in units:
                search(end, parts + [label[start:end]])
    search(0, [])
    return result


def readable_word(label, index, repertoire, slugs):
    """Indica se alguma divisão da palavra se lê com o que foi trabalhado até à palavra-chave index.

    Percorre as posições alcançáveis (tempo quadrático no comprimento), porque todas as regras de
    fronteira são locais; os contextos dependem só da grafia."""
    if _context_errors(label, index, repertoire, slugs):
        return False
    units = units_until(repertoire, slugs, index)
    longest = max(map(len, units))
    reachable = {0: None}
    for start in range(len(label)):
        if start not in reachable:
            continue
        previous = reachable[start]
        for end in range(start + 1, min(len(label), start + longest) + 1):
            unit = label[start:end]
            if unit not in units or end in reachable:
                continue
            if previous is not None and (previous[-1] not in VOWELS and unit[0] in VOWELS
                                         or previous.endswith(('gu', 'qu')) and unit[0] in VOWELS
                                         or label[start - 1:start + 1] in DIPHTHONGS + DIGRAPHS):
                continue
            reachable[end] = unit
    return len(label) in reachable


def _check_item(slug, item, index, repertoire, slugs, lexicon, first_rule=True):
    label, syllables = item['label'], item['syllables']
    if ''.join(syllables) != label:
        raise ValueError(f'{slug}: concatenação das sílabas diferente da grafia: {label}')
    units = units_until(repertoire, slugs, index)
    if not syllables or any(s not in units for s in syllables):
        raise ValueError(f'{slug}: sílabas fora do repertório: {label}')
    if errors := _context_errors(label, index, repertoire, slugs):
        raise ValueError(f'{slug}: leitura ainda não trabalhada em {label}: {errors[0]}')
    hiatus = bool(item.get('hiatus'))
    if errors := _diphthong_errors(label, syllables, hiatus):
        raise ValueError(f'{slug}: ditongo ou dígrafo partido, ou ainda não introduzido, em {label} ({errors[0]}); '
                         'se for um hiato («ra-i-nha»), registar hiatus: true')
    if errors := _boundary_errors(label, syllables, hiatus):
        raise ValueError(f'{slug}: divisão silábica inválida em {label}: {errors[0]}')
    if first_rule and index and readable_at(label, syllables, index - 1, repertoire, slugs, hiatus):
        earlier = next(i for i in range(index) if readable_at(label, syllables, i, repertoire, slugs, hiatus))
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
        start = slugs.index(function.get('from', slugs[0]))
        if not readable_at(function['word'], function.get('syllables', [function['word']]), start, repertoire, slugs):
            raise ValueError(f'Palavra funcional fora do repertório: {function["word"]}')
    ids = {}
    known, extra, sentences, result = [], [], [], {}
    for index, keyword in enumerate(ordered):
        slug = keyword['slug']
        item = dict(keyword, picturable=True, keyword=True, newIn=slug)
        known.append(item)
        if ids.get(asset_id(keyword['label']), keyword['label']) != keyword['label']:
            raise ValueError(f"{keyword['label']} e {ids[asset_id(keyword['label'])]} partilhariam os mesmos recursos.")
        ids[asset_id(keyword['label'])] = keyword['label']
        if slug not in cycle['keywords']:
            continue
        section = cycle['keywords'][slug]
        current = []
        for entry in section['newWords']:
            label = entry['label']
            if label in {w['label'] for w in ordered}:
                raise ValueError(f'{slug}: {label} é uma palavra-chave e não pode ser palavra nova.')
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
            # Verbos e adjetivos das frases não são itens de jogo: entram quando uma frase precisa deles.
            _check_item(slug, entry, index, repertoire, slugs, lexicon, first_rule=False)
            if entry['label'] in {w['label'] for w in known + extra}:
                raise ValueError(f'{slug}: palavra repetida: {entry["label"]}')
            extra.append(dict(entry, newIn=slug))
        function_words = {f['word'] for f in cycle['functionWords'] if slugs.index(f.get('from', slugs[0])) <= index}
        allowed = {w['label'].lower() for w in known + extra} | function_words
        for sentence in section['sentences']:
            tokens = sentence['tokens']
            if [t.lower() for t in tokens_of(sentence['text'])] != [t.lower() for t in tokens]:
                raise ValueError(f'{slug}: tokens não reproduzem a frase: {sentence["text"]}')
            # Tudo o que se lê ou ouve tem de estar nos cartões: só palavras, espaços e pontuação.
            if leftover(sentence['text']) or not 2 <= len(tokens) <= 12:
                raise ValueError(f'{slug}: a frase tem conteúdo fora dos cartões ou um número de palavras fora de 2 a 12: {sentence["text"]}')
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
            if not isinstance(sentence.get('scene'), list) or not 1 <= len(sentence['scene']) <= 2:
                raise ValueError(f'{slug}: falta a cena ilustrada de {sentence["text"]}')
            sentences.append(dict(sentence, slug=asset_id(sentence['text'], True), newIn=slug))
        if len({s['text'] for s in sentences}) != len(sentences):
            raise ValueError(f'{slug}: frases repetidas.')
        result[slug] = dict(
            keyword=dict(item, article=articles[slug]), words=list(known), newWords=list(current), sentenceWords=list(extra),
            functionWords=sorted(function_words), excluded=cycle['policy'].get('excludedFromSource', []),
            discoverBoards=section.get('discoverBoards'), index=index, repertoire=repertoire, slugs=slugs,
            avoidWords=sorted(cycle.get('knownWords', {}).get('avoid', [])),
            knownWords=sorted(set(cycle.get('knownWords', {}).get('words', [])) | {w['label'] for w in ordered}
                              | {w['label'] for sec in cycle['keywords'].values() for w in sec['newWords'] + sec.get('sentenceWords', [])}),
            sentences=list(sentences), families=sorted(units_until(repertoire, slugs, index)),
            visualConflicts=conflicts)
    return result


def newest_first(pool, predicate=lambda w: True, reserved=()):
    """Palavras novas desta palavra-chave primeiro; depois as anteriores, das mais recentes para as mais antigas.

    A palavra-chave e as palavras reservadas para a demonstração nunca são rondas."""
    excluded = {pool['keyword']['slug'], *reserved}
    fresh = [w for w in pool['newWords'] if predicate(w) and w['slug'] not in excluded]
    rest = [w for w in reversed(pool['words']) if w['slug'] not in excluded and w not in fresh and predicate(w)]
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


def demo_word(pool, low=2, high=3):
    """Exemplo da demonstração: a palavra-chave, ou a palavra-chave anterior mais recente com 2 a 3 sílabas
    quando a atual não cabe no jogo («flor» tem uma sílaba, «passarinho» tem quatro)."""
    keywords = [w for w in pool['words'] if w.get('keyword')]
    for word in reversed(keywords):
        if low <= len(word['syllables']) <= high:
            return word
    return keywords[-1]


def vocabulary_syllables(pool):
    """Sílabas que a criança já viu em palavras: são estas as candidatas a distrator."""
    return sorted({s for w in pool['words'] for s in w['syllables']})


def near_syllables(units, families, rng, count=3, preferred=None):
    """Distratores do mesmo tamanho e da mesma família (mesmo ataque ou mesma vogal).

    Dá prioridade a sílabas que já apareceram em palavras (`preferred`), para não mostrar
    combinações estranhas do repertório; só recorre às restantes quando faltam candidatas.
    """
    lengths = {len(u) for u in units}
    accented = any(plain(u) != u for u in units)
    def fits(f):
        return len(f) in lengths and f not in units and (plain(f) == f or (accented and plain(f) in {plain(u) for u in units}))
    pool = [f for f in (preferred or []) if fits(f)]
    if len(pool) < count:
        pool += [f for f in families if fits(f) and f not in pool and plain(f) == f]
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
    favoured = set(preferred or [])
    # Primeiro a mesma família da peça-alvo (ataque ou vogal); entre iguais, as sílabas já vistas.
    pool.sort(key=lambda f: (closeness(f), f in favoured), reverse=True)
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


def board_weight(words, known, avoid=()):
    """Peso das palavras formadas por acaso: conhecidas (celebradas ou a evitar) pesam 1, formas raras 0.25."""
    familiar = set(known) | set(avoid)
    return sum(1 if word in familiar else 0.25 for word in words)


def celebrated_sequences(pieces, words, known, index, repertoire, slugs):
    """Sequências de peças («ne·la») que formam uma palavra comum com uma divisão válida nesta etapa.

    «nel·a» não conta (divisão inválida) e «po·sa» não conta antes de casa (s entre vogais)."""
    result = set()
    for size in range(2, 4):
        for order in permutations(range(len(pieces)), size):
            parts = [pieces[i] for i in order]
            word = ''.join(parts)
            if word in words and word in known and readable_at(word, parts, index, repertoire, slugs):
                result.add('·'.join(parts))
    return sorted(result)


def discover_rounds(pool, rng, lexicon=None, max_rounds=4, max_hidden=3, reserved=()):
    """Agrupa as palavras escondidas por ronda e escolhe sílabas suficientes, sem excesso.

    Cada ronda mostra só as sílabas das suas palavras e uma sílaba a mais. São escondidas
    todas as palavras do vocabulário que se formam com essas peças, para que o contador
    corresponda ao que é possível descobrir, e nunca mais de três. A palavra-chave fica
    reservada para a demonstração: nenhum tabuleiro a deixa formar. O grupo e a sílaba a
    mais escolhem-se em conjunto, para que a sílaba a mais não forme palavras do
    vocabulário nem, havendo dicionário, outras palavras reais. O que não for possível
    evitar fica em `warnings`, para o professor rever.
    """
    usable = newest_first(pool, lambda w: 2 <= len(w['syllables']) <= 3, reserved)
    vocabulary = [w for w in pool['words'] if len(w['syllables']) <= 3]
    syllables = vocabulary_syllables(pool)
    remaining, rounds = list(usable), []
    def board(group):
        counts = {}
        for word in group:
            for syllable in dict.fromkeys(word['syllables']):
                counts[syllable] = max(counts.get(syllable, 0), word['syllables'].count(syllable))
        pieces = [s for s, n in counts.items() for _ in range(n)]
        hidden = list(group) + [w for w in usable if w not in group and formable(w['label'], pieces)]
        return pieces, hidden
    def honest(pieces, hidden):
        labels = {w['label'] for w in hidden}
        return not any(w['label'] not in labels and formable(w['label'], pieces) for w in vocabulary)
    excluded = {e['label'] for e in pool.get('excluded', [])}
    def real_words(pieces, labels):
        made = {''.join(pieces[i] for i in order) for size in range(2, 4) for order in permutations(range(len(pieces)), size)}
        # Palavras que o professor excluiu («nina», «nano») não contam como palavras para a criança.
        return sorted(word for word in made - labels - excluded if lexicon and lexicon(word))
    known = set(pool.get('knownWords', []))
    def celebrated(pieces, words):
        return celebrated_sequences(pieces, words, known, pool.get('index', 0), pool['repertoire'], pool['slugs'])
    def weight(words):
        return board_weight(words, known, pool.get('avoidWords', []))
    def surplus(pieces, hidden):
        """Peças a mais em relação às necessárias para montar as palavras escondidas (no máximo uma)."""
        need = {}
        for word in hidden:
            for syllable in set(word['syllables']):
                need[syllable] = max(need.get(syllable, 0), word['syllables'].count(syllable))
        return sum(max(0, pieces.count(p) - need.get(p, 0)) for p in set(pieces))
    if pool.get('discoverBoards'):
        # Tabuleiros já aprovados ficam fixos: uma ronda concluída nunca reabre noutra versão.
        by_label = {w['label']: w for w in pool['words']}
        units = set(pool['families'])
        for board_spec in pool['discoverBoards']:
            hidden = [by_label[label] for label in board_spec['hidden']]
            pieces = list(board_spec['pieces'])
            labels = {w['label'] for w in hidden}
            # Um tabuleiro fixo continua sujeito às mesmas regras: peças do repertório, respostas montáveis, contagem honesta.
            if any(piece not in units for piece in pieces) or not all(formable(w['label'], pieces) for w in hidden) \
                    or not 2 <= len(labels) == len(hidden) <= 3 \
                    or surplus(pieces, hidden) > 1 \
                    or not honest(pieces, hidden):
                raise ValueError(f"Tabuleiro fixo inválido em {pool['keyword']['label']}: {board_spec}")
            found = real_words(pieces, labels)
            base = {s for w in hidden for s in w['syllables']}
            rounds.append(dict(pieces=pieces, hidden=hidden, warnings=found, celebrate=celebrated(pieces, set(found)),
                               extra=any(piece not in base for piece in pieces)))
        return rounds
    while len(remaining) >= 2 and len(rounds) < max_rounds:
        sizes = (3, 2) if len(remaining) == 3 else (2,)
        used = {w['label'] for r in rounds for w in r['hidden']}
        current = pool['keyword']['slug']
        fresh_left = any(w.get('newIn') == current for w in remaining)
        options = []
        for size, first in ((size, first) for size in sizes for first in range(len(remaining))):
            for others in combinations(range(first + 1, len(remaining)), size - 1):
                group = [remaining[first]] + [remaining[i] for i in others]
                pieces, hidden = board(group)
                if len(hidden) <= max_hidden and honest(pieces, hidden):
                    # Preferir tabuleiros cujas peças base não formem palavras reais fora da lista («ano», «ova»).
                    clashes = weight(real_words(pieces, {w['label'] for w in hidden}))
                    # Enquanto houver palavras novas desta palavra-chave por usar, cada ronda leva pelo menos uma.
                    stale = fresh_left and not any(w.get('newIn') == current for w in hidden)
                    # As palavras novas só passam à frente entre tabuleiros com pouca palavra real por acaso.
                    options.append((bool(used & {w['label'] for w in hidden}), clashes > 1, stale, clashes, first, pieces, hidden))
        if not options:
            break
        # Com três palavras por usar, o trio evita deixar uma de fora; os pares só servem se o trio não for honesto.
        trios = [option for option in options if len(option[6]) >= 3 and len(remaining) == 3]
        options = trios or options
        options.sort(key=lambda option: option[:5])
        best = None
        # Cada tabuleiro compara-se na forma em que a criança o vê: com a melhor sílaba a mais,
        # ou sem ela quando só acrescentaria palavras reais fora da lista.
        for repeated, _, stale, _, _, pieces, hidden in options[:40]:
            labels = {w['label'] for w in hidden}
            base_clash = weight(real_words(pieces, labels))
            shown, clash = pieces, base_clash
            candidates = sorted(s for s in syllables if len(s) >= 2 and plain(s) == s and s not in pieces)
            rng.shuffle(candidates)
            for candidate in candidates:
                board_pieces = pieces + [candidate]
                if not honest(board_pieces, hidden):
                    continue
                # Uma peça a mais nunca tira palavras: só serve se não acrescentar nenhuma.
                if weight(real_words(board_pieces, labels)) == base_clash:
                    shown = board_pieces
                    break
            score = (repeated, clash > 1, stale, clash, shown is pieces)
            if best is None or score < best[0]:
                best = (score, shown, hidden)
            if best[0] == (False, False, False, 0, False):
                break
        _, pieces, hidden = best
        labels = {w['label'] for w in hidden}
        base = {s for w in hidden for s in w['syllables']}
        found = real_words(pieces, labels)
        rounds.append(dict(pieces=pieces, hidden=hidden, warnings=found, celebrate=celebrated(pieces, set(found)),
                           extra=any(piece not in base for piece in pieces)))
        remaining = [w for w in remaining if w['label'] not in labels]
    return rounds
