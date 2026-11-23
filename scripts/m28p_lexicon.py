"""Dicionário pt-PT (Hunspell, Universidade do Minho) para a geração do ciclo M28P.

Serve duas verificações editoriais: só entram palavras reais, e a sílaba a mais de
Descobrir palavras não forma palavras reais fora da lista. O dicionário não é
versionado no repositório (licença GPL/LGPL/MPL): descarrega-se uma vez, de uma
revisão fixa, para a cache local, e confirma-se o SHA-256.

Uso: uv run --with spylls python scripts/build_m28p_tic.py --cycle
"""
import hashlib
import urllib.request
from functools import lru_cache
from pathlib import Path

REVISION = 'fe49c662796b47cb19732d18114610a58848f5cb'
BASE_URL = f'https://raw.githubusercontent.com/LibreOffice/dictionaries/{REVISION}/pt_PT/'
FILES = {
    'pt_PT.aff': '975a209fcc892cb382fa5f34a28c391a39668661ce373ae071287809c5fcae24',
    'pt_PT.dic': 'e29ba2d7aa8a2ad43e9cb46ac6473064b661545c87002aea90e18899d98d3cc9',
}
CACHE = Path.home() / '.cache' / 'pagecraft' / 'hunspell-pt_PT'


def _fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, digest in FILES.items():
        path = CACHE / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            data = urllib.request.urlopen(BASE_URL + name, timeout=60).read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError(f'O dicionário {name} não corresponde à revisão fixada.')
            path.write_bytes(data)
    return CACHE / 'pt_PT'


@lru_cache(maxsize=1)
def load():
    """Devolve uma função palavra → bool. Exige o pacote spylls."""
    try:
        from spylls.hunspell import Dictionary
    except ImportError as error:
        raise SystemExit('Executar com: uv run --with spylls python scripts/build_m28p_tic.py --cycle') from error
    dictionary = Dictionary.from_files(str(_fetch()))
    return lru_cache(maxsize=None)(lambda word: bool(dictionary.lookup(word)))
