#!/usr/bin/env python3
"""
Gera versão Markdown (professor) a partir do DocSpec-AM JSON.
Usage: python3 build_markdown.py docspec.json > output.md
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Gera versão Markdown para professor a partir de um DocSpec-AM JSON."
    )
    parser.add_argument("docspec", help="Caminho para o DocSpec-AM JSON")
    args = parser.parse_args()

    spec = json.loads(Path(args.docspec).read_text(encoding="utf-8"))

    lines = [
        f"# {spec.get('topic', '')}",
        f"",
        f"**Ano:** {spec.get('ageRange', '')}  ",
        f"**Duração:** {spec.get('duration', '')} minutos  ",
        f"**Gerado por:** PageCraft 🛠️ — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
        "## Objetivos de aprendizagem",
        "",
    ]
    for obj in spec.get("objectives", []):
        lines.append(f"- {obj}")

    lines.extend(["", "## Materiais", ""])
    for m in spec.get("materials", []):
        lines.append(f"- {m}")

    mem = spec.get("memAlignment", {})
    if mem:
        lines.extend(["", "## Alinhamento MEM", ""])
        for mod in mem.get("modules", []):
            lines.append(f"- {mod}")
        org = mem.get("socialOrganization", "")
        if org:
            lines.append(f"- **Organização social:** {org}")

    flow = spec.get("sessionFlow", "")
    if flow:
        lines.extend(["", "## Fluxo da sessão", "", flow])

    for i, u in enumerate(spec.get("units", []), 1):
        inter = u.get("interaction", {})
        diff = u.get("differentiation", {})
        maker = u.get("maker")
        lines.extend(
            [
                "",
                f"## Unit {i}: {u.get('summary', '')} ({u.get('duration', '?')} min)",
                "",
                f"**Compreender:** {u.get('textDescription', '')}",
                "",
                f"**Constraint:** {inter.get('constraint', '')}",
                f"**Assessment:** {inter.get('assessment', '')}",
                "",
                "**Diferenciação:**",
                f"- 🟢 Apoio: {diff.get('support', '')}",
                f"- 🟡 Intermédio: {diff.get('standard', '')}",
                f"- 🔴 Desafio: {diff.get('challenge', '')}",
            ]
        )
        if maker:
            lines.extend(
                [
                    "",
                    f"### 🛠️ Maker — {maker.get('type', '').title()}",
                    f"- **Desafio:** {maker.get('challenge', '')}",
                    f"- **Grupo:** {maker.get('groupSize', '')}",
                    f"- **Ligação:** {maker.get('connection', '')}",
                    f"- **Comunicação:** {maker.get('communication', '')}",
                ]
            )
            alts = maker.get("alternatives", [])
            if alts:
                lines.append(f"- **Alternativas:** {'; '.join(alts)}")

    curriculum = spec.get("curriculum", {})
    if curriculum:
        lines.extend(
            [
                "",
                "---",
                "",
                "## Referências curriculares",
                "",
                "### Aprendizagens Essenciais",
            ]
        )
        for ae in curriculum.get("ae", []):
            lines.append(
                f"- **{ae.get('subject', '')} ({ae.get('year', '')}):** {ae.get('descriptor', '')}"
            )
        lines.extend(["", "### Perfil do Aluno"])
        for c in curriculum.get("competencies", []):
            lines.append(f"- {c}")

    lines.extend(
        ["", "---", f"*Gerado por PageCraft 🛠️ — {datetime.now().strftime('%Y-%m-%d')}*"]
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
