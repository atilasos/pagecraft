"""Incorpora o apoio definido no DocSpec antes de rever uma atividade gerada."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.activity_support import embed_activity_support


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activity', type=Path, required=True)
    parser.add_argument('--docspec', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.docspec.read_text())
    if 'support' not in spec:
        parser.error('Falta support no DocSpec. O Architect tem de preparar pistas próprias da atividade.')
    args.activity.write_text(embed_activity_support(args.activity.read_text(), spec,
                                                   args.docspec.stem.removesuffix('-docspec')))


if __name__ == '__main__':
    main()
