#!/usr/bin/env bash
# PageCraft skill installer for Claude Code.
# Usage:
#   bash skills/claude/install.sh              # project install (./.claude/)
#   bash skills/claude/install.sh --user       # user install (~/.claude/)
#   bash skills/claude/install.sh --uninstall  # remove from ./.claude/
#   bash skills/claude/install.sh --uninstall --user

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
SKILL_NAME="pagecraft"

mode="install"
scope="project"

for arg in "$@"; do
  case "$arg" in
    --user)       scope="user" ;;
    --project)    scope="project" ;;
    --uninstall)  mode="uninstall" ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "$scope" == "user" ]]; then
  CLAUDE_ROOT="$HOME/.claude"
else
  CLAUDE_ROOT="$(pwd)/.claude"
fi

SKILL_DEST="$CLAUDE_ROOT/skills/$SKILL_NAME"
AGENTS_DEST="$CLAUDE_ROOT/agents"

agents=(
  pagecraft-architect.md
  pagecraft-designer.md
  pagecraft-builder.md
  pagecraft-proofreader.md
  pagecraft-evaluator.md
)

if [[ "$mode" == "uninstall" ]]; then
  echo "Removing PageCraft skill from $CLAUDE_ROOT ..."
  rm -rf "$SKILL_DEST"
  for f in "${agents[@]}"; do
    rm -f "$AGENTS_DEST/$f"
  done
  echo "Done."
  exit 0
fi

echo "Installing PageCraft skill ($scope scope) into $CLAUDE_ROOT ..."

# Garantir que o conteúdo partilhado deste harness está alinhado com o canónico
# em skills/openclaw/. Não-op se já estiver alinhado.
SYNC_SCRIPT="$SCRIPT_DIR/../sync-from-canonical.sh"
if [[ -f "$SYNC_SCRIPT" ]]; then
  bash "$SYNC_SCRIPT" >/dev/null || {
    echo "warn: falhou sync com canónico; a continuar com conteúdo local" >&2
  }
fi

mkdir -p "$SKILL_DEST"
mkdir -p "$AGENTS_DEST"

# Copy skill content (everything except agents/ and install.sh — agents go to AGENTS_DEST).
cp "$SCRIPT_DIR/SKILL.md"   "$SKILL_DEST/SKILL.md"
cp "$SCRIPT_DIR/README.md"  "$SKILL_DEST/README.md" 2>/dev/null || true

for sub in identities references assets scripts; do
  if [[ -d "$SCRIPT_DIR/$sub" ]]; then
    rm -rf "$SKILL_DEST/$sub"
    cp -R "$SCRIPT_DIR/$sub" "$SKILL_DEST/$sub"
  fi
done

# Copy subagents.
for f in "${agents[@]}"; do
  if [[ -f "$SCRIPT_DIR/agents/$f" ]]; then
    cp "$SCRIPT_DIR/agents/$f" "$AGENTS_DEST/$f"
  else
    echo "warn: $SCRIPT_DIR/agents/$f not found" >&2
  fi
done

echo
echo "Installed:"
echo "  skill   -> $SKILL_DEST/SKILL.md"
echo "  agents  -> $AGENTS_DEST/{${agents[*]}}"
echo
echo "Next steps:"
echo "  1. Restart Claude Code (or reload skills) so the new skill is detected."
echo "  2. Inside a PageCraft repo, invoke the skill:"
echo "       /pagecraft cria uma página de 30 minutos para o 3.º ano sobre verbos"
echo "  3. (Optional) Set PAGECRAFT_VAULT if your pedagogical vault is not at ~/.openclaw/workspace/vault."
