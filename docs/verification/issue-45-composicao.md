# Correção de participantes durante a aula, #45

Implementação no ramo `t3code/melhorar-usabilidade-atividades`, verificada em 01/10/2026. Base fixa: `e23e71b335de7cbc650506d34e1c0be689835afc`. O professor confirmou o ensaio por toque no quadro/tablet: escolha dos participantes, reflexão de cada criança e gravação de uma troca de participantes no professor. O critério de aceitação restante está concluído.

## Comportamento

Só o professor pode alterar os participantes de um grupo iniciado. O editor consulta a disponibilidade atual, impede a seleção de alunos ocupados noutro dispositivo e confirma a operação no servidor. Reservas e libertações acontecem em conjunto; um conflito não deixa metade do grupo reservado.

Cada composição tem uma identificação e versão próprias. O dispositivo mantém a sua identidade ao mudar de composição. Os acontecimentos anteriores conservam os nomes e participantes originais; os novos usam a composição confirmada. A retoma após reiniciar o servidor conserva ambos os históricos.

Os envios pendentes guardam a versão e o nome do grupo que os produziu. O servidor recusa uma resposta nova de outra composição com HTTP 409 e identifica os envios em conflito. Repetir um envio antigo já aceite continua a ser idempotente. O dispositivo mostra as respostas pendentes com os nomes originais; esse arquivo não impede novos envios.

As reflexões anteriores mantêm o autor individual. A criança que continua no dispositivo pode rever a sua voz guardada; não recebe a dos colegas removidos. Rascunhos de uma composição anterior ficam identificados e acessíveis localmente para revisão com o professor. Abrir a versão atual conserva a cópia antiga, incluindo depois de guardar outra reflexão e recarregar. O arquivo local não é apresentado como sincronizado nem atribuído ao novo grupo.

A troca não recarrega a atividade. O nível confirmado volta a ser enviado ao iframe, aplicando a política de mudança de nível da própria atividade. A libertação revoga a composição atual; o encerramento bloqueia os envios e conserva o histórico.

## Testes automáticos

```sh
uv run --with playwright pytest -q
node --check server/static/student/app.js
node --check server/static/student/reflection.js
node --check server/static/teacher/class.js
git diff --check
```

Resultado: **268 aprovados, 59 omitidos, em 11,37 s**. Sintaxe dos clientes e verificação do diff passaram. Os 59 testes de browser exigem `PAGECRAFT_TEST_CDP`, não configurado porque nesta sessão foi usado o browser colaborativo nativo do T3 Code. Não são apresentados como executados.

Os 21 testes HTTP de grupos passaram. As novas regressões exercitam alteração pelo professor, autoria antes/depois, conflito de composição, revisões individuais, reservas indivisíveis, recusas de edição pelo aluno, revogação atual e retoma após reiniciar a aplicação. As falhas iniciais observáveis foram endpoint inexistente, aceitação indevida de resposta antiga e histórico anterior ausente na retoma. Os testes usam as interfaces públicas de aluno/professor, sem consultar a persistência interna.

Foram acrescentadas duas regressões de browser: fila antiga cheia e reconciliação do nível durante a troca; preservação do rascunho depois de abrir a versão atual, guardar e recarregar. Estão entre os testes omitidos. Os casos foram exercitados separadamente no browser real, como descrito abaixo.

## Browser real e HTTP da demonstração

A instância usa cópias dos ficheiros reais e dados fictícios, isolados em `/tmp/pagecraft-groups45-crhla4dw`. Aluno e professor têm origens distintas. O professor da demonstração faz operações reais através de um gateway limitado aos percursos de aula dessa instância; a credencial fica no servidor do gateway.

O professor mudou Ana + Bruno para Ana + Carla pelo formulário real. O aluno recebeu os novos nomes no mesmo iframe. Uma tentativa errada aceite antes da troca ficou apenas com Ana + Bruno; uma tentativa certa posterior ficou apenas com Ana + Carla. O histórico de Bruno mostrou zero tentativas individuais e distinguiu o trabalho conjunto da sua reflexão. A API real confirmou:

| Participante | Tentativas conjuntas registadas |
| --- | --- |
| Ana | Uma com Bruno; uma com Carla |
| Bruno | Só a anterior com Ana |
| Carla | Só a posterior com Ana |

Um envio correto anterior à troca, retido por uma falha HTTP 503 no browser, continuou no arquivo local e não entrou no histórico de Carla. Foram feitas várias trocas no ensaio para verificar os casos seguintes.

Com 200 acontecimentos pendentes, o cliente anterior recusava trabalho novo. Depois da correção, conservar esses acontecimentos não impediu novos envios. Durante a mesma falha de rede, o cabeçalho voltava a Passo a passo e a atividade ficava em Mais desafios; a correção reconciliou ambos, sem recarregar o iframe.

O browser confirmou a perda de um rascunho ao abrir a versão guardada antes da correção. Depois, o rascunho original de Bruno, "Foi o corte ao meio que me ajudou.", continuou acessível após guardar "Agora observei com a Ana." e recarregar. Apenas a nova reflexão foi sincronizada; a antiga conserva a indicação de estar por guardar.

Eva + Filipe entraram noutro dispositivo HTTP com histórico/reflexões vazios e edição recusada com 403. Duarte entrou individualmente e a sua tentativa continuou individual. O editor real do professor apresentou esses três alunos indisponíveis. Nenhuma destas reservas alterou o grupo de Ana.

O quadro mostrou o código, o professor confirmou-o pelo formulário e ambos confirmaram o emparelhamento. Abriu a atividade em `presentation=1`. Manipular os seus controlos não criou respostas de alunos. Depois de fechar a sessão, o aluno mostrou o histórico com autores originais e desativou ajuda/nível; o quadro aguardou e abriu a sessão seguinte.

As ferramentas nativas de screenshot, apontador e redimensionamento tiveram falhas. Os controlos/formulários reais foram ativados pelo DOM do browser; o teclado Enter confirmou a edição. Para o iframe opaco da atividade, um adaptador descartável de QA ativou os botões reais e devolveu o texto apresentado, sem inventar acontecimentos de negócio. Para medir as larguras, as páginas reais foram carregadas em frames do browser de 390 e 768 px. Não houve transbordamento horizontal: larguras de conteúdo 375 e 753 px. No editor, etiquetas de 64 px e botões de 48 px; no aluno, ações de 56 px e seletor de 48 px. Estas medições não substituem um ensaio de toque físico.

## Transporte dos endereços temporários

[Quick Tunnels não suportam SSE](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/). O primeiro gateway HTTP confirmou eventos na origem local, mas o túnel público não os entregava ao cliente. Apenas nesta instância descartável, um adaptador traduz os frames reais do fluxo HTTP para WebSocket e repõe os eventos no cliente. Não contém snapshots simulados, não altera o código de produção e não prova o transporte SSE do domínio de produção.

O endereço público de aluno respondeu 200 e recusou professor/bootstrap não autenticados com 401. O gateway de professor respondeu 200 aos percursos de aula e recusou configuração/jobs com 403. Não foram alterados produção, DNS ou Access.

## Revisão

Duas revisões independentes da skill code-review, contra a base fixa indicada.

### Standards

Sem violações documentais. Encontrou o bloqueio da fila cheia e a eliminação do rascunho anterior. Ambos corrigidos; revisão final sem bloqueadores. Os revisores não executaram os testes de browser.

### Spec

Encontrou o bloqueio da fila cheia e a diferença entre o nível confirmado e o nível do iframe. Ambos corrigidos; revisão final sem requisitos de código pendentes ou alargamento de âmbito.

Resultado de código: zero bloqueadores em ambas as frentes. O ensaio por toque foi confirmado pelo professor, concluindo a aceitação.

## Demonstração para o professor

- [Aluno](https://completely-paragraphs-percent-missions.trycloudflare.com/student/), código **CFQLE2**.
- [Professor ao vivo](https://balloon-icon-adaptation-archive.trycloudflare.com/teacher/class.html).
- [Quadro](https://completely-paragraphs-percent-missions.trycloudflare.com/board/).

Foi preparada uma sessão nova, com seis nomes fictícios disponíveis. A sessão anterior e os seus relatórios conservam a evidência do ensaio. Os endereços dependem dos processos locais e dos túneis temporários ativos.

## Confirmação do professor

Na conversa de 01/10/2026, à pergunta sobre escolher os participantes, responder à reflexão de cada criança e guardar uma troca de participantes no professor durante o teste por toque no quadro/tablet, o professor respondeu: «Sim, esses percursos funcionaram».

Esta é evidência do ensaio realizado pelo professor no equipamento, distinta das verificações automatizadas e das interações por DOM descritas acima. Conclui o critério de toque que mantinha #45 aberto e permite concluir a especificação de grupos #42. Não corresponde a uma implantação em produção.
