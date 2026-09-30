# Trabalho conjunto e reflexão individual nas sessões de aula

Estado: regras pedagógicas, cobertura e etapas confirmadas pelo professor em 30/09/2026. Esta especificação dá continuidade ao pedido de identificar todos os participantes de um computador partilhado. Publicada como [especificação #42](https://github.com/atilasos/pagecraft/issues/42).

## Problema

As atividades propõem colaboração, mas a entrada permite escolher apenas um aluno. Todas as respostas, pedidos de ajuda e reflexões ficam associados a essa identidade. O professor não consegue distinguir uma produção conjunta do trabalho individual nem reconhecer os restantes participantes.

## Solução

Na Sessão de aula, os alunos escolhem «Sozinho», «A pares» ou «Em grupo», selecionam os participantes da turma e trabalham juntos no mesmo computador. O professor vê os membros e o trabalho conjunto. O grupo escolhe o nível comum e pode mudá-lo. No final, cada criança faz a sua Autoavaliação da realização, identificada pelo seu nome.

Depois de começar, só o professor altera os participantes. As respostas conservam a composição do grupo que as produziu. O endereço permanente da atividade continua fora desta primeira implementação.

## Histórias de utilização

1. Como aluno, quero escolher se trabalho sozinho, a pares ou em grupo para identificar quem participa.
2. Como aluno, quero selecionar os nomes da turma para não ter de escrever os nomes dos meus colegas.
3. Como aluno, quero ver os nomes selecionados antes de começar para corrigir uma escolha acidental.
4. Como aluno, quero saber se um colega já está noutro dispositivo para pedir ajuda ao professor.
5. Como aluno, quero entrar com todos os colegas selecionados para o trabalho não ficar só em meu nome.
6. Como participante, quero escolher um nível comum com o grupo para trabalhar num desafio adequado.
7. Como participante, quero mudar o nível durante o trabalho para experimentar outro apoio sem alterar o meu perfil individual.
8. Como participante, quero que as respostas sejam reconhecidas como trabalho conjunto para não atribuírem a cada criança uma resposta individual que não foi observada.
9. Como participante, quero que um pedido de ajuda identifique o grupo para o professor saber onde intervir.
10. Como participante, quero voltar ao mesmo dispositivo e reconhecer o grupo para continuar na sessão.
11. Como participante, quero ver o meu nome na minha reflexão para distinguir a minha voz da dos colegas.
12. Como participante, quero escolher a minha autoavaliação sem copiar a escolha dos outros.
13. Como participante, quero poder deixar perguntas de reflexão por responder para manter o caráter facultativo da autoavaliação.
14. Como participante, quero que a minha reflexão não desapareça quando outro colega faz a sua.
15. Como professor, quero ver os grupos e os seus membros para acompanhar a turma.
16. Como professor, quero consultar uma produção conjunta através de qualquer participante, vendo a autoria do grupo.
17. Como professor, quero distinguir trabalho conjunto e autoavaliação individual nos relatórios para interpretar a evidência com rigor.
18. Como professor, quero alterar participantes quando necessário para corrigir a composição durante a aula.
19. Como professor, quero conservar a autoria anterior depois de uma alteração para não reatribuir respostas passadas.
20. Como professor, quero que a libertação de identidades e o encerramento da sessão respeitem os participantes para evitar reservas ou acessos incoerentes.
21. Como professor, quero que a entrada individual e os trabalhos antigos continuem legíveis para usar as atividades existentes.
22. Como professor, quero experimentar o percurso aluno/grupo/professor num endereço temporário para rever a experiência.

## Decisões de implementação

### Entrada e participantes

- O primeiro recorte aplica-se exclusivamente a Sessões de aula com lista da turma, num dispositivo por grupo. Não acrescentar colaboração sincronizada entre dispositivos.
- «Sozinho» seleciona um participante, «A pares» dois e «Em grupo» três ou mais. O número máximo é limitado pela turma disponível, sem impor um tamanho pedagógico arbitrário.
- A seleção precisa de confirmação antes de reclamar os nomes. O servidor valida participantes únicos, pertencentes à sessão e disponíveis. Reclamar o conjunto é uma operação indivisível: um conflito não reserva parcialmente o grupo.
- Não substituir a identidade do grupo pela credencial de um dos membros. O acesso do dispositivo representa o conjunto autorizado; o servidor decide a autoria e não aceita atribuições arbitrárias vindas da atividade.
- Os alunos podem corrigir a seleção antes de começar. Depois do início, a alteração pertence ao professor.
- A retoma no mesmo dispositivo usa a autorização validada pelo servidor e mostra a composição atual. Preservar o trabalho já registado e as reflexões individuais. Não prometer recuperação de manipulações em atividades que não suportam restauro.

### Trabalho e diferenciação

- O acontecimento conjunto tem uma autoria canónica do grupo e conserva os membros participantes nesse momento. Associá-lo aos membros não significa duplicá-lo como acontecimentos individuais.
- Históricos e relatórios identificam explicitamente a produção conjunta. Uma resposta certa ou errada do grupo não demonstra, por si só, a competência de cada membro.
- Pedidos de ajuda e acompanhamento do trabalho conjunto permitem ao professor intervir junto do grupo. Manter as ações individuais já existentes identificadas com o respetivo aluno.
- O grupo escolhe livremente o nível comum. Mostrar «Com pistas», «Passo a passo» e «Mais desafios»; usar Passo a passo como escolha inicial neutra e pedir a confirmação do grupo ao começar. Não escolher automaticamente o perfil mais baixo ou mais alto.
- A mudança de nível pertence ao trabalho conjunto e não altera os Perfis de diferenciação individuais. Respeitar a invalidação de respostas definida por cada atividade.
- Conservar os nomes congelados na ponte. A autoria dos acontecimentos é resolvida pelo anfitrião e pelo servidor, sem exigir que cada HTML invente autenticação ou atribuição aos membros.

### Reflexão e conclusão

- As respostas de exploração pertencem ao grupo; as Autoavaliações da realização pertencem individualmente às crianças.
- O dispositivo apresenta os participantes para fazerem a reflexão à vez, mostrando claramente de quem é a reflexão aberta. Guardar cada reflexão sem substituir as outras.
- Usar os critérios disponíveis da atividade. Não inventar uma classificação do grupo nem repartir uma nota pelos membros.
- A autoavaliação é facultativa. Cada criança pode responder, rever ou indicar que prefere não responder; a falta de respostas não é tratada como erro.
- O anfitrião disponibiliza o percurso de reflexão individual e evita transformar a reflexão interna de uma atividade antiga numa reflexão conjunta atribuída automaticamente a todos.
- Conservar a distinção entre evidência observada, voz individual e interpretação do professor. Fechar a sessão segue o ciclo de vida existente.

### Alteração pelo professor

- O professor pode corrigir a composição do grupo depois de começar. Validar novas reservas e libertações como uma operação coerente.
- Uma alteração vale para o trabalho posterior. Não reescrever membros em respostas ou reflexões já guardadas.
- Preservar o contexto das respostas pendentes de sincronização. Uma resposta gerada antes da alteração não passa silenciosamente a pertencer à nova composição; validar a versão de composição no servidor e tornar os conflitos visíveis.
- A interface do dispositivo apresenta a composição atualizada. Uma credencial ou reserva revogada não continua a autorizar operações indevidas.
- Manter a libertação de identidade e o encerramento da sessão coerentes com a reserva do grupo; preservar trabalho por defeito.

### Apresentação

- Instruções curtas, nomes legíveis, seleção visível e controlos adequados a toque e teclado. Nenhum detalhe de autenticação aparece no percurso infantil.
- Nas áreas do professor, permitir reconhecer membros e consultar o trabalho comum, mostrando a autoria conjunta e a reflexão de cada participante.
- Aplicar o mesmo modelo de identidade às atividades da sessão sem impor a divisão de páginas ou a apresentação de Frações às outras atividades.

## Decisões de teste

Validar principalmente o comportamento observado pelas crianças e pelo professor. Usar os percursos de entrada, atividade, reflexão e acompanhamento no browser, apoiados pelas interfaces HTTP existentes para confirmar autoria, reservas e persistência. As fronteiras de testes já exercitadas para reservas concorrentes, cookies, libertação de identidade, históricos, triagem e relatórios são o precedente; evitar persistência paralela ou testes que apenas repitam detalhes internos.

- Percorrer individual, par e grupo: seleção, confirmação, trabalho conjunto, acompanhamento e retoma da identidade.
- Reproduzir dois dispositivos a tentar reservar um membro comum; exatamente um entra, sem reservas parciais ou atribuição indevida.
- Confirmar que um acontecimento conjunto é guardado uma vez, associado aos participantes certos e identificado como produção do grupo nos históricos e relatórios.
- Verificar pedidos de ajuda, nível comum e mudança livre sem alteração dos perfis individuais.
- Guardar duas reflexões diferentes de um par e uma reflexão omitida; confirmar que cada uma pertence ao participante certo e que reenvios não duplicam nem substituem a voz dos colegas.
- Alterar participantes pelo professor, incluindo respostas pendentes; verificar a autoria antes e depois, reservas, atualização do dispositivo e revogação.
- Verificar recusa de alterações pelos alunos, isolamento entre grupos e impossibilidade de atribuir reflexão a um participante alheio ao dispositivo autorizado.
- Conservar os casos individuais e históricos anteriores, as permissões do Quadro e os nomes existentes na ponte.
- Experimentar por teclado e toque em computador, tablet e telemóvel. A integração final usa sessões e dados descartáveis, com revisão remota temporária no âmbito já autorizado.

O professor confirmou esta cobertura e a divisão em três entregas. Não foram executados testes da funcionalidade ainda inexistente.

## Fora deste recorte

- Entrada em grupo pelo endereço permanente, nomes livres e trabalho em casa.
- Colaboração sincronizada de um grupo em vários dispositivos.
- Formação prévia ou automática dos grupos pelo professor.
- Alteração dos perfis individuais a partir do nível escolhido pelo grupo.
- Atribuição automática de competência individual a partir de respostas conjuntas.
- Observação automática da construção externa em Minecraft.
- Publicação ou implantação em produção sem o fluxo aplicável.

## Notas

A revisão de Frações é uma fonte de casos de teste, mas não impõe a apresentação às restantes atividades. As decisões foram confirmadas em duas rondas da conversa: seleção pelos alunos e reflexão individual; sessões de aula primeiro, alterações pelo professor e nível comum escolhido pelo grupo. O campo interno «group» das realizações autónomas continua a significar turma.
