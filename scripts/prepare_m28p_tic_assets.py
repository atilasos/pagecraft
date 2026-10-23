#!/usr/bin/env python3
"""Prepare original SVGs and pt-PT whole-word recordings for independent TIC play.

SVGs have no runtime dependencies. For audio, run:
  uv run --with edge-tts python scripts/prepare_m28p_tic_assets.py --audio
Existing files are preserved unless --overwrite is explicitly supplied.
"""

import argparse
import asyncio
import hashlib
import html
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets/m28p-tic"
VOICE = "pt-PT-RaquelNeural"
RATE = "-12%"
INK = "#263e49"
SKIN = "#dca176"
TEAL = "#3d9295"
GOLD = "#f0bd4d"
WORDS = [
    ("menina", "menina"), ("menino", "menino"), ("uva", "uva"),
    ("dedo", "dedo"), ("sapato", "sapato"), ("bota", "bota"),
    ("leque", "leque"), ("casa", "casa"), ("janela", "janela"),
    ("telhado", "telhado"), ("escada", "escada"), ("chave", "chave"),
    ("galinha", "galinha"), ("gema", "gema"), ("rato", "rato"),
    ("cenoura", "cenoura"), ("girafa", "girafa"), ("palhaco", "palhaço"),
    ("zebra", "zebra"), ("bandeira", "bandeira"), ("funil", "funil"),
    ("arvore", "árvore"), ("quadro", "quadro"),
    ("passarinho", "passarinho"), ("peixe", "peixe"),
    ("cigarra", "cigarra"), ("fogueira", "fogueira"), ("flor", "flor"),
]
INSTRUCTIONS = {
    "match": "Toca na palavra igual ao modelo.",
    "pairs": "Toca no desenho. Depois, toca na palavra.",
    "hunt": "Procura as palavras iguais ao modelo.",
    "syllables": "Toca nas peças para formar a palavra.",
    "gap": "Escolhe a peça que falta.",
    "recall": "Forma a palavra. Podes ouvir outra vez.",
    "start": "Vamos jogar. Toca na seta para começar.",
    "hint": "Olha para o exemplo. Experimenta outra vez.",
    "success": "Já está. Podes continuar.",
    "retry": "Vamos tentar outra vez.",
    "finish": "Terminaste este jogo. Podes repetir.",
}


def circle(x, y, r, fill, **attrs):
    return element("circle", cx=x, cy=y, r=r, fill=fill, **attrs)


def ellipse(x, y, rx, ry, fill, **attrs):
    return element("ellipse", cx=x, cy=y, rx=rx, ry=ry, fill=fill, **attrs)


def rect(x, y, width, height, fill, rx=0, **attrs):
    return element("rect", x=x, y=y, width=width, height=height, fill=fill, rx=rx, **attrs)


def path(d, fill="none", **attrs):
    return element("path", d=d, fill=fill, **attrs)


def line(x1, y1, x2, y2, **attrs):
    return element("line", x1=x1, y1=y1, x2=x2, y2=y2, **attrs)


def element(name, **attrs):
    fields = " ".join(f'{key.replace("_", "-")}="{html.escape(str(value), quote=True)}"' for key, value in attrs.items())
    return f"<{name} {fields}/>"


def eyes(x, y, distance=26):
    return circle(x - distance / 2, y, 3, INK, stroke="none") + circle(x + distance / 2, y, 3, INK, stroke="none")


def person(girl):
    drawing = ""
    if girl:
        drawing += ellipse(85, 77, 17, 30, "#604535") + ellipse(155, 77, 17, 30, "#604535")
        drawing += path("M99 139 L89 204 M141 139 L151 204", stroke=SKIN, stroke_width=17)
        drawing += path("M95 108 L72 148 M145 108 L168 148", stroke=SKIN, stroke_width=14)
        drawing += path("M97 101 Q120 93 143 101 L163 169 L77 169 Z", "#b880b3")
    else:
        drawing += path("M100 154 L95 207 M140 154 L145 207", stroke=SKIN, stroke_width=17)
        drawing += path("M95 109 L72 151 M145 109 L168 151", stroke=SKIN, stroke_width=14)
        drawing += path("M98 100 L142 100 L156 144 L140 151 L100 151 L84 144 Z", TEAL)
        drawing += path("M95 147 L145 147 L149 177 L126 177 L120 159 L114 177 L91 177 Z", "#536f9c")
    drawing += circle(120, 65, 36, SKIN)
    drawing += path("M86 61 Q82 19 119 25 Q156 19 154 61 L144 46 L129 42 L111 48 L96 43 Z", "#604535")
    drawing += eyes(120, 65) + path("M109 82 Q120 91 131 82", stroke_width=3)
    drawing += ellipse(91, 211, 18, 8, "#40576b") + ellipse(149, 211, 18, 8, "#40576b")
    if girl:
        drawing += path("M77 52 L66 44 L66 61 Z M77 52 L90 43 L90 61 Z", GOLD)
    return drawing


def house(roof_focus=False):
    muted = "#e6e6df" if roof_focus else "#f3d8a2"
    drawing = rect(56, 107, 128, 103, muted, rx=3)
    drawing += rect(105, 152, 31, 58, "#bb9472" if roof_focus else "#91694b", rx=3)
    drawing += rect(72, 132, 24, 27, "#d5e5e8", rx=2) + rect(148, 132, 24, 27, "#d5e5e8", rx=2)
    drawing += path("M38 111 L120 39 L202 111 Z", "#b96344" if not roof_focus else "#d48144", stroke_width=5)
    drawing += path("M62 93 L178 93 M82 75 L158 75 M101 57 L139 57", stroke="#7f4c36", stroke_width=2)
    drawing += path("M100 96 L111 77 M134 96 L123 77 M112 76 L120 59 M146 76 L133 59", stroke="#7f4c36", stroke_width=2)
    if roof_focus:
        drawing += path("M206 52 L181 76 M202 72 L181 76 L185 55", stroke=INK, stroke_width=6)
    return drawing


def drawings():
    """Each drawing depicts the named referent; no emoji or rendered text."""
    art = {"menina": person(True), "menino": person(False)}
    grapes = path("M118 47 Q123 27 139 23", stroke="#5e7546", stroke_width=7)
    grapes += path("M123 43 Q147 15 174 40 Q154 67 126 52", "#79a66a")
    for x, y in [(91, 78), (124, 75), (155, 80), (75, 106), (110, 107), (144, 111), (94, 139), (128, 143), (112, 173)]:
        grapes += circle(x, y, 23, "#8568a0") + ellipse(x - 7, y - 7, 5, 4, "#c9b7d7", stroke="none")
    art["uva"] = grapes
    art["dedo"] = path("M83 205 Q65 179 65 152 L65 129 Q65 115 77 116 Q84 117 88 131 L88 49 Q88 32 100 32 Q114 32 114 49 L114 114 L118 95 Q122 83 133 88 Q142 92 139 108 Q143 94 154 99 Q163 104 158 121 Q165 111 175 118 Q184 126 178 145 L171 184 Q168 200 154 213 Z", SKIN)
    art["dedo"] += path("M90 129 L113 148 M119 116 L116 143 M142 114 L137 145 M160 127 L155 153", stroke="#996f54", stroke_width=3)
    art["dedo"] += path("M54 54 L75 54 M67 31 L79 40 M68 78 L79 69", stroke=TEAL, stroke_width=5)
    art["sapato"] = path("M41 153 L62 99 Q82 105 101 92 L132 124 Q146 141 191 144 Q210 147 210 174 L32 174 Q27 163 41 153 Z", "#b97749")
    art["sapato"] += path("M32 172 L210 172 L210 187 L32 187 Z", "#425666") + path("M100 106 L122 111 M108 118 L131 122 M118 132 L141 135", stroke="#fff5df", stroke_width=6)
    art["bota"] = path("M75 38 L149 38 L147 127 Q163 143 186 143 Q210 144 212 178 L56 178 L57 129 L73 121 Z", "#d29948")
    art["bota"] += rect(71, 31, 82, 23, "#a66d39", rx=4) + rect(55, 177, 159, 16, "#425666", rx=4) + path("M76 62 L132 62 L129 125 M60 149 L147 149", stroke="#916038", stroke_width=3)
    fan = path("M120 202 L27 100 Q44 35 120 32 Q196 35 213 100 Z", "#e5c373", stroke_width=4)
    for x, y in [(27,100), (42,72), (65,50), (92,36), (120,32), (148,36), (175,50), (198,72), (213,100)]:
        fan += line(120, 202, x, y, stroke="#946d46", stroke_width=3)
    fan += path("M53 126 Q120 71 187 126", stroke="#c57269", stroke_width=8) + circle(120, 202, 7, "#946d46")
    art["leque"] = fan
    art["casa"], art["telhado"] = house(), house(True)
    art["janela"] = rect(42, 34, 156, 164, "#c99965", rx=3) + rect(55, 47, 130, 138, "#bce1e9", rx=2)
    art["janela"] += path("M120 46 L120 186 M55 114 L185 114", stroke="#8d644a", stroke_width=9) + rect(32, 194, 176, 13, "#946849", rx=2)
    art["janela"] += path("M68 82 L88 61 M142 173 L173 142", stroke="#fffaf0", stroke_width=7)
    art["escada"] = path("M62 212 L103 33 M137 212 L178 33", stroke="#997446", stroke_width=13)
    for y in [62,96,130,164,198]:
        left = 62 + (212-y)*41/179
        art["escada"] += line(round(left), y, round(left+75), y, stroke="#b88b50", stroke_width=11)
    art["chave"] = circle(76, 82, 39, GOLD, stroke_width=5) + circle(76, 82, 18, "#fff9ed", stroke_width=5)
    art["chave"] += path("M99 112 L176 190 L197 168 L179 150 L165 163 L151 148 L164 136 L144 116 L131 128 L114 110 Z", GOLD, stroke_width=5)
    hen = path("M68 123 Q40 136 34 100 Q54 110 67 91 Q54 81 49 62 Q83 66 100 91 Q132 62 165 97 L164 63 Q164 42 184 45 Q200 48 197 68 L195 107 Q199 155 156 176 Q95 195 68 151 Z", "#eee8d8")
    hen += path("M166 48 Q153 31 165 27 Q173 26 176 36 Q178 18 188 24 Q194 28 190 40 Q204 28 208 39 Q212 51 196 55", "#c66a58")
    hen += path("M198 66 L222 77 L197 87 Z", GOLD) + circle(185, 62, 4, INK, stroke="none")
    hen += path("M105 111 Q134 83 158 113 Q151 153 112 148", "#d4cbbb") + path("M116 178 L111 202 M159 177 L164 202 M99 204 L126 204 M151 204 L178 204", stroke="#b88b50", stroke_width=6)
    art["galinha"] = hen
    art["gema"] = path("M34 143 Q31 103 71 88 Q89 53 125 78 Q157 54 187 86 Q217 99 205 139 Q223 172 183 186 Q161 209 122 190 Q73 206 53 180 Q25 176 34 143 Z", "#fffdf5", stroke_width=4)
    art["gema"] += ellipse(121, 139, 41, 36, "#f4b625", stroke="#c68c20", stroke_width=3) + ellipse(107, 126, 11, 7, "#ffe59b", stroke="none")
    art["gema"] += path("M28 59 L46 42 L65 54 L78 39 L90 60 Q69 88 44 79 Z", "#e4d3b7") + path("M173 36 L188 49 L203 37 L220 56 Q211 84 185 79 Z", "#e4d3b7")
    art["rato"] = path("M75 149 Q18 124 24 174 Q31 203 64 197", stroke="#c58e88", stroke_width=8)
    art["rato"] += ellipse(119, 139, 65, 43, "#aaa7a1") + circle(161, 99, 27, "#aaa7a1") + circle(161, 99, 16, "#dbb0a4")
    art["rato"] += path("M141 118 Q167 110 190 130 L214 153 L179 173 Q150 168 136 148", "#aaa7a1") + circle(184, 138, 4, INK, stroke="none") + circle(213, 153, 5, "#ce8d87")
    art["rato"] += path("M193 158 L225 173 M195 151 L229 151 M194 145 L222 132", stroke_width=2)
    art["cenoura"] = path("M90 75 Q120 54 157 89 Q145 153 64 211 Q61 143 90 75 Z", "#e79043", stroke_width=4)
    art["cenoura"] += path("M119 74 Q77 29 94 23 Q116 34 124 61 Q118 15 137 18 Q147 34 132 65 Q162 24 177 33 Q175 57 142 80", "#6e9b58", stroke_width=3)
    art["cenoura"] += path("M88 111 L108 125 M110 150 L125 159 M76 160 L88 168", stroke="#b76b35", stroke_width=3)
    giraffe = path("M79 204 L88 118 L110 112 L119 50 Q144 33 162 56 L158 125 L180 134 L175 204 L157 204 L153 161 L111 158 L101 204 Z", "#e7c16f", stroke_width=4)
    giraffe += path("M119 52 L110 36 L127 39 M157 55 L176 42 L175 62", "#e7c16f") + path("M132 41 L130 24 M150 43 L155 25", stroke="#95723f", stroke_width=7)
    giraffe += circle(130, 22, 5, "#95723f") + circle(156, 23, 5, "#95723f") + path("M159 63 L186 70 L183 91 L156 88", "#e7c16f") + circle(150, 62, 3, INK)
    for x,y,rx,ry in [(134,86,8,8),(142,111,8,11),(112,136,9,8),(138,145,9,8),(165,146,7,7),(93,168,5,10)]:
        giraffe += ellipse(x,y,rx,ry,"#ae7745",stroke="none")
    giraffe += path("M88 126 Q68 130 69 165", stroke="#95723f", stroke_width=5) + ellipse(69,171,5,9,"#95723f")
    art["girafa"] = giraffe
    clown = ellipse(120, 149, 65, 56, "#6b9ba3") + path("M78 166 L65 203 L102 211 L120 183 L137 210 L174 203 L160 166", "#b48bba")
    clown += circle(76, 66, 25, "#ce7851") + circle(164, 66, 25, "#ce7851") + circle(120, 72, 41, "#fff6e5")
    clown += path("M87 40 L120 13 L153 40 Z", GOLD) + circle(120, 12, 7, "#b48bba") + eyes(120,64,30)
    clown += ellipse(96,80,10,7,"#e8aa9c",stroke="none") + ellipse(144,80,10,7,"#e8aa9c",stroke="none") + circle(120,79,11,"#c76c58")
    clown += path("M104 93 Q120 110 136 93",stroke_width=4) + path("M120 121 L94 108 L94 134 Z M120 121 L146 108 L146 134 Z", GOLD)
    for y in [145,165]: clown += circle(120,y,5,GOLD)
    clown += ellipse(74,211,25,10,"#d29d4c") + ellipse(166,211,25,10,"#d29d4c")
    art["palhaco"] = clown
    zebra = path("M57 146 L52 201 L69 201 L80 159 L137 158 L147 201 L164 201 L164 128 L185 105 L202 97 L200 74 L184 62 L181 36 L170 52 L156 32 L158 68 L139 99 L96 97 Q56 97 49 128 Z", "#f7f4e9", stroke_width=4)
    zebra += path("M158 68 L139 99 L145 116 L168 78 Z M82 99 L96 98 L90 145 L76 154 Z M107 99 L121 99 L117 155 L104 156 Z M137 109 L145 121 L141 157 L130 156 Z M163 95 L178 105 L169 116 L157 109 Z M56 165 L72 168 L67 181 L54 178 Z M146 174 L163 173 L164 187 L150 188 Z", INK, stroke="none")
    zebra += circle(184,78,3,INK) + path("M50 115 Q29 122 34 160",stroke_width=5) + ellipse(35,168,5,10,INK)
    art["zebra"] = zebra
    art["bandeira"] = path("M56 214 L56 31", stroke_width=9) + circle(56,27,7,GOLD)
    art["bandeira"] += path("M61 42 Q95 24 132 42 Q171 61 204 39 L204 138 Q170 158 132 139 Q95 120 61 139 Z", TEAL, stroke_width=4)
    art["bandeira"] += path("M120 44 L120 133 Q157 155 204 138 L204 39 Q162 63 120 44", GOLD, stroke="none") + line(36,216,78,216,stroke_width=7)
    art["funil"] = path("M39 62 L201 62 L139 135 L139 192 L104 211 L104 135 Z", "#73afb6", stroke_width=5)
    art["funil"] += ellipse(120,62,81,24,"#d2eaec",stroke_width=5) + path("M70 96 L114 142 L114 177",stroke="#c5e6e8",stroke_width=8)
    art["arvore"] = path("M103 209 L108 116 L88 97 L97 87 L121 109 L143 78 L154 88 L132 126 L139 209 Z", "#9d754d", stroke_width=4)
    for x,y,r in [(78,96,39),(77,58,31),(120,48,40),(160,65,35),(166,104,37),(123,100,42)]:
        art["arvore"] += circle(x,y,r,"#81a36b",stroke="#456944",stroke_width=3)
    art["arvore"] += path("M102 211 Q121 204 142 211",stroke_width=4)
    art["quadro"] = rect(28,43,184,139,"#9c7549",rx=4) + rect(40,55,160,114,"#42665c",rx=2) + rect(22,179,196,12,"#9c7549",rx=2)
    art["quadro"] += path("M57 139 L57 104 L84 83 L111 104 L111 139 Z M51 104 L84 77 L118 104",stroke="#f0edda",stroke_width=3)
    art["quadro"] += circle(164,89,12,"#f0edda",stroke_width=2) + path("M139 145 L184 145 M139 131 L176 131",stroke="#f0edda",stroke_width=3) + rect(143,173,24,6,"#fff8e9",rx=2) + rect(177,166,26,12,"#c1b49a",rx=2)
    bird = path("M73 141 L37 116 L42 157 L83 164", "#8f7458") + ellipse(123,139,62,43,"#aa8f65") + circle(161,103,31,"#aa8f65")
    bird += path("M185 100 L213 110 L186 119 Z", GOLD) + circle(169,98,4,INK,stroke="none") + path("M102 126 Q136 111 151 141 Q123 173 101 148 Z", "#79684f")
    bird += ellipse(150,140,22,19,"#dfc8a2",stroke="none") + path("M106 180 L102 201 M141 180 L145 201 M91 202 L116 202 M134 202 L159 202",stroke="#886a44",stroke_width=4)
    bird += path("M44 208 Q120 197 199 208",stroke="#8f7458",stroke_width=7)
    art["passarinho"] = bird
    art["peixe"] = path("M72 121 L29 83 L29 162 Z", "#c18c5d") + path("M91 92 L114 57 L139 86 M97 156 L121 186 L148 159", "#d1a060")
    art["peixe"] += ellipse(139,124,74,49,"#e5b25e",stroke_width=4) + path("M159 84 Q143 122 159 163",stroke="#ad7f43",stroke_width=3) + circle(184,111,5,INK,stroke="none")
    art["peixe"] += path("M211 131 L199 131 M125 109 L104 131 L127 138",stroke_width=3)
    art["peixe"] += circle(205,67,7,"#d2eaec",stroke="#6b9ba3",stroke_width=2) + circle(220,43,5,"#d2eaec",stroke="#6b9ba3",stroke_width=2)
    cicada = path("M103 87 L70 71 L48 77 M102 111 L64 111 L43 126 M108 135 L78 157 L65 180 M137 87 L170 71 L192 77 M138 111 L176 111 L197 126 M132 135 L162 157 L175 180",stroke="#6e7050",stroke_width=5)
    cicada += ellipse(120,119,22,63,"#8c8d59",stroke_width=3)
    cicada += path("M108 79 Q59 81 53 188 Q83 191 119 140 Z", "#e1e4d2",fill_opacity="0.92",stroke="#6c7a64",stroke_width=3)
    cicada += path("M132 79 Q181 81 187 188 Q157 191 121 140 Z", "#e1e4d2",fill_opacity="0.92",stroke="#6c7a64",stroke_width=3)
    cicada += path("M108 85 L63 174 L113 133 M93 111 L93 145 M79 139 L81 160 M132 85 L177 174 L127 133 M147 111 L147 145 M161 139 L159 160",stroke="#98a58e",stroke_width=2)
    cicada += ellipse(120,70,24,20,"#8c8d59") + circle(98,66,8,"#7d5941") + circle(142,66,8,"#7d5941")
    cicada += path("M108 53 L101 37 M132 53 L139 37",stroke_width=3)
    art["cigarra"] = cicada
    art["fogueira"] = path("M45 185 L184 209 M49 210 L188 184",stroke="#7e5a3c",stroke_width=20)
    art["fogueira"] += path("M77 183 Q43 154 78 105 Q76 137 96 126 Q81 75 123 29 Q118 79 153 94 Q167 80 164 65 Q209 130 170 178 Q140 204 77 183 Z", "#de9250",stroke="#b56e3a",stroke_width=4)
    art["fogueira"] += path("M102 184 Q83 154 116 119 Q114 143 130 148 Q146 124 145 109 Q177 151 150 183 Z", "#f5cd67",stroke="none")
    art["flor"] = path("M119 210 L120 107",stroke="#65925c",stroke_width=9) + path("M117 178 Q73 179 64 143 Q100 138 119 164 M123 157 Q162 157 177 128 Q138 122 122 149", "#80a66b",stroke="#517650",stroke_width=3)
    for angle in range(0,360,60):
        x=120+math.cos(math.radians(angle))*37; y=83+math.sin(math.radians(angle))*37
        art["flor"] += ellipse(round(x,2),round(y,2),25,25,"#bc91b9",stroke="#8d658d",stroke_width=3)
    art["flor"] += circle(120,83,24,GOLD,stroke="#ae833e",stroke_width=3)
    return art


def write_if_needed(destination, content, overwrite):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not destination.exists():
        destination.write_text(content, encoding="utf-8")


def generate_images(overwrite):
    art = drawings()
    assert set(art) == {slug for slug, _ in WORDS}
    for slug, word in WORDS:
        content = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" '
            f'role="img" aria-labelledby="title-{slug}">\n'
            f'<title id="title-{slug}">{html.escape(word)}</title>\n'
            f'<g stroke="{INK}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">\n'
            f'{art[slug]}\n</g>\n</svg>\n'
        )
        write_if_needed(DEST / "images" / f"{slug}.svg", content, overwrite)


async def generate_audio(overwrite):
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit("Use uv run --with edge-tts python scripts/prepare_m28p_tic_assets.py --audio") from exc
    for slug, text in [*WORDS, *INSTRUCTIONS.items()]:
        destination = DEST / "audio" / f"{slug}.mp3"
        if destination.exists() and not overwrite:
            continue
        # An interrupted network write must not become an apparently complete asset.
        temporary = destination.with_suffix(".partial.mp3")
        try:
            await edge_tts.Communicate(text, voice=VOICE, rate=RATE).save(str(temporary))
            if temporary.stat().st_size < 800:
                raise RuntimeError(f"Audio incompleto: {slug}")
            temporary.replace(destination)
            print(f"Áudio: {slug}", flush=True)
        finally:
            temporary.unlink(missing_ok=True)


def generate_manifest():
    assets = []
    for slug, word in WORDS:
        assets.append({"slug": slug, "word": word, "image": f"images/{slug}.svg", "audio": f"audio/{slug}.mp3"})
    recordings = {**dict(WORDS), **INSTRUCTIONS}
    files = {}
    for path_ in sorted(DEST.rglob("*")):
        if path_.suffix in (".svg", ".mp3"):
            files[str(path_.relative_to(DEST))] = {"bytes": path_.stat().st_size, "sha256": hashlib.sha256(path_.read_bytes()).hexdigest()}
    manifest = {
        "version": 1,
        "illustrations": {"author": "PageCraft, ilustrações SVG originais criadas com assistência Codex", "license": "CC0-1.0", "viewBox": "0 0 240 240", "notes": "Sem texto visível nem emoji; os títulos SVG são alternativas acessíveis. A seta no telhado assinala a parte da casa."},
        "audio": {"provider": "Microsoft Edge Read Aloud, através de edge-tts", "voice": VOICE, "locale": "pt-PT", "rate": RATE, "license": "Voz sintética Microsoft; sujeita aos termos do serviço, não abrangida pela licença CC0 dos SVG.", "notes": "Palavras inteiras e instruções. Não usar estes sons para modelar fonemas ou sílabas isoladas. Reprodução só após opção da criança.", "transcripts": recordings},
        "words": assets,
        "instructions": {slug: f"audio/{slug}.mp3" for slug in INSTRUCTIONS},
        "files": files,
    }
    destination = DEST / "manifest.json"
    content = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if not destination.exists() or destination.read_text(encoding="utf-8") != content:
        destination.write_text(content, encoding="utf-8")


def verify_assets(require_audio):
    for slug, _ in WORDS:
        image = ET.parse(DEST / "images" / f"{slug}.svg").getroot()
        assert image.attrib["viewBox"] == "0 0 240 240", slug
        assert image.find("{http://www.w3.org/2000/svg}title") is not None, slug
        # SVGs remain self-contained and contain no rendered text or scripts.
        for node in image.iter():
            assert node.tag.split("}")[-1] not in {"text", "image", "script", "foreignObject"}, slug
            assert all("href" not in key and not key.startswith("on") for key in node.attrib), slug
    if require_audio:
        for slug in [*(slug for slug, _ in WORDS), *INSTRUCTIONS]:
            audio = DEST / "audio" / f"{slug}.mp3"
            assert audio.stat().st_size >= 800, slug
    print(f"Verificação: {len(WORDS)} SVG" + (f", {len(WORDS) + len(INSTRUCTIONS)} MP3" if require_audio else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", action="store_true", help="Gerar os MP3 em falta com voz portuguesa de Portugal.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerar também ficheiros já existentes.")
    parser.add_argument("--verify", action="store_true", help="Verificar SVG locais e os áudios quando usados com --audio.")
    args = parser.parse_args()
    generate_images(args.overwrite)
    if args.audio:
        asyncio.run(generate_audio(args.overwrite))
    generate_manifest()
    if args.verify:
        verify_assets(args.audio)
    print(f"Assets: {DEST}")


if __name__ == "__main__":
    main()
