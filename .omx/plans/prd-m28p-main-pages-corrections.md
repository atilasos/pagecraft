# PRD — Correção das páginas principais M28P

## Objetivo
Alinhar as 28 páginas principais do Método das 28 Palavras com `docs/m28p.md`, corrigindo as 5 prioridades identificadas: anti-memorização visual, generalização, grafofonémica/som-letra, duração de `leque`, e relatórios QA (`proofread`/`evaluation`).

## Âmbito
Inclui apenas as 28 páginas principais canónicas listadas em `docs/m28p.md`.

Exclui:
- variantes `*-cacador-silabas`;
- variantes `*-frases-vivas`;
- `menina-30min`, salvo auditoria separada futura.

## Requisitos funcionais
1. Criar `scripts/audit_m28p_alignment.py`.
2. Criar `scripts/repair_m28p_main_pages.py`.
3. Produzir `.omx/reports/m28p-audit.json` e `.omx/reports/m28p-audit.md`.
4. Produzir `.omx/reports/m28p-repair-manifest.json` com slugs, evidência antes/depois e ações.
5. Corrigir as 28 páginas principais para evidenciar:
   - contexto/imagem significativa;
   - reconhecimento global como entrada;
   - leitura/escrita da palavra;
   - segmentação silábica;
   - recombinação;
   - relação som-letra/grafofonémica;
   - leitura/escrita de palavras novas;
   - frases/textos;
   - verificação rápida;
   - princípio anti-uso puramente visual/global.
6. Corrigir palavras-alvo de generalização:
   - `menino`, `uva`, `dedo`, `casa`, `telhado`, `escada`, `galinha`, `ovo`, `rato`.
7. Corrigir palavras-alvo grafofonémicas:
   - `bota`, `zebra`, `bandeira`, `funil`, `quadro`, `passarinho`, `fogueira`, `flor`.
8. Corrigir `leque` de 40 para 45 min em catálogo, meta, DocSpec, soma de unidades, teacher guide e HTML visível.
9. Remover dependências externas das 28 páginas principais se existirem.
10. Corrigir tokens pt-PT/AO90 não permitidos, salvo allowlist justificada.
11. Criar 28 `proofread-v1.json` com evidência citada.
12. Criar 28 `evaluation-v1.json` após QA real, com evidência citada.

## Critérios de aceitação
- 28/28 páginas principais passam todos os checks de `scripts/audit_m28p_alignment.py`.
- `leque` mostra 45 min consistentemente em todos os artefactos.
- Existem 28 relatórios `proofread-v1.json` e 28 `evaluation-v1.json` com `pass: true` e evidência concreta.
- HTML das 28 páginas é offline/self-contained, sem CDN/imports remotos.
- Variantes e `menina-30min` não são alterados; provar com `git diff --name-only`.
- `catalog.json` mantém contagem estável, salvo alterações de metadados/duração previstas.

## Decisão ADR
Escolha: pipeline determinístico audit → repair → validate.

Drivers:
- rastreabilidade pedagógica;
- repetibilidade;
- baixo risco em alterações bulk;
- QA baseada em evidência.

Alternativas rejeitadas:
- Inserir bloco genérico em todas as páginas | rápido, mas superficial e pedagogicamente fraco.
- Regenerar 28 páginas inteiras | mais uniforme, mas risco alto de regressão.
- Editar manualmente página a página sem script/manifest | nuance maior, mas pouco reprodutível.

Consequências:
- Mais scripts e relatórios, mas futura manutenção fica auditável.
- O executor deve resistir a “passar por tokens”: cada relatório precisa de evidência antes/depois.

## Staffing recomendado
Preferir `$ralph`/execução sequencial solo. Escrita paralela por equipa não é recomendada porque os scripts tocarão em muitas páginas e `catalog.json`.

Se usar `$team`, limitar a equipa a:
- um lane read-only para rever o relatório de auditoria;
- um lane executor único para patches;
- um lane verifier para QA após patches.
