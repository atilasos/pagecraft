#!/usr/bin/env python3
"""
Gera PROMPT.md para o coding agent (Builder) a partir do DocSpec-AM JSON.
Inclui automaticamente a identidade do Builder se disponível.

Usage: python3 build_prompt.py docspec.json > PROMPT.md
       python3 build_prompt.py docspec.json --with-identity > TASK.md
"""

import argparse
import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
IDENTITY_PATH = SKILL_DIR / "identities" / "builder.md"


def looks_like_pagecraft_repo(path: Path) -> bool:
    return (path / "catalog.json").exists() and (path / "activities").is_dir()


def resolve_repo_root() -> Path:
    for key in ("PAGECRAFT_REPO", "PAGECRAFT_WORKSPACE"):
        value = os.environ.get(key)
        if not value:
            continue
        candidate = Path(value).expanduser().resolve()
        if looks_like_pagecraft_repo(candidate):
            return candidate
        if looks_like_pagecraft_repo(candidate / "pagecraft"):
            return candidate / "pagecraft"

    cwd = Path.cwd().resolve()
    if looks_like_pagecraft_repo(cwd):
        return cwd
    if looks_like_pagecraft_repo(cwd.parent):
        return cwd.parent

    return Path.home() / ".openclaw" / "workspace" / "pagecraft"


PAGECRAFT_REPO = resolve_repo_root()


def find_repo_rules_file(repo: Path) -> Path | None:
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        candidate = repo / name
        if candidate.exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Gera prompt para o Builder PageCraft a partir de um DocSpec-AM JSON."
    )
    parser.add_argument("docspec", help="Caminho para o DocSpec-AM JSON")
    parser.add_argument(
        "--with-identity",
        action="store_true",
        help="Incluir identities/builder.md no início do prompt",
    )
    parser.add_argument("--output", help="Caminho do HTML que o Builder deve produzir")
    args = parser.parse_args()
    docspec_path = Path(args.docspec)
    output = args.output or str(docspec_path.with_name(docspec_path.stem.removesuffix("-docspec") + ".html"))

    spec = json.loads(Path(args.docspec).read_text(encoding="utf-8"))

    topic = spec.get("topic", "Aula interactiva")
    age = spec.get("ageRange", "6-10 anos")
    duration = spec.get("duration", 40)
    objectives = spec.get("objectives", [])
    curriculum = spec.get("curriculum", {})
    units = spec.get("units", [])

    # Build units section
    units_text = []
    for i, u in enumerate(units, 1):
        inter = u.get("interaction", {})
        diff = u.get("differentiation", {})
        maker = u.get("maker")
        dur = u.get("duration", "?")

        state_desc = json.dumps(inter.get("state", []), indent=2, ensure_ascii=False)

        maker_text = ""
        if maker:
            maker_text = f"""
### Maker Challenge ({maker.get("type", "")})
- Desafio: {maker.get("challenge", "")}
- Materiais: {", ".join(maker.get("materials", []))}
- Grupo: {maker.get("groupSize", "")}
- Comunicação: {maker.get("communication", "")}
"""

        units_text.append(f"""
## Unit {i}: {u.get("summary", "")} ({dur} min)

### Texto
{u.get("textDescription", "")}

### SRTC-A (Interaction Specification)

**State variables:**
```json
{state_desc}
```

**Render:** {inter.get("render", "")}

**Transition:** {inter.get("transition", "")}

**Constraint (o aluno DESCOBRE — NÃO revelar):** {inter.get("constraint", "")}

**Assessment (observável):** {inter.get("assessment", "")}

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** {diff.get("support", "")}
- **Passo a passo — Intermédio:** {diff.get("standard", "")}
- **Mais desafios — Desafio:** {diff.get("challenge", "")}
{maker_text}""")

    # Curriculum footer
    ae_items = "\n".join(
        f"- {a.get('subject', '')} ({a.get('year', '')}): {a.get('descriptor', '')}"
        for a in curriculum.get("ae", [])
    )
    comp_items = "\n".join(f"- {c}" for c in curriculum.get("competencies", []))

    # Build prompt
    parts = []

    # Optionally prepend identity
    if args.with_identity and IDENTITY_PATH.exists():
        parts.append(IDENTITY_PATH.read_text(encoding="utf-8"))
        parts.append("\n---\n")

    rules_file = find_repo_rules_file(PAGECRAFT_REPO)
    rules_text = (
        f"Este projeto tem regras de repo em `{rules_file}`. Lê-as e cumpre-as antes de implementar."
        if rules_file
        else "Não foi encontrado AGENTS.md/CLAUDE.md/README.md no repo resolvido; cumpre as regras PageCraft desta skill e do DocSpec/design-spec."
    )

    refs = SKILL_DIR / "references"
    if not refs.is_dir():
        refs = PAGECRAFT_REPO / "server/pipeline/prompts/references"
    experience = (refs / "activity-experience.md").read_text(encoding="utf-8")
    age_rules = (refs / "age-adaptation.md").read_text(encoding="utf-8")
    parts.append(f"""# PageCraft Builder

Gera o HTML autocontido em `{output}` a partir deste DocSpec. Segue o design-spec produzido pelo Designer; planeia o percurso conforme as unidades, sem impor uma estrutura fixa.

Tema: {topic}
Idade: {age}
Duração: {duration} minutos
Objetivos: {json.dumps(objectives, ensure_ascii=False)}

## Regras do repositório
{rules_text}

## Experiência aprovada
{experience}

## Adaptação à idade
{age_rules}

## Unidades SRTC-A
{"".join(units_text)}

## Referências curriculares para o guia do professor
{ae_items}
{comp_items}

## Artefacto e verificação

HTML5, CSS e JavaScript inline, sem dependências de rede. Implementa as interações e os estados definidos nas unidades, incluindo alternativa por teclado. Usa o template da skill como referência técnica e conserva os nomes da ponte. O ficheiro deve passar pela incorporação da fonte, Proofreader e Evaluator antes de ser entregue para revisão do professor.
""")

    print("\n".join(parts))


if __name__ == "__main__":
    main()
