# Frações verticais e preferência tipográfica

Ajuste solicitado pelo professor em 01/10/2026, a partir do ecrã de associação no telemóvel. Commits incrementais desde `d1d2556`.

Os símbolos passam a mostrar numerador, barra horizontal e denominador. A mesma representação aparece nas escolhas de associação, instruções de pintura, feedback, comparações e construção de 20 blocos. Os valores das respostas continuam a ser `n/d`; a seleção e a avaliação não mudaram. Os rótulos acessíveis dos controlos foram conservados. Foi adaptada uma expectativa existente do teste de browser à nova representação do feedback.

A atividade e a interface do Studio preferem Century Gothic, confirmada como instalada no sistema e disponível no browser de ensaio. Para os dispositivos que não tenham esta fonte, a Didact Gothic fica incorporada como WOFF2 no CSS e no HTML. Não há pedidos a serviços de fontes. [Fonte e licença originais](https://github.com/google/fonts/tree/main/ofl/didactgothic) conservadas em `assets/fonts/didact-gothic/`; o script `scripts/embed_gothic_font.py` repõe os blocos incorporados e foi verificado como idempotente. As instruções de Designer/Builder e o template passam a seguir esta preferência, com a regra detalhada na referência de adaptação à idade. O pipeline do Studio incorpora deterministicamente a fonte e a licença em cada construção e reparação, antes da revisão e publicação. Rascunhos criados fora do Studio usam `python3 scripts/embed_gothic_font.py --activity drafts/<slug>.html` antes da revisão; o comando e o pipeline partilham a mesma implementação. As distribuições Codex/Claude foram sincronizadas a partir das instruções canónicas.

## Verificação

- Sintaxe do JavaScript inline validada com `node --check`.
- `uv run --with playwright pytest tests/test_fraction_draft_registration.py tests/test_schemas.py tests/test_validators.py -q`: **25 aprovados em 0,39 s**. Não foram acrescentados testes para a mudança de CSS. O teste de browser adaptado não foi executado, por não haver ligação CDP configurada.
- Browser colaborativo nativo do T3 Code, com a atividade real servida por HTTPS. A escolha de um quarto mostrou o numerador acima do denominador, barra de 2 px, estado selecionado e feedback "Ligaste as representações.". O alvo mede 80 px de altura.
- A Didact Gothic carregou a partir do data URL. O mesmo HTML foi renderizado num frame real de 390 px, forçando a alternativa Didact Gothic para representar um dispositivo sem Century Gothic: conteúdo de 375 px, sem transbordamento; numerador acima do denominador e botão de 80 px. As ferramentas de screenshot falharam; a medição e interação foram realizadas pelo DOM do browser.
- HTTPS confirmou o HTML atualizado com símbolos verticais e fonte incorporada, 131 747 bytes. `git diff --check` passou.


- Regressão pela API pública (`tests/test_generated_activity_typography.py`): o primeiro ensaio falhou porque o HTML em revisão não continha qualquer fonte incorporada. Depois da correção, passou por construção, reparação, revisão e publicação, confirmando os bytes WOFF2 reais, licença completa e CSP compatível. Só o transporte externo de IA foi simulado; o pipeline e os endpoints foram executados.
- `uv run --with playwright pytest tests/test_generated_activity_typography.py tests/test_runner.py -q`: **13 aprovados em 1,30 s**.
- Percurso normal completo da atividade real no browser nativo: uma resposta em falta manteve a página seguinte bloqueada; todas as respostas, incluindo erradas, permitiram avançar. Confirmadas pintura, associação, grelha, unidade inteira, comparação, construção e chegada à reflexão. A construção permitiu corrigir a resposta e mostrou «Um quarto são 5 blocos.».
- Em Mais desafios, a escolha `1/10` mostrou o denominador de dois algarismos abaixo do numerador, barra de 2 px, botão de 84,875 px e feedback «Um décimo são 2 blocos.». A Didact Gothic carregou sem pedidos externos; não houve transbordamento no ecrã de ensaio.
- Incorporação por CLI repetida num HTML descartável: SHA-256 igual antes/depois da segunda execução, sem duplicação do bloco.
- A primeira execução integral detetou apenas drift das distribuições de prompts. Corrigido com `bash skills/sync-from-canonical.sh`; `--check` passou. Execução final de `uv run --with playwright pytest -q`: **269 aprovados, 59 omitidos em 11,98 s**. Os 59 testes automáticos de browser requerem `PAGECRAFT_TEST_CDP`, ausente neste ambiente; não foram declarados como executados. A interação manual acima usou o browser nativo.

## Standards

Revisão paralela desde `d1d25566eb8ff4164a401793adb6ec62d9517741`: a lacuna de acesso à fonte nos providers foi corrigida por incorporação no servidor e partilha do módulo com o CLI. As cópias de instruções estão sincronizadas. **0 findings finais**, sem violações documentadas ou smells materiais pendentes.

## Spec

Revisão paralela contra `docs/design/fracoes-banda-desenhada-spec.md`: a fonte incorporada passou a estar garantida nos artefactos gerados e reparados, além da atividade existente. Frações verticais, valores internos, nomes acessíveis e comportamento da atividade foram conservados. **0 findings finais**, sem requisitos em falta ou desvios de âmbito.

Total por eixo: Standards 0; Spec 0. Nenhum problema pendente nestes eixos.

## Demonstração

[Experimentar as frações atualizadas](https://completely-paragraphs-percent-missions.trycloudflare.com/outputs/fraction-typography/index.html?presentation=1). O modo de demonstração permite escolher qualquer página, sem registos de alunos; escolher Mais desafios e 4. Associar reproduz o caso da imagem enviada.

Os ecrãs existentes de aluno e quadro da mesma instância descartável também recebem o HTML e CSS atualizados ao recarregar. Não houve alteração em produção ou nos dados da sessão.
