# Apoio contextual nas atividades geradas

Aplica a cada atividade nova, em qualquer área. O pedido do professor define tema, objetivos, etapas, produtos e recursos. Os exemplos de software, Matemática ou escrita não impõem um formato ou um banco de pistas às restantes atividades.

## Architect: escrever o plano da atividade

Acrescenta `support.version` ao DocSpec e `support` a cada unidade. Usa o schema JSON canónico em `server/pipeline/schemas/docspec.schema.json`.

- Em `support`, indica uma versão do conteúdo e as línguas pedidas. `automaticAfterFailures` usa três tentativas por defeito, aceita limiares de dois a cinco ou `0` para desativar. A faixa etária vem de `ageRange`, sem inferir características pessoais. Inclui `externalWork` apenas quando o trabalho decorrer também fora do PageCraft; o valor é o nome dessa aplicação ou contexto.
- Em cada unidade, define `objective`, `criteria` relevantes e `obstacles` previsíveis para aquela tarefa. Escolhe categorias reconhecíveis pelas crianças, próprias do tema e do que estão a fazer.
- Cada obstáculo tem um `id`, `label` por língua e duas ou três pistas progressivas. A primeira indica uma ação curta. A seguinte propõe outra abordagem, comparação ou pergunta que ajude a distinguir a causa. Cada pista tem `id` e `text.pt.individual`/`text.pt.group`; quando houver inglês, acrescenta os mesmos modos em `text.en`.
- Escreve as duas formas de tratamento; não confies numa troca automática de verbos. Uma pista mostra um próximo passo sem entregar a solução. A revisão docente da atividade inclui estas pistas.

Exemplo parcial para uma atividade de escrita:

```json
{
  "ageRange": "8-9 anos",
  "support": {"version": "convite-v1", "languages": ["pt"], "automaticAfterFailures": 3},
  "units": [{
    "summary": "Rever o convite",
    "support": {
      "objective": "Rever se o destinatário sabe onde acontece o encontro.",
      "criteria": ["Inclui a informação de que o destinatário precisa."],
      "obstacles": [{
        "id": "rever", "label": {"pt": "Perceber o que falta ao convite"},
        "hints": [
          {"id": "local", "text": {"pt": {
            "individual": "Sublinha a indicação do local. O destinatário sabe onde ir?",
            "group": "Sublinhem a indicação do local. O destinatário sabe onde ir?"
          }}},
          {"id": "destinatario", "text": {"pt": {
            "individual": "Lê o convite como se o recebesses. Que pergunta ainda terias de fazer?",
            "group": "Leiam o convite como se o recebessem. Que pergunta ainda teriam de fazer?"
          }}}
        ]
      }]
    }
  }]
}
```

O exemplo omite os outros campos obrigatórios do DocSpec e SRTC-A. As atividades arquivadas sem plano mantêm o contrato anterior; as atividades novas têm plano próprio.

## Builder: ligar o trabalho ao componente comum

Coloca `<aside data-pagecraft-support="u1"></aside>` junto da tarefa da unidade. Usa a mesma convenção `uN` do DocSpec e da ponte. O componente incorpora as pistas do plano, apresenta uma ação por vez e oferece leitura opcional, outra pista, indicação de utilidade, esclarecimento por IA e pedido ao professor. O botão de trabalho externo só existe quando o plano o declara.

Em cada mudança de etapa, resposta, manipulação relevante, produto ou nível, atualiza o contexto local. Faz esta atualização também durante a edição para invalidar uma resposta antiga; isso não pede feedback ao modelo:

```js
if (window.PageCraftSupport) PageCraftSupport.update({
  unit_id: currentUnitId,
  question: currentTask,
  answer: recentAttempt,
  product: chosenProduct || '',
  level: currentLevel,
  revision: attemptRevision
});
```

`revision` muda quando a tentativa muda. Se a interação tem um estado composto, pode transmitir `attempt` com os valores relevantes. Uma resposta só pode ser mostrada enquanto o contexto do pedido continua atual. O template sinaliza confirmações da ponte ao componente; as transições próprias da atividade continuam a precisar desta atualização explícita.

O `PageCraftSupport` pode ainda não existir durante a execução inicial do script. Atualiza o contexto ao receber `document` → `pagecraft-support-ready` e depois de cada transição. Não reimplementes a fila, a leitura ou o progresso das pistas em cada HTML. Ao substituir o DOM de uma etapa, conserva o atributo do painel; o componente volta a ligá-lo.

Para associar uma revisão a uma pista, conserva `PageCraftSupport.currentHintId()` antes de alterar a resposta e envia-o em `assessment_result.payload.detail.after_hint_id`. Uma alteração declarada sobre trabalho externo usa `detail.external_change: true`; continua a ser uma declaração. Nas sessões em grupo, os campos conjuntos usam `detail.activity` igual ao slug e `detail.field` estável, conforme o contrato do host.

O pedido ao modelo é explícito ou automático após respostas incorretas consecutivas e distintas na mesma tarefa. Atualiza o contexto antes de confirmar uma tentativa. Mantém `task_id` e `question` estáveis para esse pedido; muda-os quando começa outra questão:

```js
PageCraftBridge.attempt(currentUnitId, correct, {
  value: recentAnswer,
  question: currentQuestion,
  task_id: currentQuestionId
});
```

Emite `attempt` apenas depois de confirmar uma resposta relevante com um critério verificável. `correct` é um booleano. Campos vazios, autoavaliação, texto aberto sem critério e declarações de conclusão externa não recebem um veredicto inventado. `detail` pode ter `value`, `question` e `task_id`; uma mensagem de feedback em `detail` nunca é a resposta da criança. Atividades com integração própria podem usar `PageCraftSupport.recordAttempt({unit_id, correct, answer, question, task_id, attempt_id})`; escolhe uma via por confirmação, para evitar duplicação.

O componente conta respostas diferentes, reinicia após acerto ou mudança de tarefa e mantém um intervalo de novas tentativas antes de outro pedido automático. O limiar não bloqueia o avanço. Não o dispares por tecla, por perda de foco ou por tempo sem cliques. As pistas locais continuam disponíveis sem modelo. Não acrescentes um recetor genérico que apresente `ai_feedback` sem conferir `request_id` e contexto; o componente comum faz essa verificação.

O pedido automático inclui faixa etária, características da atividade, etapa, critérios, tentativas incorretas observadas e pistas anteriores. Quando a resposta chega para o contexto ainda atual, o componente apresenta uma única ação num modal de ecrã inteiro. O host cobre também os controlos exteriores ao iframe. Não implementes outro modal no Builder. A leitura só começa ao escolher «Ouvir». A criança escolhe «Vou experimentar», «Outra pista» ou «Pedir ajuda ao professor» para prosseguir. O fecho regista `hint_acknowledged`; não comprova leitura, compreensão ou utilidade. Uma falha do fornecedor usa a próxima pista revista do guião. Sem ligação ao host, a página autónoma mantém pistas locais e o mesmo modal, sem afirmar uma chamada à IA.

Antes do Proofreader e Evaluator, incorpora o plano e o código comum no HTML:

```sh
python3 scripts/embed_activity_support.py --activity drafts/<slug>.html --docspec drafts/<slug>-docspec.json
python3 scripts/embed_gothic_font.py --activity drafts/<slug>.html
```

Repete após reparações. O pipeline Studio faz a incorporação automaticamente antes da revisão. O HTML final mantém CSS/JS inline, sem rede nem credenciais; pedidos e resultados passam pelo host.

## Evaluator: verificar o apoio próprio da atividade

Verifica pelo menos um obstáculo de cada unidade: primeira pista visível junto da tarefa; outra abordagem após «não ajudou»; encaminhamento ao professor; leitura só ao carregar. Confirma a ligação entre pistas e critérios do DocSpec, incluindo as duas formas de tratamento e as línguas pedidas.

Confirma tentativas diferentes até ao limiar nos dois percursos com código. Confirma o reinício após acerto ou mudança de questão e que cliques repetidos na mesma resposta não contam como novas tentativas. Verifica modal em todo o ecrã, foco no seu interior, retoma explícita, outra pista, professor e ausência de áudio automático.

Muda a resposta, etapa e produto enquanto um pedido demora. A resposta anterior deve ser ignorada. Confirma também trabalho externo declarado, retorno ao guião e registos na realização ou sessão. Distingue pista apresentada, utilidade declarada e revisão observada. O PageCraft não valida um produto noutra aplicação a partir de uma declaração. Preserva a autoria do grupo e a reflexão de cada participante.

O resumo posterior deriva dos mesmos registos de qualquer atividade e liga as conclusões às fontes. Propostas de melhoria ficam para revisão antes de mudar uma versão usada na turma. Regista como não verificado o que depender de um fornecedor ou browser que não tenha sido exercitado.


## Ao alterar o componente comum

Executa `uv run pytest tests/test_activity_support.py` e `node --test tests/js/activity_support.test.cjs`. Os exemplos em `tests/fixtures/support-examples.json` verificam planos distintos de Matemática, escrita e Scratch, não a qualidade de aulas completas.

Para inspecionar o componente num browser, gera HTML autocontido com `uv run python scripts/render_support_examples.py --output /tmp/pagecraft-support-examples`. Estes ficheiros de ensaio não publicam atividades nem contactam IA. A avaliação de uma atividade gerada continua a exigir o seu próprio percurso, contexto e fontes.
