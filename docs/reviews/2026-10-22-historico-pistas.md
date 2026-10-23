# Consultar as pistas já experimentadas

Proposta 1 de `/tmp/pagecraft-audit-03.md`, primeiro incremento de consulta.
Implementação em `/home/proteu/.t3/worktrees/pagecraft/t3-9daa7bf9`, branch
`feat/consulta-historico-pistas`, a partir de `4c6ba90476a498a03b08fd88dea96c432ba767cd`.
O worktree e a branch estavam provisionados e limpos no início.

## Problema observado

Na base, pedir `alinhar` e editar a resposta deixa `currentHintId()` a `null`,
retira o texto do painel e conserva a pista apenas no registo. Pedir outra
pista apresenta `sobrepor`. Depois das duas pistas, a criança é encaminhada
ao professor, sem poder voltar a ler a primeira no apoio junto da tarefa.

A reprodução VM antes da implementação devolveu:

```json
{"firstHint":"alinhar","current":null,"firstStillVisible":false,"hasHistory":false,"aiRequests":0}
```

## Solução e limites de comportamento

O apoio inclui uma secção nativa `details`, recolhida inicialmente, chamada
"Pistas que já experimentei", com tratamento de grupo e tradução inglesa.
Cada pista tem uma abertura própria e um botão de leitura. A consulta mostra
o texto guardado, etapa, versão, pergunta, resposta original, produto quando
existe, tipo de ajuda, participantes, língua, objetivo da etapa e critérios.
Não regenera nem traduz o texto da pista com o plano atual.

O registo local da pista passa a conservar o mesmo contexto já enviado em
`hint_presented`. A retoma reutiliza os objetos recebidos em `learning_restore`.
Uma assinatura local deteta alterações durante o trabalho; na retoma comparam-se
os campos semânticos disponíveis no contexto guardado. Mudanças de etapa,
versão, pergunta, resposta, produto, nível, obstáculo, composição ou língua
assinalam a pista como anterior. As pistas novas guardam também `task_id` e
revisão, quando disponíveis, para comparar esses discriminantes após retoma.

O contexto de acontecimentos antigos não contém a revisão nem o `task_id`.
A retoma não inventa esses dados nos registos antigos: compara apenas o contexto
efetivamente guardado. Quando falta todo o contexto, apresenta essa ausência explicitamente.
As versões anteriores da mesma atividade são consultáveis, mas ficam excluídas
da seleção de pistas usadas e do contexto enviado à IA da versão atual.
O filtro de identidade da atividade é conservado.

Abrir, consultar e ouvir o histórico não emite acontecimentos, incluindo
`hint_listened`, `hint_presented`, `hint_acknowledged`, `hint_feedback` e
`feedback_request`. Não escolhe uma estratégia para reflexão, não declara
utilidade, não consome uma pista, não muda a pista atual e não cancela pedidos
IA pendentes. A leitura da pista atual conserva o contrato anterior, incluindo
o seu `hint_listened`. O som continua opt-in; a leitura histórica usa a língua
original. A indisponibilidade de voz aparece no painel e conserva foco e
aberturas.

As fontes alteradas são `server/pipeline/prompts/activity-support.js` e CSS.
As cópias em `skills/codex/assets/` e `skills/claude/assets/` foram sincronizadas
por `skills/sync-from-canonical.sh`. Não se alteraram atividades publicadas,
interfaces do professor, `reflection.js`, vocabulário ou contratos da ponte.
Distribuir o apoio numa atividade exige uma nova revisão aprovada. Foram lidos
AGENTS, CONTEXT, PRODUCT, DESIGN e ADRs 0002, 0004, 0005 e 0007; a preservação de
artefactos publicados e da autoria segue essas decisões.

## Fundamentação pedagógica

Consulta pela API local da Sebenta: `health`, pesquisa e leitura integral de
`20_Wiki/Diferenciação Pedagógica.md`, estado `review`, confiança `medium`.
A síntese da wiki defende recursos acessíveis para metas comuns e participação
dos alunos na regulação do percurso. A possibilidade de recuperar uma pista
é uma proposta de interface derivada dessa síntese. Não demonstra eficácia
pedagógica, compreensão nem utilidade da pista para uma criança concreta.

## Prova reproduzível antes e depois

Os seis testes JS acrescentados falham contra o runtime da base; os 21
anteriores continuam a passar. Com o runtime da branch passam os 27.

```bash
git show 4c6ba90:server/pipeline/prompts/activity-support.js > /tmp/pagecraft-support-before.js
PAGECRAFT_SUPPORT_SOURCE=/tmp/pagecraft-support-before.js node --test tests/js/activity_support.test.cjs
node --test tests/js/activity_support.test.cjs
```

Antes: 21 passam, 6 falham. Depois: 27 passam, 0 falham. O override de fonte
existe apenas no teste. Os registos desta execução estão em
`/tmp/pagecraft-history-before.log` e `/tmp/pagecraft-history-after.log`.

Os testes cobrem edição e consulta, retoma, leitura inglesa com interface
portuguesa, preservação dos objetos originais, versões anteriores, separação
entre atividades, conteúdo escapado, voz indisponível, contexto anterior,
progressão esgotada e pedido IA pendente. Comparam o conjunto completo de
acontecimentos antes/depois da consulta, não apenas a ausência de feedback.

```bash
uv run --project /home/proteu/pagecraft pytest -q tests/test_activity_support.py tests/test_support_summary.py tests/test_bridge_artifacts.py tests/test_session_event_types.py tests/test_canva_support_pilot.py
bash skills/sync-from-canonical.sh --check
git diff 4c6ba90..HEAD --check
```

Resultado: 35 testes Python passam, variantes sem drift e diff sem erros.

## Browser descartável

Sessão própria do Agent Browser Hub `pagecraft-historico-pistas`, perfil
`temporary`, aberta por MCP e encerrada por MCP no fim. Playwright ligou-se
exclusivamente ao CDP dessa sessão. Nenhum browser foi lançado fora do Hub.

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9334 uv run --project /home/proteu/pagecraft --with playwright pytest -q tests/browser/test_hint_history.py --basetemp=/tmp/pagecraft-historico-browser
```

Para repetir, abrir outra sessão própria e substituir o endereço CDP.
`--with playwright` fornece a dependência temporariamente: o ambiente instalado
não a incluía e não foi alterado. O servidor HTTP de teste usa uma porta livre,
o compilador real `embed_activity_support`, o DocSpec de comparação de barras
e um anfitrião de mensagens descartável com armazenamento isolado por teste.
Não acede a dados de alunos nem a atividades publicadas.

Resultado: 4 testes passam. Nos modos de anfitrião `studio` e `permanent`,
pedem-se duas pistas, edita-se a resposta, recarrega-se e abre-se a primeira
por teclado. O texto/contexto original e a marca de pista anterior permanecem.
A leitura é opt-in; os acontecimentos guardados ficam exatamente iguais.
Mudar para a segunda tarefa conserva a identificação da etapa anterior.
Não houve erros JS nem pedidos de rede fora do servidor descartável.

Os ensaios a 320 px, com escala normal e CSS zoom de 200%, verificam Tab,
Enter, Espaço, foco visível, alvo mínimo de 56 px, ausência de transbordo
horizontal e aviso de voz indisponível. O ensaio revelou quebra insuficiente
de palavras, corrigida no CSS comum, e motivou menor recuo do histórico em
ecrãs estreitos. O teste também consulta a árvore de acessibilidade para
confirmar os nomes dos controlos e a presença do contexto.

Capturas produzidas:

- `/tmp/pagecraft-historico-browser/test_edit_reload_and_reread_wi0/historico-permanent.png`
- `/tmp/pagecraft-historico-browser/test_edit_reload_and_reread_wi1/historico-studio.png`
- `/tmp/pagecraft-historico-browser/test_narrow_keyboard_voice_una0/historico-320-zoom-False.png`
- `/tmp/pagecraft-historico-browser/test_narrow_keyboard_voice_una1/historico-320-zoom-True.png`

Limites: piloto de componente com compilação real e mensagens de anfitrião,
não uma aula completa com autenticação. A síntese de voz foi substituída no
teste para verificar texto, língua e opt-in sem produzir áudio. Não houve
ensaio auditivo, com leitor de ecrã externo ou com crianças; a árvore de
acessibilidade não substitui esses ensaios.

## Commits de implementação

- `2ec70cb`: consulta e leitura das pistas anteriores, variantes e testes JS.
- `96dcdbb`: piloto de browser, adaptação estreita e prova contra a base.

A branch fica local para revisão independente pelo agente principal. Não foi
aberto PR, feito merge ou publicado qualquer conteúdo.

## Ronda 2: discriminantes na retoma

Base desta ronda: `52e65e61f4798fa5d74463699213563fd6369829`, worktree
e branch acima, limpos à entrada. Revisão Standards r1 sem achados;
Spec r1 com dois P2 reproduzidos. Relatório integral lido em
`/tmp/pagecraft-support-spec-r1.md`. Ambos aceites.

O primeiro P2 ocorria com duas tarefas da mesma etapa, pergunta e resposta
iguais. A assinatura em memória distinguia `task_id` e `revision`, mas esses
campos não viajavam em `hint_presented.context`. Após JSON e `learning_restore`,
a comparação semântica perdia a distinção. A correção guarda os valores
disponíveis no contexto e compara-os quando o registo os contém. Não reconstrói
discriminantes ausentes em registos antigos nem modifica os objetos recebidos.

```bash
node --test --test-name-pattern='retoma JSON' tests/js/activity_support.test.cjs
node --test tests/js/activity_support.test.cjs
bash skills/sync-from-canonical.sh
```

Antes de editar o runtime, os dois testes novos falharam na perda da marca
`Pista anterior`, separadamente para tarefa e revisão. Logs em
`/tmp/pagecraft-r2-retoma-before.log`. Depois, 29 testes passam, zero falhas,
em `/tmp/pagecraft-r2-retoma-after.log`. Também verificam persistência dos
dois campos, retorno ao contexto original, compatibilidade de registos antigos,
ausência de acontecimentos e ausência de áudio automático. Variantes sincronizadas.

## Ronda 2: leitura entre painéis

O segundo P2 foi reproduzido com os dois painéis montados em VM. Depois de
pedir uma pista em u1, trabalhar e pedir IA em u2, o clique no histórico de u1
passava por `update({unit_id:unit})`. A invalidação limpava a pista atual e o
pedido pendente. O teste falhou com `currentHintId()` igual a `null`.

A ação histórica é agora tratada antes da troca de unidade e termina aí.
O botão conserva o `hint_id` da pista apresentada e procura esse identificador,
sem depender da posição atual no histórico. Uma segunda reprodução reordenou
os acontecimentos numa retoma enquanto o painel anterior mantinha o DOM.
Antes, o botão da primeira pista lia o texto da segunda; depois, lê a pista
que a criança selecionou. Não foi acrescentado estado nem alterada a API.

```bash
node --test --test-name-pattern='outro painel|painel anterior' tests/js/activity_support.test.cjs
node --test tests/js/activity_support.test.cjs
bash skills/sync-from-canonical.sh
```

Antes da correção, 2 falhas específicas, em
`/tmp/pagecraft-r2-paineis-before.log`. Depois, 31 testes JS passam, zero
falhas, em `/tmp/pagecraft-r2-paineis-after.log`. A consulta mantém exatamente
os acontecimentos, o identificador da pista atual e a aceitação da resposta
IA de u2. O teste de reordenação confirma identidade do texto lido.

## Ronda 2: validação final

```bash
git show 52e65e61f4798fa5d74463699213563fd6369829:server/pipeline/prompts/activity-support.js > /tmp/pagecraft-support-r2-base.js
PAGECRAFT_SUPPORT_SOURCE=/tmp/pagecraft-support-r2-base.js node --test tests/js/activity_support.test.cjs
node --test tests/js/activity_support.test.cjs
PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 uv run --project /home/proteu/pagecraft --with playwright pytest -q tests/browser/test_hint_history.py --basetemp=/tmp/pagecraft-historico-r2-browser
uv run --project /home/proteu/pagecraft pytest -q tests/test_activity_support.py tests/test_support_summary.py tests/test_bridge_artifacts.py tests/test_session_event_types.py tests/test_canva_support_pilot.py tests/test_feedback.py tests/test_learning_feedback.py
bash skills/sync-from-canonical.sh --check
git diff --check
git diff --exit-code 52e65e61f4798fa5d74463699213563fd6369829 -- activities drafts outputs
```

Com os testes finais e o runtime da base desta ronda, 28 passam e 4 falham
pelos sintomas esperados: retoma de tarefa, retoma de revisão, pista atual
perdida entre painéis e leitura da pista errada depois de reordenação.
Log em `/tmp/pagecraft-r2-base.log`. Com o runtime corrigido, 32 testes JS
passam, zero falhas, em `/tmp/pagecraft-r2-js-final.log`. A regressão adicional
confirma que a retoma conserva o nível e obstáculo escolhidos, língua e
composição atuais, e que a próxima pista usa esses valores.

Os 75 testes Python passam, em `/tmp/pagecraft-r2-python.log`. A sincronização
canónica e `git diff --check` passam. Nenhuma alteração em atividades,
rascunhos ou outputs publicados.

No browser, 10 testes passam em 8,69 segundos, em
`/tmp/pagecraft-r2-browser.log`. A sessão Hub própria
`pagecraft-historico-ronda2`, perfil `temporary`, foi aberta e fechada por MCP.
O CDP acima pertenceu exclusivamente a essa sessão. Para repetir, abrir uma
sessão própria e substituir o endereço CDP. Não foram lançados browsers fora
do Hub nem usados dados de produção.

Os ensaios novos percorrem `studio` e `permanent`, com dois painéis reais
montados. O botão do histórico de u1 lê o texto de u1 sem mudar o identificador
da pista atual de u2, sem acrescentar acontecimentos e sem perder a resposta
IA pendente de u2. A retoma após recarregamento lê os acontecimentos JSON
guardados pelo anfitrião e conserva a marca anterior quando muda apenas
`task_id` ou apenas `revision`, mantendo pergunta e resposta iguais.
Os quatro ensaios anteriores de edição, teclado, foco, 320 px e zoom também
continuam a passar. A voz foi substituída para registar texto e língua sem
produzir áudio; continua a exigir clique explícito. A resposta IA é entregue
pelo anfitrião descartável, sem chamar um fornecedor.

Capturas dos dois painéis, com a resposta IA aceite em u2:

- `/tmp/pagecraft-historico-r2-browser/test_history_in_other_visible_0/dois-paineis-permanent.png`
- `/tmp/pagecraft-historico-r2-browser/test_history_in_other_visible_1/dois-paineis-studio.png`

Commits desta ronda:

- `1877c99`: contexto persistente de tarefa/revisão, regressão e prova.
- `3c1067b`: leitura histórica independente da tarefa ativa e identidade da pista.
- O commit de validação que inclui esta secção acrescenta os ensaios de browser
  e a regressão de escolhas, língua e composição.

A branch permanece local, pronta para revisão pelo agente principal.
Sem PR, push ou merge. Todas as edições foram feitas no worktree atribuído.
