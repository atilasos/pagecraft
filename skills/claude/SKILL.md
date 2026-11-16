---
name: pagecraft
description: "Cria atividades PageCraft para o 1.º ciclo: páginas HTML interativas e self-contained em pt-PT, com três níveis de diferenciação, apoio contextual e autoavaliação, a partir de tema, ano e duração. Consulta a Sebenta, orquestra as fases Architect, Designer, Builder, Proofreader e Evaluator com o modelo adequado a cada fase (incluindo delegação entre fornecedores no T3 Code), valida com gates determinísticos e QA em browser e deixa um rascunho para aprovação do professor antes de publicar. Usar quando for pedida uma atividade, aula, página ou ficha interativa PageCraft, uma explicação explorável, uma atividade M28P ou maker com componente digital, ou a reparação ou revisão de um rascunho PageCraft."
---

<!-- corpo comum: skills/shared/skill-body.md (sincronizado; não editar aqui) -->
# PageCraft

Produz uma atividade interativa que o professor revê e usa com a turma. O ponto de partida é o tema, o ano e a duração. Produz em `drafts/` o DocSpec, o guia do professor, o HTML self-contained e a evidência de QA. Publica só depois de o professor aprovar.

Repositório: o checkout PageCraft indicado pelo professor, senão `PAGECRAFT_REPO`, senão o destino real desta skill. Nesta máquina é `/home/proteu/pagecraft`. Corre os comandos na raiz do repositório. Os scripts precisam do ambiente `uv` do repositório.

## Invariantes

- **Página:** um HTML único, com CSS e JS inline e sem rede. Leva `lang="pt-PT"` e segue o AO90. O inglês entra só se for pedido e, nesse caso, a versão PT/EN fica completa e com seletor.
- **Aprendizagem:**
  - a criança descobre o constraint pela interação;
  - a avaliação é observável;
  - os três níveis têm a mesma meta e mudam só a via;
  - o primeiro feedback descreve o que a criança fez e faz-lhe uma pergunta;
  - a atividade fecha com algo comunicável.
- **Idade e acessibilidade:** cumprem-se os mínimos de [adaptação à idade](references/age-adaptation.md). Há foco visível e contraste AA, e tudo se faz por teclado. Até ao 2.º ano há «Ouvir».
- **Evidência:** cada fase passa o gate determinístico. A aprovação exige evidência observada no browser. Não declares verificações que não correste.
- **Aprovação:** cada atividade fica em rascunho até o professor a aprovar. A aprovação é sempre por atividade. Push, publicação e envio a terceiros só com pedido próprio. Os commits seguem as regras do repositório.

## Percurso

Lê [o percurso](references/workflow.md) antes de começar. Tem a lista de verificação, os artefactos, os gates, o ciclo de reparação e a publicação. Lê [o encaminhamento](references/routing.md) para decidir quem executa cada fase e com que modelo. As fases correm em contextos separados. O orquestrador coordena, corre `pagecraft_check.py` e decide; não carrega os ficheiros grandes das fases.

| Fase | Contrato | Saída em `drafts/` |
|---|---|---|
| 1 Architect | [agents/pagecraft-architect.md](agents/pagecraft-architect.md) | `<slug>-sources.md`, `<slug>-docspec.json` |
| 2 Designer | [agents/pagecraft-designer.md](agents/pagecraft-designer.md) | `<slug>-design-spec.json` |
| 3 Builder | [agents/pagecraft-builder.md](agents/pagecraft-builder.md) | `<slug>.html` |
| 4 Proofreader | [agents/pagecraft-proofreader.md](agents/pagecraft-proofreader.md) | `<slug>-proofread-vN.json` |
| 5 Evaluator | [agents/pagecraft-evaluator.md](agents/pagecraft-evaluator.md) | `<slug>-evaluation-vN.json` (+ ticket) |

Ao delegar uma fase, passa o contrato, os caminhos e `SKILL_DIR`, como no modelo de brief do encaminhamento. Não passes o conteúdo das referências.

## Referências

Carrega cada referência só quando a fase precisar dela.

- [experiência da atividade](references/activity-experience.md): avanço, respostas e reflexão
- [apoio contextual](references/contextual-support.md): plano de pistas por unidade e verificação
- [integração com realizações](references/learning.md): metadados de registo e a ponte
- [contrato da ponte](references/bridge-contract.md): os acontecimentos `postMessage`
- [schema do DocSpec](references/docspec-schema.md), [exemplos SRTC-A](references/srtc-examples.md) e [índice AE/PA](references/ae-index.md)
- [padrões de interação](references/interaction-patterns.md) e [padrões maker](references/maker-patterns.md)

As identidades em `identities/`, o template em `assets/` e as referências sincronizadas vêm de `server/pipeline/prompts/`, que o Studio usa em runtime. Edita-as só lá e propaga com `bash skills/sync-from-canonical.sh` (ver [CANONICAL.md](CANONICAL.md)).

## Entrega

Entrega ao professor o seguinte:
- a pré-visualização ou, se a atividade já foi aprovada e publicada, o URL público;
- os objetivos e os critérios;
- os ficheiros produzidos;
- os gates e os testes que correram, com o comando e o resultado;
- o modelo usado em cada fase;
- as limitações.

Os alunos usam `https://pagecraft.infantinho.xyz/<CODIGO>`. Nunca lhes entregues o hostname privado do Studio.
<!-- fim do corpo comum -->

## Claude Code

`SKILL_DIR=skills/claude`. As fases correm nos subagentes `pagecraft-architect`, `-designer`, `-builder`, `-proofreader` e `-evaluator`, em `.claude/agents/`. O script de sincronização mantém-nos. Se faltarem, corre `bash skills/claude/install.sh`. O `model:` do frontmatter de cada um já aplica a classe de modelo da fase.

No T3 Code segue o [encaminhamento](references/routing.md):
- as fases Claude correm com `Agent`;
- o Builder corre noutro fornecedor, via `delegate_task`;
- o Evaluator é de família diferente da do Builder.

Para o browser, usa `preview_*` no T3 e `agent-browser-hub` nos outros ambientes.
