#!/usr/bin/env python3
"""Arquiva uma coleção M28P sem alterar os conteúdos entregues.

Por defeito mostra os candidatos. --apply guarda um inventário com metadados
anteriores, marca os metadados e regenera o catálogo pela função canónica.
Uma repetição não altera os ficheiros já arquivados nem o inventário.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.publish import regenerate_catalog


def save_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


# Cada coleção é um ato de arquivo com data, razão e seleção próprias.
COLLECTIONS = {
    'm28p-2026-10-23': {
        'title': 'Coleção anterior das 28 palavras',
        'date': '2026-10-23',
        'reason': 'Substituição por percursos fundamentados e articulados com o MEM.',
        # Os percursos v2 e v3 têm identidade própria e nunca são alvo deste arquivo.
        'selects': lambda slug, tags: 'm28p' in tags and not {'m28p-v2', 'm28p-v3'} & set(tags),
    },
    'm28p-v3-2026-11-23': {
        'title': 'Coleção v3 das 28 palavras: seis minijogos por palavra',
        'date': '2026-11-23',
        'reason': 'Substituída pelo ciclo completo das 28 palavras (16/11/2026), que acrescenta '
                  'a recombinação de sílabas, a leitura de palavras novas e as frases.',
        # Os jogos do ciclo também têm a etiqueta m28p-v3: a seleção é pelo slug.
        'selects': lambda slug, tags: slug.startswith('m28p-v3-'),
    },
}


def archive(root: Path, apply: bool = False, collection: str = 'm28p-2026-10-23') -> list[str]:
    spec = COLLECTIONS[collection]
    manifest_path = root / 'docs' / 'archives' / f'{collection}.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'title': spec['title'],
        'date': spec['date'],
        'reason': spec['reason'],
        'policy': 'Retiradas dos catálogos; conteúdo e endereços anteriores preservados.',
        'activities': {},
    }
    candidates = []
    planned = []
    for path in sorted((root / 'activities').glob('*/meta.json')):
        meta = json.loads(path.read_text())
        if meta.get('status') == 'archived' or not spec['selects'](path.parent.name, meta.get('tags', [])):
            continue
        candidates.append(path.parent.name)
        if apply:
            manifest['activities'].setdefault(path.parent.name, meta.copy())
            meta.update(status='archived', archivedAt=manifest['date'],
                        archiveReason=manifest['reason'], archiveCollection=spec['title'])
            planned.append((path, meta))
    if apply and candidates:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        # Guardar todos os originais antes de modificar o primeiro metadado.
        save_json(manifest_path, manifest)
        for path, meta in planned:
            save_json(path, meta)
    if apply and manifest_path.exists():
        # Recuperar também interrupções depois dos metadados e antes do índice.
        regenerate_catalog(root)
    return candidates


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--collection', choices=sorted(COLLECTIONS), default='m28p-2026-10-23')
    args = parser.parse_args()
    candidates = archive(ROOT, args.apply, args.collection)
    print(json.dumps({'applied': args.apply, 'count': len(candidates), 'slugs': candidates},
                     ensure_ascii=False, indent=2))
