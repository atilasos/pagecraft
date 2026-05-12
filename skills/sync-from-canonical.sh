#!/usr/bin/env bash
# Sincroniza conteúdo partilhado a partir de skills/openclaw/ (canónico) para
# skills/claude/ e skills/codex/. Mantém intactos os ficheiros específicos
# de cada harness: SKILL.md, agents/, install.sh, README.md.
#
# Usage:
#   bash skills/sync-from-canonical.sh           # sync com diff
#   bash skills/sync-from-canonical.sh --check   # falha se houver drift

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CANONICAL="$SCRIPT_DIR/openclaw"
TARGETS=("$SCRIPT_DIR/claude" "$SCRIPT_DIR/codex")

SHARED=(
  "assets/template-base.html"
  "identities/architect.md"
  "identities/designer.md"
  "identities/builder.md"
  "identities/proofreader.md"
  "identities/evaluator.md"
  "references/ae-index.md"
  "references/age-adaptation.md"
  "references/docspec-schema.md"
  "references/interaction-patterns.md"
  "references/maker-patterns.md"
  "references/srtc-examples.md"
  "scripts/build_markdown.py"
  "scripts/build_prompt.py"
  "scripts/pagecraft.py"
  "scripts/publish_to_catalog.py"
)

mode="sync"
for arg in "$@"; do
  case "$arg" in
    --check) mode="check" ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

drift=0
for target in "${TARGETS[@]}"; do
  name="$(basename "$target")"
  for f in "${SHARED[@]}"; do
    src="$CANONICAL/$f"
    dst="$target/$f"
    [[ -f "$src" ]] || { echo "missing canonical: $src" >&2; exit 1; }
    if ! cmp -s "$src" "$dst" 2>/dev/null; then
      if [[ "$mode" == "check" ]]; then
        echo "drift: $name/$f"
        drift=1
      else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "synced: $name/$f"
      fi
    fi
  done
done

if [[ "$mode" == "check" ]]; then
  [[ $drift -eq 0 ]] && echo "ok: no drift from canonical" || exit 1
else
  echo "done."
fi
