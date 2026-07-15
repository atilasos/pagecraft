#!/usr/bin/env bash
# Sincroniza conteúdo partilhado a partir das fontes canónicas para
# skills/claude/ e skills/codex/. Mantém intactos os ficheiros específicos
# de cada harness: SKILL.md, agents/, install.sh, README.md.
#
# Fontes canónicas:
#   - identities/references/template: server/pipeline/prompts/ (usadas pelo
#     PageCraft Studio em runtime — editar lá, sincronizar para os harnesses)
#   - scripts: skills/shared/scripts/
#
# Usage:
#   bash skills/sync-from-canonical.sh           # sync com diff
#   bash skills/sync-from-canonical.sh --check   # falha se houver drift

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PROMPTS="$REPO_ROOT/server/pipeline/prompts"
SHARED_SCRIPTS="$SCRIPT_DIR/shared/scripts"
TARGETS=("$SCRIPT_DIR/claude" "$SCRIPT_DIR/codex")

# pares "caminho canónico|destino relativo ao harness"
MAPPINGS=(
  "$PROMPTS/template-base.html|assets/template-base.html"
  "$PROMPTS/architect.md|identities/architect.md"
  "$PROMPTS/designer.md|identities/designer.md"
  "$PROMPTS/builder.md|identities/builder.md"
  "$PROMPTS/proofreader.md|identities/proofreader.md"
  "$PROMPTS/evaluator.md|identities/evaluator.md"
  "$PROMPTS/references/ae-index.md|references/ae-index.md"
  "$PROMPTS/references/bridge-contract.md|references/bridge-contract.md"
  "$PROMPTS/references/age-adaptation.md|references/age-adaptation.md"
  "$PROMPTS/references/docspec-schema.md|references/docspec-schema.md"
  "$PROMPTS/references/interaction-patterns.md|references/interaction-patterns.md"
  "$PROMPTS/references/maker-patterns.md|references/maker-patterns.md"
  "$PROMPTS/references/srtc-examples.md|references/srtc-examples.md"
  "$SHARED_SCRIPTS/build_markdown.py|scripts/build_markdown.py"
  "$SHARED_SCRIPTS/build_prompt.py|scripts/build_prompt.py"
  "$SHARED_SCRIPTS/pagecraft.py|scripts/pagecraft.py"
  "$SHARED_SCRIPTS/publish_to_catalog.py|scripts/publish_to_catalog.py"
)

mode="sync"
for arg in "$@"; do
  case "$arg" in
    --check) mode="check" ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

drift=0
for target in "${TARGETS[@]}"; do
  name="$(basename "$target")"
  for pair in "${MAPPINGS[@]}"; do
    src="${pair%%|*}"
    rel="${pair##*|}"
    dst="$target/$rel"
    [[ -f "$src" ]] || { echo "missing canonical: $src" >&2; exit 1; }
    if ! cmp -s "$src" "$dst" 2>/dev/null; then
      if [[ "$mode" == "check" ]]; then
        echo "drift: $name/$rel"
        drift=1
      else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "synced: $name/$rel"
      fi
    fi
  done
done

if [[ "$mode" == "check" ]]; then
  [[ $drift -eq 0 ]] && echo "ok: no drift from canonical" || exit 1
else
  echo "done."
fi
