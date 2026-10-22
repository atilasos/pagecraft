"""Offline font packaging shared by generated lessons and checked-in examples."""
from __future__ import annotations

import base64
from pathlib import Path
import re

FONT_DIR = Path(__file__).resolve().parents[1] / "assets/fonts/didact-gothic"
FONT_STACK = '"Century Gothic", "Didact Gothic", "URW Gothic", "Avant Garde", sans-serif'
START = "/* BEGIN BUNDLED DIDACT GOTHIC */"
END = "/* END BUNDLED DIDACT GOTHIC */"


def bundled_font_css() -> str:
    encoded = base64.b64encode((FONT_DIR / "DidactGothic-Regular.woff2").read_bytes()).decode("ascii")
    license_text = (FONT_DIR / "OFL.txt").read_text().strip()
    return f'''{START}
/* {license_text} */
@font-face {{
  font-family: "Didact Gothic";
  src: url("data:font/woff2;base64,{encoded}") format("woff2");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}}
{END}'''


def embed_activity_typography(html: str) -> str:
    # Replace our own block on repairs; the model need not preserve font bytes.
    html = re.sub(r'<style\s+id="pagecraft-typography">.*?</style>\s*', "", html, flags=re.DOTALL | re.IGNORECASE)
    style = f'''<style id="pagecraft-typography">
{bundled_font_css()}
body, h1, h2, h3, h4, h5, h6, button, input, select, textarea {{
  font-family: {FONT_STACK} !important;
}}
</style>
'''
    head_end = re.search(r"</head\s*>", html, flags=re.IGNORECASE)
    if head_end:
        return html[:head_end.start()] + style + html[head_end.start():]
    return style + html
