# Trabalho a pares e em grupo

Estado em 30/09/2026: definição do percurso, antes da implementação. Continuação do pedido do professor sobre atividades cooperativas em que atualmente só consegue entrar um aluno.

## Pedido confirmado

As crianças devem poder indicar que trabalham a pares ou em grupo e identificar os participantes. O trabalho cooperativo não deve aparecer apenas em nome da criança que entrou no dispositivo. O campo «Turma» não representa membros de um grupo.

A revisão de Frações está concluída como rascunho para revisão do professor; a identificação dos participantes é um trabalho separado, conforme a [especificação](fracoes-banda-desenhada-spec.md).

## Decisões em aberto

Primeira ronda apresentada ao professor:

1. Quem forma o grupo num computador partilhado: os alunos selecionam os participantes da turma ou o professor prepara os grupos?
2. A reflexão final é individual ou conjunta? Proposta em discussão: respostas da atividade como trabalho conjunto associado aos participantes; autoavaliação de cada criança.

Estas propostas ainda não foram confirmadas. Não implicam atribuir a cada criança uma resposta individual que só foi observada como resposta do grupo.

Depois destas escolhas, definir o âmbito de entrada (sessão de aula e realização por código), mudanças de composição, retoma, diferenciação e apresentação dos registos ao professor. Consultar o comportamento existente antes de perguntar por factos do sistema.

## Comportamento atual verificado

- Na sessão de aula, o código abre a lista da turma; a criança escolhe um único nome. Os nomes ocupados ficam indisponíveis. A reserva e a credencial representam um aluno, e o servidor atribui-lhe os acontecimentos (`server/static/student/app.js`, `server/classroom/service.py`).
- A reentrada recupera a identidade anterior do dispositivo. Históricos, triagem, pedidos de ajuda e relatórios agregam por aluno (`server/access.py`, `server/classroom/session_state.py`, `server/reports.py`). Uma seleção múltipla só na interface seria insuficiente.
- No endereço permanente, a entrada usa nome livre e turma opcional, sem ligação à lista da turma. Cada realização tem uma credencial, um estado e uma autoavaliação (`server/static/learning/activity.html`, `server/learning.py`).
- O domínio define a autoavaliação como voz do aluno, distinta das evidências observadas e da interpretação do professor (`CONTEXT.md`). Uma reflexão conjunta exigiria explicitar essa autoria.

## Limites

Nenhuma alteração funcional implementada nesta fase. Preservar as realizações individuais e os trabalhos existentes. A aprovação do rascunho de Frações para publicação é independente destas decisões.
