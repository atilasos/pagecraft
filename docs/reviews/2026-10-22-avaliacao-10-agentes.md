# Avaliação do PageCraft com dez agentes

## Base e método

Esta ronda começa em `4c6ba90`, depois das melhorias dos PRs #51 a #55.
O objetivo é avaliar o funcionamento, confrontar dez leituras independentes e
implementar as propostas com benefício pedagógico e evidência técnica.

As alterações locais preexistentes em `catalog.json` e nas atividades
`spike-prime-primeiros-movimentos` e `unidades-dezenas-2ano-30min` ficam fora
desta ronda. A avaliação e as implementações usam worktrees separados.

As dez frentes são autonomia e PIT; avaliação cooperada e comunicação;
diferenciação e inclusão; catálogo e descoberta; resiliência do trabalho;
feedback formativo e IA; pipeline e qualidade pedagógica; segurança e
privacidade; experiência do professor; criatividade didática e interação.

Cada agente deve ler código e páginas integrais da Sebenta e apresentar
propostas com problema, evidência, comportamento esperado, risco, esforço e
verificação. A seleção considera benefício para a criança ou professor,
gravidade do problema demonstrado, possibilidade de testar e independência
dos restantes trabalhos. Uma proposta criativa precisa de servir uma ação
pedagógica concreta.

## Fundamentação pedagógica

Consultadas pela API local da Sebenta em 22 de outubro de 2026:

- [[Avaliação Formativa]], `20_Wiki/Avaliação Formativa.md`. A informação
  recolhida serve a regulação quando permite ajustar o trabalho; os critérios
  precisam de ser apropriados pela criança.
- [[Avaliação Cooperada]], `20_Wiki/Avaliação Cooperada.md`. A participação
  na avaliação pressupõe participação na planificação. Os instrumentos
  apoiam decisões partilhadas e podem ser revistos pelo grupo.
- [[Diferenciação Pedagógica]], `20_Wiki/Diferenciação Pedagógica.md`.
  Variar apoios e organização conserva metas comuns e evita agrupamentos
  fixos que rotulem crianças.

As três páginas estão em estado `review`, com confiança `medium`. Estas são
sínteses da wiki. As decisões de produto desta ronda são propostas derivadas,
sem alegação de eficácia demonstrada em sala nem de conformidade legal.

## Verificação inicial

- `uv run pytest -q --ignore=tests/browser`: 337 testes aprovados.
- `node --test tests/js/activity_support.test.cjs`: 21 testes aprovados.
- `bash skills/sync-from-canonical.sh --check`: sem divergências.
- `PAGECRAFT_TEST_CDP=<CDP do Hub> uv run --offline --with playwright==1.63.0 pytest tests/browser -q`: 66 testes aprovados, em 109,70 segundos.

Os testes usam dados descartáveis. O browser pertence ao Agent Browser Hub;
as sessões e registos reais de produção ficam fora dos ensaios.

## Confronto das dez avaliações

Os [dez relatórios independentes](2026-10-22-auditorias/) conservam fontes,
evidências, estimativas, riscos e critérios de aceitação. As estimativas são
juízos dos agentes, não tempos medidos em sala ou compromissos de entrega.

| Frente | Proposta com maior interesse nesta ronda | Decisão |
|---|---|---|
| 01. Autonomia e PIT | Bilhete de regresso com a intenção da criança | Implementar sem impor nova reflexão |
| 02. Avaliação cooperada | Critérios discutidos e revistos pela turma | Desenhar participação e versões antes de implementar |
| 03. Diferenciação | Consultar pistas anteriores | Implementar consulta sem consumo nem juízo de utilidade |
| 04. Catálogo | Anos destinatários explícitos e comuns às interfaces | Implementar, sem deduzir escolaridade da idade |
| 05. Resiliência | Autoria entre separadores e fila individual persistente | Implementar ambas; bilhete coincide com 01 |
| 06. Feedback e IA | Seleção de ações revistas pela IA | Adiar até definir curadoria e ensaio de um obstáculo |
| 07. Pipeline | Artefactos isolados e aprovação vinculada ao que foi revisto | Implementar com teste de colisão entre gerações |
| 08. Privacidade | Stream do Quadro limitado à sessão atual | Implementar também a revogação de uma ligação já aberta |
| 09. Professor | Contexto do pedido de ajuda no primeiro toque | Implementar sem associar pistas de tarefas diferentes |
| 10. Criatividade | Duas pontes iguais vistas de cima | Preparar rascunho privado e testar o contraexemplo |

A seleção produz nove frentes de implementação. As falhas de autoria,
aprovação e projeção têm prioridade porque comprometem a confiança nos
registos. Bilhete, pistas e contexto docente usam informação já existente
para apoiar decisões. O rascunho das pontes testa uma proposta didática nova
com uma variável observável e um contraexemplo concreto.

O catálogo foi observado no browser da base: pesquisar Tinkercad e selecionar
o 3.º ano devolve "Sem resultados", embora a atividade declare 3.º e 4.º anos.
Captura em `/home/proteu/agent-browser-hub/screenshots/pagecraft-deep-catalogo-3ano-antes.png`.

## Propostas que exigem desenho ou ensaio posterior

- Critérios negociados, perfis disciplinares, convites e PIT no computador do
  par precisam de contratos de participação, versões e autoria próprios.
- O Momento de comunicação exige escolha explícita do recorte e controlo da
  sua retirada. Abrir todo o histórico no Quadro contrariaria a privacidade.
- A visibilidade pública de `/outputs` contradiz a noção atual de rascunho,
  mas está deliberadamente prevista no ADR-0004. A mudança exige inventariar
  endereços históricos e rever essa decisão.
- IA limitada a pistas revistas requer curadoria pedagógica. Um filtro de
  palavras não prova que uma pista livre é pertinente ou respeitosa.
- Recuperação curricular por tema e cenários executáveis por atividade
  merecem pilotos próprios; não são substituídos pelo isolamento de ficheiros.
- Plano de aula, comparação de estratégias, procura conjunta por vários anos,
  leitura das opções de apoio e novos mecanismos de revisão permanecem como
  propostas documentadas nos relatórios, sem alegação de implementação.

## Contrato de integração

Cada frente usa branch e worktree próprios, commits pequenos e dados
descartáveis. A revisão independente confronta o diff com os padrões do
repositório e com o âmbito selecionado. Achados acionáveis regressam à
implementação antes do PR ou merge. A verificação final combina as branches
para detetar interações que os testes isolados não mostram.

O rascunho das pontes pode ser integrado no repositório sem se tornar atividade
publicada. A revisão específica do professor continua a ser necessária antes
de o disponibilizar aos alunos, conforme a skill PageCraft e o ADR-0005.

## Revisão da avaliação e do comando de verificação

Duas revisões independentes sobre `4c6ba90...3c5befb`:

- Standards: zero violações documentadas. Uma observação operacional pediu
  execução offline no comando de verificação; acrescentado `--offline` nas
  duas invocações de uv.
- Spec: zero achados. Confirmados os dez relatórios, fontes e limites da
  Sebenta e separação entre seleção e implementação concluída.

O comando pressupõe dependências já instaladas ou em cache. Preparação inicial
do ambiente: `uv sync`; para preparar a dependência opcional de browser,
`uv run --with playwright==1.63.0 python -c 'import playwright'`. Os ensaios
usam o browser aberto pelo Hub, sem instalar ou lançar um browser paralelo.

## Standards das implementações

As revisões independentes identificaram duas violações documentadas, ambas
corrigidas e novamente revistas sem achados:

- Bilhete: intenções longas precisavam do limite de leitura do `DESIGN.md`.
  Os textos ficam limitados a 50ch, com ensaio a 320px.
- Contexto de ajuda: um `student_id` também pode indicar destinatário de uma
  mensagem docente ou do assistente. A cronologia passou a consultar o autor
  no vocabulário central e a apresentar o destinatário separadamente.

Catálogo, fila individual, autoria das realizações, Quadro e gerações isoladas
receberam pareceres Standards sem violações documentadas ou smells acionáveis.
As cópias canónicas das pistas continuam sincronizadas.

## Spec das implementações

A primeira revisão encontrou cinco problemas de cumprimento dos contratos:

- Quadro: B podia nascer durante uma leitura assíncrona da seleção de A.
  A revisão da seleção no serviço obriga a repetir a consulta quando criação,
  retoma ou fecho a invalidam. A reprodução independente deixou de emitir
  a mensagem antiga depois da mudança.
- Bilhete: rever só a estratégia apagava a intenção anterior. Vazio mantém
  o passo guardado, texto novo substitui e retirar exige escolha explícita.
- Autoria: depois de concluir e expirar a credencial, a referência local
  impedia começar outra realização. A saída explícita verifica ausência de
  pendentes e remove apenas a referência do separador. O conflito A/B continua
  a impedir substituição e os dados incertos são conservados.
- Histórico de pistas: a retoma perdia os discriminantes de tarefa e revisão.
  Os novos acontecimentos conservam esses campos sem inventar dados antigos.
- Histórico de pistas: ouvir uma pista noutro painel mudava a tarefa ativa e
  cancelava um pedido IA. A consulta é tratada antes da mudança de unidade.

Os três primeiros receberam segunda revisão Spec sem achados. A segunda
revisão das pistas e do contexto docente e a avaliação final do novo rascunho
ainda estão em curso neste ponto do registo.

## Integração local

O checkout `review/integracao-melhorias-10-agentes` combina as branches antes
dos merges no GitHub. As sobreposições na publicação e interface infantil
foram resolvidas preservando os dois contratos de cada lado. Os PRs dependentes
expõem essas relações: catálogo antes de gerações; fila antes de bilhete.

A combinação de anos declarados e publicação revista tem regressões próprias
de repetição idempotente e rejeição de metadados inválidos antes da instalação.
Os 94 testes focados passaram; o revisor repetiu 134 testes e um percurso completo
de geração, preview, aprovação e restart, verificando bytes e anos no catálogo/API.

A verificação geral intermédia encontrou uma expectativa antiga no teste do
cookie, que não admitia a versão da identidade devolvida no claim. Atualizada
para verificar também a mesma versão na retoma, mantendo a ausência de credencial
no corpo e os atributos HttpOnly. Os 18 testes de cookie e API relacionados passaram.
