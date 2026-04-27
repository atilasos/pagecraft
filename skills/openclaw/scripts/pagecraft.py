#!/usr/bin/env python3
"""
PageCraft — Multi-agent orchestrator for interactive lesson pages.

Pipeline: Architect → [Human Review] → Writer + Builder (parallel) → Evaluator → Assessor → Output

Usage:
    python3 pagecraft.py --topic "Estados da água" --year "3o ano" --duration 40
    python3 pagecraft.py --topic "Frações" --year "3o ano" --duration 35 --maker lego,whiteboard
    python3 pagecraft.py --topic "Simetria" --year "2o ano" --duration 30 --no-maker
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path


# --- Paths ---
SKILL_DIR = Path(__file__).resolve().parent.parent


def looks_like_pagecraft_repo(path: Path) -> bool:
    return (path / "catalog.json").exists() and (path / "activities").is_dir()


def resolve_workspace() -> Path:
    override = os.environ.get("PAGECRAFT_WORKSPACE") or os.environ.get(
        "OPENCLAW_WORKSPACE"
    )
    if override:
        return Path(override).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if looks_like_pagecraft_repo(cwd):
        return cwd
    if looks_like_pagecraft_repo(cwd.parent):
        return cwd.parent

    return Path.home() / ".openclaw" / "workspace"


WORKSPACE = resolve_workspace()
VAULT = WORKSPACE / "vault"
AE_DIR = VAULT / "documentos-oficiais" / "aprendizagens-essenciais"
KB_DIR = VAULT / "Knowledge"
OUTPUT_DIR = WORKSPACE / "outputs" / "lessons"
REFS_DIR = SKILL_DIR / "references"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[àáâãä]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_year(year_str: str) -> dict:
    """Parse year string into structured data."""
    year_str = year_str.lower().strip()
    # Handle "3o ano", "3.º ano", "3º ano", "pre-escolar", "pré-escolar"
    if "pre" in year_str or "pré" in year_str:
        return {"year": "pré-escolar", "age_range": "4-5 anos", "cycle": "pré-escolar"}

    match = re.search(r"(\d)", year_str)
    if match:
        y = int(match.group(1))
        ages = {1: "6-7", 2: "7-8", 3: "8-9", 4: "9-10"}
        return {
            "year": f"{y}.º ano",
            "age_range": f"{ages.get(y, '6-10')} anos",
            "cycle": "1.º ciclo",
        }
    return {"year": year_str, "age_range": "6-10 anos", "cycle": "1.º ciclo"}


def find_ae_files(year_info: dict) -> list[Path]:
    """Find relevant AE files for the given year."""
    if not AE_DIR.exists():
        return []

    year = year_info["year"]
    files = []

    if "pré" in year:
        # Pre-school: look for pre-escolar files or 1-ciclo generic ones
        for f in AE_DIR.glob("*1-ciclo*.md"):
            files.append(f)
    else:
        match = re.search(r"(\d)", year)
        if match:
            y = match.group(1)
            # Year-specific files
            for f in AE_DIR.glob(f"*{y}-ano-1-ciclo*.md"):
                files.append(f)
            # Cycle-wide files
            for f in AE_DIR.glob("*1-ciclo.md"):
                files.append(f)

    # Always include TIC
    tic = AE_DIR / "tic-1-ano-1-ciclo.md"
    if tic.exists() and tic not in files:
        files.append(tic)

    return sorted(set(files))


def load_reference(name: str) -> str:
    """Load a reference file content."""
    path = REFS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def build_architect_prompt(
    topic: str,
    year_info: dict,
    duration: int,
    maker_types: list[str],
    ae_files: list[Path],
) -> str:
    """Build the Architect agent prompt."""

    # Load AE summaries (first 100 lines of each relevant file)
    ae_context = []
    core_subjects = ["estudo-do-meio", "matematica", "portugues", "tic"]
    for f in ae_files:
        if any(s in f.stem for s in core_subjects):
            try:
                lines = f.read_text(encoding="utf-8").split("\n")[:100]
                ae_context.append(f"### {f.stem}\n" + "\n".join(lines))
            except Exception:
                pass

    ae_text = "\n\n".join(ae_context[:4])  # Max 4 AE files

    # Load schema
    schema = load_reference("docspec-schema.md")

    # Load maker patterns if applicable
    maker_context = ""
    if maker_types:
        maker_context = load_reference("maker-patterns.md")

    # Load interaction patterns
    patterns = load_reference("interaction-patterns.md")

    maker_instruction = ""
    if maker_types:
        maker_instruction = f"""
## Extensões Maker
Recursos disponíveis: {", ".join(maker_types)}
Incluir maker challenges adequados para cada knowledge unit (ou para as units onde faz sentido).
Cada maker challenge deve ter: type, challenge, materials, groupSize, connection, communication, alternatives.

{maker_context}
"""
    else:
        maker_instruction = """
## Maker
Não incluir maker challenges nesta página (--no-maker). Focar apenas na interacção digital.
"""

    prompt = f"""# Tarefa: Gerar DocSpec-AM para PageCraft

## Tópico
{topic}

## Contexto
- Ano: {year_info["year"]} ({year_info["age_range"]})
- Duração: {duration} minutos
- Ciclo: {year_info["cycle"]}

## Instruções

Gera um DocSpec-AM completo em JSON válido para o tópico acima.

### Requisitos obrigatórios:
1. Consulta as Aprendizagens Essenciais abaixo e referencia descritores específicos
2. Mapeia para áreas de competência do Perfil do Aluno (PA-A a PA-J)
3. Alinha com módulos MEM (TEA, projecto cooperativo, comunicação, conselho)
4. Cada knowledge unit tem SRTC-A completo (State, Render, Transition, Constraint, Assessment)
5. Diferenciação obrigatória em 3 níveis (apoio/intermédio/desafio)
6. Linguagem adequada à faixa etária: {year_info["age_range"]}
7. O Constraint (C) é algo que o aluno DESCOBRE, não que lhe é dito
8. O Assessment (A) é observável: o que o aluno FAZ/DIZ/PRODUZ
9. Duration total das units deve somar ≤ {duration} minutos
10. Incluir sessionFlow descrevendo o encadeamento temporal

### Interaction Patterns disponíveis:
{patterns}

{maker_instruction}

## Aprendizagens Essenciais relevantes:
{ae_text}

## Schema DocSpec-AM:
{schema}

## Output
Responde APENAS com o JSON do DocSpec-AM válido. Sem explicações antes ou depois.
"""
    return prompt


def build_writer_prompt(docspec: dict) -> str:
    """Build the Writer agent prompt from DocSpec-AM."""
    units_text = []
    for i, unit in enumerate(docspec.get("units", []), 1):
        units_text.append(f"""
### Unit {i}: {unit.get("summary", "")}

**Text Description:** {unit.get("textDescription", "")}

**Constraint:** {unit.get("interaction", {}).get("constraint", "")}

**Differentiation:**
- 🟢 Apoio: {unit.get("differentiation", {}).get("support", "")}
- 🟡 Intermédio: {unit.get("differentiation", {}).get("standard", "")}
- 🔴 Desafio: {unit.get("differentiation", {}).get("challenge", "")}
""")

    maker_sections = []
    for i, unit in enumerate(docspec.get("units", []), 1):
        maker = unit.get("maker")
        if maker:
            maker_sections.append(f"""
### Unit {i} — Desafio Maker ({maker.get("type", "")})
**Desafio:** {maker.get("challenge", "")}
**Ligação ao digital:** {maker.get("connection", "")}
**Comunicação:** {maker.get("communication", "")}
""")

    maker_text = (
        "\n".join(maker_sections)
        if maker_sections
        else "(Sem extensões maker nesta página)"
    )

    prompt = f"""# Tarefa: Gerar texto para página PageCraft

## Tópico: {docspec.get("topic", "")}
## Ano: {docspec.get("ageRange", "")}
## Objectivos: {json.dumps(docspec.get("objectives", []), ensure_ascii=False)}

## Knowledge Units:
{"".join(units_text)}

## Extensões Maker:
{maker_text}

## Instruções:
1. Para cada unit, escreve o texto explicativo em HTML (fragmento, não página completa)
2. Linguagem pt-PT (AO90), frases curtas, adequada à idade
3. Usa analogias concretas do quotidiano das crianças
4. NÃO revelar o Constraint directamente — o texto deve guiar a descoberta
5. Incluir uma frase de activação/pergunta no início de cada unit
6. Se houver maker, incluir secção "🛠️ Desafio Maker" com instruções claras para os alunos
7. Incluir secção final de mini-avaliação (3-5 perguntas/desafios observáveis)

## Output:
Para cada unit, responde com:
```html
<!-- UNIT_N_START -->
<section class="unit" id="unit-N">
  ... HTML do texto ...
</section>
<!-- UNIT_N_END -->
```

Inclui também:
```html
<!-- INTRO_START -->
<header>... introdução da página ...</header>
<!-- INTRO_END -->

<!-- ASSESSMENT_START -->
<section class="assessment">... mini-avaliação ...</section>
<!-- ASSESSMENT_END -->
```
"""
    return prompt


def build_builder_prompt(docspec: dict) -> str:
    """Build the Builder agent prompt from DocSpec-AM SRTC-A specs."""
    units_specs = []
    for i, unit in enumerate(docspec.get("units", []), 1):
        interaction = unit.get("interaction", {})
        diff = unit.get("differentiation", {})
        units_specs.append(f"""
### Unit {i}: {unit.get("summary", "")}

**State variables:**
```json
{json.dumps(interaction.get("state", []), indent=2, ensure_ascii=False)}
```

**Render:** {interaction.get("render", "")}

**Transition:** {interaction.get("transition", "")}

**Constraint:** {interaction.get("constraint", "")}

**Assessment:** {interaction.get("assessment", "")}

**Differentiation:**
- 🟢 Apoio: {diff.get("support", "")}
- 🟡 Intermédio: {diff.get("standard", "")}
- 🔴 Desafio: {diff.get("challenge", "")}
""")

    prompt = f"""# Tarefa: Gerar interacções HTML/CSS/JS para PageCraft

## Tópico: {docspec.get("topic", "")}
## Ano: {docspec.get("ageRange", "")}

## Especificações SRTC-A por unit:
{"".join(units_specs)}

## Requisitos técnicos:
1. HTML5 + CSS3 + JavaScript vanilla (sem frameworks/bibliotecas externas)
2. Self-contained: todo o CSS e JS inline
3. Responsive: funcionar em tablet (min-width 768px) e quadro interactivo (1920px)
4. Touch-friendly: áreas clicáveis mínimo 44x44px, suporte touch events
5. Acessibilidade: aria-labels, contraste adequado, tamanho de fonte mínimo 16px
6. Cores vivas e amigáveis para crianças, com feedback visual claro
7. Animações suaves (CSS transitions/requestAnimationFrame)
8. Implementar os 3 níveis de diferenciação como tabs ou botões seleccionáveis
9. O Constraint NÃO deve ser revelado — a interacção deve levar à descoberta
10. Incluir feedback visual quando o aluno descobre o Constraint (confetti, cor, mensagem)

## Output:
Para cada unit, responde com:
```html
<!-- INTERACTIVE_N_START -->
<div class="interactive" id="interactive-N">
  <style>/* scoped CSS */</style>
  ... HTML da interacção ...
  <script>/* JS da interacção */</script>
</div>
<!-- INTERACTIVE_N_END -->
```
"""
    return prompt


def build_evaluator_prompt(docspec: dict, html_content: str) -> str:
    """Build the Evaluator agent prompt."""
    prompt = f"""# Tarefa: Avaliar página PageCraft

## DocSpec-AM original:
```json
{json.dumps(docspec, indent=2, ensure_ascii=False)[:8000]}
```

## HTML gerado:
```html
{html_content[:12000]}
```

## Verificações obrigatórias:
1. **Correcção factual**: O conteúdo é cientificamente correcto para o nível?
2. **Alinhamento com Constraint**: A interacção permite descobrir o invariante pedagógico?
3. **Assessment observável**: O critério de avaliação é praticável em sala de aula?
4. **Diferenciação**: Os 3 níveis estão implementados e são distintos?
5. **HTML válido**: Sem erros de sintaxe, tags fechadas, IDs únicos?
6. **Acessibilidade**: aria-labels, contraste, touch targets?
7. **Adequação à idade**: Linguagem, complexidade visual, tamanho de texto?
8. **Maker (se aplicável)**: O desafio maker liga-se logicamente à exploração digital?

## Output:
Responde com JSON:
```json
{{
  "pass": true/false,
  "score": {{ "factual": 1-5, "alignment": 1-5, "accessibility": 1-5, "differentiation": 1-5 }},
  "issues": ["lista de problemas encontrados"],
  "suggestions": ["lista de melhorias sugeridas"],
  "critical": ["problemas que DEVEM ser corrigidos antes de publicar"]
}}
```
"""
    return prompt


def build_html_page(
    topic: str,
    slug: str,
    intro: str,
    units_text: list[str],
    units_interactive: list[str],
    assessment: str,
    docspec: dict,
) -> str:
    """Assemble the final HTML page."""

    # Build units HTML
    units_html = ""
    for i, (text, interactive) in enumerate(zip(units_text, units_interactive), 1):
        units_html += f"""
    <article class="knowledge-unit" id="unit-{i}">
      {text}
      {interactive}
    </article>
"""

    # Curriculum footer
    curriculum = docspec.get("curriculum", {})
    ae_refs = curriculum.get("ae", [])
    competencies = curriculum.get("competencies", [])
    ae_html = "".join(
        f"<li>{ae.get('subject', '')} {ae.get('year', '')}: {ae.get('descriptor', '')}</li>"
        for ae in ae_refs
    )
    comp_html = "".join(f"<li>{c}</li>" for c in competencies)

    maker_units = [u for u in docspec.get("units", []) if u.get("maker")]
    maker_html = ""
    if maker_units:
        maker_items = "".join(
            f"<li><strong>{u['maker']['type'].title()}</strong>: {u['maker']['challenge']}</li>"
            for u in maker_units
        )
        maker_html = f"""
    <section class="maker-challenges">
      <h2>🛠️ Desafios Maker</h2>
      <ul>{maker_items}</ul>
    </section>
"""

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PageCraft — {topic}</title>
  <style>
    :root {{
      --primary: #4A90D9;
      --secondary: #7BC67E;
      --accent: #FFB84D;
      --danger: #E57373;
      --bg: #FAFBFC;
      --text: #2D3436;
      --radius: 12px;
      --shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 18px;
      line-height: 1.6;
      padding: 1rem;
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      background: linear-gradient(135deg, var(--primary), #6C5CE7);
      color: white;
      padding: 2rem;
      border-radius: var(--radius);
      margin-bottom: 2rem;
      text-align: center;
    }}
    header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
    header .meta {{ font-size: 0.9rem; opacity: 0.9; }}
    .knowledge-unit {{
      background: white;
      border-radius: var(--radius);
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: var(--shadow);
    }}
    .knowledge-unit h2 {{
      color: var(--primary);
      margin-bottom: 1rem;
      font-size: 1.5rem;
    }}
    .interactive {{
      background: #F8F9FA;
      border: 2px solid #E9ECEF;
      border-radius: var(--radius);
      padding: 1.5rem;
      margin: 1.5rem 0;
    }}
    .diff-tabs {{
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }}
    .diff-tab {{
      padding: 0.5rem 1rem;
      border: 2px solid #DDD;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
      background: white;
      touch-action: manipulation;
      min-height: 44px;
      display: flex;
      align-items: center;
    }}
    .diff-tab.active {{ border-color: var(--primary); background: var(--primary); color: white; }}
    .diff-tab:hover {{ border-color: var(--primary); }}
    .assessment {{
      background: #FFF3E0;
      border: 2px solid var(--accent);
      border-radius: var(--radius);
      padding: 2rem;
      margin-bottom: 2rem;
    }}
    .assessment h2 {{ color: #E65100; margin-bottom: 1rem; }}
    .maker-challenges {{
      background: #E8F5E9;
      border: 2px solid var(--secondary);
      border-radius: var(--radius);
      padding: 2rem;
      margin-bottom: 2rem;
    }}
    .maker-challenges h2 {{ color: #2E7D32; margin-bottom: 1rem; }}
    .curriculum-footer {{
      background: #F3E5F5;
      border-radius: var(--radius);
      padding: 1.5rem;
      font-size: 0.85rem;
      margin-top: 2rem;
    }}
    .curriculum-footer h3 {{ margin-bottom: 0.5rem; color: #7B1FA2; }}
    .curriculum-footer ul {{ margin-left: 1.5rem; }}
    input[type="range"] {{
      width: 100%;
      height: 44px;
      cursor: pointer;
      -webkit-appearance: none;
      background: transparent;
    }}
    input[type="range"]::-webkit-slider-thumb {{
      -webkit-appearance: none;
      height: 28px;
      width: 28px;
      border-radius: 50%;
      background: var(--primary);
      cursor: pointer;
      margin-top: -10px;
    }}
    input[type="range"]::-webkit-slider-runnable-track {{
      height: 8px;
      background: #DDD;
      border-radius: 4px;
    }}
    select {{
      font-size: 1rem;
      padding: 0.5rem 1rem;
      border-radius: 8px;
      border: 2px solid #DDD;
      min-height: 44px;
      background: white;
    }}
    button {{
      font-size: 1rem;
      padding: 0.5rem 1.5rem;
      border-radius: 8px;
      border: 2px solid var(--primary);
      background: var(--primary);
      color: white;
      cursor: pointer;
      min-height: 44px;
      touch-action: manipulation;
      transition: all 0.2s;
    }}
    button:hover {{ opacity: 0.9; transform: scale(1.02); }}
    @media (max-width: 768px) {{
      body {{ font-size: 16px; padding: 0.5rem; }}
      header {{ padding: 1.5rem; }}
      header h1 {{ font-size: 1.5rem; }}
      .knowledge-unit {{ padding: 1rem; }}
    }}
    .pagecraft-footer {{
      text-align: center;
      font-size: 0.75rem;
      color: #999;
      margin-top: 2rem;
      padding: 1rem;
    }}
  </style>
</head>
<body>
  {intro}

  <main>
    {units_html}
  </main>

  {assessment}

  {maker_html}

  <footer class="curriculum-footer">
    <h3>📚 Referências Curriculares</h3>
    <p><strong>Aprendizagens Essenciais:</strong></p>
    <ul>{ae_html}</ul>
    <p><strong>Áreas de Competência (Perfil do Aluno):</strong></p>
    <ul>{comp_html}</ul>
  </footer>

  <div class="pagecraft-footer">
    Gerado por PageCraft 🛠️ — {datetime.now().strftime("%Y-%m-%d")}
  </div>
</body>
</html>"""
    return html


def build_markdown(topic: str, docspec: dict) -> str:
    """Generate the Markdown companion file (teacher version)."""

    lines = [
        f"# {topic}",
        f"",
        f"**Ano:** {docspec.get('ageRange', '')}",
        f"**Duração:** {docspec.get('duration', '')} minutos",
        f"",
        f"## Objectivos",
    ]
    for obj in docspec.get("objectives", []):
        lines.append(f"- {obj}")

    lines.append("")
    lines.append("## Materiais")
    for mat in docspec.get("materials", []):
        lines.append(f"- {mat}")

    # Session flow
    flow = docspec.get("sessionFlow", "")
    if flow:
        lines.extend(["", "## Fluxo da sessão", flow])

    # MEM alignment
    mem = docspec.get("memAlignment", {})
    if mem:
        lines.extend(["", "## Alinhamento MEM"])
        for mod in mem.get("modules", []):
            lines.append(f"- {mod}")
        org = mem.get("socialOrganization", "")
        if org:
            lines.append(f"- **Organização social:** {org}")

    # Units
    for i, unit in enumerate(docspec.get("units", []), 1):
        lines.extend(
            [
                "",
                f"## Unit {i}: {unit.get('summary', '')}",
                "",
                f"**O aluno deve compreender:** {unit.get('textDescription', '')}",
                "",
                f"**Interacção:**",
                f"- Constraint: {unit.get('interaction', {}).get('constraint', '')}",
                f"- Assessment: {unit.get('interaction', {}).get('assessment', '')}",
                "",
                f"**Diferenciação:**",
                f"- 🟢 Apoio: {unit.get('differentiation', {}).get('support', '')}",
                f"- 🟡 Intermédio: {unit.get('differentiation', {}).get('standard', '')}",
                f"- 🔴 Desafio: {unit.get('differentiation', {}).get('challenge', '')}",
            ]
        )

        maker = unit.get("maker")
        if maker:
            lines.extend(
                [
                    "",
                    f"**🛠️ Desafio Maker ({maker.get('type', '')}):**",
                    f"- Desafio: {maker.get('challenge', '')}",
                    f"- Grupo: {maker.get('groupSize', '')} alunos",
                    f"- Ligação ao digital: {maker.get('connection', '')}",
                    f"- Comunicação: {maker.get('communication', '')}",
                ]
            )
            alts = maker.get("alternatives", [])
            if alts:
                lines.append(f"- Alternativas: {'; '.join(alts)}")

    # Curriculum
    curriculum = docspec.get("curriculum", {})
    if curriculum:
        lines.extend(
            ["", "## Referências Curriculares", "", "### Aprendizagens Essenciais"]
        )
        for ae in curriculum.get("ae", []):
            lines.append(
                f"- **{ae.get('subject', '')} ({ae.get('year', '')})**: {ae.get('descriptor', '')}"
            )
        lines.extend(["", "### Perfil do Aluno"])
        for comp in curriculum.get("competencies", []):
            lines.append(f"- {comp}")

    lines.extend(
        ["", "---", f"*Gerado por PageCraft 🛠️ — {datetime.now().strftime('%Y-%m-%d')}*"]
    )

    return "\n".join(lines)


def save_outputs(topic: str, html: str, markdown: str, docspec: dict) -> dict:
    """Save all output files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slug = slugify(topic)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    base = f"{date_prefix}-{slug}"

    html_path = OUTPUT_DIR / f"{base}.html"
    md_path = OUTPUT_DIR / f"{base}.md"
    spec_path = OUTPUT_DIR / f"{base}-docspec.json"

    html_path.write_text(html, encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    spec_path.write_text(
        json.dumps(docspec, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "html": str(html_path),
        "markdown": str(md_path),
        "docspec": str(spec_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="PageCraft — Multi-agent interactive lesson page generator"
    )
    parser.add_argument("--topic", required=True, help="Tópico da aula")
    parser.add_argument(
        "--year", required=True, help="Ano escolar (ex: '3o ano', 'pre-escolar')"
    )
    parser.add_argument(
        "--duration", type=int, default=40, help="Duração em minutos (default: 40)"
    )
    parser.add_argument(
        "--maker",
        default="",
        help="Recursos maker separados por vírgula (ex: minecraft,lego,whiteboard)",
    )
    parser.add_argument("--no-maker", action="store_true", help="Sem extensões maker")
    parser.add_argument(
        "--architect-only",
        action="store_true",
        help="Gerar apenas o DocSpec-AM (sem HTML)",
    )
    parser.add_argument(
        "--from-spec", help="Caminho para DocSpec-AM JSON existente (skip Architect)"
    )
    parser.add_argument("--output-dir", help="Directório de output alternativo")

    args = parser.parse_args()

    if args.output_dir:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output_dir)

    # Parse year
    year_info = parse_year(args.year)

    # Parse maker types
    maker_types = []
    if not args.no_maker:
        if args.maker:
            maker_types = [m.strip() for m in args.maker.split(",") if m.strip()]
        else:
            maker_types = ["whiteboard"]  # Default: at least whiteboard

    # Find AE files
    ae_files = find_ae_files(year_info)

    print(f"🛠️  PageCraft — {args.topic}")
    print(f"📚 Ano: {year_info['year']} ({year_info['age_range']})")
    print(f"⏱️  Duração: {args.duration} min")
    print(f"🎮 Maker: {', '.join(maker_types) if maker_types else 'nenhum'}")
    print(f"📄 AE encontradas: {len(ae_files)} ficheiros")
    print()

    slug = slugify(args.topic)
    html_path = OUTPUT_DIR / f"{slug}.html"
    md_path = OUTPUT_DIR / f"{slug}.md"
    spec_path = OUTPUT_DIR / f"{slug}-docspec.json"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Phase 1: Architect ---
    if args.from_spec:
        print("📋 A carregar DocSpec-AM existente...")
        try:
            docspec = json.loads(Path(args.from_spec).read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"❌ Erro ao carregar --from-spec: {exc}")
            sys.exit(1)
    else:
        print("🎯 [1/5] Architect — a gerar DocSpec-AM...")
        architect_prompt = build_architect_prompt(
            args.topic, year_info, args.duration, maker_types, ae_files
        )

        # Save prompt for debugging / manual use
        prompt_path = OUTPUT_DIR / "_last_architect_prompt.md"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(architect_prompt, encoding="utf-8")
        print(f"   Prompt guardado: {prompt_path}")

        if args.architect_only:
            print(
                "\n✅ Modo --architect-only: prompt gerado. Usar com outro agente ou fase manual para gerar DocSpec-AM."
            )
            print(f"   Prompt: {prompt_path}")
            sys.exit(0)

        print(
            "   ⚠️  O pipeline completo deve ser conduzido pelo orchestrator/agente que carregou a skill."
        )
        print(
            "   💡 Próximo passo: delegar Architect/Designer/Builder/Proofreader/Evaluator com as ferramentas disponíveis do ambiente."
        )
        print(f"   📄 Prompt: {prompt_path}")
        sys.exit(0)

    if not spec_path.exists():
        spec_path.write_text(
            json.dumps(docspec, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # --- Phase 2: Writer + Builder prompts (artefactos para o orchestrator externo) ---
    print("✍️  [2/5] Writer — a gerar prompt...")
    writer_prompt = build_writer_prompt(docspec)
    (OUTPUT_DIR / "_last_writer_prompt.md").write_text(writer_prompt, encoding="utf-8")

    print("🔧 [3/5] Builder — a gerar prompt...")
    builder_prompt = build_builder_prompt(docspec)
    (OUTPUT_DIR / "_last_builder_prompt.md").write_text(
        builder_prompt, encoding="utf-8"
    )

    # --- Phase 4-5: ficam a cargo do orchestrator externo ---
    markdown = build_markdown(args.topic, docspec)
    md_path.write_text(markdown, encoding="utf-8")
    print("\n📁 Artefactos gerados para o orchestrator:")
    print(f"   Markdown: {md_path}")
    print(f"   DocSpec:  {spec_path}")
    print(f"   Writer:   {OUTPUT_DIR / '_last_writer_prompt.md'}")
    print(f"   Builder:  {OUTPUT_DIR / '_last_builder_prompt.md'}")


if __name__ == "__main__":
    main()
