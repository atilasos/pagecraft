# Etapas de Frações em banda desenhada

Divisão da [especificação](fracoes-banda-desenhada-spec.md) aceite pelo professor em 29/09/2026 para esta atividade. Nas restantes atividades, rever a divisão caso a caso. A primeira etapa está implementada e verificada; as etapas 2 e 3 permanecem por implementar. Publicados a [especificação #38](https://github.com/atilasos/pagecraft/issues/38) e três tickets no GitHub, com a etiqueta `ready-for-agent`. Dependências nativas verificadas: #40 depende de #39; #41 depende de #40. Depois de fechar #39, o próximo ticket disponível é #40. Cada ticket referencia o protótipo `prototype/fracoes-visuais`, commit `58331ac`, variante B.

## 1. Partilhar o pão num rascunho com progressão por respostas

[Ticket #39](https://github.com/atilasos/pagecraft/issues/39). Implementado. [Verificação](../verification/issue-39-fracoes.md).

**Bloqueado por:** nenhum.

**Entrega:** um novo rascunho que o professor pode abrir e no qual a criança percorre a primeira unidade completa, em banda desenhada. Serve de percurso inicial demonstrável para validar a integração antes de estender às outras unidades.

- [x] Conservar o conteúdo publicado e preparar a revisão com novo identificador, seguindo o fluxo de rascunhos existente.
- [x] Apresentar Imagina, Experimenta e Repara, adaptados a tablet, telemóvel e teclado.
- [x] Oferecer a primeira unidade nos três Níveis de diferenciação, com Árvore jovem por defeito na ausência de perfil.
- [x] Pedir a escolha do corte e a resposta sobre as metades; impedir avanço com resposta parcial e permitir avanço com erro.
- [x] Dar uma pista visual, permitir corrigir e conservar as respostas ao voltar. Alterar o corte invalida a resposta dependente.
- [x] Aplicar a mesma regra de Página respondida aos botões e à navegação entre páginas.
- [x] Registar a tentativa real pelo contrato existente da ponte, preservando a distinção entre responder e acertar. Verificar em sessão de teste que o professor recebe a evidência.
- [x] Permitir demonstração por professor ou Quadro sem inventar respostas da criança; o rascunho parcial mostra claramente que é uma revisão em curso.
- [x] Acrescentar testes de comportamento que falhem antes da implementação e passem com o percurso acima, incluindo as interações no browser do Hub.

## 2. Completar a exploração das cinco unidades

[Ticket #40](https://github.com/atilasos/pagecraft/issues/40).

**Bloqueado por:** etapa 1, que estabelece o rascunho e as regras de navegação e integração.

**Entrega:** a criança percorre partes e símbolos, associações, unidade inteira e comparação, além da partilha do pão, com pedidos explícitos e pistas visuais nos três níveis.

- [ ] Implementar os pedidos observáveis da especificação para as quatro unidades restantes, com uma lista finita de desafios por nível.
- [ ] Tratar valores iniciais como exemplos; contar uma representação apenas depois de a criança responder ou a confirmar.
- [ ] Conservar associações erradas como respostas, permitir corrigi-las e não exigir acertos para mudar de página.
- [ ] Confirmar uma representação na grelha; manter desenho livre como forma de expressão sem o classificar automaticamente.
- [ ] Invalidar respostas dependentes quando a criança muda a representação, os operandos ou o nível, conservando o restante trabalho.
- [ ] Manter a unidade constante nas comparações e representar corretamente todos os exemplos.
- [ ] Registar tentativas e correções, sem duplicar acontecimentos quando apenas se redesenha a página.
- [ ] Percorrer os cinco temas em todos os níveis no browser, com respostas em falta e erradas; verificar teclado, toque, foco e larguras de 390, 768 e 1280 px.

## 3. Concluir no Minecraft e preparar a revisão da atividade completa

[Ticket #41](https://github.com/atilasos/pagecraft/issues/41).

**Bloqueado por:** etapa 2, porque esta entrega verifica e encerra o percurso completo das cinco unidades até à reflexão final.

**Entrega:** a criança passa da exploração digital à construção externa, confirma o trabalho e conclui a reflexão; o professor recebe um rascunho completo e um guia coerente para revisão.

- [ ] Representar os exemplos Minecraft com uma unidade comum de 20 blocos, incluindo 1/4 com cinco blocos, sem arredondamentos matematicamente errados.
- [ ] Pedir «Já fizemos» e uma resposta curta sobre a construção; exigir ambos para avançar, mantendo o avanço com erros e as pistas visuais.
- [ ] Conservar a alternativa com papel ou cubos e os papéis cooperativos, sem fingir que já existe identificação dos membros do grupo.
- [ ] Integrar a Autoavaliação da realização pelo fluxo existente, sem classificação automática nem conclusão duplicada.
- [ ] Alinhar especificação pedagógica, apresentação, metadados e guia com o percurso revisto e os três níveis.
- [ ] Validar o percurso completo no contexto de realização e de demonstração, conservando os nomes da ponte e o isolamento dos relatórios de alunos.
- [ ] Demonstrar que a atividade publicada anteriormente e os seus trabalhos permanecem intactos; preparar a revisão final pelo professor antes de publicar para alunos.
- [ ] Registar as verificações executadas e disponibilizar uma pré-visualização remota da revisão, no âmbito já pedido pelo professor.

## Decisão do professor

Confirmadas as três entregas, as dependências 1 → 2 → 3 e a cobertura por percursos reais de aluno, professor e quadro para esta atividade. A ressalva do professor é rever a divisão caso a caso nas outras atividades, tanto no percurso pedagógico como nas etapas de implementação.

A identificação de grupos e a aplicação das regras às restantes atividades continuam registadas nas decisões gerais. Não dependem da aprovação desta divisão para continuarem a ser problemas a resolver.
