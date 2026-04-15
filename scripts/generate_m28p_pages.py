from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVITIES_DIR = ROOT / "activities"
VARIANTS_PATH = ROOT / "scripts" / "m28p_page_variants.json"


WORD_EMOJIS = {
    "menina": "👧",
    "menino": "👦",
    "uva": "🍇",
    "dedo": "☝️",
    "sapato": "👟",
    "bota": "🥾",
    "leque": "🪭",
    "casa": "🏡",
    "janela": "🪟",
    "telhado": "🏠",
    "escada": "🪜",
    "chave": "🔑",
    "galinha": "🐔",
    "ovo": "🥚",
    "rato": "🐭",
    "cenoura": "🥕",
    "girafa": "🦒",
    "palhaco": "🤡",
    "zebra": "🦓",
    "bandeira": "🚩",
    "funil": "⚗️",
    "arvore": "🌳",
    "quadro": "🖼️",
    "passarinho": "🐦",
    "peixe": "🐟",
    "cigarra": "🦗",
    "fogueira": "🔥",
    "flor": "🌸",
}


AO90_REPLACEMENTS = [
    (r"\bObjectivos\b", "Objetivos"),
    (r"\bobjectivos\b", "objetivos"),
    (r"\bObjectivo\b", "Objetivo"),
    (r"\bobjectivo\b", "objetivo"),
    (r"\bObjecto\b", "Objeto"),
    (r"\bobjecto\b", "objeto"),
    (r"\bObjectos\b", "Objetos"),
    (r"\bobjectos\b", "objetos"),
    (r"\bInteractiva\b", "Interativa"),
    (r"\binteractiva\b", "interativa"),
    (r"\bInteractivo\b", "Interativo"),
    (r"\binteractivo\b", "interativo"),
    (r"\bInteractivos\b", "Interativos"),
    (r"\binteractivos\b", "interativos"),
    (r"\bInteractivas\b", "Interativas"),
    (r"\binteractivas\b", "interativas"),
    (r"\bInteracção\b", "Interação"),
    (r"\binteracção\b", "interação"),
    (r"\bInteracções\b", "Interações"),
    (r"\binteracções\b", "interações"),
    (r"\bActividade\b", "Atividade"),
    (r"\bactividade\b", "atividade"),
    (r"\bActividades\b", "Atividades"),
    (r"\bactividades\b", "atividades"),
    (r"\bActivo\b", "Ativo"),
    (r"\bactivo\b", "ativo"),
    (r"\bActiva\b", "Ativa"),
    (r"\bactiva\b", "ativa"),
    (r"\bActivar\b", "Ativar"),
    (r"\bactivar\b", "ativar"),
    (r"\bActivação\b", "Ativação"),
    (r"\bactivação\b", "ativação"),
    (r"\bCorrecto\b", "Correto"),
    (r"\bcorrecto\b", "correto"),
    (r"\bCorrecta\b", "Correta"),
    (r"\bcorrecta\b", "correta"),
    (r"\bCorrectamente\b", "Corretamente"),
    (r"\bcorrectamente\b", "corretamente"),
    (r"\bSelecciona\b", "Seleciona"),
    (r"\bselecciona\b", "seleciona"),
    (r"\bSeleccionar\b", "Selecionar"),
    (r"\bseleccionar\b", "selecionar"),
    (r"\bSeleccionada\b", "Selecionada"),
    (r"\bseleccionada\b", "selecionada"),
    (r"\bSeleccionado\b", "Selecionado"),
    (r"\bseleccionado\b", "selecionado"),
    (r"\bSeleccionando\b", "Selecionando"),
    (r"\bseleccionando\b", "selecionando"),
    (r"\bSelecção\b", "Seleção"),
    (r"\bselecção\b", "seleção"),
    (r"\bSelecções\b", "Seleções"),
    (r"\bselecções\b", "seleções"),
    (r"\bDirecção\b", "Direção"),
    (r"\bdirecção\b", "direção"),
    (r"\bDirecções\b", "Direções"),
    (r"\bdirecções\b", "direções"),
    (r"\bColecção\b", "Coleção"),
    (r"\bcolecção\b", "coleção"),
    (r"\bColectivo\b", "Coletivo"),
    (r"\bcolectivo\b", "coletivo"),
    (r"\bColectiva\b", "Coletiva"),
    (r"\bcolectiva\b", "coletiva"),
    (r"\bRespectivos\b", "Respetivos"),
    (r"\brespectivos\b", "respetivos"),
    (r"\bRespectivo\b", "Respetivo"),
    (r"\brespectivo\b", "respetivo"),
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ao90(text: str) -> str:
    if not text:
        return ""
    updated = text.replace("\u00a0", " ")
    for pattern, replacement in AO90_REPLACEMENTS:
        updated = re.sub(pattern, replacement, updated)
    updated = re.sub(r"\s+\n", "\n", updated)
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated.strip()


def esc(text: str) -> str:
    return html.escape(ao90(str(text)), quote=True)


def paragraphize(text: str) -> str:
    if not text:
        return ""
    blocks = [block.strip() for block in ao90(text).split("\n") if block.strip()]
    return "".join(f"<p>{esc(block)}</p>" for block in blocks)


def slug_to_word(meta_title: str) -> str:
    return ao90(meta_title.split("—")[-1].strip())


def lowercase_word(word: str) -> str:
    return ao90(word.lower())


def first_phrase(word: str, objectives: list[str], units: list[dict]) -> str:
    pattern = re.compile(r"['\"]([^'\"]+)['\"]")
    haystacks = list(objectives)
    for unit in units:
        haystacks.append(unit.get("textDescription", ""))
    for item in haystacks:
        for candidate in pattern.findall(item):
            if word.lower() in ao90(candidate).lower():
                return ao90(candidate)
    return f"A palavra é {lowercase_word(word)}."


def teaser(objectives: list[str]) -> list[str]:
    return [esc(item) for item in objectives[:3]]


def choice_words(current_index: int, words: list[str], current_word: str) -> list[str]:
    prev_word = words[current_index - 1] if current_index > 0 else words[-1]
    next_word = words[(current_index + 1) % len(words)]
    options = [
        lowercase_word(current_word),
        lowercase_word(prev_word),
        lowercase_word(next_word),
    ]
    seen = []
    for option in options:
        if option not in seen:
            seen.append(option)
    return seen[:3]


def normalize_id(text: str) -> str:
    base = ao90(text).lower()
    base = re.sub(r"[^a-z0-9áàâãçéêíóôõúü-]+", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    return base or "secao"


def render_list(items: list[str]) -> str:
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def render_teacher_guide(docspec: dict, selected_units: list[tuple[int, dict]]) -> str:
    curriculum = docspec.get("curriculum", {})
    ae_items = []
    for item in curriculum.get("ae", []):
        subject = ao90(item.get("subject", ""))
        year = ao90(item.get("year", ""))
        descriptor = ao90(item.get("descriptor", ""))
        label = " · ".join(part for part in [subject, year] if part)
        ae_items.append(f"<li><strong>{esc(label)}</strong>: {esc(descriptor)}</li>")
    competencies = render_list(curriculum.get("competencies", []))
    materials = render_list(docspec.get("materials", []))
    mem = docspec.get("memAlignment", {})
    mem_items = []
    if mem.get("modules"):
        mem_items.append(
            f"<li><strong>Módulos:</strong> {esc(', '.join(mem['modules']))}</li>"
        )
    if mem.get("instruments"):
        mem_items.append(
            f"<li><strong>Instrumentos:</strong> {esc(', '.join(mem['instruments']))}</li>"
        )
    if mem.get("socialOrganization"):
        mem_items.append(
            f"<li><strong>Organização:</strong> {esc(mem['socialOrganization'])}</li>"
        )
    selected_objectives = docspec.get("objectives", [])[
        : max(2, min(4, len(selected_units)))
    ]
    session_flow = render_list(
        [
            f"Unidade {index}: {ao90(unit.get('summary', f'Unidade {index}'))}"
            for index, unit in selected_units
        ]
    )
    return f"""
    <details class=\"teacher-guide\">
      <summary>Guia do professor</summary>
      <div class=\"teacher-grid\">
        <article class=\"teacher-card\">
          <h3>Objetivos desta página</h3>
          {render_list(selected_objectives)}
        </article>
        <article class=\"teacher-card\">
          <h3>Materiais</h3>
          {materials}
        </article>
        <article class=\"teacher-card\">
          <h3>Organização MEM</h3>
          <ul>{"".join(mem_items)}</ul>
        </article>
        <article class=\"teacher-card\">
          <h3>Percurso desta página</h3>
          {session_flow}
        </article>
        <article class=\"teacher-card teacher-card-wide\">
          <h3>Referências curriculares</h3>
          <ul>{"".join(ae_items)}</ul>
          {competencies}
        </article>
      </div>
    </details>
    """


def render_unit(
    unit: dict,
    index: int,
    focus_units: set[int],
    syllables: list[str],
    phrase: str,
    variant_index: int,
    choices: list[str],
    prompts: list[str],
) -> str:
    summary = ao90(unit.get("summary", f"Unidade {index}"))
    section_id = f"u{index}-{normalize_id(summary)}"
    text_description = paragraphize(unit.get("textDescription", ""))
    interaction = unit.get("interaction", {})
    render_text = paragraphize(interaction.get("render", ""))
    transition_text = paragraphize(interaction.get("transition", ""))
    assessment = paragraphize(interaction.get("assessment", ""))
    support = ao90(unit.get("differentiation", {}).get("support", ""))
    standard = ao90(unit.get("differentiation", {}).get("standard", ""))
    challenge = ao90(unit.get("differentiation", {}).get("challenge", ""))
    maker = unit.get("maker") or {}
    highlight = (
        '<span class="unit-badge">Em destaque</span>' if index in focus_units else ""
    )

    widgets = {
        1: f"""
        <div class=\"play-card\">
          <button class=\"pill-btn reveal-btn\" data-target=\"story-{index}\">Mostrar a história</button>
          <button class=\"pill-btn speak-btn\" data-speak=\"{esc(phrase)}\">Ouvir</button>
          <div id=\"story-{index}\" class=\"reveal-box hidden\">{text_description}</div>
        </div>
        """,
        2: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Escolhe a palavra certa.</p>
          <div class=\"choice-row\">
            {"".join(f'<button class="choice-btn" data-answer="{esc(lowercase_word(choices[0]))}" data-choice="{esc(option)}">{esc(option)}</button>' for option in choices)}
          </div>
          <p class=\"feedback\" aria-live=\"polite\">Procura a palavra completa.</p>
        </div>
        """,
        3: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Toca nas sílabas para formar a palavra.</p>
          <div class=\"syllable-bank\" data-compose=\"compose-{index}\">{"".join(f'<button class="syllable-chip" style="--chip:{esc(color)}" data-syllable="{esc(syllable)}">{esc(syllable)}</button>' for syllable, color in syllables)}</div>
          <div id=\"compose-{index}\" class=\"compose-output\">__</div>
          <div class=\"compose-actions\"><button class=\"pill-btn clear-compose\" data-compose-clear=\"compose-{index}\">Limpar</button></div>
        </div>
        """,
        4: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Experimenta combinações com as sílabas.</p>
          <div class=\"syllable-bank\" data-compose=\"mix-{index}\">{"".join(f'<button class="syllable-chip" style="--chip:{esc(color)}" data-syllable="{esc(syllable)}">{esc(syllable)}</button>' for syllable, color in syllables)}</div>
          <div id=\"mix-{index}\" class=\"compose-output\">__</div>
          <p class=\"helper-text\">Nem todas as combinações resultam em palavras reais. O importante é experimentar.</p>
        </div>
        """,
        5: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Completa a palavra.</p>
          <div class=\"cloze-word\">{esc(" ".join("___" if i == (variant_index - 1) % max(len(syllables), 1) else syllable for i, (syllable, _) in enumerate(syllables)))}</div>
          <div class=\"choice-row\">{"".join(f'<button class="choice-btn cloze-option" data-cloze-answer="{esc(syllables[(variant_index - 1) % max(len(syllables), 1)][0])}" data-choice="{esc(syllable)}">{esc(syllable)}</button>' for syllable, _ in syllables)}</div>
          <p class=\"feedback\" aria-live=\"polite\">Escolhe a sílaba em falta.</p>
        </div>
        """,
        6: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Lê a frase e escreve a tua.</p>
          <div class=\"phrase-card\">{esc(phrase)}</div>
          <div class=\"compose-actions\"><button class=\"pill-btn speak-btn\" data-speak=\"{esc(phrase)}\">Ouvir a frase</button></div>
          <textarea class=\"phrase-input\" rows=\"3\" placeholder=\"Escreve aqui uma frase com a palavra.\"></textarea>
        </div>
        """,
        7: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Marca o que já consegues fazer.</p>
          <div class=\"check-grid\">
            <button class=\"check-card\">Reconheço a palavra</button>
            <button class=\"check-card\">Separo as sílabas</button>
            <button class=\"check-card\">Reconstruo a palavra</button>
            <button class=\"check-card\">Uso a palavra numa frase</button>
          </div>
        </div>
        """,
        8: f"""
        <div class=\"play-card\">
          <p class=\"play-label\">Escolhe uma proposta final.</p>
          <div class=\"prompt-grid\">{"".join(f'<button class="prompt-card">{esc(prompt)}</button>' for prompt in prompts)}</div>
        </div>
        """,
    }

    maker_html = ""
    if maker:
        maker_bits = []
        if maker.get("challenge"):
            maker_bits.append(
                f"<p><strong>Desafio maker:</strong> {esc(maker['challenge'])}</p>"
            )
        if maker.get("materials"):
            maker_bits.append(
                f"<p><strong>Materiais:</strong> {esc(', '.join(maker['materials']))}</p>"
            )
        if maker.get("communication"):
            maker_bits.append(
                f"<p><strong>Comunicação:</strong> {esc(maker['communication'])}</p>"
            )
        maker_html = f'<div class="maker-box">{"".join(maker_bits)}</div>'

    return f"""
    <section id=\"{section_id}\" class=\"unit-card\">
      <div class=\"unit-head\">
        <div>
          <span class=\"unit-kicker\">Unidade {index}</span>
          <h2>{esc(summary)}</h2>
        </div>
        {highlight}
      </div>
      <div class=\"unit-grid\">
        <article class=\"unit-copy\">
          {text_description}
          <div class=\"unit-flow\">
            <div>
              <h3>O que vais fazer</h3>
              {render_text or "<p>Segue a proposta apresentada e experimenta a palavra com atenção.</p>"}
            </div>
            <div>
              <h3>O que observar</h3>
              {assessment or "<p>Verifica se consegues reconhecer, ler e usar a palavra com confiança.</p>"}
            </div>
          </div>
          {transition_text}
          {maker_html}
        </article>
        <aside class=\"unit-play\">{widgets[index]}</aside>
      </div>
      <div class=\"diff-switcher\">
        <button class=\"diff-btn is-active\" data-diff=\"support-{index}\">🟢 Com ajuda</button>
        <button class=\"diff-btn\" data-diff=\"standard-{index}\">🟡 Objetivo</button>
        <button class=\"diff-btn\" data-diff=\"challenge-{index}\">🔴 Desafio</button>
      </div>
      <div class=\"diff-panels\">
        <div id=\"support-{index}\" class=\"diff-panel is-active\">{paragraphize(support)}</div>
        <div id=\"standard-{index}\" class=\"diff-panel\">{paragraphize(standard)}</div>
        <div id=\"challenge-{index}\" class=\"diff-panel\">{paragraphize(challenge)}</div>
      </div>
    </section>
    """


def build_page(
    activity_dir: Path,
    meta: dict,
    docspec: dict,
    design: dict,
    variant: dict,
    words: list[str],
    current_index: int,
) -> str:
    word = slug_to_word(meta["title"])
    lower_word = lowercase_word(word)
    order = meta["order"]
    slug = meta["slug"]
    emoji = WORD_EMOJIS.get(slug, "✨")
    page_links = [
        {"filename": item["filename"], "navLabel": item["navLabel"]}
        for item in VARIANTS
    ]
    syllables = [(ao90(k), v) for k, v in design.get("syllableColors", {}).items()]
    objectives = [ao90(item) for item in docspec.get("objectives", [])]
    units = docspec.get("units", [])[:8]
    visible_units = variant["visibleUnits"]
    focus_units = set(variant["focusUnits"])
    selected_units = [
        (idx, unit) for idx, unit in enumerate(units, start=1) if idx in visible_units
    ]
    phrase = first_phrase(word, objectives, units)
    choices = choice_words(current_index, words, word)
    page_title = f"M28P #{order} — {lower_word} | PageCraft"
    section_nav = "".join(
        f'<a class="nav-pill" href="#u{index}-{normalize_id(unit.get("summary", str(index)))}">{index}</a>'
        for index, unit in selected_units
    )
    page_nav = "".join(
        f'<a class="page-link{" is-current" if link["filename"] == variant["filename"] else ""}" href="./{link["filename"]}">{esc(link["navLabel"])}<span>{"Atual" if link["filename"] == variant["filename"] else "Abrir"}</span></a>'
        for link in page_links
    )
    objective_chips = "".join(f"<li>{item}</li>" for item in teaser(objectives))
    units_html = "".join(
        render_unit(
            unit,
            idx,
            focus_units,
            syllables,
            phrase,
            VARIANTS.index(variant) + 1,
            choices,
            variant["extensionPrompts"],
        )
        for idx, unit in selected_units
    )
    teacher_guide = render_teacher_guide(docspec, selected_units)
    return f"""<!doctype html>
<html lang=\"pt-PT\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{esc(page_title)}</title>
  <link rel=\"icon\" href=\"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCI+PHRleHQgeT0iNTAiIGZvbnQtc2l6ZT0iNDgiPvCfk5g8L3RleHQ+PC9zdmc+\" />
  <style>
    :root {{
      --bg: {esc(design["palette"]["bg"])};
      --surface: {esc(design["palette"]["surface"])};
      --primary: {esc(design["palette"]["primary"])};
      --accent: {esc(design["palette"]["accent"])};
      --text: {esc(design["palette"]["text"])};
      --correct: #22c55e;
      --correct-bg: #f0fdf4;
      --incorrect: #F59E0B;
      --incorrect-bg: #fffbeb;
      --radius: 16px;
      --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      --font: 'Nunito', 'Comic Sans MS', 'Chalkboard SE', sans-serif;
      --touch-size: 48px;
      --card-gap: 1rem;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      font-family: var(--font);
      background:
        radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 20%, transparent), transparent 38%),
        linear-gradient(180deg, color-mix(in srgb, var(--primary) 8%, var(--bg)), var(--bg));
      color: var(--text);
      font-size: 20px;
      line-height: 1.55;
      min-height: 100vh;
    }}
    a, button, summary, textarea {{ font: inherit; }}
    .skip-link {{ position: absolute; left: 1rem; top: -4rem; background: var(--surface); color: var(--text); padding: 0.75rem 1rem; border-radius: 9999px; z-index: 1000; border: 2px solid var(--primary); }}
    .skip-link:focus {{ top: 1rem; }}
    :focus-visible {{ outline: 3px solid var(--primary); outline-offset: 2px; }}
    .shell {{ max-width: 1120px; margin: 0 auto; padding: 1rem 1rem 3rem; }}
    .hero {{
      position: relative;
      overflow: hidden;
      border-radius: 28px;
      padding: 1.4rem;
      background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 72%, white), color-mix(in srgb, var(--accent) 60%, white));
      color: white;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.14);
    }}
    .hero::after {{ content: ""; position: absolute; inset: auto -8% -24% auto; width: 260px; height: 260px; border-radius: 50%; background: rgba(255,255,255,0.14); }}
    .hero-top {{ display: flex; gap: 1rem; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; position: relative; z-index: 1; }}
    .hero-kicker, .hero-badge, .meta-chip, .nav-pill, .page-link span {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: var(--touch-size);
      min-width: var(--touch-size);
      border-radius: 9999px;
      padding: 0.75rem 1.25rem;
      font-weight: 700;
    }}
    .hero-kicker {{ background: rgba(255,255,255,0.16); }}
    .hero-badge {{ background: rgba(255,255,255,0.22); }}
    .hero-grid {{ display: grid; gap: 1.25rem; grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.9fr); margin-top: 1.25rem; position: relative; z-index: 1; }}
    .hero-copy h1 {{ font-size: clamp(2.2rem, 6vw, 3.6rem); line-height: 1.05; margin: 0.4rem 0 0.7rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }}
    .hero-copy p {{ margin: 0.4rem 0; max-width: 45rem; }}
    .word-scene {{ background: rgba(255,255,255,0.14); border: 2px solid rgba(255,255,255,0.28); border-radius: 24px; padding: 1rem; backdrop-filter: blur(4px); }}
    .word-scene .emoji {{ font-size: clamp(3rem, 10vw, 5.5rem); line-height: 1; }}
    .meta-row, .objective-row, .syllable-row, .page-switch, .section-nav {{ display: flex; gap: 0.75rem; flex-wrap: wrap; }}
    .meta-row {{ margin-top: 1rem; }}
    .meta-chip {{ background: rgba(255,255,255,0.18); }}
    .objective-row {{ margin: 1rem 0 0; padding: 0; list-style: none; }}
    .objective-row li {{ background: rgba(255,255,255,0.22); border-radius: 9999px; padding: 0.75rem 1rem; font-weight: 700; min-height: var(--touch-size); display: inline-flex; align-items: center; }}
    .word-spotlight {{ margin-top: 1rem; display: grid; gap: 1rem; grid-template-columns: 1.1fr 1fr; }}
    .spot-card {{ background: var(--surface); color: var(--text); border: 2px solid color-mix(in srgb, var(--primary) 70%, white); border-radius: 24px; padding: 1rem; box-shadow: var(--shadow); }}
    .spot-card h2 {{ margin: 0 0 0.75rem; font-size: clamp(1.5rem, 4vw, 2rem); font-weight: 800; }}
    .spot-card .word-display {{ font-size: clamp(2.4rem, 7vw, 3.8rem); font-weight: 800; color: var(--primary); letter-spacing: 0.05em; text-transform: uppercase; }}
    .spot-card .mission {{ margin-top: 0.75rem; }}
    .syllable-row {{ margin-top: 1rem; }}
    .syllable-token, .syllable-chip {{
      min-height: var(--touch-size);
      min-width: var(--touch-size);
      border-radius: 12px;
      border: none;
      color: white;
      font-weight: 800;
      font-size: clamp(1.5rem, 4vw, 2rem);
      padding: 0.55rem 1rem;
      background: var(--chip, var(--primary));
      box-shadow: var(--shadow);
    }}
    .page-switch {{ margin: 1.2rem 0 0.5rem; }}
    .page-link {{
      text-decoration: none;
      background: var(--surface);
      color: var(--text);
      border: 2px solid color-mix(in srgb, var(--primary) 28%, white);
      border-radius: 18px;
      padding: 0.85rem 1rem;
      min-height: var(--touch-size);
      display: flex;
      gap: 0.75rem;
      align-items: center;
      justify-content: space-between;
      flex: 1 1 200px;
      box-shadow: var(--shadow);
      font-weight: 700;
    }}
    .page-link.is-current {{ background: color-mix(in srgb, var(--accent) 20%, var(--surface)); border-color: var(--accent); }}
    .section-nav {{ position: sticky; top: 0; z-index: 10; padding: 0.85rem 0 1rem; background: linear-gradient(180deg, var(--bg), rgba(255,248,240,0.88)); backdrop-filter: blur(6px); }}
    .nav-pill {{ text-decoration: none; background: var(--surface); color: var(--text); border: 2px solid color-mix(in srgb, var(--primary) 24%, white); padding: 0.55rem 1rem; }}
    .content {{ display: grid; gap: 1.1rem; }}
    .unit-card {{ background: var(--surface); border: 2px solid color-mix(in srgb, var(--primary) 35%, white); border-radius: 24px; padding: 1.15rem; box-shadow: var(--shadow); }}
    .unit-head {{ display: flex; gap: 1rem; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }}
    .unit-head h2 {{ margin: 0.2rem 0 0; font-size: clamp(1.45rem, 4vw, 2.1rem); font-weight: 800; }}
    .unit-kicker {{ color: color-mix(in srgb, var(--primary) 80%, black); font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; font-size: 0.9rem; }}
    .unit-badge {{ background: color-mix(in srgb, var(--accent) 22%, var(--surface)); border: 2px solid var(--accent); border-radius: 9999px; padding: 0.65rem 1rem; font-weight: 800; min-height: var(--touch-size); display: inline-flex; align-items: center; }}
    .unit-grid {{ display: grid; gap: 1rem; grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.95fr); margin-top: 1rem; }}
    .unit-copy p {{ margin: 0.65rem 0; }}
    .unit-flow {{ display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 1rem; }}
    .unit-flow > div, .play-card, .maker-box, .teacher-card {{ background: color-mix(in srgb, var(--bg) 70%, white); border-radius: 18px; padding: 0.95rem; border: 2px solid color-mix(in srgb, var(--primary) 18%, white); }}
    .play-label {{ font-weight: 800; margin: 0 0 0.8rem; }}
    .pill-btn, .choice-btn, .check-card, .prompt-card {{
      min-height: var(--touch-size);
      min-width: var(--touch-size);
      border-radius: 9999px;
      border: 2px solid transparent;
      padding: 0.75rem 1.2rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
    }}
    .pill-btn:hover, .choice-btn:hover, .check-card:hover, .prompt-card:hover, .page-link:hover {{ transform: scale(1.05); box-shadow: 0 10px 24px rgba(0,0,0,0.12); }}
    .pill-btn:active, .choice-btn:active, .check-card:active, .prompt-card:active, .page-link:active {{ transform: scale(0.97); }}
    .pill-btn {{ background: var(--primary); color: white; }}
    .choice-row, .check-grid, .prompt-grid, .compose-actions {{ display: flex; gap: 0.75rem; flex-wrap: wrap; }}
    .choice-btn, .check-card, .prompt-card {{ background: var(--surface); color: var(--text); border-color: color-mix(in srgb, var(--primary) 22%, white); }}
    .choice-btn.is-right, .check-card.is-done {{ background: var(--correct-bg); border-color: var(--correct); color: #166534; }}
    .choice-btn.is-wrong {{ background: var(--incorrect-bg); border-color: var(--incorrect); color: #92400e; }}
    .feedback, .helper-text {{ margin: 0.85rem 0 0; font-weight: 700; }}
    .feedback {{ min-height: 1.4em; }}
    .compose-output, .phrase-card, .cloze-word {{ min-height: 72px; border-radius: 18px; background: var(--surface); border: 2px dashed color-mix(in srgb, var(--primary) 35%, white); display: grid; place-items: center; font-size: clamp(1.8rem, 5vw, 2.6rem); font-weight: 800; color: var(--primary); padding: 0.9rem; margin-top: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    .phrase-card {{ text-transform: none; font-size: 1.3rem; color: var(--text); }}
    .phrase-input {{ width: 100%; margin-top: 0.85rem; border-radius: 18px; border: 2px solid color-mix(in srgb, var(--primary) 25%, white); padding: 0.9rem 1rem; min-height: 120px; background: #fff; }}
    .diff-switcher {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }}
    .diff-btn {{ min-height: var(--touch-size); min-width: var(--touch-size); border-radius: 9999px; border: 2px solid color-mix(in srgb, var(--primary) 28%, white); background: var(--surface); padding: 0.7rem 1rem; font-weight: 700; cursor: pointer; }}
    .diff-btn.is-active {{ background: color-mix(in srgb, var(--accent) 20%, var(--surface)); border-color: var(--accent); }}
    .diff-panel {{ display: none; background: color-mix(in srgb, var(--bg) 72%, white); border-radius: 18px; padding: 0.95rem; margin-top: 0.8rem; border: 2px solid color-mix(in srgb, var(--primary) 18%, white); }}
    .diff-panel.is-active {{ display: block; }}
    .teacher-guide {{ background: var(--surface); border: 2px solid color-mix(in srgb, var(--primary) 30%, white); border-radius: 24px; padding: 0.9rem 1rem; box-shadow: var(--shadow); }}
    .teacher-guide summary {{ min-height: var(--touch-size); display: flex; align-items: center; cursor: pointer; font-weight: 800; font-size: 1.2rem; }}
    .teacher-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); padding-top: 1rem; }}
    .teacher-card-wide {{ grid-column: 1 / -1; }}
    .teacher-card h3 {{ margin-top: 0; }}
    .footer {{ text-align: center; padding: 1.4rem 0 0; font-weight: 700; color: color-mix(in srgb, var(--text) 72%, white); }}
    .hidden {{ display: none !important; }}
    @media (max-width: 900px) {{
      .hero-grid, .word-spotlight, .unit-grid, .unit-flow, .teacher-grid {{ grid-template-columns: 1fr; }}
      .section-nav {{ position: static; }}
    }}
    @media (max-width: 640px) {{
      body {{ font-size: 18px; }}
      .shell {{ padding: 0.75rem 0.75rem 2.4rem; }}
      .hero {{ padding: 1rem; border-radius: 22px; }}
      .hero-copy h1 {{ font-size: clamp(2rem, 9vw, 3rem); }}
      .page-link {{ flex-basis: 100%; }}
      .objective-row li, .meta-chip, .hero-kicker, .hero-badge, .nav-pill {{ width: 100%; justify-content: center; }}
      .unit-card, .spot-card, .teacher-guide {{ border-radius: 20px; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{ animation: none !important; transition: none !important; }}
    }}
  </style>
</head>
<body data-page-variant=\"{esc(variant["filename"])}\" data-visible-units=\"{esc(",".join(str(i) for i in visible_units))}\">
  <a href="#main" class="skip-link">Ir para o conteúdo</a>
  <div class="shell">
    <header class="hero">
      <div class="hero-top">
        <span class="hero-kicker">M28P #{order}</span>
        <span class="hero-badge">{esc(variant["badge"])}</span>
      </div>
      <div class="hero-grid">
        <div class="hero-copy">
          <p>{esc(variant["heroTitle"])}</p>
          <h1>{esc(word)}</h1>
          <p>{esc(variant["heroNote"])}</p>
          <div class="meta-row">
            <span class="meta-chip">{emoji} Palavra {order}</span>
            <span class="meta-chip">{esc(meta["year"])}</span>
            <span class="meta-chip">{esc(str(meta["duration"]))} min</span>
          </div>
          <ul class="objective-row">{objective_chips}</ul>
        </div>
        <aside class="word-scene" aria-hidden="true">
          <div class="emoji">{emoji}</div>
          <p><strong>{esc(variant["mission"])}</strong></p>
          <p>Paleta própria, leitura em pt-PT AO90 e navegação pensada para toque.</p>
          <p>Esta página trabalha as unidades {esc(", ".join(str(i) for i in visible_units))}.</p>
        </aside>
      </div>
    </header>

    <div class="page-switch" aria-label="Outras páginas desta palavra">{page_nav}</div>

    <section class="word-spotlight" aria-label="Destaque da palavra">
      <article class="spot-card">
        <h2>Palavra em destaque</h2>
        <div class="word-display">{esc(word)}</div>
        <p class="mission">{esc(phrase)}</p>
        <div class="compose-actions">
          <button class="pill-btn speak-btn" data-speak="{esc(word)}">Ouvir a palavra</button>
        </div>
      </article>
      <article class="spot-card">
        <h2>Sílabas</h2>
        <div class="syllable-row">{"".join(f'<span class="syllable-token" style="--chip:{esc(color)}">{esc(syllable)}</span>' for syllable, color in syllables)}</div>
        <p class="mission">{esc(variant["mission"])}</p>
      </article>
    </section>

    <nav class="section-nav" aria-label="Navegação das unidades">{section_nav}</nav>

    <main id="main" class="content">
      {units_html}
      {teacher_guide}
    </main>

    <footer class="footer">PageCraft · Método das 28 Palavras · {esc(word)}</footer>
  </div>

  <script>
    const synth = window.speechSynthesis;

    document.querySelectorAll('.reveal-btn').forEach((button) => {{
      button.addEventListener('click', () => {{
        const target = document.getElementById(button.dataset.target);
        if (!target) return;
        target.classList.toggle('hidden');
      }});
    }});

    document.querySelectorAll('.speak-btn').forEach((button) => {{
      button.addEventListener('click', () => {{
        if (!synth) return;
        const utterance = new SpeechSynthesisUtterance(button.dataset.speak || '');
        utterance.lang = 'pt-PT';
        synth.cancel();
        synth.speak(utterance);
      }});
    }});

    document.querySelectorAll('.choice-row').forEach((row) => {{
      const feedback = row.parentElement.querySelector('.feedback');
      row.querySelectorAll('.choice-btn').forEach((button) => {{
        button.addEventListener('click', () => {{
          row.querySelectorAll('.choice-btn').forEach((item) => item.classList.remove('is-right', 'is-wrong'));
          const rightAnswer = button.dataset.answer || button.dataset.clozeAnswer || '';
          if (button.dataset.choice === rightAnswer) {{
            button.classList.add('is-right');
            if (feedback) feedback.textContent = 'Muito bem!';
          }} else {{
            button.classList.add('is-wrong');
            if (feedback) feedback.textContent = 'Tenta outra vez.';
          }}
        }});
      }});
    }});

    document.querySelectorAll('[data-compose]').forEach((bank) => {{
      const output = document.getElementById(bank.dataset.compose);
      const parts = [];
      bank.querySelectorAll('.syllable-chip').forEach((chip) => {{
        chip.addEventListener('click', () => {{
          parts.push(chip.dataset.syllable || '');
          if (output) output.textContent = parts.join('');
        }});
      }});
    }});

    document.querySelectorAll('.clear-compose').forEach((button) => {{
      button.addEventListener('click', () => {{
        const output = document.getElementById(button.dataset.composeClear);
        if (output) output.textContent = '__';
      }});
    }});

    document.querySelectorAll('.check-card').forEach((card) => {{
      card.addEventListener('click', () => card.classList.toggle('is-done'));
    }});

    document.querySelectorAll('.diff-switcher').forEach((switcher) => {{
      const panels = switcher.nextElementSibling;
      switcher.querySelectorAll('.diff-btn').forEach((button) => {{
        button.addEventListener('click', () => {{
          switcher.querySelectorAll('.diff-btn').forEach((item) => item.classList.remove('is-active'));
          panels.querySelectorAll('.diff-panel').forEach((panel) => panel.classList.remove('is-active'));
          button.classList.add('is-active');
          const target = panels.querySelector('#' + CSS.escape(button.dataset.diff));
          if (target) target.classList.add('is-active');
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def load_variants() -> list[dict]:
    return read_json(VARIANTS_PATH)


def ordered_m28p_dirs() -> list[Path]:
    items = []
    for meta_path in ACTIVITIES_DIR.glob("*/meta.json"):
        meta = read_json(meta_path)
        if isinstance(meta.get("order"), int) and 1 <= meta["order"] <= 28:
            items.append((meta["order"], meta_path.parent))
    items.sort(key=lambda item: item[0])
    return [path for _, path in items]


def main() -> None:
    ordered_dirs = ordered_m28p_dirs()
    if len(ordered_dirs) != 28:
        raise SystemExit(f"Expected 28 M28P folders, found {len(ordered_dirs)}")

    global VARIANTS
    VARIANTS = load_variants()
    words = []
    metas = []
    docspecs = []
    designs = []
    for activity_dir in ordered_dirs:
        meta = read_json(activity_dir / "meta.json")
        docspec = read_json(activity_dir / "docspec.json")
        design = read_json(activity_dir / "design-spec.json")
        metas.append(meta)
        docspecs.append(docspec)
        designs.append(design)
        words.append(slug_to_word(meta["title"]))

    for index, activity_dir in enumerate(ordered_dirs):
        meta = metas[index]
        docspec = docspecs[index]
        design = designs[index]
        for variant in VARIANTS:
            html_doc = build_page(
                activity_dir, meta, docspec, design, variant, words, index
            )
            (activity_dir / variant["filename"]).write_text(html_doc, encoding="utf-8")
        print(f"Generated 4 pages for {meta['slug']}")


if __name__ == "__main__":
    main()
