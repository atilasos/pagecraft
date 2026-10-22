# Verificação da entrada e produção conjunta

Em 30/09/2026, a etapa [#43](https://github.com/atilasos/pagecraft/issues/43) foi implementada no ramo `t3code/melhorar-usabilidade-atividades`. Os alunos escolhem Sozinho, A pares ou Em grupo, confirmam participantes e nível e trabalham no mesmo dispositivo. A reserva é indivisível. O professor consulta grupos, participantes e produção conjunta, sem multiplicar as respostas nem apresentá-las como resultados individuais.

## Comportamentos verificados

- Reserva de dois ou três participantes, disputa entre dispositivos, composição inválida e recusa de nomes exteriores à turma, sem reservas parciais.
- Credencial HttpOnly própria do grupo; retoma dos participantes e nível validados pelo servidor. A credencial não entra no JavaScript nem nas projeções públicas. O dispositivo não consulta históricos individuais nem o trabalho de outros grupos.
- Uma tentativa conjunta fica uma vez no registo e no total da sessão. Os históricos dos membros apontam para o mesmo acontecimento, com autores identificados. Os números individuais não recebem cópias da tentativa.
- Pedidos de ajuda e feedback têm autoria conjunta. O serviço de feedback reconhece o grupo, responde ao destinatário correto e não repete respostas após reiniciar.
- O nível comum altera a atividade e conserva os perfis individuais. Mudanças feitas nos controlos antigos também chegam ao anfitrião. Uma mudança ainda por enviar não é substituída por uma projeção anterior da sessão.
- A libertação pelo professor de um membro revoga o dispositivo inteiro, liberta as reservas e conserva o histórico. O encerramento impede novo trabalho.
- A entrada individual continua disponível e abre o rascunho registado sem o publicar. O plano individual fica disponível só nesta entrada.

## Testes automáticos

```sh
uv run --with playwright pytest -q
node --check server/static/student/app.js
node --check server/static/teacher/class.js
```

Resultado final da suite: **260 aprovados, 54 omitidos, em 10,58 s**. Os 54 são testes de browser: a fixture existente exige `PAGECRAFT_TEST_CDP`, que não foi configurado nesta sessão. A sintaxe dos dois clientes e `git diff --check` passaram. Não se apresentam esses testes omitidos como executados.

A regressão de feedback passou de ausência de resposta para resposta conjunta única. Os testes HTTP exercitam as interfaces de aluno/professor com dados descartáveis, incluindo concorrência de reserva, validação, autoria, relatórios, stream, revogação e encerramento. Acrescentaram-se regressões de browser para os cartões iniciais do professor, nível pendente, retoma e entrada individual em rascunho; ficam disponíveis para a fixture existente.

## Browser real e limites

Foi usado o browser colaborativo nativo do T3 Code, através de HTTPS temporário, com uma instância de Studio e dados fictícios. O browser partilhado não alcançava o loopback da origem, pelo que se usou o túnel autorizado. Não se alterou a implantação de produção.

No percurso do aluno, foram ensaiados um par e um grupo de três: confirmação bloqueada enquanto faltam nomes, confirmação válida, abertura de Frações, nível comum, resposta errada com pista visual, pedido de ajuda e retoma da composição. A tentativa real do par foi confirmada pela API do professor: um acontecimento conjunto, presente nos dois históricos, com contagem única. A entrada individual abriu também o rascunho. A entrada e o cabeçalho foram inspecionados a 390, 768 e 1280 px; os nomes têm alvos de 56 px e não houve transbordamento horizontal no anfitrião.

A mudança pendente foi reproduzida retendo os envios de nível com resposta HTTP 503 e fazendo chegar outra atualização real da sessão. Antes da correção o cabeçalho voltava a Com pistas; depois conservou Mais desafios e sincronizou esse nível quando os envios voltaram a estar disponíveis.

O HTML e JavaScript reais do professor foram ensaiados com uma captura das respostas HTTP autorizadas e do snapshot real da sessão, num transporte de demonstração só de leitura. Isso revelou cartões criados mas não inseridos no primeiro snapshot; a correção passou de zero para quatro cartões. O grupo, o pedido de ajuda e os históricos de Ana e Bruno mostram a autoria conjunta. Esta vista testa renderização com dados do ensaio; **não constitui teste de autenticação remota ou ligação SSE contínua de professor**. As permissões são verificadas por HTTP. O percurso remoto completo pertence à etapa #45.

Uma matriz no browser carregou sete HTML publicados reais com o adaptador de produção: Frações, Bota, Árvore, Canva, Classificar objetos, Dobro até 10 e Dedo. A leitura de teste do DOM confirmou os controlos selecionados, incluindo `standard`, `middle`, `intermedio`, `medio` e os nomes portugueses. O rascunho de Frações confirmou o seu seletor próprio. As atividades publicadas não foram reescritas.

## Revisão

Base fixa: `65e4c47f615036a6f02726367565c9a9e66f22fb`. Revisões Standards e Spec independentes; os dois achados de especificação foram corrigidos: compatibilidade dos níveis e identificação dos autores no histórico.

### Standards

Sem infrações documentadas ou bloqueios. Permanecem duas sugestões de manutenção: reunir os ciclos de ingestão individual/conjunta e representar o destinatário do feedback num único valor de domínio. São sugestões, não falhas funcionais desta entrega.

### Spec

Sem achados bloqueantes na etapa #43 após as correções. Reflexão por participante (#44), alteração de composição pelo professor e verificação remota integral (#45) continuam pendentes. A retoma aqui preserva identidade e nível; não promete restauro de manipulações em HTML antigos.

## Demonstração temporária

- [Aluno](https://democratic-program-nurses-smile.trycloudflare.com/student/): código **JF423S**, oito nomes fictícios disponíveis no fim do ensaio. Escolher modo, nomes, nível e Começar.
- [Vista do professor](https://democratic-program-nurses-smile.trycloudflare.com/outputs/groups-teacher/index.html?v=4): fotografia só de leitura do ensaio anterior de Ana + Bruno; permite consultar os percursos. Não acompanha os novos envios da demonstração do aluno.

A origem é `127.0.0.1:18781`, com raiz descartável `/tmp/pagecraft-groups-43-lw7de0b_` e configuração explícita de dados, atividades e outputs isolados. A origem e o Quick Tunnel precisam de permanecer ativos. O endereço e o código são temporários. Para encerrar apenas esta demonstração, terminar os processos de `/tmp/pagecraft-groups-resume.py` e do túnel correspondente; os dados de produção não são afetados.
