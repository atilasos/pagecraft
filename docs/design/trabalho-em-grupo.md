# Trabalho a pares e em grupo

Estado em 30/09/2026: regras do percurso confirmadas; especificação e etapas preparadas para revisão, antes da implementação. Continuação do pedido do professor sobre atividades cooperativas em que atualmente só consegue entrar um aluno.

## Pedido confirmado

As crianças devem poder indicar que trabalham a pares ou em grupo e identificar os participantes. O trabalho cooperativo não deve aparecer apenas em nome da criança que entrou no dispositivo. O campo «Turma» não representa membros de um grupo.

A revisão de Frações está concluída como rascunho para revisão do professor; a identificação dos participantes é um trabalho separado, conforme a [especificação](fracoes-banda-desenhada-spec.md).

## Decisões confirmadas

- Os alunos escolhem «Sozinho / A pares / Em grupo» no computador partilhado e selecionam os participantes da turma. O grupo fica visível ao professor.
- As respostas da atividade constituem trabalho conjunto, associado a todos os participantes e identificado como produção do grupo.
- Cada criança faz a sua autoavaliação individual. Uma resposta conjunta não é convertida numa demonstração individual de cada participante.
- Começar nas sessões de aula com lista da turma. A entrada em grupo pelo endereço permanente fica para outro recorte.
- Depois de começar, só o professor altera os participantes. Preservar quem participou nas respostas anteriores.
- O grupo escolhe e pode mudar o nível comum entre «Com pistas», «Passo a passo» e «Mais desafios», mesmo quando os perfis individuais são diferentes.

## Preparação da implementação

As decisões pedagógicas desta ronda estão confirmadas. A [especificação](trabalho-em-grupo-spec.md) e as [etapas propostas](trabalho-em-grupo-etapas.md) consolidam o percurso. Falta validar a divisão em entregas e a cobertura pelos percursos reais de aluno e professor, antes de publicar os tickets.

## Comportamento atual verificado

- Na sessão de aula, o código abre a lista da turma; a criança escolhe um único nome. Os nomes ocupados ficam indisponíveis. A reserva e a credencial representam um aluno, e o servidor atribui-lhe os acontecimentos (`server/static/student/app.js`, `server/classroom/service.py`).
- A reentrada recupera a identidade anterior do dispositivo. Históricos, triagem, pedidos de ajuda e relatórios agregam por aluno (`server/access.py`, `server/classroom/session_state.py`, `server/classroom/reports.py`). Uma seleção múltipla só na interface seria insuficiente.
- No endereço permanente, a entrada usa nome livre e turma opcional, sem ligação à lista da turma. Cada realização tem uma credencial, um estado e uma autoavaliação (`server/static/learning/activity.html`, `server/learning.py`).
- O domínio define a autoavaliação como voz do aluno, distinta das evidências observadas e da interpretação do professor (`CONTEXT.md`). Uma reflexão conjunta exigiria explicitar essa autoria.

## Limites

Nenhuma alteração funcional implementada nesta fase. Preservar as realizações individuais e os trabalhos existentes. A aprovação do rascunho de Frações para publicação é independente destas decisões.
