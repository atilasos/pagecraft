# Etapas de trabalho em grupo

Estado: divisão e cobertura aprovadas pelo professor em 30/09/2026. Publicados os tickets [#43](https://github.com/atilasos/pagecraft/issues/43), [#44](https://github.com/atilasos/pagecraft/issues/44) e [#45](https://github.com/atilasos/pagecraft/issues/45), associados à [especificação #42](https://github.com/atilasos/pagecraft/issues/42). Etapa 1 implementada e verificada no ramo; ver [evidência da entrega #43](../verification/issue-43-grupos.md). Etapa 2 implementada e verificada; ver [evidência da reflexão individual #44](../verification/issue-44-reflexoes.md). Etapa 3 implementada e revista; ver [evidência da correção de composição #45](../verification/issue-45-composicao.md). O professor confirmou o ensaio por toque no quadro/tablet em 01/10/2026. As dependências nativas foram verificadas: #44 depende de #43; #45 depende de #43 e #44. A demonstração remota da etapa #45 foi usada no ensaio. A [especificação](trabalho-em-grupo-spec.md) consolida as decisões confirmadas. Esta divisão é própria do trabalho em grupo e abrange entregas completas que o professor pode experimentar.

## 1. Entrar e trabalhar em conjunto

[Ticket #43](https://github.com/atilasos/pagecraft/issues/43). Implementado e verificado.

**Bloqueado por:** nenhum.

**Entrega:** depois de entrar com o código da sessão, os alunos escolhem Sozinho/A pares/Em grupo, confirmam os nomes e o nível, trabalham no mesmo dispositivo e aparecem ao professor como grupo. As respostas ficam identificadas como trabalho conjunto, com autoria preservada nos históricos e relatórios.

- [x] Seleção e confirmação dos membros da turma com regras de tamanho e disponibilidade.
- [x] Reserva indivisível; conflito entre dispositivos não deixa reservas parciais.
- [x] Autorização do dispositivo para o grupo e retoma da composição validada pelo servidor.
- [x] Nível comum escolhido e alterável sem mudar os perfis individuais.
- [x] Respostas e ajuda com autoria do grupo; um registo canónico associado aos membros, sem duplicação como respostas individuais.
- [x] Grupo e membros visíveis no acompanhamento e históricos do professor.
- [x] Entrada individual e acontecimentos anteriores continuam legíveis.
- [x] Testes pelos percursos aluno/professor e interfaces existentes, incluindo disputa de reserva e isolamento.

## 2. Fazer e consultar a reflexão individual

[Ticket #44](https://github.com/atilasos/pagecraft/issues/44). Implementado e verificado.

**Dependência concluída:** etapa 1, que estabelece a autoria conjunta e os participantes autorizados no dispositivo.

**Entrega:** os membros do grupo fazem a autoavaliação à vez no mesmo computador. O professor consulta a produção comum e a reflexão individual de cada criança.

- [x] Mostrar claramente a criança cuja reflexão está aberta.
- [x] Usar os critérios da atividade; reflexão facultativa, com possibilidade de omissão.
- [x] Guardar e rever as reflexões sem substituir a dos colegas ou duplicar envios.
- [x] Validar o participante no servidor e recusar atribuição a crianças de outros grupos.
- [x] Integrar com as atividades existentes sem atribuir automaticamente reflexão conjunta a todos.
- [x] Históricos e relatórios distinguem autoria conjunta e voz individual.
- [x] Testes com reflexões diferentes, omissão, revisão e repetição do envio.

## 3. Corrigir participantes durante a aula e verificar o percurso completo

[Ticket #45](https://github.com/atilasos/pagecraft/issues/45). Implementado, revisto e aceite após a confirmação do toque pelo professor. Dependências #43 e #44 concluídas.

**Dependências concluídas:** etapas 1 e 2, que estabelecem respostas conjuntas e reflexões individuais.

**Entrega:** o professor altera os participantes durante a sessão; o dispositivo mostra a alteração, o novo trabalho usa a nova composição e os registos anteriores conservam a autoria. O percurso completo fica disponível para revisão remota temporária.

- [x] Alteração apenas pelo professor, com reservas e libertações coerentes.
- [x] Respostas e reflexões anteriores mantêm os participantes originais.
- [x] Respostas pendentes conservam a composição em que foram geradas; conflitos tornam-se visíveis.
- [x] Retoma, revogação, libertação e encerramento coerentes com a composição atual.
- [x] Validar integralmente aluno, professor, grupos diferentes e Quadro sem respostas atribuídas a alunos.
- [x] Verificar teclado, larguras de computador/tablet/telemóvel e regressões individuais.
- [x] Confirmar toque físico no quadro/tablet: o professor confirmou seleção de participantes, reflexões individuais e gravação da troca de participantes.
- [x] Registar evidência de testes e rever código contra normas e especificação.
- [x] Entregar demonstração remota com dados descartáveis, sem expor dados reais da turma.

## Cobertura aprovada

Testar os percursos reais de aluno e professor no browser e confirmar reservas, autoria e relatórios pelas interfaces HTTP já existentes. Exercitar comportamentos observáveis em vez de comparar estruturas internas. O professor confirmou esta divisão e cobertura.
