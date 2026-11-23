#!/usr/bin/env python3
"""Publica em activities/ os jogos do ciclo M28P gerados e aprovados.

Usa o mesmo ato de publicação do Studio (publish_activity), que escreve index.html,
teacher.md, docspec.json, design-spec.json e meta.json e regenera o Catálogo.
Sem --apply, mostra apenas o plano. Só publica jogos com estado «generated» no
relatório de geração e com os artefactos completos.

  uv run python scripts/publish_m28p_cycle.py --word menina --word menino --word uva --apply
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.publish import publish_activity  # noqa: E402

BASE = ROOT / 'drafts/m28p-v3'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--word', action='append', required=True, help='Slug da palavra-chave a publicar (repetível), por exemplo palhaco.')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    report = json.loads((BASE / 'cycle-generation-report.json').read_text())
    # O relatório guarda o slug da palavra-chave («palhaco», «arvore»), que é também o nome da pasta.
    selected = [item for item in report if item['keyword'] in args.word and item['status'] == 'generated']
    plan = []
    for item in selected:
        slug = item['slug']
        folder = BASE / item['keyword']
        files = dict(html=folder / f'{slug}.html', docspec=folder / f'{slug}-docspec.json',
                     design=folder / f'{slug}-design-spec.json', guide=folder / f'{slug}-guia-docente.md')
        missing = [str(path) for path in files.values() if not path.is_file()]
        if missing:
            parser.error(f'Artefactos em falta para {slug}: {missing}')
        plan.append((slug, files))
    print(json.dumps([slug for slug, _ in plan], ensure_ascii=False, indent=2))
    if not args.apply:
        return
    for slug, files in plan:
        publish_activity(ROOT, slug, files['html'], json.loads(files['docspec'].read_text()),
                         files['guide'].read_text(), json.loads(files['design'].read_text()))
    print(f'Publicados: {len(plan)}')


if __name__ == '__main__':
    main()
