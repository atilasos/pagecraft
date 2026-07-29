# Os nomes com que um acontecimento atravessa para dentro da atividade são congelados e append-only

Cada acontecimento de sessão que atravessa para dentro de uma atividade tem dois nomes: o nome interno do servidor e o **nome na ponte**, que a atividade conhece. Hoje o servidor diz `teacher_highlight` e a atividade diz `highlight`. Os dois nomes ficam declarados como campos distintos do vocabulário de acontecimentos, e os nomes na ponte **nunca se renomeiam — apenas se acrescentam**, porque estão gravados no recetor injetado em cada atividade publicada e não há forma de os atualizar sem reescrever ficheiros já entregues. Decidido em 2026-07-29, ao unificar o vocabulário de Acontecimento de sessão.

## Consequences

- Quem ler o código vai encontrar dois nomes para o mesmo acontecimento e ler isso como descuido. **Não é.** Uniformizar os nomes parte, em silêncio, todas as atividades já publicadas: elas deixam simplesmente de reagir, sem erro, sem log, sem teste vermelho. À data da decisão eram 103.
- A alternativa era uma varredura pelas atividades publicadas a cada renomeação. Rejeitada: as atividades são artefactos entregues e self-contained, e reescrevê-las em lote a cada mudança de vocabulário contraria essa natureza.
- O custo assumido é vocabulário que envelhece: nomes na ponte mal escolhidos ficam. O preço de um nome feio é menor do que o de uma atividade que deixa de responder a meio de uma aula.
- Renomear é possível, mas é uma operação deliberada e datada — acrescentar o nome novo, publicar atividades que o usem, e só remover o antigo quando nenhuma atividade viva o usar. Nunca uma substituição.
