# Frações verticais e preferência tipográfica

Ajuste solicitado pelo professor em 01/10/2026, a partir do ecrã de associação no telemóvel. Commits incrementais desde `d1d2556`.

Os símbolos passam a mostrar numerador, barra horizontal e denominador. A mesma representação aparece nas escolhas de associação, instruções de pintura, feedback, comparações e construção de 20 blocos. Os valores das respostas continuam a ser `n/d`; a seleção e a avaliação não mudaram. Os rótulos acessíveis dos controlos foram conservados. Foi adaptada uma expectativa existente do teste de browser à nova representação do feedback.

A atividade e a interface do Studio preferem Century Gothic, confirmada como instalada no sistema e disponível no browser de ensaio. Para os dispositivos que não tenham esta fonte, a Didact Gothic fica incorporada como WOFF2 no CSS e no HTML. Não há pedidos a serviços de fontes. [Fonte e licença originais](https://github.com/google/fonts/tree/main/ofl/didactgothic) conservadas em `assets/fonts/didact-gothic/`; o script `scripts/embed_gothic_font.py` repõe os blocos incorporados e foi verificado como idempotente. As instruções de Designer/Builder e o template passam a seguir esta preferência, com a regra detalhada na referência de adaptação à idade.

## Verificação

- Sintaxe do JavaScript inline validada com `node --check`.
- `uv run --with playwright pytest tests/test_fraction_draft_registration.py tests/test_schemas.py tests/test_validators.py -q`: **25 aprovados em 0,39 s**. Não foram acrescentados testes para a mudança de CSS. O teste de browser adaptado não foi executado, por não haver ligação CDP configurada.
- Browser colaborativo nativo do T3 Code, com a atividade real servida por HTTPS. A escolha de um quarto mostrou o numerador acima do denominador, barra de 2 px, estado selecionado e feedback "Ligaste as representações.". O alvo mede 80 px de altura.
- A Didact Gothic carregou a partir do data URL. O mesmo HTML foi renderizado num frame real de 390 px, forçando a alternativa Didact Gothic para representar um dispositivo sem Century Gothic: conteúdo de 375 px, sem transbordamento; numerador acima do denominador e botão de 80 px. As ferramentas de screenshot falharam; a medição e interação foram realizadas pelo DOM do browser.
- HTTPS confirmou o HTML atualizado com símbolos verticais e fonte incorporada, 131 747 bytes. `git diff --check` passou.

## Demonstração

[Experimentar as frações atualizadas](https://completely-paragraphs-percent-missions.trycloudflare.com/outputs/fraction-typography/index.html?presentation=1). O modo de demonstração permite escolher qualquer página, sem registos de alunos; escolher Mais desafios e 4. Associar reproduz o caso da imagem enviada.

Os ecrãs existentes de aluno e quadro da mesma instância descartável também recebem o HTML e CSS atualizados ao recarregar. Não houve alteração em produção ou nos dados da sessão.
