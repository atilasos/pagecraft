"""Embed the bundled fallback in the Studio CSS and standalone fraction lesson."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.typography import START, END, bundled_font_css, embed_activity_typography


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activity', type=Path, help='Package an individual generated HTML draft before review')
    args = parser.parse_args()
    if args.activity:
        args.activity.write_text(embed_activity_typography(args.activity.read_text(encoding='utf-8')), encoding='utf-8')
        return
    block = bundled_font_css()
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
