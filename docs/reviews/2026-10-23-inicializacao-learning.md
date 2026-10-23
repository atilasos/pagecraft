# Inicialização da realização permanente

Investigação na branch `fix/protect-learning-authorship`, worktree
`/home/proteu/.t3/worktrees/pagecraft/t3-ae3a563b`, a partir de
`4d240205b0a6386f97cbcae3e93ba7926ff654bc`.

## Falha demonstrada e limite da atribuição

O teste isolado indicado pela raiz passou inicialmente em 2,38 s. Uma repetição
limitada de 20 execuções, com instrumentação local das mensagens e dos gestos,
produziu 18 passes e duas falhas depois de recarregar, ao abrir o desenho. Não
reproduziu a falha inicial de `finish_bread` observada na integração.

A experiência controlada demonstrou um defeito de produto com o mesmo sintoma
de perda do corte. O iframe já aceita trabalho quando ainda não consumiu o
restauro autorizado. Reter a entrega de `learning_restore` e
`learning_preferences`, cortar ao meio e libertar as mensagens repõe o corte
nulo do checkpoint anterior. O botão "Sim", que estava ativo, fica desativado.
Esta experiência falhou três vezes em três execuções, em 3,47 s no total.

Também se demonstrou que mudar o nível no anfitrião antes de executar o seu
callback `load` envia preferências ao iframe prematuramente. Uma resposta do
iframe a uma mensagem de prova, enfileirada depois da preferência, confirma a
ordem de entrega. A demonstração não depende de esperar um número de segundos.

As hipóteses consideradas foram restauro tardio, preferências tardias, remoção
do botão durante o gesto e interferência entre testes. O restauro tardio foi
confirmado com uma sequência controlada. Não ficou demonstrado que explique a
falha inicial da suíte de nove frentes. Essa atribuição continua em aberto.

## Correção

O anfitrião conserva as escolhas atuais dos controlos, mas só envia
`learning_preferences` depois do `load` do iframe. Envia primeiro
`learning_restore`, com os acontecimentos autorizados e a fila pendente, e
depois as preferências. `translate()` deixa de antecipar a inicialização.

O URL do iframe recebe o fragmento `#learning`. O rascunho de frações reconhece
esse modo antes de apresentar os controlos. Enquanto espera, mostra
"A recuperar o teu trabalho…", torna o documento `inert` e oculta os controlos.
Só os expõe depois de consumir restauro e preferências. A fronteira de prontidão
é a visibilidade dos controlos, sem sleeps, retries ou confirmação nova.

O fragmento não viaja no pedido HTTP nem autentica acesso. As atividades antigas
não precisam de reconhecer o fragmento nem de emitir um novo acknowledgment.
Não existe espera por uma resposta nova das atividades antigas. A pesquisa em
`activities/` não encontrou usos de `location.hash` ou `hashchange`.
As atividades standalone e os outros anfitriões conservam o funcionamento
anterior. Nenhum ficheiro de `activities/` foi alterado.

A versão do JavaScript no HTML anfitrião foi atualizada. O header
`X-PageCraft-Realization`, as verificações de origem das mensagens, o sandbox, a
CSP e as políticas de acesso mantêm-se. A correção não interpreta silêncio como
conclusão e não altera o contrato de `completed_at` ou expiração.

## Regressões e prova red/green

`tests/browser/test_learning_initialization.py` retém apenas a entrega das duas
mensagens, usando os handlers reais. O teste permite duas soluções válidas:
preservar uma ação antecipada aceite ou adiar a interação. Não exige uma
implementação particular para obter vermelho no código antigo.

O commit `be4ef75` acrescentou as primeiras três regressões antes da correção.
As três falharam. `cfdbe07` corrigiu o anfitrião e o rascunho; as três regressões
e o teste original passaram em conjunto, quatro passes em 5,43 s.

A versão final das regressões também foi executada com os três ficheiros de
produto temporariamente repostos a partir do SHA inicial. Os bytes foram
comparados com `git show` antes do ensaio e os ficheiros corrigidos foram
repostos num `finally`. O ensaio final deu duas falhas em 6,89 s:

- Na retoma, o corte antecipado é aceite e desaparece ao consumir o restauro.
  A asserção final encontra "Sim" desativado.
- Antes de `load`, o iframe recebe a preferência `challenge` prematuramente.

O log local deste ensaio é `/tmp/pagecraft-initialization-baseline.log`.
Os blobs de base verificados foram `f21b1e05c0f415f53fbdb01ee48ae7810a171b56`
para `activity.js`, `af6291e720d892d629fd896a43a6ab9b9d7cc2c5` para o HTML
anfitrião e `12b10e6028553e9ada0981fe564a4b98c215a658` para o rascunho.

O quarto teste conserva nível e corte pendentes durante HTTP 503, recarrega,
confirma o conteúdo do restauro, restabelece a ligação e lê o trabalho gravado.
Confirma a mesma realização, uma única tentativa e o header de autoria correto.
Os quatro testes passaram em 3,83 s antes da validação alargada. A versão final,
com a prova do corte aceite em vez de exigir `inert`, também passou na suíte
completa. Essa revisão de testes está no commit `b03c7b4`.

Comandos de regressão, no worktree atribuído:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 uv run --project /home/proteu/pagecraft --offline --with playwright==1.63.0 pytest -q tests/browser/test_learning_initialization.py
PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 uv run --project /home/proteu/pagecraft --offline --with playwright==1.63.0 pytest -q tests/browser/test_fraction_units.py::test_realization_restores_all_units_and_drawing_without_duplicate_attempts
uv run --project /home/proteu/pagecraft --offline pytest -q tests --ignore=tests/browser
node --check server/static/learning/activity.js
git diff --check
```

## Validação alargada e limites

A suíte completa de browser deste worktree terminou com 94 passes e uma falha
em 167,34 s. A falha permanece no teste original, depois de `page.reload()`, em
`test_fraction_units.py:238`, ao abrir "Desenho livre (opcional)". O início e o
corte passaram nesta execução. Os quatro testes de inicialização passaram,
assim como as verificações de autoria, retoma, reflexão e atividades antigas.
O teste original não foi alterado. A validação global não está verde.

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 uv run --project /home/proteu/pagecraft --offline --with playwright==1.63.0 pytest -q -o faulthandler_timeout=30 tests/browser
```

Os 384 testes sem browser passaram em 11,15 s. Os 28 testes de autoria e
recuperação passaram em 57,50 s, incluindo filas, reflexão, conflitos, reentrada,
realizações concluídas e credenciais expiradas.

Depois da correção, cinco repetições sequenciais do teste original passaram em
10,40 s. Uma execução concorrente de duas suítes no mesmo browser teve 15 passes
e cinco falhas, todas após recarga ao abrir o desenho. Outro ensaio concorrente
falhou à espera da atividade após recarga. Os registos mostram gestos recebidos
pelo anfitrião, sem o gesto correspondente no iframe. Não foi determinada a
causa destas falhas, nem demonstrada relação com a corrida de restauro corrigida.
Uma execução alargada anterior ficou sem progresso depois de 19 casos e foi
terminada; os processos próprios foram fechados. Estes resultados não são
contados como validação verde.

A screenshot local da falha investigada é `/tmp/pagecraft-init-failed.png`.
A instrumentação exploratória foi removida antes da entrega.
Os testes permanentes contêm apenas os controlos de ordem necessários à regressão.

O browser pertence à sessão Agent Browser Hub `pagecraft-init-20261023`, perfil
`temporary`, porta 9331 confirmada por `hub_browser_status`. A sessão `research`
da raiz na porta 9330 não foi usada. Todos os servidores e dados são descartáveis.
A sessão própria foi fechada por `hub_browser_close`, com confirmação `ok=true`.
Não houve produção, chamadas a fornecedor IA, push, criação ou edição de PR, nem
merge. O checkout original e o worktree de integração não foram editados.


## Entrega para decisão da raiz

Os commits locais são `be4ef75`, com as primeiras regressões, `cfdbe07`, com a
correção, e `b03c7b4`, com a prova final e a conservação de pendentes. A correção
resolve uma corrida de produto demonstrada. Não certifica a resolução da falha
inicial observada em `e105d76`, nem da falha posterior ao abrir o desenho. Não foi
feita alteração especulativa para essas falhas restantes.

A única alteração ao comportamento da criança é adiar os controlos até consumir
o restauro. Não foram alterados objetivos, critérios ou escolhas pedagógicas.

## Revisão de acessibilidade da espera

A revisão independente de `df433ea` identificou que `body.inert` também retira
`#learning-loading[role=status]` da árvore acessível. A espera passa a ser
assinalada por `data-learning-loading` no elemento raiz; apenas `.wrap` e
`.skip`, que contêm os controlos ocultos, ficam inertes. A mensagem permanece
visível e sem qualquer antepassado inerte até consumir restauro e preferências.

As regressões verificam a visibilidade e ausência de antepassado inerte do
status, a impossibilidade de focar o corte enquanto oculto e a ausência de ação
por teclado. Usam Enter para ativação: Espaço, sem um botão focado, deslocava o
anfitrião e introduzia uma segunda variável na investigação de encaminhamento
do rato. O cenário alternativo que aceita o corte antecipado e verifica se o
restauro o apaga mantém-se intacto.

Antes da correção, a nova asserção do status falhou nas duas variantes, em
1,67 s (`/tmp/pagecraft-loading-accessibility-red.log`). Depois, os quatro testes
de `test_learning_initialization.py` passaram em 3,89 s, sem instrumentação
externa (`/tmp/pagecraft-loading-accessibility-green.log`).
