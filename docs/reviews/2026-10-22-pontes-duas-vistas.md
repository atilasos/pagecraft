# Duas pontes iguais de cima, rascunho privado

## Âmbito e isolamento

Implementação da proposta 1 de `/tmp/pagecraft-audit-10.md`, autorizada para 3.º/4.º ano, 15 minutos, português europeu. Slug `pontes-duas-vistas`. Worktree `/home/proteu/.t3/worktrees/pagecraft/t3-4e77fc67`, branch `feat/pontes-duas-vistas`, base inicial `4c6ba90476a498a03b08fd88dea96c432ba767cd`, estado inicial limpo. A branch descritiva já existia no worktree atribuído.

O recorte acrescenta o rascunho e as provas e inclui a correção de foco na fonte canónica do modal comum, sua sincronização e versões de cache nos dois anfitriões. Não inclui registo de atividades em produção, publicação, catálogo, PR ou merge. Os cinco papéis da skill são executados por subagentes sequenciais no mesmo worktree, sem escrita concorrente das fases. O orquestrador integra e verifica.

## Antes

A atividade entregue `activities/tinkercad-pontes-3e4/index.html` conserva a configuração atual e uma anterior para desfazer. A função `outcome` depende das alturas, mas a vista superior não as representa. `renderTrial` substitui o resultado atual; não há um par de ensaios escolhidos conservado para comparação.

Confirmação no Hub, sessão própria `pagecraft-pontes-before`, perfil `temporary`, fechada após o ensaio. Servidor estático exclusivamente em loopback, porta 8837. No percurso real: apoios nas margens, tabuleiro presente, A 2/2 atravessa; mudar apenas altura direita para 1 e testar substitui o resultado pela pista das alturas. A interface não mostra os dois ensaios lado a lado.

Provas locais preservadas:

- `/tmp/pagecraft-pontes-proof/before.json`
- `/home/proteu/agent-browser-hub/screenshots/pontes-duas-vistas-before.png`

Leitura reproduzível da base: `git show 4c6ba90:activities/tinkercad-pontes-3e4/index.html`, funções `outcome`, `draw`, `renderTrial`, `changed` e `test`. A atividade existente não é alterada.

## Depois e validação

O novo rascunho conserva duas fichas A/B. Cada uma confronta a previsão confirmada antes dos testes com o resultado observado. A altura direita é a única variável: A 2/2 atravessa, B 2/1 para. Os SVG superiores são gerados pela mesma representação sem alturas nem resultado sobreposto; as laterais mostram a diferença. Cada lateral só é revelada pelo teste explícito da respetiva ponte.

A criança escolhe a variável, mantém ou revê a hipótese e explica por escrito ou confirma uma explicação oral. Um colega testa uma altura direita 1/2/3 e aprecia a explicação concreta do par, podendo declarar que encontrou um contraexemplo ou que não encontrou. A interface não julga texto livre nem infere que a fala aconteceu. A revisão invalida a apreciação do colega ligada à versão anterior, conservando os ensaios e as evidências anteriores no host.

O avanço depende de pedidos respondidos, incluindo respostas incorretas. Os três apoios são livres, oferecem pistas diferentes e conservam as respostas. Reflexão facultativa, sem nota. O modo autónomo só guarda nesta aba; no iframe usa a ponte e o restauro autorizado, com autoria gerida pelo host. Os critérios aparecem antes do trabalho.

## Artefactos e papéis

Todos os caminhos seguintes têm prefixo `drafts/pontes-duas-vistas`:

- Architect: `-sources.md`, `-docspec.json`, `.md`. Pesquisa na Sebenta e leitura da fonte curricular extraída; síntese, original e proposta distinguidos.
- Designer: `-design-spec.json`. Vistas e estados, fonte Gothic, mínimos 20 px/48 px, foco e larguras.
- Builder: `.html`, `-builder.json` e prompt gerado `-builder-prompt.md`. Apoio contextual comum e Didact Gothic com licença incorporados pelos scripts canónicos.
- Proofreader: `-proofread.json`. AO90 e reflexão individual corrigidos. A revisão encontrou a revelação precoce de laterais; o Builder corrigiu em `c0cf22c` e a rechecagem `fdc8914` aprovou, conservando o histórico.
- Evaluator: `-evaluation.json` e testes de browser dedicados, em execução à data desta atualização.
- Orquestração: `-run-manifest.json`, `-before.json`, este relatório e teste API `tests/test_pontes_draft.py`.

O catálogo e as atividades existentes não são alterados. A correção partilhada de teclado pertence à fonte canónica `server/static/student/support-modal.js`, com sincronização dos assets das skills e cache dos anfitriões. O alinhamento curricular usa as Orientações Curriculares de TIC para o ciclo, sem inventar AE específicas nem usar uma proposta de revisão como referencial homologado. Fontes, limitações e comandos de pesquisa constam do documento de fontes.

## Verificações executadas

`uv run --project /home/proteu/pagecraft pytest tests/test_pontes_draft.py -q`: **1 passou**, repetido após a reparação e revisão. O teste cria um repositório e dados temporários próprios, regista só nesse Studio descartável e nunca publica. Confirma pré-visualização privada, CSP sem rede, fonte binária e licença exatas, recusa de conteúdo/entrada/início públicos e da rota de drafts, inexistência de catálogo/publicação e exclusão do ensaio dos relatórios.

DocSpec e design validados contra os esquemas canónicos. Duração 3+5+4+3=15, três critérios de reflexão do host e apoio nas quatro unidades. O Builder verificou sintaxe dos scripts inline, estado, revelação por teste próprio e envelope Unicode máximo de 3278 bytes num harness Node temporário. Estas verificações de estado não substituem o browser. O relatório Builder identifica o comando e a natureza temporária dessa prova.

Incorporação reproduzível:

```sh
python3 scripts/embed_activity_support.py --activity drafts/pontes-duas-vistas.html --docspec drafts/pontes-duas-vistas-docspec.json
python3 scripts/embed_gothic_font.py --activity drafts/pontes-duas-vistas.html
```

## Prova vermelha e reparações

A primeira avaliação completa no Hub executou 20 cenários: **15 passaram e cinco falharam**, correspondendo a três causas. Prova preservada em `drafts/pontes-duas-vistas-red-tests.txt` e `-red-evaluation.json`, commits `403e6b5` e `2bb1b97`. As falhas exercitam o comportamento real, não uma mutação artificial:

- `modal-focus-wrap`: Tab no último botão deixava `document.activeElement` em BODY, também nos dois adaptadores do componente. A ausência de um ciclo explícito de Tab foi corrigida na fonte canónica `server/static/student/support-modal.js`, sincronizada para `skills/{codex,claude}/assets/support-modal.js`. Os dois anfitriões passam a carregar `?v=2`; o HTML do rascunho foi reincorporado. Commit `2e90460`. O teclado não depende de um remendo exclusivo da atividade.
- `stale-navigation-warning`: depois de guardar A/B, o aviso ainda pedia esse trabalho. A navegação recalcula o pedido em falta e esconde o aviso resolvido.
- `support-first-click-lost`: sair de um texto emitia a evidência e notificava outra vez um contexto já sincronizado. O apoio reconstruía o botão entre mousedown e click. A atividade conserva a evidência, o valor e `after_hint_id`, mas evita essa notificação local redundante no flush. Não usa temporizadores nem um segundo clique. Estas duas reparações pertencem ao commit `6a03829`.

Após as reparações, `uv run --project /home/proteu/pagecraft pytest tests/test_pontes_draft.py tests/test_activity_support.py -q`: **14 passaram**. `node --test tests/js/activity_support.test.cjs`: **21 passaram**. `bash skills/sync-from-canonical.sh --check`, `node --check server/static/student/support-modal.js` e `git diff --check` passaram. As atividades já entregues e o catálogo permanecem intactos.

A prova verde de browser e os testes das páginas reais dos dois anfitriões serão acrescentados após o fecho da reavaliação.
