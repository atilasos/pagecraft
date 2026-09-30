# Etapas de trabalho em grupo

Estado: divisão e cobertura aprovadas pelo professor em 30/09/2026. Publicados os tickets [#43](https://github.com/atilasos/pagecraft/issues/43), [#44](https://github.com/atilasos/pagecraft/issues/44) e [#45](https://github.com/atilasos/pagecraft/issues/45), associados à [especificação #42](https://github.com/atilasos/pagecraft/issues/42). Sem implementação funcional. As dependências nativas foram verificadas: #44 depende de #43; #45 depende de #43 e #44. O primeiro ticket disponível é #43. A [especificação](trabalho-em-grupo-spec.md) consolida as decisões confirmadas. Esta divisão é própria do trabalho em grupo e abrange entregas completas que o professor pode experimentar.

## 1. Entrar e trabalhar em conjunto

[Ticket #43](https://github.com/atilasos/pagecraft/issues/43). `ready-for-agent`.

**Bloqueado por:** nenhum.

**Entrega:** depois de entrar com o código da sessão, os alunos escolhem Sozinho/A pares/Em grupo, confirmam os nomes e o nível, trabalham no mesmo dispositivo e aparecem ao professor como grupo. As respostas ficam identificadas como trabalho conjunto, com autoria preservada nos históricos e relatórios.

- [ ] Seleção e confirmação dos membros da turma com regras de tamanho e disponibilidade.
- [ ] Reserva indivisível; conflito entre dispositivos não deixa reservas parciais.
- [ ] Autorização do dispositivo para o grupo e retoma da composição validada pelo servidor.
- [ ] Nível comum escolhido e alterável sem mudar os perfis individuais.
- [ ] Respostas e ajuda com autoria do grupo; um registo canónico associado aos membros, sem duplicação como respostas individuais.
- [ ] Grupo e membros visíveis no acompanhamento e históricos do professor.
- [ ] Entrada individual e acontecimentos anteriores continuam legíveis.
- [ ] Testes pelos percursos aluno/professor e interfaces existentes, incluindo disputa de reserva e isolamento.

## 2. Fazer e consultar a reflexão individual

[Ticket #44](https://github.com/atilasos/pagecraft/issues/44). `ready-for-agent`, bloqueado por #43.

**Bloqueado por:** etapa 1, que estabelece a autoria conjunta e os participantes autorizados no dispositivo.

**Entrega:** os membros do grupo fazem a autoavaliação à vez no mesmo computador. O professor consulta a produção comum e a reflexão individual de cada criança.

- [ ] Mostrar claramente a criança cuja reflexão está aberta.
- [ ] Usar os critérios da atividade; reflexão facultativa, com possibilidade de omissão.
- [ ] Guardar e rever as reflexões sem substituir a dos colegas ou duplicar envios.
- [ ] Validar o participante no servidor e recusar atribuição a crianças de outros grupos.
- [ ] Integrar com as atividades existentes sem atribuir automaticamente reflexão conjunta a todos.
- [ ] Históricos e relatórios distinguem autoria conjunta e voz individual.
- [ ] Testes com reflexões diferentes, omissão, revisão e repetição do envio.

## 3. Corrigir participantes durante a aula e verificar o percurso completo

[Ticket #45](https://github.com/atilasos/pagecraft/issues/45). `ready-for-agent`, bloqueado por #43 e #44.

**Bloqueado por:** etapas 1 e 2, pois alterações de composição precisam de preservar tanto respostas como reflexões.

**Entrega:** o professor altera os participantes durante a sessão; o dispositivo mostra a alteração, o novo trabalho usa a nova composição e os registos anteriores conservam a autoria. O percurso completo fica disponível para revisão remota temporária.

- [ ] Alteração apenas pelo professor, com reservas e libertações coerentes.
- [ ] Respostas e reflexões anteriores mantêm os participantes originais.
- [ ] Respostas pendentes conservam a composição em que foram geradas; conflitos tornam-se visíveis.
- [ ] Retoma, revogação, libertação e encerramento coerentes com a composição atual.
- [ ] Validar integralmente aluno, professor, grupos diferentes e Quadro sem respostas atribuídas a alunos.
- [ ] Verificar teclado, toque, larguras de computador/tablet/telemóvel e regressões individuais.
- [ ] Registar evidência de testes e rever código contra normas e especificação.
- [ ] Entregar demonstração remota com dados descartáveis, sem expor dados reais da turma.

## Cobertura aprovada

Testar os percursos reais de aluno e professor no browser e confirmar reservas, autoria e relatórios pelas interfaces HTTP já existentes. Exercitar comportamentos observáveis em vez de comparar estruturas internas. O professor confirmou esta divisão e cobertura.
