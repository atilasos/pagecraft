# Feedback com contexto integral e pedidos idempotentes

## Problema e requisito

Na base `480521e`, `server/feedback_context.py` removia acentos, maiúsculas e espaços repetidos de `question`, `expected` e `answer` antes de calcular a chave. Na mesma unidade, «avó» e «avô» recebiam a mesma chave. O mesmo acontecia com «Lisboa» e «lisboa». O segundo pedido podia receber a pista da primeira resposta, sem consultar o modelo.

A cache deve preservar o contexto que o modelo recebe, incluindo a escrita exata. Apenas o `request_id`, usado para transporte e correlação, fica fora da chave. A correção é partilhada pelas sessões de aula e pelas realizações permanentes.

Na ref `fb7caf9`, `LearningFeedback` também permite uma corrida entre a leitura do histórico e a conclusão de um pedido. Uma segunda leitura obtém o histórico sem desfecho, enquanto `_run` termina e o callback remove a tarefa. Quando essa leitura retoma, cria outra tarefa para o mesmo `request_id`. Com uma pista válida, o segundo resultado passa de `source=ai` para `source=cache`, apesar de a persistência conservar `ai`. Sem pista utilizável, há duas chamadas ao provider.

## Critérios de aceitação

- Alterar acentos, maiúsculas ou espaços em pergunta, resposta esperada ou resposta do aluno produz outra chave.
- Nos dois percursos, respostas com essas diferenças recebem a pista produzida para o novo pedido.
- Repetir o contexto com outro `request_id` reutiliza a cache e devolve o identificador atual.
- Entradas persistidas com o algoritmo antigo não são reutilizadas.
- Pedidos concorrentes ou posteriores com o mesmo `request_id` devolvem o desfecho integral persistido, incluindo `source`, mesmo quando está indisponível.
- A concorrência não duplica chamadas ao provider nem tentativas de registar o pedido ou o desfecho. As tarefas concluídas saem de `tasks`.
- A mudança não cria classificações nem altera atividades, frontend ou relatórios.

## Evidência antes e depois

Com dados sintéticos e providers simulados, executar:

```bash
uv run pytest -q tests/test_feedback.py tests/test_learning_feedback.py -k 'spelling_distinctions or legacy_normalized_cache'
```

Antes da correção: **5 falhas**. Os dois percursos devolviam a primeira pista para a segunda resposta. Uma cache persistida antiga devolvia `source=cache` para um contexto cuja escrita original já não era recuperável.

Depois: os casos passam. A chave preserva o texto integral e inclui `feedback-v2`, que impede colisões com entradas antigas. Estas entradas ficam no ficheiro, mas deixam de ser consultadas. Testes adicionais cobrem os três campos e a reutilização com outro identificador.

Para reproduzir a corrida na ref `fb7caf9`, acrescentar o teste de regressão e executar:

```bash
uv run pytest -q tests/test_learning_feedback.py -k completion_during_repeated --tb=short
```

Antes: **2 falhas**, reproduzidas em duas execuções. A pista válida devolve `ai` no primeiro pedido e `cache` no segundo. A resposta inutilizável provoca **2 chamadas** ao provider. O teste usa `asyncio.Event`, a leitura real de `attempt()` e ficheiros temporários. Suspende a segunda leitura até o primeiro pedido terminar no código antigo ou a conclusão esperar pelo lock no código corrigido. O limite de cinco segundos deteta bloqueios, sem determinar a ordem dos pedidos.

Depois: **2 aprovados**. `_run` persiste o desfecho sob o mesmo lock de feedback que protege a leitura e a criação. Assim, uma leitura sem desfecho encontra a tarefa em curso antes de ela terminar e ser removida. A geração fica fora desse lock. Mantém-se a ordem dos locks, primeiro feedback, depois realização. O teste verifica igualdade integral entre respostas e persistência, uma chamada ao provider, um único registo de cada acontecimento e libertação de `tasks`. O teste API existente também compara agora os três resultados concorrentes com o desfecho persistido e recupera-o numa nova instância.

A suite focada `uv run pytest -q tests/test_feedback.py tests/test_learning_feedback.py tests/test_providers.py` passou com **52 aprovados**, incluindo os casos «avó» e «avô». Testes de browser não foram executados. Nenhum modelo externo, publicação real ou dado real de aluno foi usado.

Validação final: `uv run pytest -q --ignore=tests/browser`, **331 aprovados**.

## Fundamento pedagógico

A síntese da Sebenta fornecida no pedido referencia [[Avaliação Formativa]], [[Diferenciação Pedagógica]] e [[Avaliação Cooperada]]. As páginas estão em revisão, com confiança média. São fundamento para esta decisão, sem constituírem certificação pedagógica.

Uma pista precisa de responder à evidência observada para ajudar a criança a reparar o erro e regular o trabalho. Acentos e maiúsculas podem ser precisamente o objeto de aprendizagem. Apagar essas diferenças antes de escolher uma pista impede ajustar o apoio à resposta atual. Conservar o contexto também mantém os critérios e as pistas anteriores na escolha do apoio, sem atribuir um nível fixo à criança. Esta correção não interpreta a reflexão do aluno nem a transforma em juízo docente.

Conservar o mesmo desfecho nas repetições mantém coerência entre o apoio entregue e o registo que o professor consulta. Um pedido repetido não representa uma nova dificuldade nem uma nova intervenção. Esta coerência não comprova que a criança leu a pista ou que ela ajudou.

## Riscos e oportunidades adiadas

- A cache deixa de juntar variantes de escrita. Pode aumentar o número de chamadas ao provider, sobretudo após a atualização, que invalida todas as chaves antigas. Remover entradas antigas e limitar a cache ficam para revisão própria.
- O lock de feedback passa a abranger a escrita do desfecho em disco. Pode atrasar outros pedidos da mesma realização durante essa escrita. A garantia continua limitada à arquitetura atual de um processo escritor. Coordenação entre processos fica fora do escopo.
- A qualidade pedagógica de cada texto gerado continua a exigir revisão. Esta mudança prova que a cache distingue os contextos testados, sem provar que o modelo produz sempre uma pista adequada.
