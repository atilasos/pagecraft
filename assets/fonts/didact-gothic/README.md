# Didact Gothic

Alternative bundled with PageCraft when Century Gothic is not installed on the reader's device. Century Gothic remains the first CSS family. The fallback is embedded as a data URL so standalone activities retain their offline behavior and the sandbox's `font-src data:` policy.

Original font and SIL Open Font License: https://github.com/google/fonts/tree/main/ofl/didactgothic

`DidactGothic-Regular.ttf` is the original font. `DidactGothic-Regular.woff2` contains the same glyphs in WOFF2 format, converted with FontTools, without subsetting. The regular face also supplies browser synthesized bold. Both files retain the font metadata and license.

To regenerate WOFF2:

```sh
uv run --with fonttools --with brotli python - <<'PY'
from fontTools.ttLib import TTFont
from pathlib import Path
path = Path('assets/fonts/didact-gothic/DidactGothic-Regular.ttf')
font = TTFont(path)
font.flavor = 'woff2'
font.save(path.with_suffix('.woff2'))
PY
python3 scripts/embed_gothic_font.py
```

`server/typography.py` packages the actual WOFF2 and license for every pipeline build and repair before AI review and publication. It also supplies the CSS block used by the script, so providers do not need filesystem access to font assets. Model content is validated before packaging to keep the minimum-content check independent of the font payload.

The script updates marked CSS blocks in the Studio stylesheet and the standalone Fractions draft. It includes the complete font license in each artifact. Re-running it with unchanged assets produces identical files.
