#!/usr/bin/env python3
"""Arquiva a coleção M28P anterior sem alterar os conteúdos entregues.

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


def archive(root: Path, apply: bool = False) -> list[str]:
    manifest_path = root / 'docs' / 'archives' / 'm28p-2026-10-23.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'date': '2026-10-23',
        'reason': 'Substituição por percursos fundamentados e articulados com o MEM.',
        'policy': 'Retiradas dos catálogos; conteúdo e endereços anteriores preservados.',
        'activities': {},
    }
    candidates = []
    planned = []
    for path in sorted((root / 'activities').glob('*/meta.json')):
        meta = json.loads(path.read_text())
        if 'm28p' not in meta.get('tags', []) or meta.get('status') == 'archived':
            continue
        # Novos percursos têm identidade própria e nunca são alvo deste arquivo.
        if 'm28p-v2' in meta.get('tags', []):
            continue
        candidates.append(path.parent.name)
        if apply:
            manifest['activities'].setdefault(path.parent.name, meta.copy())
            meta.update(status='archived', archivedAt='2026-10-23',
                        archiveReason=manifest['reason'])
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
    args = parser.parse_args()
    candidates = archive(ROOT, args.apply)
    print(json.dumps({'applied': args.apply, 'count': len(candidates), 'slugs': candidates},
                     ensure_ascii=False, indent=2))
