# Integração dos roteiros com o novo painel do professor — 15/11/2026

## O que foi integrado

- Os seis commits locais dos **Roteiros da aula** e da aprovação em lote foram reaplicados sobre `origin/main`, que já incluía o PR #69 (biblioteca com pesquisa, filtros, paginação e navegação por `#atividades`/`#registos`).
- A seleção em lote passou a viver dentro da biblioteca paginada. Usa os filtros da biblioteca e conserva a seleção entre páginas e filtros. Não há um segundo conjunto de filtros.
- `PageCraftActivitySelection` continua a servir o ecrã dos roteiros. `wordOf` passou a ser partilhado com a biblioteca.
- «Roteiros da aula» faz parte da navegação de todas as páginas do professor. A ligação «Ver registos deste roteiro» abre `#registos`.

## Revisão independente

`codex exec` (só de leitura) sobre `origin/main..integra/roteiros-painel` → exit 0, cinco achados P2, todos confirmados no código e corrigidos com testes:

1. Publicação em lote sobreposta ao mudar filtros ou páginas durante o pedido.
2. Rascunho publicado individualmente continuava na seleção.
3. Roteiros lentos atrasavam os registos.
4. Falha a carregar os roteiros perdia em silêncio o roteiro pedido no endereço.
5. O resumo do apoio ignorava o filtro de roteiro (agora também no servidor: `lesson` em `/api/learning/support-summary`).

Os dois testes de browser novos falham com o `teacher.js` anterior às correções e passam depois delas.

## Evidência

- `uv run pytest -q --ignore=tests/browser` → 589 aprovados + 1 teste novo do resumo por roteiro. `test_generated_activity_typography` excede os 5 s sob carga da máquina, tanto no `main` anterior como no integrado (≈15 s com limite alargado, aprovado).
- `PAGECRAFT_TEST_CDP=… uv run --with playwright pytest tests/browser` sem `test_m28p_tic.py` → 214 aprovados em 7 min 17 s (Chrome headless descartável).
- `tests/browser/test_teacher_dashboard.py`, `test_lesson_plans.py`, `test_generation_review.py` → 15 aprovados depois da última alteração.
- `test_m28p_tic.py` (milhares de casos dos jogos M28P) não foi corrido até ao fim. Não é tocado por esta integração.
- Studio reiniciado (`systemctl --user restart pagecraft.service`) → `/api/health` ok. `/api/jobs` aceita 60 min e recusa 91.
