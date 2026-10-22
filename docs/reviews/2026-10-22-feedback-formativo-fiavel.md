# Cache de feedback que conserva o texto da tarefa

## Problema e requisito

Na base `480521e`, `server/feedback_context.py` removia acentos, maiúsculas e espaços repetidos de `question`, `expected` e `answer` antes de calcular a chave. Na mesma unidade, «avó» e «avô» recebiam a mesma chave. O mesmo acontecia com «Lisboa» e «lisboa». O segundo pedido podia receber a pista da primeira resposta, sem consultar o modelo.

A cache deve preservar o contexto que o modelo recebe, incluindo a escrita exata. Apenas o `request_id`, usado para transporte e correlação, fica fora da chave. A correção é partilhada pelas sessões de aula e pelas realizações permanentes.

## Critérios de aceitação

- Alterar acentos, maiúsculas ou espaços em pergunta, resposta esperada ou resposta do aluno produz outra chave.
- Nos dois percursos, respostas com essas diferenças recebem a pista produzida para o novo pedido.
- Repetir o contexto com outro `request_id` reutiliza a cache e devolve o identificador atual.
- Entradas persistidas com o algoritmo antigo não são reutilizadas.
- A mudança não cria classificações nem altera atividades, frontend ou relatórios.

## Evidência antes e depois

Com dados sintéticos e providers simulados, executar:

```bash
uv run pytest -q tests/test_feedback.py tests/test_learning_feedback.py -k 'spelling_distinctions or legacy_normalized_cache'
```

Antes da correção: **5 falhas**. Os dois percursos devolviam a primeira pista para a segunda resposta. Uma cache persistida antiga devolvia `source=cache` para um contexto cuja escrita original já não era recuperável.

Depois: os casos passam. A chave preserva o texto integral e inclui `feedback-v2`, que impede colisões com entradas antigas. Estas entradas ficam no ficheiro, mas deixam de ser consultadas. Testes adicionais cobrem os três campos e a reutilização com outro identificador.

Validação final de código: `uv run pytest -q --ignore=tests/browser`, **329 aprovados**. A suite focada de feedback e providers também passou com **50 aprovados**. Testes de browser não foram executados. Nenhum modelo externo, publicação real ou dado real de aluno foi usado.

## Fundamento pedagógico

A síntese da Sebenta fornecida no pedido referencia [[Avaliação Formativa]], [[Diferenciação Pedagógica]] e [[Avaliação Cooperada]]. As páginas estão em revisão, com confiança média. São fundamento para esta decisão, sem constituírem certificação pedagógica.

Uma pista precisa de responder à evidência observada para ajudar a criança a reparar o erro e regular o trabalho. Acentos e maiúsculas podem ser precisamente o objeto de aprendizagem. Apagar essas diferenças antes de escolher uma pista impede ajustar o apoio à resposta atual. Conservar o contexto também mantém os critérios e as pistas anteriores na escolha do apoio, sem atribuir um nível fixo à criança. Esta correção não interpreta a reflexão do aluno nem a transforma em juízo docente.

## Riscos e oportunidades adiadas

- A cache deixa de juntar variantes de escrita. Pode aumentar o número de chamadas ao provider, sobretudo após a atualização, que invalida todas as chaves antigas. Remover entradas antigas e limitar a cache ficam para revisão própria.
- O teste existente `test_permanent_code_feedback_is_contextual_private_and_idempotent` falhou intermitentemente em duas execuções focadas, apesar de passar na suite final. O texto era igual, mas `source` diferia entre resposta e persistência. Uma reprodução controlada com `LearningFeedback` e `cache_key` originais de `480521e` confirmou: `primeiro=ai, segundo=cache, persistido=ai, chamadas=1`. Para reproduzir, pausar a leitura do segundo pedido após obter o histórico sem desfecho, deixar o primeiro terminar e libertar essa leitura antiga. A tarefa já saiu de `tasks`, e o segundo pedido volta a executar `_run`. Corrigir a coordenação entre leitura e conclusão fica fora desta alteração.
- A qualidade pedagógica de cada texto gerado continua a exigir revisão. Esta mudança prova que a cache distingue os contextos testados, sem provar que o modelo produz sempre uma pista adequada.
