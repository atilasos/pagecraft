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
    args = parser.parse_args()

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

- 🟢 **Apoio:** {diff.get("support", "")}
- 🟡 **Intermédio:** {diff.get("standard", "")}
- 🔴 **Desafio:** {diff.get("challenge", "")}
{maker_text}""")

    # Curriculum footer
    ae_items = "\n".join(
        f"- {a.get('subject', '')} ({a.get('year', '')}): {a.get('descriptor', '')}"
        for a in curriculum.get("ae", [])
    )
    comp_items = "\n".join(f"- {c}" for c in curriculum.get("competencies", []))

    # Maker summary
    maker_units = [u for u in units if u.get("maker")]
    maker_summary = ""
    if maker_units:
        items = "\n".join(
            f"- **{u['maker']['type'].title()}:** {u['maker']['challenge']}"
            for u in maker_units
        )
        maker_summary = f"""
## Secção Maker (🛠️ Desafios Maker)
Incluir secção visual com fundo verde:
{items}
"""

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

    parts.append(f"""# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: {topic}
- Ano: {age}
- Duração: {duration} minutos
- Objectivos: {json.dumps(objectives, ensure_ascii=False)}

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"

{"".join(units_text)}

{maker_summary}

## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
{ae_items}

### Perfil do Aluno
{comp_items}

## Requisitos técnicos OBRIGATÓRIOS

1. **HTML5 + CSS3 + JavaScript vanilla** — ZERO dependências externas, ZERO CDNs
2. **Self-contained** — TODO o CSS e JS inline no ficheiro HTML
3. **Responsive** — funcionar em tablet (768px) e quadro interactivo (1920px)
4. **Touch-friendly** — áreas clicáveis mínimo 44x44px, suporte touch events + mouse
5. **Acessibilidade** — aria-labels, contraste WCAG AA, font-size mínimo 16px
6. **Cores vivas** — amigáveis para crianças, feedback visual claro
7. **Animações** — CSS transitions + requestAnimationFrame para partículas/canvas
8. **Diferenciação** — 3 níveis como tabs/botões (🟢 Apoio, 🟡 Intermédio, 🔴 Desafio)
9. **Constraint** — NÃO revelar directamente; a interacção leva à descoberta
10. **Feedback** — visual+sonoro quando o aluno descobre algo (confetti, cor, mensagem)
11. **Drag-and-drop** — funcional com touch events E mouse events
12. **Offline** — funcionar sem internet
13. **Linguagem** — pt-PT (AO90), frases curtas, adequada a {age}

## Guardar como
`page.html` — ficheiro único, completo, pronto a abrir no browser.

## IMPORTANTE
- Usar `template.html` como referência de estilo CSS (se existir no directório)
- Implementar TODAS as interacções descritas nas specs SRTC-A
- Cada slider, matching, sorting, toggle deve ser FUNCIONAL, não placeholder
- Canvas com partículas animadas quando especificado
- Testar mentalmente que a página funciona antes de gravar

## Design obrigatório (PageCraft)
{rules_text}

Resumo das regras críticas PageCraft:
- Fonte: 'Nunito', 'Comic Sans MS', 'Chalkboard SE' — nunca Inter/Roboto/Arial
- Tamanho base body: 20px; sílabas: 36-48px, font-weight 800
- Touch targets mínimo 48px em todos os eixos
- Cada sílaba com cor própria do design-spec.json (syllableColors)
- Botões pill, border-radius 16px nos cards, feedback correto/incorreto conforme spec
- Aplicar a skill de design `anthropics-frontend-design`: página única, identidade visual
  baseada na paleta da palavra, playful/toy-like, animações de stagger no load
- Respeitar `prefers-reduced-motion` nas animações
- Focus ring: outline 3px solid var(--primary), outline-offset 2px
""")

    print("\n".join(parts))


if __name__ == "__main__":
    main()
