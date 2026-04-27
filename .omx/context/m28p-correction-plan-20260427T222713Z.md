# Context snapshot — M28P correction plan

## Task statement
Planear a implementação das 5 prioridades de correção das páginas do Método das 28 Palavras contra `docs/m28p.md`.

## Desired outcome
Plano consensual, testável e executável para alinhar as páginas M28P publicadas com os princípios do método antes de implementação.

## Known facts/evidence
- Documento de referência: `docs/m28p.md`.
- Catálogo atual tem 28 páginas principais M28P, 56 variantes e uma página extra `menina-30min`.
- Auditoria anterior encontrou:
  1. 28/28 páginas principais não explicitam suficientemente o risco de uso puramente global/visual.
  2. 9/28 páginas principais precisam reforçar generalização para palavras novas.
  3. 8/28 páginas principais precisam reforçar relação som-letra/grafofonémica.
  4. `leque` está com 40 min; restantes principais com 45 min.
  5. 28 páginas principais não têm `proofread-v1.json` nem `evaluation-v1.json` publicados.
- Variantes 56 parecem alinhadas nesta auditoria: 30 min, palavra-alvo, sílabas, frases/texto, generalização.

## Constraints
- Não implementar nesta fase; apenas planear.
- Preservar slugs e catálogo salvo decisão explícita em contrário.
- Usar pt-PT AO90.
- HTML deve permanecer self-contained e offline.
- Seguir `docs/m28p.md`: palavra significativa + imagem/contexto, reconhecimento global, segmentação silábica, relações som-letra, recombinação, frases/textos, verificação e generalização; evitar memorização visual isolada.
- Manter fluxo PageCraft/QA: DocSpec/design/HTML/teacher/proofread/evaluation.

## Unknowns/open questions
- Se a página extra `menina-30min` deve ficar como exceção/alternativa ou ser integrada no mesmo padrão de auditoria.
- Se todas as principais devem ser exatamente 45 min ou se pode haver duração variável; auditoria sugere uniformizar `leque` para 45 min.
- Se a implementação deve regenerar páginas completas ou aplicar patch mínimo aos artefactos existentes.

## Likely codebase touchpoints
- `docs/m28p.md`
- `activities/{word}/docspec.json`
- `activities/{word}/teacher.md`
- `activities/{word}/index.html`
- `activities/{word}/meta.json`
- `activities/{word}/proofread-v1.json`
- `activities/{word}/evaluation-v1.json`
- `catalog.json`
- possível script de auditoria/patch em `scripts/` ou `outputs/lessons/`
