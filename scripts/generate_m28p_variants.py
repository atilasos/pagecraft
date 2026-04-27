#!/usr/bin/env python3
"""Generate two additional M28P PageCraft pages per word.

Creates:
- <word>-cacador-silabas
- <word>-frases-vivas

The generated pages are self-contained, pt-PT, keyboard/click accessible, and reuse
existing M28P docspec/design metadata as the source of truth for word order,
syllables and palette.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ACTIVITIES = ROOT / "activities"
CATALOG = ROOT / "catalog.json"
NOW = "2026-04-27T00:00:00Z"

WORD_DATA: dict[str, dict[str, str]] = {
    "menina": {"emoji": "👧", "sentence": "A menina sorri no recreio.", "place": "no recreio"},
    "menino": {"emoji": "👦", "sentence": "O menino lê no tapete.", "place": "no tapete"},
    "uva": {"emoji": "🍇", "sentence": "A uva roxa está no prato.", "place": "no prato"},
    "dedo": {"emoji": "☝️", "sentence": "O dedo aponta para a palavra.", "place": "na mão"},
    "sapato": {"emoji": "👞", "sentence": "O sapato fica junto da porta.", "place": "junto da porta"},
    "bota": {"emoji": "🥾", "sentence": "A bota salta na poça.", "place": "na poça"},
    "leque": {"emoji": "🪭", "sentence": "O leque faz vento devagar.", "place": "na mão"},
    "casa": {"emoji": "🏠", "sentence": "A casa tem uma janela azul.", "place": "na rua"},
    "janela": {"emoji": "🪟", "sentence": "A janela deixa entrar luz.", "place": "na sala"},
    "telhado": {"emoji": "🏠", "sentence": "O telhado protege a casa.", "place": "na casa"},
    "escada": {"emoji": "🪜", "sentence": "A escada tem muitos degraus.", "place": "no pátio"},
    "chave": {"emoji": "🔑", "sentence": "A chave abre a porta.", "place": "na porta"},
    "galinha": {"emoji": "🐔", "sentence": "A galinha procura milho.", "place": "no quintal"},
    "ovo": {"emoji": "🥚", "sentence": "O ovo está no ninho.", "place": "no ninho"},
    "rato": {"emoji": "🐭", "sentence": "O rato corre para a toca.", "place": "na toca"},
    "cenoura": {"emoji": "🥕", "sentence": "A cenoura cresce na horta.", "place": "na horta"},
    "girafa": {"emoji": "🦒", "sentence": "A girafa estica o pescoço.", "place": "na savana"},
    "palhaco": {"emoji": "🤡", "sentence": "O palhaço faz rir a turma.", "place": "no circo"},
    "zebra": {"emoji": "🦓", "sentence": "A zebra tem riscas pretas.", "place": "na savana"},
    "bandeira": {"emoji": "🚩", "sentence": "A bandeira dança ao vento.", "place": "no mastro"},
    "funil": {"emoji": "📯", "sentence": "O funil ajuda a deitar água.", "place": "na mesa"},
    "arvore": {"emoji": "🌳", "sentence": "A árvore dá sombra fresca.", "place": "no jardim"},
    "quadro": {"emoji": "🟩", "sentence": "O quadro mostra a palavra.", "place": "na sala"},
    "passarinho": {"emoji": "🐦", "sentence": "O passarinho canta na árvore.", "place": "na árvore"},
    "peixe": {"emoji": "🐟", "sentence": "O peixe nada no lago.", "place": "no lago"},
    "cigarra": {"emoji": "🦗", "sentence": "A cigarra canta no verão.", "place": "no verão"},
    "fogueira": {"emoji": "🔥", "sentence": "A fogueira aquece a roda.", "place": "na roda"},
    "flor": {"emoji": "🌸", "sentence": "A flor abre de manhã.", "place": "no jardim"},
}

VOWELS = "aeiouáéíóúâêôãõà"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sanitize_design(design: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(design)
    typography = clean.setdefault("typography", {})
    typography.pop("fontUrl", None)
    typography["fontFamily"] = "'Nunito', 'Comic Sans MS', 'Chalkboard SE', sans-serif"
    notes = clean.get("notes", "")
    offline_note = "Sem fontes remotas; usar fontes locais/fallback para garantir funcionamento offline."
    clean["notes"] = (notes + " " + offline_note).strip() if offline_note not in notes else notes
    return clean


def slugify(text: str) -> str:
    text = text.lower().strip()
    trans = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçñ", "aaaaaeeeeiiiiooooouuuucn")
    text = text.translate(trans)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def word_from_title(title: str, fallback: str) -> str:
    if "—" in title:
        return title.split("—")[-1].strip()
    return fallback.replace("-", " ").title()


def article_for(word: str) -> str:
    first = word.lower()[0]
    if first in VOWELS:
        return "a"
    # Common masculine M28P words
    masc = {"dedo", "sapato", "leque", "telhado", "ovo", "rato", "funil", "quadro", "peixe"}
    return "o" if slugify(word) in masc else "a"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def sentence_tokens(sentence: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sentence)


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
    .meta,.pills,.row {{ display:flex; flex-wrap:wrap; gap:.55rem; align-items:center; }}
    .pill {{ border:2px solid rgba(255,255,255,.72); background:rgba(255,255,255,.20); color:inherit; border-radius:999px; padding:.35rem .75rem; font-weight:800; }}
    .card {{ background:var(--surface); border:2px solid var(--primary); border-radius:var(--radius); box-shadow:var(--shadow); padding:1rem; margin:1rem 0; }}
    .soft {{ background:color-mix(in srgb,var(--bg) 72%, white); border-style:dashed; }}
    button,.button {{ min-width:var(--touch); min-height:var(--touch); border:2px solid color-mix(in srgb,var(--primary) 70%, black); background:var(--primary); color:white; border-radius:999px; padding:.65rem 1rem; font:inherit; font-weight:900; cursor:pointer; touch-action:manipulation; box-shadow:0 5px 14px rgba(0,0,0,.12); transition:transform .18s ease, box-shadow .18s ease, background .18s ease; }}
    button:hover,.button:hover {{ transform:scale(1.04); }} button:active {{ transform:scale(.97); }}
    button.secondary {{ background:white; color:color-mix(in srgb,var(--primary) 72%, black); }}
    button.good {{ background:var(--ok); border-color:#15803d; }}
    button.warn {{ background:var(--try); border-color:#b45309; }}
    :focus-visible {{ outline:4px solid var(--accent); outline-offset:3px; }}
    .tabs {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:.75rem 0; }}
    .tab {{ background:white; color:var(--text); border-color:#d6cec7; }} .tab[aria-selected='true'] {{ background:var(--primary); color:white; border-color:color-mix(in srgb,var(--primary) 70%, black); }}
    .level {{ display:none; }} .level.active {{ display:block; animation:pop .22s ease; }}
    .syllables,.slots,.choices,.word-bank {{ display:flex; gap:.7rem; flex-wrap:wrap; justify-content:center; margin:1rem 0; }}
    .syllable,.slot,.word-token {{ border-radius:16px; min-height:58px; min-width:64px; display:inline-grid; place-items:center; padding:.45rem .85rem; font-size:clamp(1.45rem,5vw,2.25rem); font-weight:1000; letter-spacing:.02em; }}
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
    c = design.get("syllableColors", {}).get(s, design.get("palette", {}).get("primary", "#2563EB"))
    return f"background:{escape(c)}"


def html_variant_a(base: dict[str, Any], design: dict[str, Any], word: str, slug: str, order: int) -> str:
    sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
    data = WORD_DATA.get(base["slug"], {"emoji": "⭐", "sentence": f"{cap(article_for(word))} {word} aparece na página.", "place": "na página"})
    shuffled = sylls[1:] + sylls[:1] if len(sylls) > 1 else sylls
    options = sorted({len(sylls), max(1, len(sylls)-1), len(sylls)+1})
    syll_buttons = "\n".join(f'<button class="syllable" style="{syllable_style(s, design)}" data-syll="{escape(s)}" aria-label="Sílaba {escape(s)}">{escape(s)}</button>' for s in shuffled)
    slots = "\n".join(f'<span class="slot" data-index="{i}" aria-label="Espaço {i+1}">?</span>' for i in range(len(sylls)))
    opt_buttons = "\n".join(f'<button class="secondary count-choice" data-count="{n}">{n}</button>' for n in options)
    return f"""<!DOCTYPE html>
<html lang="pt-PT">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>M28P #{order} — {escape(word)} · Caça às sílabas | PageCraft</title>
  <style>{common_css(design)}</style>
</head>
<body>
<a class="skip-link" href="#main">Ir para o conteúdo</a>
<div class="wrap">
  <header class="hero">
    <div class="meta"><span class="pill">M28P · Palavra {order}</span><span class="pill">1.º ano</span><span class="pill">Caça às sílabas</span></div>
    <h1>{data['emoji']} {escape(word)} — Caça às sílabas</h1>
    <p>Uma página para ouvir, tocar e reconstruir a palavra por partes, sem dar a regra pronta.</p>
  </header>
  <main id="main">
    <section class="card soft" aria-labelledby="objetivo">
      <h2 id="objetivo">O desafio</h2>
      <p>Toca nas sílabas pela ordem certa. Quando a palavra ficar completa, observa o que acontece e explica à turma como descobriste.</p>
      <div class="target-word" aria-label="Palavra alvo">{escape(word)}</div>
    </section>

    <section class="card" aria-labelledby="niveis">
      <h2 id="niveis">Escolhe o teu nível</h2>
      <div class="tabs" role="tablist" aria-label="Níveis de diferenciação">
        <button class="tab" role="tab" aria-selected="true" data-tab="apoio">🟢 Apoio</button>
        <button class="tab" role="tab" aria-selected="false" data-tab="objetivo">🟡 Objetivo</button>
        <button class="tab" role="tab" aria-selected="false" data-tab="desafio">🔴 Desafio</button>
      </div>
      <div class="level active" id="apoio"><p>Com ajuda: lê as sílabas em voz alta antes de tocar.</p></div>
      <div class="level" id="objetivo"><p>Objetivo: reconstrói a palavra sem ajuda do adulto.</p></div>
      <div class="level" id="desafio"><p>Desafio: depois de construir, tapa a palavra e escreve-a no caderno.</p></div>
    </section>

    <section class="card" aria-labelledby="construir">
      <h2 id="construir">1. Constrói a palavra</h2>
      <p class="mini">Usa o clique ou o teclado. Também funciona em tablet.</p>
      <div class="slots" id="slots" aria-live="polite">{slots}</div>
      <div class="syllables" id="syllables">{syll_buttons}</div>
      <div class="row" style="justify-content:center"><button id="reset" class="secondary">Recomeçar</button><button id="hear">Bater palmas</button></div>
      <p id="buildFeedback" class="feedback idle" role="status">Toca na primeira sílaba para começar.</p>
    </section>

    <section class="card" aria-labelledby="contar">
      <h2 id="contar">2. Quantas partes ouvimos?</h2>
      <p>Depois de bater palmas, escolhe o número de sílabas da palavra.</p>
      <div class="choices">{opt_buttons}</div>
      <p id="countFeedback" class="feedback idle" role="status">Escuta a palavra: {escape(' · '.join(sylls))}</p>
    </section>

    <section class="card teacher" aria-labelledby="professor">
      <h2 id="professor">Nota para o professor</h2>
      <p><strong>Regra a descobrir:</strong> a palavra escrita pode ser reconstruída juntando as partes sonoras na ordem correta.</p>
      <p><strong>Evidência observável:</strong> o aluno ordena as sílabas {escape('–'.join(sylls))}, identifica {len(sylls)} partes e verbaliza a estratégia usada.</p>
    </section>
  </main>
  <footer>PageCraft · Método das 28 Palavras · {escape(word)}</footer>
</div>
<script>
const expected = {json.dumps(sylls, ensure_ascii=False)};
let placed = [];
const slots = [...document.querySelectorAll('.slot')];
const fb = document.getElementById('buildFeedback');
function render() {{
  slots.forEach((slot,i)=>{{ slot.textContent = placed[i] || '?'; slot.classList.toggle('filled', Boolean(placed[i])); }});
  document.querySelectorAll('.syllable').forEach(btn=>{{ btn.disabled = placed.includes(btn.dataset.syll); btn.style.opacity = btn.disabled ? .45 : 1; }});
}}
function say(message, ok=false) {{ fb.textContent = message; fb.className = 'feedback ' + (ok ? 'ok' : ''); }}
document.getElementById('syllables').addEventListener('click', e=>{{
  const btn = e.target.closest('button[data-syll]'); if(!btn) return;
  const s = btn.dataset.syll; const need = expected[placed.length];
  if(s === need) {{ placed.push(s); render();
    if(placed.length === expected.length) say('Muito bem! Descobriste a palavra {escape(word)} juntando as sílabas pela ordem certa.', true);
    else say('Boa! Agora procura a próxima sílaba.');
  }} else {{ say('Quase! Escuta outra vez e procura a sílaba que vem agora.'); }}
}});
document.getElementById('reset').addEventListener('click', ()=>{{ placed=[]; render(); say('Toca na primeira sílaba para começar.'); }});
document.getElementById('hear').addEventListener('click', ()=>{{
  let i=0; say('Vamos bater palmas: ' + expected.join(' · '), true);
  const all=[...document.querySelectorAll('.syllable')];
  const tick=()=>{{ all.forEach(b=>b.style.transform=''); const b=all.find(x=>x.dataset.syll===expected[i]); if(b) b.style.transform='scale(1.16)'; i++; if(i<expected.length) setTimeout(tick,520); else setTimeout(()=>all.forEach(b=>b.style.transform=''),560); }}; tick();
}});
document.querySelectorAll('.count-choice').forEach(btn=>btn.addEventListener('click',()=>{{
  const ok = Number(btn.dataset.count) === expected.length;
  const out = document.getElementById('countFeedback');
  out.textContent = ok ? 'Certo! A palavra tem ' + expected.length + ' partes: ' + expected.join(' · ') + '.' : 'Ainda não. Bate palmas e conta só as partes que ouves.';
  out.className = 'feedback ' + (ok ? 'ok' : '');
}}));
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{{
  document.querySelectorAll('.tab').forEach(t=>t.setAttribute('aria-selected','false')); tab.setAttribute('aria-selected','true');
  document.querySelectorAll('.level').forEach(l=>l.classList.remove('active')); document.getElementById(tab.dataset.tab).classList.add('active');
}}));
render();
</script>
</body>
</html>
"""


def html_variant_b(base: dict[str, Any], design: dict[str, Any], word: str, slug: str, order: int, all_words: list[str]) -> str:
    sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
    data = WORD_DATA.get(base["slug"], {"emoji": "⭐", "sentence": f"{cap(article_for(word))} {word} aparece na página.", "place": "na página"})
    sentence = data["sentence"]
    tokens = sentence_tokens(sentence)
    shuffled = tokens[1::2] + tokens[0::2]
    distractors = [w for w in all_words if slugify(w) != base["slug"]][:3]
    cloze = re.sub(r"\b" + re.escape(word) + r"\b", "_____", sentence, count=1, flags=re.IGNORECASE)
    options = [word] + distractors[:2]
    option_buttons = "\n".join(f'<button class="secondary word-option" data-word="{escape(o)}">{escape(o)}</button>' for o in options)
    bank = "\n".join(f'<button class="word-token" data-token="{escape(t)}">{escape(t)}</button>' for t in shuffled)
    syll_badges = " ".join(f'<span class="syllable" style="{syllable_style(s, design)}">{escape(s)}</span>' for s in sylls)
    return f"""<!DOCTYPE html>
<html lang="pt-PT">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>M28P #{order} — {escape(word)} · Frases vivas | PageCraft</title>
  <style>{common_css(design)}</style>
</head>
<body>
<a class="skip-link" href="#main">Ir para o conteúdo</a>
<div class="wrap">
  <header class="hero">
    <div class="meta"><span class="pill">M28P · Palavra {order}</span><span class="pill">1.º ano</span><span class="pill">Frases vivas</span></div>
    <h1>{data['emoji']} {escape(word)} — Frases vivas</h1>
    <p>Da palavra à frase: lê, escolhe, ordena e comunica a tua descoberta.</p>
  </header>
  <main id="main">
    <section class="card soft">
      <h2>Recorda a palavra</h2>
      <div class="grid"><div><div class="big-emoji" aria-hidden="true">{data['emoji']}</div></div><div><div class="target-word">{escape(word)}</div><div class="syllables" aria-label="Sílabas da palavra">{syll_badges}</div></div></div>
    </section>

    <section class="card">
      <h2>1. Completa a frase</h2>
      <p class="target-word" style="font-size:clamp(1.6rem,5vw,2.6rem); text-transform:none">{escape(cloze)}</p>
      <div class="choices">{option_buttons}</div>
      <p id="clozeFeedback" class="feedback idle" role="status">Escolhe a palavra que faz sentido na frase.</p>
    </section>

    <section class="card">
      <h2>2. Ordena a frase</h2>
      <p>Toca nas palavras pela ordem certa. Se te enganares, recomeça.</p>
      <div class="sentence-board" id="sentenceBoard" aria-live="polite"></div>
      <div class="word-bank" id="wordBank">{bank}</div>
      <div class="row" style="justify-content:center"><button id="resetSentence" class="secondary">Recomeçar frase</button></div>
      <p id="sentenceFeedback" class="feedback idle" role="status">Começa pela primeira palavra da frase.</p>
    </section>

    <section class="card">
      <h2>3. Diferenciação</h2>
      <div class="tabs" role="tablist" aria-label="Níveis de diferenciação">
        <button class="tab" role="tab" aria-selected="true" data-tab="apoio">🟢 Apoio</button>
        <button class="tab" role="tab" aria-selected="false" data-tab="objetivo">🟡 Objetivo</button>
        <button class="tab" role="tab" aria-selected="false" data-tab="desafio">🔴 Desafio</button>
      </div>
      <div class="level active" id="apoio"><p>Lê a frase com o adulto e aponta a palavra <strong>{escape(word)}</strong>.</p></div>
      <div class="level" id="objetivo"><p>Ordena a frase e lê-a a um colega.</p></div>
      <div class="level" id="desafio"><p>Cria uma nova frase com <strong>{escape(word)}</strong> e uma palavra já aprendida.</p></div>
    </section>

    <section class="card teacher">
      <h2>Nota para o professor</h2>
      <p><strong>Regra a descobrir:</strong> a palavra ganha sentido quando entra numa frase oralmente legível.</p>
      <p><strong>Evidência observável:</strong> o aluno completa a frase com {escape(word)}, ordena “{escape(sentence)}” e lê a frase a pares.</p>
    </section>
  </main>
  <footer>PageCraft · Método das 28 Palavras · {escape(word)}</footer>
</div>
<script>
const answerWord = {json.dumps(word, ensure_ascii=False)};
const expected = {json.dumps(tokens, ensure_ascii=False)};
let chosen = [];
function setFeedback(id, msg, ok=false) {{ const el=document.getElementById(id); el.textContent=msg; el.className='feedback ' + (ok ? 'ok' : ''); }}
document.querySelectorAll('.word-option').forEach(btn=>btn.addEventListener('click',()=>{{
  const ok = btn.dataset.word === answerWord;
  setFeedback('clozeFeedback', ok ? 'Certo! A frase ficou com sentido.' : 'Lê outra vez. Essa palavra não combina tão bem com a imagem e a frase.', ok);
}}));
function renderSentence() {{
  document.getElementById('sentenceBoard').innerHTML = chosen.map(t=>'<span class="word-token used">'+t+'</span>').join('');
  document.querySelectorAll('#wordBank .word-token').forEach(btn=>{{ btn.disabled = chosen.includes(btn.dataset.token); btn.classList.toggle('used', chosen.includes(btn.dataset.token)); }});
}}
document.getElementById('wordBank').addEventListener('click', e=>{{
  const btn=e.target.closest('button[data-token]'); if(!btn) return;
  const need=expected[chosen.length]; const tok=btn.dataset.token;
  if(tok===need) {{ chosen.push(tok); renderSentence();
    if(chosen.length===expected.length) setFeedback('sentenceFeedback','Muito bem! A frase está completa e pode ser lida em voz alta.',true);
    else setFeedback('sentenceFeedback','Boa! Procura a próxima palavra.');
  }} else setFeedback('sentenceFeedback','Ainda não. Diz a frase devagar e procura a palavra que vem agora.');
}});
document.getElementById('resetSentence').addEventListener('click',()=>{{ chosen=[]; renderSentence(); setFeedback('sentenceFeedback','Começa pela primeira palavra da frase.'); }});
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{{
  document.querySelectorAll('.tab').forEach(t=>t.setAttribute('aria-selected','false')); tab.setAttribute('aria-selected','true');
  document.querySelectorAll('.level').forEach(l=>l.classList.remove('active')); document.getElementById(tab.dataset.tab).classList.add('active');
}}));
renderSentence();
</script>
</body>
</html>
"""


def make_docspec(base_spec: dict[str, Any], base_meta: dict[str, Any], word: str, variant: str, variant_title: str, sylls: list[str]) -> dict[str, Any]:
    spec = deepcopy(base_spec)
    spec["topic"] = f"M28P · Palavra {base_meta.get('order')} — {word} · {variant_title}"
    spec["duration"] = 35
    if variant == "cacador-silabas":
        spec["objectives"] = [
            f"Segmentar a palavra '{word}' em sílabas e reconstruí-la pela ordem correta",
            "Associar som, gesto e bloco escrito numa sequência observável",
            "Verbalizar a estratégia usada para descobrir a palavra",
        ]
        spec["units"] = [
            {
                "summary": f"Caça às sílabas de {word}",
                "textDescription": f"O aluno toca nas sílabas de {word}, escuta a sequência e reconstrói a palavra.",
                "duration": 20,
                "interaction": {"state": {"syllables": sylls}, "render": "blocos silábicos coloridos e espaços de construção", "transition": "tocar na sílaba certa preenche o próximo espaço", "constraint": "a palavra só fica legível quando as sílabas estão na ordem sonora correta", "assessment": "o aluno ordena as sílabas e identifica o número de partes"},
                "differentiation": {"support": "ler sílabas em voz alta com ajuda", "standard": "ordenar autonomamente", "challenge": "escrever a palavra sem modelo"},
            },
            {
                "summary": "Contagem silábica com palmas",
                "textDescription": "O aluno confirma quantas partes sonoras ouviu.",
                "duration": 15,
                "interaction": {"state": {"count": len(sylls)}, "render": "botões com números", "transition": "seleção do número dá feedback", "constraint": "cada palma corresponde a uma parte sonora", "assessment": "o aluno escolhe a contagem correta e explica"},
                "differentiation": {"support": "palmas acompanhadas", "standard": "contagem autónoma", "challenge": "comparar com outra palavra M28P"},
            },
        ]
    else:
        data = WORD_DATA.get(base_meta["slug"], {"sentence": f"{cap(article_for(word))} {word} aparece na página."})
        spec["objectives"] = [
            f"Reconhecer '{word}' em contexto de frase simples",
            "Ordenar palavras para construir uma frase com sentido",
            "Ler a frase a pares, respeitando a sequência oral",
        ]
        spec["units"] = [
            {
                "summary": f"Completar uma frase com {word}",
                "textDescription": "O aluno escolhe a palavra que torna a frase coerente com a imagem/contexto.",
                "duration": 15,
                "interaction": {"state": {"targetWord": word}, "render": "frase lacunar e opções de palavra", "transition": "seleção dá feedback sem punição", "constraint": "a palavra precisa de fazer sentido na frase", "assessment": "o aluno completa a frase corretamente"},
                "differentiation": {"support": "ler com adulto", "standard": "escolher e justificar", "challenge": "criar nova frase"},
            },
            {
                "summary": "Ordenar frase viva",
                "textDescription": f"O aluno ordena os cartões para formar: {data['sentence']}",
                "duration": 20,
                "interaction": {"state": {"sentence": data["sentence"]}, "render": "cartões de palavras e tabuleiro de frase", "transition": "cada palavra correta entra na frase", "constraint": "a frase tem uma ordem que permite leitura com sentido", "assessment": "o aluno ordena e lê a frase"},
                "differentiation": {"support": "modelo oral", "standard": "ordenação autónoma", "challenge": "substituir uma palavra mantendo sentido"},
            },
        ]
    spec["materials"] = ["Tablet/computador ou quadro interativo", "Caderno ou quadro para registo", "Cartões de sílabas/palavras opcionais"]
    spec["sessionFlow"] = "Ativação oral breve → exploração digital autónoma/pares → leitura em voz alta → registo no caderno → comunicação curta à turma."
    return spec


def make_teacher(meta: dict[str, Any], word: str, variant_title: str, sylls: list[str]) -> str:
    return f"""# {meta['title']}

**Ano:** {meta['year']}  
**Duração:** {meta['duration']} minutos  
**Modalidade:** atividade digital PageCraft, self-contained

## Objetivos

- Consolidar a palavra **{word}** no Método das 28 Palavras.
- Ligar reconhecimento global, consciência silábica e leitura com sentido.
- Observar evidências de leitura/escrita sem avaliação punitiva.

## Sílabas trabalhadas

{', '.join(f'`{s}`' for s in sylls)}

## Fluxo sugerido

1. Ler a palavra em coro e individualmente.
2. Realizar a exploração digital em pares ou pequeno grupo.
3. Pedir que uma criança explique a estratégia usada.
4. Registar no caderno uma palavra/frase descoberta.
5. Partilhar no circuito de comunicação da turma.

## Diferenciação

- 🟢 **Apoio:** adulto lê as instruções e acompanha palmas/ordenação.
- 🟡 **Objetivo:** criança resolve e lê em voz alta com autonomia.
- 🔴 **Desafio:** criança cria novo exemplo com a palavra e compara com outra palavra M28P.

## Evidência observável

A atividade está concluída quando a criança consegue explicar, por gesto ou fala, como descobriu a palavra/frase e realizar a interação principal sem erro crítico.
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
        "duration": 35,
        "topic": f"M28P · Palavra {base_meta.get('order')} — {word} · {variant_title}",
        "maker": "none",
        "order": base_meta.get("order"),
        "variantOf": base_meta["slug"],
        "variantIndex": variant_index,
        "variantTitle": variant_title,
        "createdAt": old.get("createdAt", NOW),
        "updatedAt": NOW,
        "status": "published",
        "tags": ["m28p", "m28p-extra", "m28p-variant", "leitura", "escrita", "1ano", "silabas", f"palavra{base_meta.get('order')}", base_meta["slug"], variant_slug],
        "paths": {"activity": "./index.html", "teacher": "./teacher.md", "docspec": "./docspec.json"},
    }


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
    base_items = [it for it in catalog["items"] if "m28p" in [t.lower() for t in it.get("tags", [])] and it.get("order") and not it.get("variantOf")]
    base_items.sort(key=lambda x: int(x["order"]))
    all_words = [word_from_title(i["title"], i["slug"]) for i in base_items]
    made = []
    for item in base_items:
        base_dir = ACTIVITIES / item["slug"]
        base_meta = load_json(base_dir / "meta.json")
        base_spec = load_json(base_dir / "docspec.json")
        design = sanitize_design(load_json(base_dir / "design-spec.json"))
        word = word_from_title(base_meta["title"], base_meta["slug"])
        sylls = list(design.get("syllableColors", {}).keys()) or [word.lower()]
        variants = [
            ("cacador-silabas", "Caça às sílabas", 1, html_variant_a),
            ("frases-vivas", "Frases vivas", 2, html_variant_b),
        ]
        for vslug, vtitle, vidx, html_func in variants:
            meta = variant_meta(base_meta, word, vslug, vtitle, vidx)
            out = ACTIVITIES / meta["slug"]
            out.mkdir(parents=True, exist_ok=True)
            if vslug == "cacador-silabas":
                html = html_func(base_meta, design, word, meta["slug"], int(base_meta["order"]))
            else:
                html = html_func(base_meta, design, word, meta["slug"], int(base_meta["order"]), all_words)
            (out / "index.html").write_text(html, encoding="utf-8")
            dump_json(out / "meta.json", meta)
            dump_json(out / "docspec.json", make_docspec(base_spec, base_meta, word, vslug, vtitle, sylls))
            dump_json(out / "design-spec.json", design)
            (out / "teacher.md").write_text(make_teacher(meta, word, vtitle, sylls), encoding="utf-8")
            made.append(meta["slug"])
    build_catalog()
    print(f"Generated/updated {len(made)} activities")
    for slug in made[:10]: print(slug)
    if len(made) > 10: print("...")

if __name__ == "__main__":
    main()
