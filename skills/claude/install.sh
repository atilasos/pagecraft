#!/usr/bin/env bash
# Instala a skill PageCraft para Claude Code por links (o repositório é a fonte).
# Uso:
#   bash skills/claude/install.sh              # projeto: .claude/skills/pagecraft + .claude/agents
#   bash skills/claude/install.sh --user       # utilizador: ~/.claude/skills/pagecraft + ~/.claude/agents
#   bash skills/claude/install.sh --uninstall [--user]
# O link de projeto (.claude/skills/pagecraft -> ../../skills/claude) é versionado,
# pelo que qualquer checkout ou worktree deste repositório já tem a skill.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
AGENTS=(pagecraft-architect pagecraft-designer pagecraft-builder pagecraft-proofreader pagecraft-evaluator)

mode="install"; scope="project"
for arg in "$@"; do
  case "$arg" in
    --user) scope="user" ;;
    --project) scope="project" ;;
    --uninstall) mode="uninstall" ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "Opção desconhecida: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$scope" == "user" ]]; then
  ROOT="$HOME/.claude"; SKILL_TARGET="$SCRIPT_DIR"; AGENT_TARGET="$SCRIPT_DIR/agents"
else
  ROOT="$REPO_ROOT/.claude"; SKILL_TARGET="../../skills/claude"; AGENT_TARGET=""
fi
SKILL_DEST="$ROOT/skills/pagecraft"

if [[ "$mode" == "uninstall" ]]; then
  [[ -L "$SKILL_DEST" ]] && rm "$SKILL_DEST"
  if [[ "$scope" == "user" ]]; then
    for a in "${AGENTS[@]}"; do [[ -L "$ROOT/agents/$a.md" ]] && rm "$ROOT/agents/$a.md"; done
  fi
  echo "Removido de $ROOT (só links; ficheiros reais preservados)."
  exit 0
fi

mkdir -p "$ROOT/skills" "$ROOT/agents"
if [[ -e "$SKILL_DEST" && ! -L "$SKILL_DEST" ]]; then
  echo "Existe uma cópia antiga em $SKILL_DEST; remove-a ou move-a antes de instalar o link." >&2
  exit 1
fi
ln -sfn "$SKILL_TARGET" "$SKILL_DEST"

if [[ "$scope" == "user" ]]; then
  for a in "${AGENTS[@]}"; do ln -sfn "$AGENT_TARGET/$a.md" "$ROOT/agents/$a.md"; done
else
  # os subagentes do projeto são cópias versionadas mantidas pela sincronização
  bash "$REPO_ROOT/skills/sync-from-canonical.sh" >/dev/null
fi

echo "skill  -> $SKILL_DEST -> $(readlink "$SKILL_DEST")"
echo "agents -> $ROOT/agents/{$(IFS=,; echo "${AGENTS[*]}")}.md"
echo "Abre uma nova sessão (ou recarrega as skills) e invoca /pagecraft."
