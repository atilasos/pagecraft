# Fontes de Duas pontes, duas vistas

Consulta em 22/10/2026. Rascunho privado, slug `pontes-duas-vistas`, 3.º/4.º ano, 15 minutos, PT. Fase Architect. Não houve registo nem publicação.

## Pesquisa e leitura

A API da Sebenta respondeu `status: ok`. Foram feitas pesquisas `search --kind wiki` por `TIC no Ensino Básico`, `pontes` e `avaliação cooperada`. A pesquisa por pontes não encontrou uma página sobre engenharia de pontes. Foram lidas pela API as páginas integrais abaixo. As páginas são sínteses em estado `review`, confiança `medium`; a atividade não as apresenta como prova da eficácia da interface.

- `20_Wiki/TIC no Ensino Básico.md`, atualizada em 08/09/2026. Situa as TIC do 1.º ciclo na integração transversal e descreve a necessidade de progressão escolhida pelo professor. O contexto docente inclui turmas de 3.º e 4.º ano e articulação com titulares. A proposta de revisão das OC de março de 2026 surge como proposta na wiki, sem ser usada aqui como requisito curricular.
- `20_Wiki/Trabalho de Projeto.md`, atualizada em 09/07/2026. Fundamenta perguntas investigáveis, antecipação de hipóteses, alteração de um fator de cada vez, comunicação e registos proporcionais ao grupo. Esta microatividade dirigida de 15 minutos não é apresentada como projeto completo nem como substituto da negociação da turma.
- `20_Wiki/Circuitos de Comunicação.md`, atualizada em 08/07/2026. Fundamenta apresentar evidências a destinatários que perguntam, criticam e propõem melhorias. A própria página assinala fontes por verificar e limites de cobertura.
- `20_Wiki/Avaliação Cooperada.md`, atualizada em 09/07/2026. Distingue avaliar de classificar e liga a participação na avaliação à participação na planificação. A revisão por um colega e a reflexão desta atividade apoiam a regulação; não comprovam por si uma organização integral de avaliação cooperada.

Foi lida integralmente também a fonte original extraída, através de `source`:

- `documentos-oficiais/aprendizagens-essenciais/tic-1-ano-1-ciclo.md`, fonte DGE `oc_1_tic_1.pdf`. Apesar do nome/metadados locais, o corpo é explicitamente **Orientações Curriculares de TIC para todo o 1.º ciclo**, sem descritor por ano. Páginas 2–3: progressão definida pelo docente e investigação/colaboração. Página 7: comunicar com ferramentas digitais para expressar ideias, explicar ou argumentar. Página 8: colaborar para criar um produto digital e apresentar/partilhar produtos. O alinhamento deste rascunho é uma operacionalização desses descritores, não uma AE específica de 3.º ou 4.º ano. A extração foi lida; não foi feita nesta fase uma nova verificação da tabela DGE nem da homologação de revisões em 22/10/2026.

As fontes brutas pedagógicas citadas pelas páginas da wiki, como de Vecchi/Giordan e Santana, não foram relidas nesta fase. As afirmações acima atribuem-se às sínteses consultadas, sem fingir consulta dos originais.

## Fontes canónicas do checkout

- `AGENTS.md`, `CONTEXT.md`, `PRODUCT.md`, `DESIGN.md`.
- `docs/adr/0002-nomes-de-ponte-congelados.md`, `0003-catalogo-e-indice-derivado.md`, `0004-acesso-com-negacao-por-omissao.md`, `0005-realizacoes-e-professor-remoto.md`, `0007-retoma-do-trabalho-por-grupo.md`.
- `skills/codex/SKILL.md`, `skills/codex/agents/pagecraft-architect.md`, `skills/codex/identities/architect.md`.
- `server/pipeline/prompts/references/activity-experience.md`, `age-adaptation.md`, `contextual-support.md`, `bridge-contract.md` e `server/pipeline/schemas/docspec.schema.json`.
- `activities/tinkercad-pontes-3e4/index.html`, funções `outcome` e `draw`, e `teacher.md`. A vista superior ignora as alturas. O modelo atravessa quando há tabuleiro, apoios nas margens e alturas iguais. Trata-se de uma regra didática, não de uma simulação de resistência nem de segurança de pontes reais. Nenhum destes ficheiros foi alterado.
- `/tmp/pagecraft-audit-10.md`, proposta 1, e `/tmp/pagecraft-delegate/SKILL.md`, brief e fronteira de trabalho.

## Proposta desta atividade

A comparação fixa A 2/2 e B 2/1, as previsões separadas antes dos resultados, os quatro momentos de trabalho, o confronto de uma hipótese e a procura de um contraexemplo são decisões de arquitetura desta atividade. A altura do apoio direito é a única variável manipulável. Os dois ensaios guardados preservam as previsões e o resultado para confronto; os testes do colega não acrescentam uma terceira ficha ao par A/B.

O benefício esperado é tornar observável a diferença entre antecipar, testar e explicar. Não foi ainda observado com crianças. A revisão do professor deve decidir a adequação à turma, o apoio à expressão oral e o tempo real. O HTML e a usabilidade pertencem às fases seguintes; este documento não declara testes de browser.

## Comandos reproduzíveis da consulta

```sh
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py health
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py search 'TIC no Ensino Básico' --kind wiki --limit 3
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py search pontes --kind wiki --limit 4
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py search 'avaliação cooperada' --kind wiki --limit 3
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py read 'TIC no Ensino Básico' --content
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py read 'Trabalho de Projeto' --content
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py read 'Circuitos de Comunicação' --content
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py read 'Avaliação Cooperada' --content
python3 /home/proteu/.codex/skills/sebenta-wiki/scripts/sebenta_api.py source documentos-oficiais/aprendizagens-essenciais/tic-1-ano-1-ciclo.md
```
