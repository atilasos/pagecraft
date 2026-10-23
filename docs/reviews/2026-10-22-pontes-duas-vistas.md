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

## Integração e revisão da representação

Por instrução do coordenador, foi feito `git merge --no-edit feat/consulta-historico-pistas`, SHA `474e961c65dd40cb89932b0c28a0fdc0e4f02f8f`, sem conflitos, em `b93be60`. O apoio foi reincorporado a partir desse canónico em `637b55d`. O PR65 do coordenador tem essa branch como base; esta implementação não abriu outro PR nem fez push. O worktree de integração não foi alterado.

A revisão Spec independente encontrou a personagem ausente na lateral. `4a6b0f6` acrescenta uma figura decorativa com posição final derivada do teste, descrição acessível e resultado textual redundante. Antes do teste próprio não existe figura. A mantém a personagem na margem direita; B para à esquerda; o colega vê o resultado do caso atual depois de testar e perde a figura ao mudar a altura até voltar a testar. A vista superior permanece byte a byte igual. A regressão persistente verifica circle/path, geometria, transform, descrição acessível, invariância do topo e os casos 1/2/3 do colega, além do texto. A revisão Spec R2 não encontrou pendências.

## Retoma do foco nos anfitriões reais

Os primeiros ensaios com abertura simulada não percorriam a correlação da pista, pelo que a asserção de retorno foi descartada como prova de produto. O teste foi substituído por `PageCraftSupport.requestHint('u1', true)` nos anfitriões reais, usando uma pista revista local sem fornecedor de IA. A prova genuína encontrou **21 passaram / dois falharam**: os identificadores pedido, recebido e atual coincidiam e a ação chegava, mas o foco ficava em BODY após fechar. `drafts/pontes-duas-vistas-resume-red-tests.txt` e o ticket `-repair-ticket-r3.json` conservam essa evidência.

`c4c8e6a` corrige a retoma cooperativa na fonte canónica `server/pipeline/prompts/activity-support.js`. Depois de continuar ou pedir o professor, o componente no iframe foca a ação atual. Outra pista conserva o foco no novo modal; pistas obsoletas e painéis escondidos/inertes não recebem foco. Uma confirmação assíncrona do pedido ao professor conserva o foco já recuperado. Os espelhos e o rascunho foram sincronizados. Não se relaxou o sandbox nem se leu o DOM do iframe a partir do anfitrião.

Com o canónico final integrado: **14 testes Python e 35 JavaScript passaram**, incluindo três regressões da retoma nos percursos autónomo, permanente e Studio. A rechecagem linguística `08091a7` manteve PASS com texto, ARIA, figura e pistas preservados. HTML para a prova final: SHA256 `c4e77ff6fe3ba903a16332361cd759b23d42cc55e244bbaee1dcce30ab2fb1d5`.

## Prova verde final

**23/23 cenários passaram em Chromium real do Hub, 32,25 s**, no commit `08091a7`, com o SHA256 acima. A sessão própria do Evaluator foi `pagecraft-pontes-evaluation`, perfil `temporary`, processo 3274139. A porta 9331 foi atribuída pelo Hub à nova sessão e confirmada no seu registo; não foi reutilizada a sessão de outro agente. As sessões temporárias próprias foram fechadas. A sessão `research` do coordenador não foi utilizada.

Reprodução, depois de abrir uma sessão própria do Hub e obter o seu CDP atual:

```sh
PAGECRAFT_TEST_CDP=<URL-CDP-da-sessão-própria> uv run --project /home/proteu/pagecraft --with playwright pytest tests/browser/test_pontes_duas_vistas.py -q
uv run --project /home/proteu/pagecraft pytest tests/test_pontes_draft.py tests/test_activity_support.py -q
node --test tests/js/activity_support.test.cjs
bash skills/sync-from-canonical.sh --check
git diff --check
```

As fixtures HTTP e Studio do teste são próprias, em loopback e com repositório/dados descartáveis. Não se publica a atividade nem se contacta um fornecedor real de IA. Os dois anfitriões são páginas reais: atividade permanente em pré-visualização privada e `/student/` após turma/sessão/entrada normais. O guião local gera identificadores genuínos e o teste verifica a ação correlacionada, o foco no apoio e a continuação por teclado. Os restantes percursos incluem os três apoios, cada pedido obrigatório, respostas erradas completas, revisão, retoma sem duplicação, modal, resposta tardia ignorada, offline, fonte real, alvos e larguras 390/768/1280.

O envelope máximo observado no browser foi **4092 bytes**. O harness extremo do Builder, com controlos JSON escapados e revisão máxima, mediu **4095 bytes**. Ambos ficam abaixo de 4096. Os textos obrigatórios são preservados; a reflexão opcional pode encolher nesse caso extremo de controlos escapados. A incorporação final corresponde exatamente às fontes canónicas de `activity-support.js`, CSS e `support-modal.js`, à fonte Didact Gothic binária e à licença OFL.

Provas principais, todas com prefixo `drafts/pontes-duas-vistas`:

- `-green-tests.txt`, `-final-tests.txt`, `-evaluation.json`, `-repair-resolution.json`: prova verde e resolução dos achados, preservando as provas vermelhas.
- `-green-character-ab.png`, `-green-character-peer.png`, `-green-character-evidence.json`: referente visual e invariância das vistas superiores.
- `-green-real-learning-evidence.json`, `-green-real-student-evidence.json` e respetivos `-resumed.png`: hosts reais, cache v2, teclado e retoma com foco.
- `-final-embedded-assets.json`, `-browser-metrics.json`: fontes incorporadas e orçamento de checkpoint.
- `-private-report.txt`: relatório de ensaio descartável com evidência e voz do aluno separadas, excluído dos relatórios de alunos.

O orquestrador repetiu os testes finais: **14 Python e 35 JavaScript passaram**, sincronização canónica sem drift e diff sem erros. A comparação com a base `feat/consulta-historico-pistas` não altera `activities/` nem `catalog.json`.

As execuções normais dos testes guardam novas capturas e diagnósticos numa
pasta temporária do pytest, preservando as provas desta avaliação commitadas.
Para regenerar deliberadamente as provas no repositório, acrescentar
`PAGECRAFT_PONTES_PROOF=drafts` ao comando e rever o diff antes de commitar.

## Entrega e limites

Rascunho privado pronto para revisão do professor, sem registo ou publicação de produção e sem push por este agente. O coordenador criou o PR65 draft e fará a atualização remota. A revisão humana da adequação à turma continua necessária; não houve ensaio com crianças, dispositivos físicos, leitor de ecrã ou fornecedor de IA real. As provas de hosts usam uma realização individual e um aluno de sessão descartáveis; não comprovam um percurso completo de grupo com múltiplos participantes.
