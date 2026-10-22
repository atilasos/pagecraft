#!/usr/bin/env bash
# Verificação conjunta. Browser apenas numa sessão já aberta pelo Hub.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run pytest -q --ignore=tests/browser
node --test tests/js/*.test.cjs
bash skills/sync-from-canonical.sh --check
git diff --check

if [[ -n "${PAGECRAFT_TEST_CDP:-}" ]]; then
  uv run --with playwright==1.63.0 pytest tests/browser -q
else
  printf '%s\n' 'Browser omitido: abre uma sessão do Agent Browser Hub e define PAGECRAFT_TEST_CDP para incluir os testes de interface.'
fi
