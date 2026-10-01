# Retomar o trabalho de uma turma entre aulas

O professor pode continuar uma atividade já realizada pela mesma turma. A sessão conserva identidade, grupos, autoria, respostas e reflexão, mas cada reativação abre uma nova janela de aula, com códigos e credenciais renovados. A escolha explícita «Começar novo trabalho» cria outra sessão e conserva a anterior.

Uso: selecionar turma e atividade → «Continuar trabalho» → projetar códigos → cada grupo escreve o seu código em `/student/` → recuperar o trabalho guardado no servidor. A retoma funciona noutro computador, sem depender de um separador aberto.

## Decisão

Conservar o registo da sessão e acrescentar o acontecimento `session_resumed`. A janela ativa tem a sua data de início, distinta do início original do trabalho. Fechar a janela conserva os acontecimentos. Os limites de oito horas e de fim do dia continuam a aplicar-se à aula e às credenciais, conforme ADR-0004.

Cada grupo atual recebe um código de oito caracteres, usado apenas para reclamar esse grupo na aula ativa. O código é consumido na entrada e substituído por um cookie HttpOnly. O professor pode emitir outro código para mudar de computador. A retoma não recria participantes nem duplica evidências. Códigos projetados mostram nomes e estado de entrada, sem respostas ou reflexões.

A página da atividade continua a comunicar por `postMessage`. O anfitrião conserva os objetos de declaração e checkpoints `activity_state`, e envia `learning_restore` com o histórico autorizado antes de permitir novo trabalho. Checkpoints não contam como evidência nem entram na linha do tempo. As declarações de trabalho são distintas da antiga autoavaliação conjunta, que continua recusada.

## Alternativa considerada

Criar uma realização independente que agregasse várias sessões exigiria transferir autoria, grupos, reflexões e relatórios existentes para outro proprietário. Nesta alteração, a sessão já reúne esses dados e pode conservar o registo enquanto renova a janela de acesso. Uma realização agregadora só se justifica quando houver requisitos de combinar sessões ou atividades diferentes.

## Limites

O código dá acesso ao trabalho do grupo correspondente, apenas durante a aula ativada pelo professor. Escrever o mesmo nome continua sem conceder acesso a históricos: os nomes usados individualmente ficam reservados na retoma e só o professor pode libertá-los para autorizar outra entrada. Uma página antiga que não implemente `learning_restore` conserva as evidências no servidor, mas não recupera automaticamente manipulações do seu HTML. O Canva mantém o seu próprio design e acesso; estes códigos recuperam os registos PageCraft.
