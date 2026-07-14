#!/usr/bin/env python3
"""Injeta o pagecraft-bridge-lite (recetor de «chamar a atenção») em todas as
atividades publicadas que ainda não têm recetor de highlight.

Uso: uv run python scripts/inject_bridge_lite.py [--dry-run]
Idempotente: correr duas vezes não duplica o excerto.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.bridge_snippet import ensure_bridge_lite  # noqa: E402


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    repo_root = Path(__file__).resolve().parent.parent
    changed = skipped = 0
    for index in sorted((repo_root / "activities").glob("*/index.html")):
        original = index.read_text(encoding="utf-8")
        updated = ensure_bridge_lite(original)
        if updated == original:
            skipped += 1
            continue
        changed += 1
        if not dry_run:
            index.write_text(updated, encoding="utf-8")
        print(f"{'[dry-run] ' if dry_run else ''}injetado: {index.parent.name}")
    print(f"\n{changed} atividades atualizadas, {skipped} já tinham recetor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
