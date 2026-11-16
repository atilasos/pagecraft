"""Dados cumulativos do ciclo M28P, independentes da lista editorial do piloto."""
import hashlib
import re
import unicodedata

CYCLE_GAMES = {
    'listen-build': ('Ouvir e montar', 'Ouve e junta as sílabas.', 'Monto uma palavra a partir do áudio.'),
    'read-choose': ('Ler e escolher', 'Lê e escolhe a imagem.', 'Escolho a imagem da palavra escrita.'),
    'sentence': ('Montar frases', 'Ordena as palavras da frase.', 'Ordeno palavras para formar uma frase.'),
    'discover': ('Descobrir palavras', 'Junta sílabas. Descobre palavras.', 'Experimento combinações e guardo palavras.'),
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
        if slug not in cycle['keywords']:
            continue
        section = cycle['keywords'][slug]
        known.append(dict(keyword, picturable=True))
        for item in section['newWords']:
            label = item['label']
            if ''.join(item['syllables']) != label:
                raise ValueError(f'{slug}: concatenação das sílabas diferente da grafia: {label}')
            if not 2 <= len(item['syllables']) <= 3 or any(s not in families for s in item['syllables']):
                raise ValueError(f'{slug}: sílabas fora do repertório: {label}')
            if any(g in label and g not in groups for g in ('nh','lh','ch','rr','ss','ai','ei','oi','ui','au','eu','ou','ão','ãe','õe')):
                raise ValueError(f'{slug}: dígrafo ou ditongo ainda não introduzido: {label}')
            if label in {w['label'] for w in known}:
                raise ValueError(f'{slug}: palavra repetida: {label}')
            if not isinstance(item['picturable'], bool):
                raise ValueError(f'{slug}: picturable deve ser booleano: {label}')
            known.append(dict(item, slug=asset_id(label)))
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
        result[slug] = dict(words=list(known), sentences=list(sentences), families=sorted(families))
    return result
