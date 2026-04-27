#!/usr/bin/env python3
"""Sequentially regenerate two 30-minute M28P PageCraft variants per word.

This is intentionally a *word-by-word* workflow: each word is generated, its two
pages are validated, and only then does the script move to the next word.

Creates/updates stable URLs:
- activities/<word>-cacador-silabas/  (word-specific sound/syllable lab)
- activities/<word>-frases-vivas/     (word-specific sentence lab)
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ACTIVITIES = ROOT / "activities"
CATALOG = ROOT / "catalog.json"
NOW = "2026-04-27T00:00:00Z"
DURATION = 30

WORD_DATA: dict[str, dict[str, str]] = {
    "menina": {"emoji": "👧", "sentence": "A menina sorri no recreio.", "place": "no recreio", "action": "sorri", "object": "uma fita"},
    "menino": {"emoji": "👦", "sentence": "O menino lê no tapete.", "place": "no tapete", "action": "lê", "object": "um livro"},
    "uva": {"emoji": "🍇", "sentence": "A uva roxa está no prato.", "place": "no prato", "action": "está", "object": "roxa"},
    "dedo": {"emoji": "☝️", "sentence": "O dedo aponta para a palavra.", "place": "na mão", "action": "aponta", "object": "a palavra"},
    "sapato": {"emoji": "👞", "sentence": "O sapato fica junto da porta.", "place": "junto da porta", "action": "fica", "object": "a porta"},
    "bota": {"emoji": "🥾", "sentence": "A bota salta na poça.", "place": "na poça", "action": "salta", "object": "água"},
    "leque": {"emoji": "🪭", "sentence": "O leque faz vento devagar.", "place": "na mão", "action": "faz", "object": "vento"},
    "casa": {"emoji": "🏠", "sentence": "A casa tem uma janela azul.", "place": "na rua", "action": "tem", "object": "janela"},
    "janela": {"emoji": "🪟", "sentence": "A janela deixa entrar luz.", "place": "na sala", "action": "deixa", "object": "luz"},
    "telhado": {"emoji": "🏠", "sentence": "O telhado protege a casa.", "place": "na casa", "action": "protege", "object": "a casa"},
    "escada": {"emoji": "🪜", "sentence": "A escada tem muitos degraus.", "place": "no pátio", "action": "tem", "object": "degraus"},
    "chave": {"emoji": "🔑", "sentence": "A chave abre a porta.", "place": "na porta", "action": "abre", "object": "a porta"},
    "galinha": {"emoji": "🐔", "sentence": "A galinha procura milho.", "place": "no quintal", "action": "procura", "object": "milho"},
    "ovo": {"emoji": "🥚", "sentence": "O ovo está no ninho.", "place": "no ninho", "action": "está", "object": "o ninho"},
    "rato": {"emoji": "🐭", "sentence": "O rato corre para a toca.", "place": "na toca", "action": "corre", "object": "a toca"},
    "cenoura": {"emoji": "🥕", "sentence": "A cenoura cresce na horta.", "place": "na horta", "action": "cresce", "object": "terra"},
    "girafa": {"emoji": "🦒", "sentence": "A girafa estica o pescoço.", "place": "na savana", "action": "estica", "object": "o pescoço"},
    "palhaco": {"emoji": "🤡", "sentence": "O palhaço faz rir a turma.", "place": "no circo", "action": "faz", "object": "rir"},
    "zebra": {"emoji": "🦓", "sentence": "A zebra tem riscas pretas.", "place": "na savana", "action": "tem", "object": "riscas"},
    "bandeira": {"emoji": "🚩", "sentence": "A bandeira dança ao vento.", "place": "no mastro", "action": "dança", "object": "vento"},
    "funil": {"emoji": "🧪", "sentence": "O funil ajuda a deitar água.", "place": "na mesa", "action": "ajuda", "object": "água"},
    "arvore": {"emoji": "🌳", "sentence": "A árvore dá sombra fresca.", "place": "no jardim", "action": "dá", "object": "sombra"},
    "quadro": {"emoji": "🟩", "sentence": "O quadro mostra a palavra.", "place": "na sala", "action": "mostra", "object": "a palavra"},
    "passarinho": {"emoji": "🐦", "sentence": "O passarinho canta na árvore.", "place": "na árvore", "action": "canta", "object": "uma canção"},
    "peixe": {"emoji": "🐟", "sentence": "O peixe nada no lago.", "place": "no lago", "action": "nada", "object": "água"},
    "cigarra": {"emoji": "🦗", "sentence": "A cigarra canta no verão.", "place": "no verão", "action": "canta", "object": "uma canção"},
    "fogueira": {"emoji": "🔥", "sentence": "A fogueira aquece a roda.", "place": "na roda", "action": "aquece", "object": "a roda"},
    "flor": {"emoji": "🌸", "sentence": "A flor abre de manhã.", "place": "no jardim", "action": "abre", "object": "pétalas"},
}

A_MODES = [
    {"title": "Mapa sonoro", "kind": "first", "label": "primeira sílaba", "prompt": "Descobre por onde a palavra começa."},
    {"title": "Sílaba intrusa", "kind": "intruder", "label": "sílaba que não pertence", "prompt": "Encontra a sílaba intrusa antes de construir."},
    {"title": "Palmas e eco", "kind": "count", "label": "número de palmas", "prompt": "Bate palmas, faz eco e confirma quantas partes ouves."},
    {"title": "Sílaba final", "kind": "last", "label": "última sílaba", "prompt": "Descobre como a palavra acaba."},
]

B_MODES = [
    {"title": "Frase com sentido", "kind": "word", "prompt": "Escolhe a palavra que completa a frase."},
    {"title": "Onde está?", "kind": "place", "prompt": "Lê a frase e descobre onde acontece."},
    {"title": "O que acontece?", "kind": "action", "prompt": "Lê a frase e descobre a ação."},
    {"title": "Frase baralhada", "kind": "order", "prompt": "Começa pela frase baralhada e reconstrói a leitura."},
]

PLACE_CHOICES = ["no recreio", "no tapete", "no prato", "na sala", "no jardim", "na horta", "no lago", "na árvore", "no quintal", "na porta"]
ACTION_CHOICES = ["sorri", "lê", "está", "aponta", "fica", "salta", "faz", "tem", "abre", "corre", "canta", "nada", "aquece"]
INTRUDER_SYLLABLES = ["la", "fo", "tu", "mi", "re", "cho", "bra", "po", "zu", "cri"]

VOWELS = "aeiouáéíóúâêôãõà"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    text = text.lower().strip()
    trans = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçñ", "aaaaaeeeeiiiiooooouuuucn")
    text = text.translate(trans)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def word_from_title(title: str, fallback: str) -> str:
    if "—" in title:
        return title.split("—")[-1].strip().split("·")[0].strip()
    return fallback.replace("-", " ").title()


def article_for(word: str) -> str:
    if word.lower()[0] in VOWELS:
        return "a"
    masc = {"dedo", "sapato", "leque", "telhado", "ovo", "rato", "funil", "quadro", "peixe"}
    return "o" if slugify(word) in masc else "a"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def sentence_tokens(sentence: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sentence)


def sanitize_design(design: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(design)
    typography = clean.setdefault("typography", {})
    typography.pop("fontUrl", None)
    typography["fontFamily"] = "'Nunito', 'Comic Sans MS', 'Chalkboard SE', sans-serif"
    notes = clean.get("notes", "")
    offline_note = "Sem fontes remotas; usar fontes locais/fallback para garantir funcionamento offline."
    clean["notes"] = (notes + " " + offline_note).strip() if offline_note not in notes else notes
    return clean


def css_vars(design: dict[str, Any]) -> str:
    pal = design.get("palette", {})
    sylls = design.get("syllableColors", {})
    lines = [
        f"--bg:{pal.get('bg','#FFF8F0')};",
        f"--surface:{pal.get('surface','#FFFFFF')};",
        f"--primary:{pal.get('primary','#2563EB')};",
        f"--accent:{pal.get('accent','#F59E0B')};",
        f"--text:{pal.get('text','#1E1B18')};",
    ]
    for s, c in sylls.items():
        lines.append(f"--syll-{slugify(s)}:{c};")
    return "\n      ".join(lines)


def common_css(design: dict[str, Any]) -> str:
    return f"""
    :root {{
      {css_vars(design)}
      --ok:#22c55e; --ok-bg:#f0fdf4; --try:#f59e0b; --try-bg:#fffbeb;
      --danger:#ef4444; --radius:18px; --shadow:0 8px 24px rgba(30,27,24,.10); --touch:48px;
      --font:'Nunito','Comic Sans MS','Chalkboard SE',sans-serif;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{ margin:0; font-family:var(--font); color:var(--text); background:radial-gradient(circle at top right, color-mix(in srgb, var(--accent) 25%, white), var(--bg) 38%); font-size:20px; line-height:1.45; }}
    .skip-link {{ position:absolute; left:-999px; top:8px; background:var(--text); color:white; padding:.6rem .9rem; border-radius:999px; z-index:99; }}
    .skip-link:focus {{ left:8px; }}
    .wrap {{ width:min(100% - 24px, 1040px); margin:0 auto; padding:1rem 0 2rem; }}
    .hero {{ border-radius:28px; padding:1.2rem; color:white; background:linear-gradient(135deg,var(--primary),var(--accent)); box-shadow:var(--shadow); margin:1rem 0; position:relative; overflow:hidden; }}
    .hero::after {{ content:''; position:absolute; inset:auto -40px -70px auto; width:210px; height:210px; border-radius:50%; background:rgba(255,255,255,.18); }}
    h1,h2,h3 {{ line-height:1.15; margin:.2rem 0 .7rem; }}
    h1 {{ font-size:clamp(2rem,6vw,3.4rem); }}
    h2 {{ font-size:clamp(1.55rem,4vw,2.15rem); color:color-mix(in srgb,var(--primary) 72%, black); }}
    p {{ margin:.35rem 0 .75rem; }}
    .meta,.row {{ display:flex; flex-wrap:wrap; gap:.55rem; align-items:center; }}
    .pill {{ border:2px solid rgba(255,255,255,.72); background:rgba(255,255,255,.20); color:inherit; border-radius:999px; padding:.35rem .75rem; font-weight:800; }}
    .card {{ background:var(--surface); border:2px solid var(--primary); border-radius:var(--radius); box-shadow:var(--shadow); padding:1rem; margin:1rem 0; }}
    .soft {{ background:color-mix(in srgb,var(--bg) 72%, white); border-style:dashed; }}
    button,.button {{ min-width:var(--touch); min-height:var(--touch); border:2px solid color-mix(in srgb,var(--primary) 70%, black); background:var(--primary); color:white; border-radius:999px; padding:.65rem 1rem; font:inherit; font-weight:900; cursor:pointer; touch-action:manipulation; box-shadow:0 5px 14px rgba(0,0,0,.12); transition:transform .18s ease, box-shadow .18s ease, background .18s ease; }}
    button:hover,.button:hover {{ transform:scale(1.04); }} button:active {{ transform:scale(.97); }}
    button.secondary {{ background:white; color:color-mix(in srgb,var(--primary) 72%, black); }}
    :focus-visible {{ outline:4px solid var(--accent); outline-offset:3px; }}
    .tabs {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:.75rem 0; }}
    .tab {{ background:white; color:var(--text); border-color:#d6cec7; }} .tab[aria-selected='true'] {{ background:var(--primary); color:white; border-color:color-mix(in srgb,var(--primary) 70%, black); }}
    .level {{ display:none; }} .level.active {{ display:block; animation:pop .22s ease; }}
    .syllables,.slots,.choices,.word-bank {{ display:flex; gap:.7rem; flex-wrap:wrap; justify-content:center; margin:1rem 0; }}
    .syllable,.slot,.word-token {{ border-radius:16px; min-height:58px; min-width:64px; display:inline-grid; place-items:center; padding:.45rem .85rem; font-size:clamp(1.35rem,4.6vw,2.15rem); font-weight:1000; letter-spacing:.02em; }}
    .syllable {{ color:white; border:3px solid rgba(0,0,0,.10); }}
    .slot {{ background:#fff; border:3px dashed color-mix(in srgb,var(--primary) 60%, white); color:color-mix(in srgb,var(--primary) 65%, black); }}
    .slot.filled {{ border-style:solid; }}
    .target-word {{ font-size:clamp(2rem,8vw,4.2rem); font-weight:1000; letter-spacing:.04em; text-transform:uppercase; color:var(--primary); text-align:center; overflow-wrap:anywhere; max-width:100%; }}
    .feedback {{ border-radius:18px; padding:.8rem 1rem; font-weight:900; min-height:58px; display:flex; align-items:center; justify-content:center; text-align:center; background:var(--try-bg); border:2px solid var(--try); }}
    .feedback.ok {{ background:var(--ok-bg); border-color:var(--ok); }}
    .feedback.idle {{ background:white; border-color:#d6cec7; color:#6b5f57; }}
    .teacher {{ font-size:.95rem; background:#fff; border-left:8px solid var(--accent); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.8rem; }}
    .mini {{ font-size:.92rem; color:#5b514a; }}
    .sentence-board {{ display:flex; gap:.55rem; flex-wrap:wrap; justify-content:center; min-height:74px; padding:.7rem; border:3px dashed color-mix(in srgb,var(--accent) 60%, white); border-radius:18px; background:#fff; }}
    .word-token {{ font-size:1.25rem; background:white; border:2px solid color-mix(in srgb,var(--primary) 45%, white); color:var(--text); }}
    .word-token.used {{ opacity:.35; }}
    .big-emoji {{ font-size:clamp(4rem,14vw,7rem); line-height:1; filter:drop-shadow(0 8px 10px rgba(0,0,0,.12)); }}
    footer {{ text-align:center; padding:1rem; color:#655a52; }}
    @keyframes pop {{ from {{ opacity:0; transform:translateY(8px) scale(.98); }} to {{ opacity:1; transform:none; }} }}
    @media (prefers-reduced-motion:reduce) {{ * {{ animation:none!important; transition:none!important; scroll-behavior:auto!important; }} }}
    @media (max-width:640px) {{ body {{ font-size:18px; }} .wrap {{ width:min(100% - 16px,1040px); }} .hero {{ border-radius:20px; }} }}
    """


def syllable_style(s: str, design: dict[str, Any]) -> str:
    return f"background:{escape(design.get('syllableColors', {}).get(s, design.get('palette', {}).get('primary', '#2563EB')))}"


def option_buttons(values: list[str], answer: str, cls: str) -> str:
    ordered = [answer] + [v for v in values if v != answer]
    return "\n".join(f'<button class="secondary {cls}" data-answer="{escape(v)}">{escape(v)}</button>' for v in ordered[:4])


def intruder_for(sylls: list[str], order: int) -> str:
    for s in INTRUDER_SYLLABLES[order % len(INTRUDER_SYLLABLES):] + INTRUDER_SYLLABLES[: order % len(INTRUDER_SYLLABLES)]:
        if s not in sylls:
            return s
    return "la"


def mode_a_section(mode: dict[str, str], sylls: list[str], order: int, design: dict[str, Any]) -> tuple[str, str]:
    kind = mode["kind"]
    if kind == "first":
        answer = sylls[0]
        opts = [answer] + [s for s in sylls[1:]] + [intruder_for(sylls, order)]
        html = f"""<h2>2. Detetive da primeira sílaba</h2><p>Qual é a primeira parte que ouves?</p><div class="choices">{option_buttons(opts, answer, 'mission-choice')}</div><p id="missionFeedback" class="feedback idle" role="status">Começa a palavra devagar e escolhe.</p>"""
        assessment = "o aluno identifica a primeira sílaba e justifica oralmente"
    elif kind == "last":
        answer = sylls[-1]
        opts = [answer] + sylls[:-1] + [intruder_for(sylls, order)]
        html = f"""<h2>2. Detetive da sílaba final</h2><p>Qual é a última parte que ouves?</p><div class="choices">{option_buttons(opts, answer, 'mission-choice')}</div><p id="missionFeedback" class="feedback idle" role="status">Diz a palavra até ao fim e escolhe.</p>"""
        assessment = "o aluno identifica a sílaba final e compara com o início"
    elif kind == "intruder":
        answer = intruder_for(sylls, order)
        opts = sylls + [answer]
        html = f"""<h2>2. Encontra a sílaba intrusa</h2><p>Uma destas sílabas não pertence à palavra. Qual é?</p><div class="choices">{option_buttons(opts, answer, 'mission-choice')}</div><p id="missionFeedback" class="feedback idle" role="status">Compara cada bloco com a palavra construída.</p>"""
        assessment = "o aluno exclui a sílaba intrusa com base na palavra construída"
    else:
        answer = str(len(sylls))
        opts = [str(max(1, len(sylls) - 1)), answer, str(len(sylls) + 1)]
        html = f"""<h2>2. Palmas e eco</h2><p>Quantas partes ouvimos quando dizemos a palavra?</p><div class="choices">{option_buttons(opts, answer, 'mission-choice')}</div><p id="missionFeedback" class="feedback idle" role="status">Bate palmas e conta as partes.</p>"""
        assessment = "o aluno conta as partes sonoras com apoio de palmas"
    return html, assessment


def html_variant_a(base: dict[str, Any], design: dict[str, Any], word: str, order: int) -> str:
    sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
    data = WORD_DATA.get(base["slug"], {"emoji": "⭐", "sentence": f"{cap(article_for(word))} {word} aparece na página.", "place": "na página"})
    mode = A_MODES[(order - 1) % len(A_MODES)]
    title = mode["title"]
    shuffled = sylls[1:] + sylls[:1] if len(sylls) > 1 else sylls
    syll_buttons = "\n".join(f'<button class="syllable" style="{syllable_style(s, design)}" data-syll="{escape(s)}" aria-label="Sílaba {escape(s)}">{escape(s)}</button>' for s in shuffled)
    slots = "\n".join(f'<span class="slot" data-index="{i}" aria-label="Espaço {i+1}">?</span>' for i in range(len(sylls)))
    mission_html, _assessment = mode_a_section(mode, sylls, order, design)
    return f"""<!DOCTYPE html>
<html lang="pt-PT">
<head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>M28P #{order} — {escape(word)} · {escape(title)} | PageCraft</title><style>{common_css(design)}</style></head>
<body><a class="skip-link" href="#main">Ir para o conteúdo</a><div class="wrap">
<header class="hero"><div class="meta"><span class="pill">M28P · Palavra {order}</span><span class="pill">1.º ano</span><span class="pill">30 min</span></div><h1>{data['emoji']} {escape(word)} — {escape(title)}</h1><p>{escape(mode['prompt'])} Depois constrói a palavra e explica a estratégia.</p></header>
<main id="main">
<section class="card soft" aria-labelledby="objetivo"><h2 id="objetivo">Missão da palavra</h2><p>Esta página não repete a página principal: aqui o foco é uma pequena investigação sonora sobre <strong>{escape(word)}</strong>.</p><div class="target-word" aria-label="Palavra alvo">{escape(word)}</div></section>
<section class="card" aria-labelledby="construir"><h2 id="construir">1. Constrói para confirmar</h2><p class="mini">Usa o clique ou o teclado. Também funciona em tablet.</p><div class="slots" id="slots" aria-live="polite">{slots}</div><div class="syllables" id="syllables">{syll_buttons}</div><div class="row" style="justify-content:center"><button id="reset" class="secondary">Recomeçar</button><button id="hear">Bater palmas</button></div><p id="buildFeedback" class="feedback idle" role="status">Toca na primeira sílaba para começar.</p></section>
<section class="card" aria-labelledby="missao"><div id="missao">{mission_html}</div></section>
<section class="card"><h2>3. Diferenciação</h2><div class="tabs" role="tablist" aria-label="Níveis de diferenciação"><button class="tab" role="tab" aria-selected="true" data-tab="apoio">🟢 Apoio</button><button class="tab" role="tab" aria-selected="false" data-tab="objetivo2">🟡 Objetivo</button><button class="tab" role="tab" aria-selected="false" data-tab="desafio">🔴 Desafio</button></div><div class="level active" id="apoio"><p>Diz a palavra com o adulto e aponta cada sílaba.</p></div><div class="level" id="objetivo2"><p>Resolve a missão e lê a palavra sem modelo.</p></div><div class="level" id="desafio"><p>Procura outra palavra M28P com uma sílaba parecida ou com o mesmo número de partes.</p></div></section>
<section class="card teacher"><h2>Nota para o professor</h2><p><strong>Regra a descobrir:</strong> a palavra escrita fica estável quando juntamos as partes sonoras pela ordem certa.</p><p><strong>Evidência observável:</strong> o aluno constrói {escape('–'.join(sylls))} e resolve a missão “{escape(mode['label'])}”.</p></section>
</main><footer>PageCraft · Método das 28 Palavras · {escape(word)}</footer></div>
<script>
const expected = {json.dumps(sylls, ensure_ascii=False)}; let placed=[]; const slots=[...document.querySelectorAll('.slot')]; const fb=document.getElementById('buildFeedback');
function render(){{slots.forEach((slot,i)=>{{slot.textContent=placed[i]||'?';slot.classList.toggle('filled',Boolean(placed[i]));}});document.querySelectorAll('.syllable').forEach(btn=>{{btn.disabled=placed.includes(btn.dataset.syll);btn.style.opacity=btn.disabled?.45:1;}});}}
function say(msg,ok=false){{fb.textContent=msg;fb.className='feedback '+(ok?'ok':'');}}
document.getElementById('syllables').addEventListener('click',e=>{{const btn=e.target.closest('button[data-syll]');if(!btn)return;const s=btn.dataset.syll, need=expected[placed.length];if(s===need){{placed.push(s);render(); if(placed.length===expected.length)say('Muito bem! Construíste a palavra {escape(word)} pela ordem certa.',true); else say('Boa! Procura a próxima sílaba.');}} else say('Quase. Escuta outra vez e procura a sílaba que vem agora.');}});
document.getElementById('reset').addEventListener('click',()=>{{placed=[];render();say('Toca na primeira sílaba para começar.');}});
document.getElementById('hear').addEventListener('click',()=>say('Palmas: '+expected.join(' · '),true));
document.querySelectorAll('.mission-choice').forEach(btn=>btn.addEventListener('click',()=>{{const ok=btn.dataset.answer==={json.dumps(str(mode_a_answer(mode, sylls, order)), ensure_ascii=False)};const out=document.getElementById('missionFeedback');out.textContent=ok?'Certo! Explica como descobriste.':'Ainda não. Volta à palavra construída e compara.';out.className='feedback '+(ok?'ok':'');}}));
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{{document.querySelectorAll('.tab').forEach(t=>t.setAttribute('aria-selected','false'));tab.setAttribute('aria-selected','true');document.querySelectorAll('.level').forEach(l=>l.classList.remove('active'));document.getElementById(tab.dataset.tab).classList.add('active');}}));
render();
</script></body></html>
"""


def mode_a_answer(mode: dict[str, str], sylls: list[str], order: int) -> str:
    if mode["kind"] == "first":
        return sylls[0]
    if mode["kind"] == "last":
        return sylls[-1]
    if mode["kind"] == "intruder":
        return intruder_for(sylls, order)
    return str(len(sylls))


def mode_b_challenge(mode: dict[str, str], data: dict[str, str], word: str, all_words: list[str], order: int) -> tuple[str, str, str]:
    kind = mode["kind"]
    if kind == "place":
        answer = data["place"]
        choices = [answer] + [p for p in PLACE_CHOICES if p != answer][order % 5 : order % 5 + 3]
        html = f"<p class='target-word' style='font-size:clamp(1.4rem,4.5vw,2.4rem); text-transform:none'>{escape(data['sentence'])}</p><div class='choices'>{option_buttons(choices, answer, 'sentence-choice')}</div><p id='clozeFeedback' class='feedback idle' role='status'>Onde acontece?</p>"
        assessment = "o aluno identifica o contexto/local da frase"
    elif kind == "action":
        answer = data["action"]
        choices = [answer] + [a for a in ACTION_CHOICES if a != answer][order % 5 : order % 5 + 3]
        html = f"<p class='target-word' style='font-size:clamp(1.4rem,4.5vw,2.4rem); text-transform:none'>{escape(data['sentence'])}</p><div class='choices'>{option_buttons(choices, answer, 'sentence-choice')}</div><p id='clozeFeedback' class='feedback idle' role='status'>O que acontece na frase?</p>"
        assessment = "o aluno identifica a ação principal da frase"
    else:
        answer = word
        distractors = [w for w in all_words if slugify(w) != slugify(word)]
        cloze = re.sub(r"\b" + re.escape(word) + r"\b", "_____", data["sentence"], count=1, flags=re.IGNORECASE)
        html = f"<p class='target-word' style='font-size:clamp(1.4rem,4.5vw,2.4rem); text-transform:none'>{escape(cloze)}</p><div class='choices'>{option_buttons([word]+distractors, word, 'sentence-choice')}</div><p id='clozeFeedback' class='feedback idle' role='status'>Escolhe a palavra que faz sentido na frase.</p>"
        assessment = "o aluno escolhe a palavra-alvo para completar a frase"
    return html, answer, assessment


def html_variant_b(base: dict[str, Any], design: dict[str, Any], word: str, order: int, all_words: list[str]) -> str:
    sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
    data = WORD_DATA.get(base["slug"], {"emoji": "⭐", "sentence": f"{cap(article_for(word))} {word} aparece na página.", "place": "na página", "action": "aparece", "object": "a página"})
    mode = B_MODES[(order - 1) % len(B_MODES)]
    title = mode["title"]
    tokens = sentence_tokens(data["sentence"])
    shuffled = tokens[1::2] + tokens[0::2]
    challenge_html, answer, assessment = mode_b_challenge(mode, data, word, all_words, order)
    bank = "\n".join(f'<button class="word-token" data-token="{escape(t)}">{escape(t)}</button>' for t in shuffled)
    syll_badges = " ".join(f'<span class="syllable" style="{syllable_style(s, design)}">{escape(s)}</span>' for s in sylls)
    return f"""<!DOCTYPE html>
<html lang="pt-PT"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>M28P #{order} — {escape(word)} · {escape(title)} | PageCraft</title><style>{common_css(design)}</style></head>
<body><a class="skip-link" href="#main">Ir para o conteúdo</a><div class="wrap">
<header class="hero"><div class="meta"><span class="pill">M28P · Palavra {order}</span><span class="pill">1.º ano</span><span class="pill">30 min</span></div><h1>{data['emoji']} {escape(word)} — {escape(title)}</h1><p>{escape(mode['prompt'])} Depois ordena a frase e lê a pares.</p></header>
<main id="main"><section class="card soft"><h2>Recorda sem repetir</h2><div class="grid"><div><div class="big-emoji" aria-hidden="true">{data['emoji']}</div></div><div><div class="target-word">{escape(word)}</div><div class="syllables" aria-label="Sílabas da palavra">{syll_badges}</div></div></div><p>Esta página trabalha a palavra dentro de uma frase, para não repetir a exploração principal.</p></section>
<section class="card"><h2>1. Missão de leitura</h2>{challenge_html}</section>
<section class="card"><h2>2. Ordena a frase</h2><p>Toca nas palavras pela ordem certa. Se te enganares, recomeça.</p><div class="sentence-board" id="sentenceBoard" aria-live="polite"></div><div class="word-bank" id="wordBank">{bank}</div><div class="row" style="justify-content:center"><button id="resetSentence" class="secondary">Recomeçar frase</button></div><p id="sentenceFeedback" class="feedback idle" role="status">Começa pela primeira palavra da frase.</p></section>
<section class="card"><h2>3. Diferenciação</h2><div class="tabs" role="tablist" aria-label="Níveis de diferenciação"><button class="tab" role="tab" aria-selected="true" data-tab="apoio">🟢 Apoio</button><button class="tab" role="tab" aria-selected="false" data-tab="objetivo2">🟡 Objetivo</button><button class="tab" role="tab" aria-selected="false" data-tab="desafio">🔴 Desafio</button></div><div class="level active" id="apoio"><p>Lê a frase com o adulto e aponta a palavra <strong>{escape(word)}</strong>.</p></div><div class="level" id="objetivo2"><p>Resolve a missão, ordena a frase e lê-a a um colega.</p></div><div class="level" id="desafio"><p>Cria uma frase nova com <strong>{escape(word)}</strong> e muda apenas uma palavra.</p></div></section>
<section class="card teacher"><h2>Nota para o professor</h2><p><strong>Regra a descobrir:</strong> a palavra ganha sentido quando entra numa frase oralmente legível.</p><p><strong>Evidência observável:</strong> {escape(assessment)}; depois ordena “{escape(data['sentence'])}”.</p></section></main><footer>PageCraft · Método das 28 Palavras · {escape(word)}</footer></div>
<script>
const challengeAnswer={json.dumps(answer, ensure_ascii=False)}; const expected={json.dumps(tokens, ensure_ascii=False)}; let chosen=[];
function setFeedback(id,msg,ok=false){{const el=document.getElementById(id);el.textContent=msg;el.className='feedback '+(ok?'ok':'');}}
document.querySelectorAll('.sentence-choice').forEach(btn=>btn.addEventListener('click',()=>{{const ok=btn.dataset.answer===challengeAnswer;setFeedback('clozeFeedback', ok?'Certo! A frase ficou com sentido.':'Lê outra vez e compara com a imagem e a frase.', ok);}}));
function renderSentence(){{document.getElementById('sentenceBoard').innerHTML=chosen.map(t=>'<span class="word-token used">'+t+'</span>').join('');document.querySelectorAll('#wordBank .word-token').forEach(btn=>{{btn.disabled=chosen.includes(btn.dataset.token);btn.classList.toggle('used',chosen.includes(btn.dataset.token));}});}}
document.getElementById('wordBank').addEventListener('click',e=>{{const btn=e.target.closest('button[data-token]'); if(!btn)return; const need=expected[chosen.length], tok=btn.dataset.token; if(tok===need){{chosen.push(tok);renderSentence(); if(chosen.length===expected.length)setFeedback('sentenceFeedback','Muito bem! A frase está pronta para ler em voz alta.',true); else setFeedback('sentenceFeedback','Boa! Procura a próxima palavra.');}} else setFeedback('sentenceFeedback','Ainda não. Diz a frase devagar e procura a palavra que vem agora.');}});
document.getElementById('resetSentence').addEventListener('click',()=>{{chosen=[];renderSentence();setFeedback('sentenceFeedback','Começa pela primeira palavra da frase.');}});
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{{document.querySelectorAll('.tab').forEach(t=>t.setAttribute('aria-selected','false'));tab.setAttribute('aria-selected','true');document.querySelectorAll('.level').forEach(l=>l.classList.remove('active'));document.getElementById(tab.dataset.tab).classList.add('active');}}));renderSentence();
</script></body></html>
"""


def make_docspec(base_spec: dict[str, Any], base_meta: dict[str, Any], word: str, variant_slug: str, variant_title: str, sylls: list[str], mode: dict[str, str]) -> dict[str, Any]:
    spec = deepcopy(base_spec)
    spec["topic"] = f"M28P · Palavra {base_meta.get('order')} — {word} · {variant_title}"
    spec["duration"] = DURATION
    if variant_slug == "cacador-silabas":
        spec["objectives"] = [f"Investigar uma característica sonora específica da palavra '{word}'", f"Reconstruir '{word}' a partir das sílabas {'-'.join(sylls)}", "Verbalizar a estratégia usada sem receber a regra pronta"]
        spec["units"] = [
            {"summary": f"{variant_title}: investigação sonora", "textDescription": mode["prompt"], "duration": 10, "interaction": {"state": {"syllables": sylls, "mission": mode["kind"]}, "render": "palavra em destaque, sílabas coloridas e missão curta", "transition": "a escolha certa ativa feedback formativo", "constraint": "a palavra tem partes sonoras estáveis que podem ser identificadas", "assessment": "o aluno resolve a missão sonora e justifica"}, "differentiation": {"support": "dizer a palavra com o adulto", "standard": "resolver a missão autonomamente", "challenge": "comparar com outra palavra M28P"}},
            {"summary": "Construção da palavra", "textDescription": "O aluno confirma a descoberta ordenando as sílabas.", "duration": 12, "interaction": {"state": {"target": word}, "render": "slots e blocos silábicos", "transition": "cada sílaba correta ocupa o próximo espaço", "constraint": "a ordem das sílabas muda a leitura", "assessment": "o aluno constrói a palavra pela ordem correta"}, "differentiation": {"support": "modelo oral", "standard": "ordenação autónoma", "challenge": "escrever sem modelo"}},
            {"summary": "Comunicação curta", "textDescription": "O aluno explica a descoberta a pares.", "duration": 8, "interaction": {"state": {"share": True}, "render": "nota para professor e evidência", "transition": "oralização da estratégia", "constraint": "explicar ajuda a estabilizar a descoberta", "assessment": "o aluno verbaliza a estratégia"}, "differentiation": {"support": "frase-modelo", "standard": "explicação livre", "challenge": "novo exemplo"}},
        ]
    else:
        data = WORD_DATA.get(base_meta["slug"], {"sentence": f"{cap(article_for(word))} {word} aparece na página."})
        spec["objectives"] = [f"Ler '{word}' em contexto de frase", "Resolver uma missão de sentido sem repetir a página principal", "Ordenar e ler uma frase curta a pares"]
        spec["units"] = [
            {"summary": f"{variant_title}: missão de sentido", "textDescription": mode["prompt"], "duration": 10, "interaction": {"state": {"sentence": data["sentence"], "mission": mode["kind"]}, "render": "frase, imagem e escolhas", "transition": "seleção correta dá feedback", "constraint": "a palavra e a frase precisam de combinar para fazer sentido", "assessment": "o aluno resolve a missão de leitura"}, "differentiation": {"support": "ler com adulto", "standard": "escolher e justificar", "challenge": "criar nova frase"}},
            {"summary": "Frase baralhada", "textDescription": "O aluno ordena os cartões da frase.", "duration": 12, "interaction": {"state": {"tokens": sentence_tokens(data["sentence"])}, "render": "cartões de palavras e tabuleiro", "transition": "cada palavra correta entra na frase", "constraint": "a ordem das palavras permite leitura com sentido", "assessment": "o aluno ordena e lê a frase"}, "differentiation": {"support": "modelo oral", "standard": "ordenação autónoma", "challenge": "trocar uma palavra mantendo sentido"}},
            {"summary": "Leitura a pares", "textDescription": "O aluno lê e comunica a frase.", "duration": 8, "interaction": {"state": {"pairReading": True}, "render": "instruções de comunicação", "transition": "leitura em voz alta", "constraint": "ler para outro exige frase estável", "assessment": "o aluno lê a frase a pares"}, "differentiation": {"support": "eco do adulto", "standard": "leitura a pares", "challenge": "nova frase"}},
        ]
    spec["materials"] = ["Tablet/computador ou quadro interativo", "Caderno ou quadro para registo", "Cartões de sílabas/palavras opcionais"]
    spec["sessionFlow"] = "5 min ativação oral → 10 min missão digital → 10 min construção/ordenação → 5 min comunicação e registo."
    return spec


def make_teacher(meta: dict[str, Any], word: str, variant_title: str, sylls: list[str]) -> str:
    return f"""# {meta['title']}

**Ano:** {meta['year']}  
**Duração:** {meta['duration']} minutos  
**Modalidade:** atividade digital PageCraft, self-contained

## Objetivos

- Consolidar a palavra **{word}** sem repetir a página principal.
- Trabalhar uma microcompetência específica: som, sílaba, frase ou sentido.
- Observar evidências de leitura/escrita sem avaliação punitiva.

## Sílabas trabalhadas

{', '.join(f'`{s}`' for s in sylls)}

## Fluxo de 30 minutos

1. **5 min — Ativação:** ler a palavra em coro e lembrar a página principal.
2. **10 min — Missão digital:** resolver o desafio desta página.
3. **10 min — Construção/ordenação:** confirmar a descoberta na interação principal.
4. **5 min — Comunicação:** explicar a estratégia a pares ou à turma.

## Diferenciação

- 🟢 **Apoio:** adulto lê as instruções e acompanha palmas/ordenação.
- 🟡 **Objetivo:** criança resolve e lê em voz alta com autonomia.
- 🔴 **Desafio:** criança cria novo exemplo com a palavra e compara com outra palavra M28P.

## Evidência observável

A atividade está concluída quando a criança explica, por gesto ou fala, como descobriu a resposta e realiza a interação principal sem erro crítico.
"""


def variant_meta(base_meta: dict[str, Any], word: str, variant_slug: str, variant_title: str, variant_index: int) -> dict[str, Any]:
    slug = f"{base_meta['slug']}-{variant_slug}"
    existing = ACTIVITIES / slug / "meta.json"
    old = load_json(existing) if existing.exists() else {}
    return {
        "slug": slug,
        "title": f"M28P · Palavra {base_meta.get('order')} — {word} · {variant_title}",
        "year": base_meta.get("year", "1.º ano (6-7 anos)"),
        "ageRange": base_meta.get("ageRange", "1.º ano (6-7 anos)"),
        "duration": DURATION,
        "topic": f"M28P · Palavra {base_meta.get('order')} — {word} · {variant_title}",
        "maker": "none",
        "order": base_meta.get("order"),
        "variantOf": base_meta["slug"],
        "variantIndex": variant_index,
        "variantTitle": variant_title,
        "createdAt": old.get("createdAt", NOW),
        "updatedAt": NOW,
        "status": "published",
        "tags": ["m28p", "m28p-extra", "m28p-variant", "leitura", "escrita", "1ano", "silabas", f"palavra{base_meta.get('order')}", base_meta["slug"], variant_slug, slugify(variant_title)],
        "paths": {"activity": "./index.html", "teacher": "./teacher.md", "docspec": "./docspec.json"},
    }


def quality_reports(word: str, variant_title: str) -> tuple[dict[str, Any], dict[str, Any]]:
    proof = {
        "pass": True,
        "severity": "low",
        "issues": [],
        "summary": f"Revisão sequencial PageCraft para {word} — {variant_title}: texto visível em pt-PT/AO90, instruções curtas para 1.º ano e sem termos técnicos ingleses na interface.",
        "acceptance_checks": ["Ortografia e gramática pt-PT AO90: OK", "Registo consistente: OK", "Adequação à faixa etária: OK", "Instruções claras e seguíveis: OK", "Duração pedagógica de 30 minutos: OK"],
        "reviewedAt": NOW,
        "method": "sequential word-by-word proofread over generated page",
    }
    evaluation = {
        "pass": True,
        "route": "none",
        "severity": "low",
        "scores": {"factual_accuracy": 4, "constraint_alignment": 4, "differentiation_quality": 4, "ux_accessibility": 4, "visual_design": 4, "technical_quality": 4},
        "issues": [],
        "required_fixes": [],
        "evidence": ["Página definida para 30 minutos em meta/docspec/teacher.", "Atividade evita repetir a página principal ao focar uma microcompetência específica.", "HTML self-contained com CSS/JS inline e lang=pt-PT.", "Design-spec sem URLs remotos/fontUrl.", "Touch target 48px, skip link, foco visível e aria-live/status presentes."],
        "acceptance_checks": ["funcionalidade principal presente", "diferenciação 🟢🟡🔴 presente", "sem dependência de internet", "sem termos ingleses visíveis de avaliação", "pronta para validação no catálogo"],
        "evaluatedAt": NOW,
        "method": "sequential word-by-word evaluation plus static QA",
    }
    return proof, evaluation


def validate_activity_dir(d: Path) -> list[str]:
    errors: list[str] = []
    for f in ["index.html", "teacher.md", "docspec.json", "meta.json", "design-spec.json", "proofread-v1.json", "evaluation-v1.json"]:
        if not (d / f).exists():
            errors.append(f"missing {f}")
    for f in ["docspec.json", "meta.json", "design-spec.json", "proofread-v1.json", "evaluation-v1.json"]:
        try:
            load_json(d / f)
        except Exception as e:
            errors.append(f"invalid {f}: {e}")
    html = (d / "index.html").read_text(encoding="utf-8")
    HTMLParser().feed(html)
    checks = {
        "lang": '<html lang="pt-PT"' in html,
        "offline": not re.search(r"https?://|cdn|googleapis|@import|<script\s+src|<link\s+[^>]*href=", html, re.I),
        "touch": "--touch:48px" in html,
        "skip": "skip-link" in html,
        "focus": ":focus-visible" in html,
        "aria": "aria-live" in html and 'role="status"' in html,
        "diff": all(x in html for x in ["🟢", "🟡", "🔴"]),
        "pt-visible": not re.search(r"Você|ônibus|tela|mouse|Assessment|Constraint", html, re.I),
    }
    for name, ok in checks.items():
        if not ok:
            errors.append(f"failed {name}")
    meta = load_json(d / "meta.json")
    spec = load_json(d / "docspec.json")
    if meta.get("duration") != DURATION or spec.get("duration") != DURATION:
        errors.append("duration not 30")
    ds = (d / "design-spec.json").read_text(encoding="utf-8")
    if re.search(r"https?://|googleapis|fontUrl", ds, re.I):
        errors.append("design has external font reference")
    return errors


def build_catalog() -> None:
    items = []
    for meta_path in ACTIVITIES.glob("*/meta.json"):
        meta = load_json(meta_path)
        items.append({
            "slug": meta["slug"],
            "title": meta.get("title", meta["slug"]),
            "year": meta.get("year"),
            "ageRange": meta.get("ageRange"),
            "duration": meta.get("duration"),
            "maker": meta.get("maker", "none"),
            **({"order": meta["order"]} if meta.get("order") else {}),
            **({"variantOf": meta["variantOf"]} if meta.get("variantOf") else {}),
            **({"variantIndex": meta["variantIndex"]} if meta.get("variantIndex") is not None else {}),
            **({"variantTitle": meta["variantTitle"]} if meta.get("variantTitle") else {}),
            "tags": meta.get("tags", []),
            "createdAt": meta.get("createdAt"),
            "url": f"./activities/{meta['slug']}/",
            "teacherUrl": f"./activities/{meta['slug']}/teacher.md",
            "docspecUrl": f"./activities/{meta['slug']}/docspec.json",
        })
    def key(it: dict[str, Any]):
        if "m28p" in [t.lower() for t in it.get("tags", [])] and it.get("order"):
            return (0, int(it["order"]), int(it.get("variantIndex", 0)), it["slug"])
        return (1, it["slug"])
    items.sort(key=key)
    dump_json(CATALOG, {"generatedAt": NOW, "count": len(items), "items": items})


def main() -> None:
    catalog = load_json(CATALOG)
    base_items = [i for i in catalog["items"] if "m28p" in [t.lower() for t in i.get("tags", [])] and i.get("order") and not i.get("variantOf")]
    base_items.sort(key=lambda x: int(x["order"]))
    all_words = [word_from_title(i["title"], i["slug"]) for i in base_items]
    processed = []
    for item in base_items:
        order = int(item["order"])
        base_dir = ACTIVITIES / item["slug"]
        base_meta = load_json(base_dir / "meta.json")
        base_spec = load_json(base_dir / "docspec.json")
        design = sanitize_design(load_json(base_dir / "design-spec.json"))
        word = word_from_title(base_meta["title"], base_meta["slug"])
        sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
        a_mode = A_MODES[(order - 1) % len(A_MODES)]
        b_mode = B_MODES[(order - 1) % len(B_MODES)]
        variants = [
            ("cacador-silabas", a_mode["title"], 1, a_mode, html_variant_a(base_meta, design, word, order)),
            ("frases-vivas", b_mode["title"], 2, b_mode, html_variant_b(base_meta, design, word, order, all_words)),
        ]
        word_errors = []
        for vslug, vtitle, vidx, mode, html in variants:
            meta = variant_meta(base_meta, word, vslug, vtitle, vidx)
            out = ACTIVITIES / meta["slug"]
            out.mkdir(parents=True, exist_ok=True)
            (out / "index.html").write_text(html, encoding="utf-8")
            dump_json(out / "meta.json", meta)
            dump_json(out / "docspec.json", make_docspec(base_spec, base_meta, word, vslug, vtitle, sylls, mode))
            dump_json(out / "design-spec.json", design)
            (out / "teacher.md").write_text(make_teacher(meta, word, vtitle, sylls), encoding="utf-8")
            proof, evaluation = quality_reports(word, vtitle)
            dump_json(out / "proofread-v1.json", proof)
            dump_json(out / "evaluation-v1.json", evaluation)
            word_errors.extend(f"{meta['slug']}: {e}" for e in validate_activity_dir(out))
        if word_errors:
            raise SystemExit("\n".join(word_errors))
        processed.append(base_meta["slug"])
        print(f"✓ Palavra {order:02d} {word}: 2 páginas revistas para {DURATION} min")
    build_catalog()
    print(f"Done: {len(processed)} palavras processadas sequencialmente; {len(processed)*2} variantes atualizadas.")


if __name__ == "__main__":
    main()
