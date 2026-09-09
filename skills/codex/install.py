#!/usr/bin/env python3
"""Instala links pessoais para Codex e OpenClaw, preservando instalações distintas."""
from pathlib import Path

source = Path(__file__).resolve().parent
root = Path.home() / '.agents' / 'skills'
root.mkdir(parents=True, exist_ok=True)
links = {
    'pagecraft-codex': source,
    'sebenta-wiki': Path.home() / '.codex/skills/sebenta-wiki',
    'cloudflare-publish': Path.home() / '.codex/skills/cloudflare-publish',
}
for name, target in links.items():
    if not (target / 'SKILL.md').is_file():
        raise SystemExit(f'Skill em falta: {target}')
    destination = root / name
    if destination.exists() or destination.is_symlink():
        if destination.resolve() != target.resolve():
            raise SystemExit(f'Instalação existente preservada: {destination}')
    else:
        destination.symlink_to(target, target_is_directory=True)
    print(f'{name}: {destination} -> {target}')
