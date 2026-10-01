"""Embed the bundled fallback in the Studio CSS and standalone fraction lesson."""
from pathlib import Path
import base64

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / 'assets/fonts/didact-gothic'
START = '/* BEGIN BUNDLED DIDACT GOTHIC */'
END = '/* END BUNDLED DIDACT GOTHIC */'


def main():
    encoded = base64.b64encode((FONT / 'DidactGothic-Regular.woff2').read_bytes()).decode('ascii')
    license_text = (FONT / 'OFL.txt').read_text().strip()
    block = f'''{START}
/* {license_text} */
@font-face {{
  font-family: "Didact Gothic";
  src: url("data:font/woff2;base64,{encoded}") format("woff2");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}}
{END}'''
    for relative in ['server/static/studio.css', 'drafts/fracoes-banda-desenhada-2ano.html']:
        path = ROOT / relative
        content = path.read_text()
        if START in content:
            first = content.index(START)
            last = content.index(END, first) + len(END)
            content = content[:first] + block + content[last:]
        elif path.suffix == '.html':
            content = content.replace('<style>', '<style>\n' + block, 1)
        else:
            content = block + '\n\n' + content
        path.write_text(content)


if __name__ == '__main__':
    main()
