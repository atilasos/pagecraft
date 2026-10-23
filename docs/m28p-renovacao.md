# Renovação dos percursos das 28 palavras

A coleção anterior, com 90 atividades, foi arquivada em 23/10/2026. Os conteúdos e os endereços anteriores permanecem para consulta de realizações; os catálogos público e do professor omitem os metadados com `status: archived`. O inventário com os metadados originais está em [arquivo](archives/m28p-2026-10-23.json). `python3 scripts/archive_m28p.py --apply` permite repetir a operação e recuperar uma interrupção sem perder o inventário.

A nova coleção tem 28 percursos e 448 páginas, distribuídas por quatro sessões por palavra. Cada palavra foi atribuída a um agente próprio; o [registo de delegação](../drafts/m28p-v2/delegation.json) conserva os identificadores. A posição 14 é **gema**, conforme a sequência editorial consultada; **ovo** pertence à variante anterior.

## Consultar os materiais

- [Índice de revisão docente](../drafts/m28p-v2/index.html): abre cada percurso e o respetivo guia.
- [Investigação com fontes e limites de leitura](research/metodo-28-palavras-2026.md).
- [Princípios de implementação](m28p-principios-implementacao.md).
- [Fontes da Sebenta sobre leitura, escrita e MEM](../drafts/m28p-renovacao-sources.md).
- Pareceres pedagógicos [1–14](reviews/2026-10-23-m28p-pedagogia-1-14.md) e [15–28](reviews/2026-10-23-m28p-pedagogia-15-28.md), e [revisão técnica](reviews/2026-10-23-m28p-motor.md).

Na Sebenta, as cópias de projeto estão em `30_Projects/PageCraft/28-palavras-2026/`. As versões navegáveis e pesquisáveis pela aplicação estão em `Research/pagecraft/28-palavras-2026/`; a leitura do relatório completo foi confirmada pela API com HTTP 200. A página `20_Wiki/Método das 28 Palavras.md` recebeu uma atualização identificada por data, preservando o registo anterior. Nenhuma fonte em `10_Sources/` foi alterada.

## Controlar os itens novos

O [mapa de 56 reservas](m28p-corpus-reservado.json) identifica uma leitura nova inicial e outra diferida por palavra, com referências ao ensino previsto. A [auditoria do corpus](reviews/2026-10-23-m28p-corpus.md) discrimina retenção e novidade. O auditor conta também os cartões preparados pelo adulto e as palavras nas pistas/instruções; o resultado não comprova ensino efetivo ou autonomia. Uma exposição fora da coleção pode retirar a novidade para aquela criança.

## Gerar e verificar

Os conteúdos editáveis de cada palavra estão em `drafts/m28p-v2/<palavra>/content.json` e `guia-docente.md`. O [contrato](m28p-contrato-percursos.md) define a estrutura. O HTML, DocSpec, design, metadata e manifesto são derivados:

```bash
python3 scripts/audit_m28p_corpus.py
python3 scripts/build_m28p_journeys.py --all --validate-only
python3 scripts/build_m28p_journeys.py --all
uv run --offline pytest --ignore=tests/browser -q
node --test tests/js/*.test.cjs
```

Para testar o browser, abrir uma sessão com a skill `agent-browser-hub`, obter o respetivo endereço CDP e executar:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:PORTA uv run --offline --with playwright==1.63.0 pytest tests/browser/test_m28p_journeys.py -q
```

O ensaio percorre os artefactos reais, inclui respostas incorretas, os três apoios, larguras de computador/telemóvel, ordenação, escrita, declarações orais, recuperação e reflexão. Um caso com servidor descartável verifica registo, privacidade do rascunho e recuperação no anfitrião permanente. Os registos desse ensaio não são dados de alunos nem publicação de atividades.

## Rever e publicar com o professor

Os percursos são **rascunhos**. Integrar em `main` conserva os materiais e os testes; não os publica para os alunos. A aprovação docente é individual por atividade, segundo a skill PageCraft. A inspeção documental e os ensaios técnicos não demonstram eficácia em sala.

O motor cria aliases relativos em `drafts/`, compatíveis com o helper de registo e publicação. Por exemplo, no checkout usado pelo servidor:

```bash
python3 skills/codex/scripts/activity.py register m28p-v2-gema --metadata drafts/m28p-v2-gema-activity.json
```

O comando devolve um código e uma pré-visualização privada. Depois de rever e aprovar esse percurso, o professor pode autorizar `activity.py publish CODIGO --approved`. O publicador canónico conserva o ano, as etiquetas e a ordem do método declarados no DocSpec e regenera o catálogo. Nunca editar `catalog.json` diretamente.

O adulto modela os sons, observa a primeira leitura e identifica a ajuda prestada. Os cartões reservados não são antecipados por imagens ou modelos. A produção escrita pode usar papel, letras móveis e ditado ao adulto, com modalidades distintas no registo. Um clique, uma declaração ou a conclusão das páginas não comprova domínio da leitura.
