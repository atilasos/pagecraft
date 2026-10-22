# Avaliação do PageCraft com dez agentes

## Base e método

Esta ronda começa em `4c6ba90`, depois das melhorias dos PRs #51 a #55.
O objetivo é avaliar o funcionamento, confrontar dez leituras independentes e
implementar as propostas com benefício pedagógico e evidência técnica.

As alterações locais preexistentes em `catalog.json` e nas atividades
`spike-prime-primeiros-movimentos` e `unidades-dezenas-2ano-30min` ficam fora
desta ronda. A avaliação e as implementações usam worktrees separados.

As dez frentes são autonomia e PIT; avaliação cooperada e comunicação;
diferenciação e inclusão; catálogo e descoberta; resiliência do trabalho;
feedback formativo e IA; pipeline e qualidade pedagógica; segurança e
privacidade; experiência do professor; criatividade didática e interação.

Cada agente deve ler código e páginas integrais da Sebenta e apresentar
propostas com problema, evidência, comportamento esperado, risco, esforço e
verificação. A seleção considera benefício para a criança ou professor,
gravidade do problema demonstrado, possibilidade de testar e independência
dos restantes trabalhos. Uma proposta criativa precisa de servir uma ação
pedagógica concreta.

## Fundamentação pedagógica

Consultadas pela API local da Sebenta em 22 de outubro de 2026:

- [[Avaliação Formativa]], `20_Wiki/Avaliação Formativa.md`. A informação
  recolhida serve a regulação quando permite ajustar o trabalho; os critérios
  precisam de ser apropriados pela criança.
- [[Avaliação Cooperada]], `20_Wiki/Avaliação Cooperada.md`. A participação
  na avaliação pressupõe participação na planificação. Os instrumentos
  apoiam decisões partilhadas e podem ser revistos pelo grupo.
- [[Diferenciação Pedagógica]], `20_Wiki/Diferenciação Pedagógica.md`.
  Variar apoios e organização conserva metas comuns e evita agrupamentos
  fixos que rotulem crianças.

As três páginas estão em estado `review`, com confiança `medium`. Estas são
sínteses da wiki. As decisões de produto desta ronda são propostas derivadas,
sem alegação de eficácia demonstrada em sala nem de conformidade legal.

## Verificação inicial

- `uv run pytest -q --ignore=tests/browser`: 337 testes aprovados.
- `node --test tests/js/activity_support.test.cjs`: 21 testes aprovados.
- `bash skills/sync-from-canonical.sh --check`: sem divergências.

Os testes usam dados descartáveis. O browser pertence ao Agent Browser Hub;
as sessões e registos reais de produção ficam fora dos ensaios.
