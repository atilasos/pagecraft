# Quadro vinculado à sessão atual

Implementação da proposta 1 de `/tmp/pagecraft-audit-08.md`, sobre a base
`4c6ba90476a498a03b08fd88dea96c432ba767cd`.

Worktree isolado: `/home/proteu/.t3/worktrees/pagecraft/t3-95965c1b`.
Branch local: `fix/quadro-session-stream`. O checkout começou limpo na base
pedida e já tinha esta branch descritiva. Não foram criados PRs nem feito merge.

## Problema e prova anterior

Com duas sessões vivas, A e depois B, `/api/board/session` indicava B e o
HTML de A devolvia 404. O stream de A aceitava a credencial de um Quadro
emparelhado e devolvia 200, incluindo um snapshot com nomes e um código de grupo
de oito caracteres. A credencial continuava válida, mas já não autorizava
projetar A.

A reprodução usa a aplicação ASGI real, emparelhamento por HTTP, relógio
controlado e armazenamento temporário. No primeiro commit, antes da correção:

```bash
uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_board_pairing_access.py -k 'old_board or after_switch' -q
```

Resultado: **3 failed, 10 deselected**. A primeira falha mostra 200 em vez de
404, com `session_state_snapshot`, nome do grupo e código. As outras duas
atingem o timeout: o stream continua aberto depois de um acontecimento de A
e depois de um heartbeat sem acontecimentos em A.

O commit `813c1d4` conserva essa reprodução sobre o código anterior. Para a
repetir sem mudar este checkout, pode ser usado um worktree temporário nesse
commit e o comando acima.

## Correção

`server/api/classroom.py` define `_current_board_session`, que seleciona a
sessão pelo mesmo serviço usado em `/api/board/session` e compara o identificador
pedido. `server/api/board.py` usa essa função para o HTML. O ramo Quadro do
stream usa-a antes de aceitar o pedido e volta a verificar a seleção com a
credencial antes do snapshot, em cada acontecimento e em cada heartbeat.

Um acontecimento pode produzir vários frames. O stream revalida também antes
dos deltas seguintes, pois o consumidor pode suspender entre dois `yield` e
entretanto o professor pode começar B. Quando A deixa de ser atual, o gerador
termina sem emitir outro frame de A, incluindo os de fecho. As subscrições e
tarefas pendentes são libertadas pelo `finally` existente.

O cliente em `server/static/board/app.js` fecha o EventSource, remove o `src`
do iframe e limpa nomes, códigos e título. Apresenta uma mensagem de espera e
consulta novamente `/api/board/session` após 1,5 segundos. A espera existente
de 2,5 ou 3 segundos continua a regular as tentativas quando não há sessão ou
há uma falha. Callbacks de EventSources substituídos são ignorados. A versão
do script no HTML foi atualizada para evitar reutilizar o cliente em cache.

Professor e Alunos continuam a poder aceder a A. A seleção do Quadro não fecha
A nem invalida os seus códigos de grupo ou credenciais. Não há alterações a
`/outputs`, atividades publicadas, autoria, dados de produção ou Momento de
comunicação. Foram lidos AGENTS, CONTEXT, PRODUCT, DESIGN e os ADRs existentes,
com particular relevância de 0004, 0006 e 0007. Esta correção aplica a fronteira
de acesso já definida; não acrescenta um comportamento pedagógico.

## Verificação posterior

```bash
uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_board_pairing_access.py -k 'old_board or after_switch' -q
# 5 passed, 13 deselected in 0.60s

uv run --project /home/proteu/pagecraft python -m pytest \
  tests --ignore=tests/browser -q
# 345 passed in 9.71s
```

Os testes cobrem:

- 404 no HTML e SSE de A quando B já é atual, sem snapshot nem nomes/códigos.
- Corte do stream já aberto ao receber um evento coletivo, um evento privado,
  um novo código de grupo ou um heartbeat. Só permanece o snapshot enviado
  enquanto A era atual; nenhum novo frame de A passa.
- Mudança de seleção durante a autorização, entre a preparação da resposta e
  o snapshot, e entre o acontecimento e o delta produzido pelo mesmo registo.
- Acesso do aluno a `/me` de A, entrada de outro dispositivo pelo código do
  grupo de A, acesso docente a A viva e streams autorizados de Professor/Aluno
  de A depois de B ter começado.
- Filtragem coletiva, emparelhamento, revogação e acessos existentes.

O teste antigo de estado vivo esperava frames depois de fechar a sessão. Agora
termina no último estado ainda autorizado. A fixture `board_frame_received`
observa a entrega real dos frames para sincronizar o produtor antes do fecho,
sem depender de uma pausa arbitrária.

## Browser real

Usei uma sessão própria do Agent Browser Hub, perfil `temporary`, nome
`pagecraft-quadro-sessao`. Os testes ligaram Playwright apenas ao CDP dessa
sessão. O servidor local usou dados descartáveis e cópias temporárias dos
ficheiros. A sessão foi fechada pelo Hub no fim.

```bash
# Abrir primeiro uma sessão própria no Hub e usar o respetivo URL CDP.
PAGECRAFT_TEST_CDP=http://127.0.0.1:9337 \
  uv run --with playwright --project /home/proteu/pagecraft python -m pytest \
  tests/browser/test_board_session_switch.py -q
# 2 passed in 38.71s
```

Os dois casos exercitam A com nomes e código de grupo, mudança para B, limpeza
do iframe e dos códigos, espera e redescoberta de B. Um usa um evento de A;
o outro deixa A sem eventos e aguarda o heartbeat periódico real de 30 segundos.
Durante a espera, o teste retém a segunda resposta de descoberta para inspecionar
a limpeza. Após abrir B, callbacks atrasados de A não alteram a interface nem
criam outra tentativa de descoberta. Não houve erros JavaScript.

Screenshots locais, com dados exclusivamente sintéticos:

- `/tmp/pagecraft-quadro-event-a.png`
- `/tmp/pagecraft-quadro-event-espera.png`
- `/tmp/pagecraft-quadro-event-b.png`
- `/tmp/pagecraft-quadro-heartbeat-a.png`
- `/tmp/pagecraft-quadro-heartbeat-espera.png`
- `/tmp/pagecraft-quadro-heartbeat-b.png`

Limite temporal: sem eventos em A, a ligação antiga pode ficar aberta até ao
próximo heartbeat, cujo intervalo é 30 segundos. Nesse intervalo, não emite
novos frames; qualquer acontecimento que chegue obriga a revalidar antes de
emitir. Depois de detetar o fim da ligação, o cliente aguarda 1,5 segundos para
redescobrir a sessão. Não é possível retirar frames já entregues ao browser
antes da troca.

## Commits de implementação

- `813c1d4`: reprodução da fuga entre sessões.
- `d331f44`: seleção comum de HTML/SSE e revalidação durante o stream.
- `2deceb2`: limpeza, redescoberta e testes reais de browser.
- `b394633`: novos códigos e eventos privados depois da mudança.
- `08b53d9`: sincronização da entrega de frames, retoma de A e corridas adicionais.

`git diff --check` passou. O principal pode rever esta branch local antes de
criar o PR.

## Ronda 2: invalidar seleções durante leituras assíncronas

A revisão Spec do PR #57 encontrou uma corrida ainda presente na base
`74c92232913c492ff7d6d9c18f6717263d27fcee`. `list_sessions()` enumera os
ficheiros antes de os ler com `await`. Se B nasce durante a leitura de A,
B fica fora da enumeração e a revalidação pode continuar a autorizar A.
As verificações anteriores não cobriam esta janela e não bastavam para
declarar o problema resolvido.

### Reprodução determinista

O commit `1132318` acrescenta um teste parametrizado que conduz o iterador
SSE real. A sessão e o emparelhamento são criados por HTTP. O teste suspende
`storage.read_json(A/session.json)` com dois `asyncio.Event`, depois da
enumeração, cria B por HTTP e só então liberta a leitura. Não usa sleeps.

```bash
uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_board_pairing_access.py -k creation_during_session_read -q --tb=short
# Antes da correção: 3 failed, 18 deselected in 1.42s
```

As falhas mostram um `session_state_snapshot` de A depois de B, um frame
`teacher_highlight` com `unit_id: OLD-A` depois de B e um timeout no caso
do heartbeat, pois a ligação antiga continua aberta. O heartbeat usa o
publicador real, acionado após observar a subscrição, sem esperar pelo relógio.

### Correção no serviço

`ClassroomService` mantém uma revisão da seleção do Quadro. Criação, retoma
e fecho incrementam essa revisão após persistir a mudança de sessão.
O fecho automático passa pelo mesmo método de fecho e também a incrementa.
`current_board_session()` lê a revisão antes de consultar as sessões e
repete toda a consulta se a revisão tiver mudado durante os `await`.
Não há `await` entre a comparação final e o retorno da projeção.

Assim, uma criação concluída durante a leitura obriga a enumerar B.
Retoma e fecho obrigam a reler sessões já processadas nessa consulta.
A ordenação continua em `list_sessions()`: data de janela mais recente,
com desempate estável pela ordem crescente dos caminhos, tanto para
`started_at` como para `active_since`. Não há novos guards nos handlers.
A revisão é local ao processo, de acordo com o modelo existente do serviço
e dos locks por sessão; o arranque continua a selecionar a partir do disco.

Os testes adicionais suspendem a leitura da última sessão enumerada e
retomam ou fecham outra sessão já lida. Também verificam os empates na
criação e na retoma e a convergência após expiração automática.

### Verificação da ronda 2

Comandos executados no worktree desta branch:

```bash
uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_board_pairing_access.py -q
# 21 passed in 1.22s

uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_classroom.py tests/test_board_pairing_access.py -q
# 38 passed in 1.42s

uv run --project /home/proteu/pagecraft python -m pytest \
  tests --ignore=tests/browser -q
# 352 passed in 10.11s

PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 \
  uv run --with playwright --project /home/proteu/pagecraft python -m pytest \
  tests/browser/test_board_session_switch.py -q
# 2 passed in 38.58s
```

O browser foi aberto pelo Agent Browser Hub na sessão própria
`pagecraft-quadro-ronda2`, perfil `temporary`, e fechado no fim. Os testes
usaram dados descartáveis e confirmaram limpeza de nomes, códigos e iframe,
redescoberta de B e ausência de erros JavaScript, com evento e com heartbeat
periódico real. As seis screenshots nos caminhos acima foram atualizadas.
Mantém-se o limite de 30 segundos até ao próximo heartbeat quando A não
recebe acontecimentos.

Esta ronda altera apenas o serviço, os testes Python e este relatório.
Os testes existentes continuam a verificar o acesso de Professor e Aluno
a A. Não houve alterações a `/outputs` ou ao Momento de comunicação.
O checkout partilhado não foi editado, e não houve push, novo PR ou merge.

Commits incrementais desta ronda:

- `1132318`: reprodução de snapshot, evento e heartbeat durante a leitura.
- `e10e92d`: revisão e repetição da seleção após criação, retoma ou fecho.
- `c674b70`: regressões de retoma, fecho, empates e expiração.

`git diff --check` passou. A branch local fica pronta para o principal
atualizar o PR #57 e pedir nova revisão independente.
