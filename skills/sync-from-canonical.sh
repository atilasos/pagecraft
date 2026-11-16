#!/usr/bin/env bash
# Sincroniza conteúdo partilhado a partir das fontes canónicas para
# skills/claude/ e skills/codex/, e os contratos de fase para .claude/agents/
# (subagentes do projeto). Mantém intactos os ficheiros específicos de cada
# harness: SKILL.md, install.*, README.md, CANONICAL.md, references/runtime.md.
#
# Fontes canónicas:
#   - identities/references/template: server/pipeline/prompts/ (usadas pelo
#     PageCraft Studio em runtime — editar lá, sincronizar para os harnesses)
#   - scripts, contratos de fase (agents/) e referências do percurso:
#     skills/shared/{scripts,agents,references}/
#
# Usage:
#   bash skills/sync-from-canonical.sh           # sync com diff
#   bash skills/sync-from-canonical.sh --check   # falha se houver drift

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PROMPTS="$REPO_ROOT/server/pipeline/prompts"
SHARED="$SCRIPT_DIR/shared"
SHARED_SCRIPTS="$SHARED/scripts"
TARGETS=("$SCRIPT_DIR/claude" "$SCRIPT_DIR/codex")

# pares "caminho canónico|destino relativo ao harness"
MAPPINGS=(
  "$PROMPTS/template-base.html|assets/template-base.html"
  "$PROMPTS/activity-support.js|assets/activity-support.js"
  "$REPO_ROOT/server/static/student/support-modal.js|assets/support-modal.js"
  "$PROMPTS/activity-support.css|assets/activity-support.css"
  "$PROMPTS/references/contextual-support.md|references/contextual-support.md"
  "$PROMPTS/architect.md|identities/architect.md"
  "$PROMPTS/designer.md|identities/designer.md"
  "$PROMPTS/builder.md|identities/builder.md"
  "$PROMPTS/proofreader.md|identities/proofreader.md"
  "$PROMPTS/evaluator.md|identities/evaluator.md"
  "$PROMPTS/references/ae-index.md|references/ae-index.md"
  "$PROMPTS/references/bridge-contract.md|references/bridge-contract.md"
  "$PROMPTS/references/age-adaptation.md|references/age-adaptation.md"
  "$PROMPTS/references/activity-experience.md|references/activity-experience.md"
  "$PROMPTS/references/docspec-schema.md|references/docspec-schema.md"
  "$PROMPTS/references/interaction-patterns.md|references/interaction-patterns.md"
  "$PROMPTS/references/maker-patterns.md|references/maker-patterns.md"
  "$PROMPTS/references/srtc-examples.md|references/srtc-examples.md"
  "$SHARED_SCRIPTS/build_markdown.py|scripts/build_markdown.py"
  "$SHARED_SCRIPTS/build_prompt.py|scripts/build_prompt.py"
  "$SHARED_SCRIPTS/pagecraft.py|scripts/pagecraft.py"
  "$SHARED_SCRIPTS/publish_to_catalog.py|scripts/publish_to_catalog.py"
  "$SHARED_SCRIPTS/pagecraft_check.py|scripts/pagecraft_check.py"
  "$SHARED_SCRIPTS/activity.py|scripts/activity.py"
  "$SHARED/references/workflow.md|references/workflow.md"
  "$SHARED/references/routing.md|references/routing.md"
  "$SHARED/references/learning.md|references/learning.md"
)
AGENTS=(pagecraft-architect pagecraft-designer pagecraft-builder pagecraft-proofreader pagecraft-evaluator)
for agent in "${AGENTS[@]}"; do
  MAPPINGS+=("$SHARED/agents/$agent.md|agents/$agent.md")
done

mode="sync"
for arg in "$@"; do
  case "$arg" in
    --check) mode="check" ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

sync_pair() {
  local src="$1" dst="$2" label="$3"
  [[ -f "$src" ]] || { echo "missing canonical: $src" >&2; exit 1; }
  if ! cmp -s "$src" "$dst" 2>/dev/null; then
    if [[ "$mode" == "check" ]]; then
      echo "drift: $label"
      drift=1
    else
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
      echo "synced: $label"
    fi
  fi
}

drift=0
# subagentes do projeto (.claude/agents) carregados pelo Claude Code neste repo
for agent in "${AGENTS[@]}"; do
  sync_pair "$SHARED/agents/$agent.md" "$REPO_ROOT/.claude/agents/$agent.md" ".claude/agents/$agent.md"
done
for target in "${TARGETS[@]}"; do
  name="$(basename "$target")"
  for pair in "${MAPPINGS[@]}"; do
    src="${pair%%|*}"
    rel="${pair##*|}"
    sync_pair "$src" "$target/$rel" "$name/$rel"
  done
done

# corpo comum das SKILL.md: o bloco entre marcadores vem de skills/shared/skill-body.md
for target in "${TARGETS[@]}"; do
  skill="$target/SKILL.md"
  expected="$(python3 - "$skill" "$SHARED/skill-body.md" <<'PY'
import sys
skill, body = (open(p, encoding="utf-8").read() for p in sys.argv[1:3])
begin, end = "<!-- corpo comum:", "<!-- fim do corpo comum -->"
i = skill.index(begin); i = skill.index("\n", i) + 1; j = skill.index(end)
sys.stdout.write(skill[:i] + body + skill[j:])
PY
)"
  if [[ "$expected" != "$(cat "$skill")" ]]; then
    if [[ "$mode" == "check" ]]; then
      echo "drift: $(basename "$target")/SKILL.md (corpo comum)"; drift=1
    else
      printf '%s\n' "$expected" > "$skill"; echo "synced: $(basename "$target")/SKILL.md (corpo comum)"
    fi
  fi
done

if [[ "$mode" == "check" ]]; then
  [[ $drift -eq 0 ]] && echo "ok: no drift from canonical" || exit 1
else
  echo "done."
fi
