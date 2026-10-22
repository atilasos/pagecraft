# Contexto do pedido de ajuda no drawer docente

Implementação da proposta 1 de `/tmp/pagecraft-audit-09.md`, sobre a base `4c6ba90476a498a03b08fd88dea96c432ba767cd`.

Worktree isolado: `/home/proteu/.t3/worktrees/pagecraft/t3-13bf0fef`.
Branch: `feat/help-request-context-drawer`.

## Problema observado

O histórico autorizado já continha a nota do pedido, o contexto da tarefa e as pistas. Ao abrir o percurso, o professor via apenas "pediu ajuda", "hint presented" e "hint feedback". Era necessário procurar os dados fora do painel para compreender o pedido.

O primeiro teste percorreu o servidor descartável e o drawer real, num browser do Agent Browser Hub. Antes da implementação falhou com `Locator expected to contain text` para a nota do pedido, porque `#drawer-help` não existia. A cronologia mostrava "pediu ajuda" sem a nota. O teste foi guardado antes da implementação, no commit `c039f4c`.

## Comportamento implementado

O drawer apresenta os pedidos pendentes antes das ações e da cronologia, com nota, etapa, tarefa, resposta disponível, contexto, pista associada e utilidade declarada. Cada fonte tem data completa, referência ao registo e autoria; os identificadores do pedido, pista, tarefa e versão aparecem quando existem. Campos sem dados dizem "não registado". Falhas de carregamento têm uma mensagem própria, sem apresentar dados anteriores de outra criança.

`teacher/evidence.js` concentra a projeção e a criação de elementos de texto. Os valores dos alunos entram por `textContent`, incluindo objetos descritos em texto legível. Não há nova persistência, API, resolução automática nem alteração de atividades publicadas. O catálogo e os filtros de `class.js` ficaram intactos.

Regras de associação:

- A autoria usa `work_group_id` e os participantes gravados no acontecimento, ou `student_id` para trabalho individual. O grupo atual não substitui a autoria histórica.
- A nota, tarefa e resposta do próprio pedido têm prioridade. Uma resposta de outro acontecimento só entra se for anterior ao pedido, da mesma autoria, etapa e `task_id`. Atividade e versão também têm de ser compatíveis.
- Uma pista exige o `hint_id` indicado no pedido, apresentação anterior, mesma autoria e etapa. Valores de tarefa, atividade ou versão presentes apenas de um lado, ou diferentes, excluem a associação. Não se escolhe a pista mais próxima no tempo.
- A utilidade exige uma apresentação de pista validada e uma declaração posterior com o mesmo `hint_id`, autoria e âmbito. A apresentação e a declaração conservam referências próprias.
- `help_resolved` com identificador retira apenas o pedido correspondente do mesmo autor. A declaração antiga sem identificador retira os pedidos pendentes desse autor, conservando os registos na cronologia.
- Uma nova tentativa, pista ou declaração de utilidade não resolve ajuda. Abrir e fechar o drawer só lê o histórico.

A cronologia continua em ordem inversa. Acrescenta nota, detalhe das tentativas, pistas e declarações legíveis. A reflexão individual mantém a voz da criança e nunca fornece resposta ou utilidade ao pedido conjunto. O drawer aberto acompanha novos acontecimentos relevantes por SSE, sem recarregar a cada heartbeat. Respostas HTTP antigas não podem substituir o painel de outra criança ou uma leitura mais recente.

## Fundamentação e limites

Foram lidos `AGENTS.md`, `CONTEXT.md`, `PRODUCT.md`, `DESIGN.md` e os ADRs 0002, 0004, 0005 e 0007. Mantêm-se o acesso existente, os identificadores, a autoria e os nomes da ponte.

Consultei a Sebenta por API com `health`, `search "avaliação formativa" --kind wiki --limit 2` e `read "Avaliação Formativa" --content`. A síntese de `20_Wiki/Avaliação Formativa.md`, revista em 09-07-2026, estado `review`, confiança `medium`, distingue recolha, interpretação e decisão que ajusta o trabalho. Esta implementação é uma proposta de apresentação de informação disponível. A wiki não demonstra a sua eficácia.

A projeção é deliberadamente conservadora: metadados incompletos podem deixar uma pista ou resposta legítima sem associação. Esses registos continuam na cronologia. Não se reconstrói uma tarefa por proximidade temporal, nome do aluno ou conteúdo semelhante. A resposta apresentada descreve o que foi registado no pedido ou antes dele; não prova o estado atual de um produto externo. Utilidade declarada não comprova aprendizagem, compreensão individual nem efeito causal da pista.

## Verificação reproduzível

Sessão própria do Hub `help-context-drawer`, perfil `temporary`, CDP `http://127.0.0.1:9335`. O CDP deve ser substituído pelo endereço de uma nova sessão Hub ao repetir os testes. Playwright liga-se apenas ao browser do Hub. O fixture `studio_origin` copia os estáticos deste worktree e inicia um Studio com dados descartáveis.

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9335 uv run --project /home/proteu/pagecraft --with playwright python -m pytest tests/browser/test_help_context_drawer.py tests/browser/test_group_reflections.py -q
uv run --project /home/proteu/pagecraft python -m pytest tests/test_teacher_client_access.py tests/test_work_groups.py tests/test_classroom_api_authority.py tests/test_support_summary.py -q
node --check server/static/teacher/evidence.js
node --check server/static/teacher/class.js
git diff --check
```

Resultados: **12 testes de browser passaram**, incluindo os sete novos, e **33 testes de acesso, grupos e resumo passaram**. As verificações de sintaxe e whitespace passaram.

Os sete casos novos cobrem dois grupos e três etapas; nota com HTML malicioso apresentada como texto; respostas de tarefas diferentes na mesma etapa; resolução por pedido e declaração antiga sem ID; tentativa posterior que não resolve ajuda; pista antiga sem ligação; mesmo ID de pista noutra composição; conflitos de etapa, tarefa e versão; autoria individual; isolamento da reflexão; acesso recusado ao histórico docente pelo grupo; falha de carregamento sem contexto residual. Abrir, fechar e trocar de aluno conserva o histórico exatamente igual.

## Prova antes/depois

A comparação adicional `/tmp/pagecraft-drawer-proof.py` abriu o mesmo histórico descartável com os estáticos originais de `4c6ba90` e depois com os estáticos desta branch. Ligou-se à sessão Hub e guardou imagens e texto em `/tmp/pagecraft-drawer-proof/`:

- `before.png` e `before.txt`: apenas "pediu ajuda", sem "Não conseguimos organizar as duas zonas."; pistas sem texto legível.
- `after.png` e `after.txt`: a nota aparece primeiro, seguida de "Como distribuir os animais?", "Um animal de cada lado", pista identificada e "Não ajudou, segundo o grupo". A pista antiga da etapa u1 fica apenas na cronologia.
- Resultado do script: `before_note_visible=false`, `after_note_visible=true`, `opening_preserved_history=true`.

As imagens foram inspecionadas. Estes artefactos complementares são locais e temporários; os testes versionados acima são a prova repetível na revisão.

Não foi aberto PR nem feito merge. A branch fica local para revisão independente pelo agente principal.
