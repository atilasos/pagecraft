# Frações em banda desenhada

Estado: proposta preparada em 29/09/2026 para confirmar a cobertura dos testes e a divisão do trabalho antes de publicar no GitHub.

## Problema

As crianças encontram explicações longas, têm dificuldade em perceber o que fazer e conseguem mudar de página sem responder. A atividade publicada de frações apresenta cinco unidades, construção em Minecraft e avaliação, mas várias interações apenas exploram exemplos e não distinguem uma resposta dada de um valor inicial. O professor escolheu a opção B do protótipo para tornar as ações e as perguntas mais claras.

## Solução

Preparar uma revisão completa de Frações com Minecraft, do 2.º ano, em banda desenhada. Cada página apresenta a situação em «Imagina», a manipulação em «Experimenta» e a pergunta e o feedback em «Repara». A criança avança quando a página está respondida, mesmo com erros, recebe pistas visuais e pode corrigir. O professor revê um novo rascunho antes da publicação para os alunos.

## Histórias de utilização

1. Como criança, quero ver uma situação ilustrada para perceber o desafio sem ler uma explicação longa.
2. Como criança, quero encontrar a instrução junto do objeto em que devo tocar.
3. Como criança, quero manipular o pão e comparar os tamanhos das partes.
4. Como criança, quero responder se o corte produziu duas metades, incluindo quando penso que não.
5. Como criança, quero saber visualmente o que falta responder antes de avançar.
6. Como criança, quero continuar depois de responder, mesmo quando me engano.
7. Como criança, quero uma pista visual que me ajude a corrigir a minha resposta.
8. Como criança, quero voltar a uma página e experimentar outra resposta.
9. Como criança, quero que a pergunta volte a precisar de resposta quando altero o objeto sobre o qual respondi.
10. Como criança, quero relacionar as partes pintadas e o total de partes com o símbolo da fração.
11. Como criança, quero associar imagens, palavras e símbolos e poder corrigir associações erradas.
12. Como criança, quero representar uma fração numa grelha e explorar também o desenho livre.
13. Como criança, quero completar uma unidade e responder se ainda falta alguma parte.
14. Como criança, quero comparar partes de unidades do mesmo tamanho.
15. Como criança, quero escolher um Nível de diferenciação e receber desafios adequados a esse nível.
16. Como criança, quero confirmar o trabalho feito no Minecraft e responder sobre a construção.
17. Como criança, quero concluir com a minha Autoavaliação da realização, sem uma nota automática.
18. Como criança num tablet, quero tocar nos controlos sem depender de movimentos precisos ou de passar o rato por cima.
19. Como criança que usa teclado, quero percorrer os controlos e perceber onde está o foco.
20. Como professor, quero rever o percurso completo antes de o disponibilizar à turma.
21. Como professor, quero distinguir respostas erradas, correções e falta de resposta nas Evidências existentes.
22. Como professor, quero conservar os trabalhos e os endereços da atividade já publicada.
23. Como professor, quero abrir a revisão no quadro e demonstrar cada página sem os bloqueios destinados ao trabalho autónomo da criança.
24. Como professor, quero exemplos matematicamente corretos e instruções coerentes entre a atividade e o guia.

## Decisões de implementação

### Conteúdo e apresentação

- Usar a opção B como referência visual e conservar o protótipo na branch separada. A implementação final não inclui o seletor A/B/C nem o estado de diagnóstico.
- Dividir o percurso em páginas curtas, preservando as cinco ideias curriculares da atividade, o trabalho Minecraft e a reflexão final. Uma unidade pode ocupar mais de uma página quando contém vários pedidos.
- Dispor as vinhetas lado a lado onde houver espaço; em ecrãs estreitos, conservar a ordem Imagina, Experimenta, Repara numa coluna.
- Usar instruções curtas, controlos de pelo menos 48 px, foco visível, rótulos acessíveis e feedback que não dependa só da cor.
- Manter Broto, Árvore jovem e Árvore robusta, com Árvore jovem por defeito quando não existe Perfil de diferenciação. Mudar de nível continua livre e invalida apenas respostas cujo desafio mudou; não apaga trabalho de outras páginas.
- Não exigir que a criança escreva explicações longas para concluir. Desenho livre e explicação oral são oportunidades de expressão; o avanço usa respostas observáveis na página.

### Página respondida

- Cada página declara os seus pedidos obrigatórios. Uma resposta presente e uma resposta correta são estados distintos.
- Valores apresentados inicialmente em seletores, exemplos e grelhas não contam como respostas. A criança responde ou confirma explicitamente a sua representação.
- «Seguinte» e outros caminhos de avanço obedecem à mesma regra. Uma página por responder impede saltar para as páginas seguintes; a criança pode voltar às anteriores.
- Alterar o objeto de uma pergunta invalida a resposta dependente e volta a bloquear o avanço até nova resposta. Conservar as respostas independentes.
- Uma resposta errada recebe primeiro uma pista visual. A criança pode corrigir ou continuar. O feedback descreve o que observou, sem nota automática.
- Reabrir uma página durante a mesma realização conserva o trabalho. A revisão utiliza o ciclo de vida existente das realizações; não cria persistência paralela em nome da criança.

### Critérios observáveis por unidade

| Parte | Pedidos que precisam de resposta | Feedback visual |
| --- | --- | --- |
| Partilha do pão | Escolher o corte e responder se as partes formam metades | Alinhar ou sobrepor as partes para comparar tamanhos |
| Partes e símbolo | Representar a fração pedida e confirmar a representação | Distinguir o total de partes iguais das partes escolhidas |
| Representações | Responder a cada associação apresentada e confirmar uma representação na grelha | Destacar as partes iguais e as partes pintadas de cada representação |
| Unidade inteira | Confirmar a composição e responder se representa a unidade inteira | Mostrar as partes que ocupam ou deixam livre a mesma moldura |
| Comparação | Escolher A, B ou iguais para o par apresentado | Alinhar barras com unidades do mesmo tamanho |
| Minecraft | Confirmar «Já fizemos» e responder à pergunta sobre a construção proposta | Mostrar como formar grupos de igual tamanho |

As associações da terceira unidade ficam registadas mesmo quando erradas. Exigir apenas associações certas contrariaria a decisão de Página respondida. A lista de desafios de cada nível deve ser finita e visível, sem exigir que a criança adivinhe que exemplos explorar.

### Minecraft e precisão matemática

- A confirmação «Já fizemos» é declarada pela criança. A aplicação não verifica o mundo Minecraft.
- Corrigir o exemplo legado de um quarto de 10 blocos, que arredonda 2,5 para 3. Usar uma unidade comum de 20 blocos para os exemplos de 1/2, 1/4, 2/5 e 1/10, com grupos de tamanhos inteiros e iguais.
- Nas escolhas livres do desafio Minecraft, oferecer apenas frações compatíveis com a unidade proposta. Os outros denominadores continuam nas explorações digitais adequadas.
- Manter a alternativa de construção com papel quadriculado ou cubos. A pergunta e a declaração de realização aplicam-se da mesma forma.
- Atualizar a atividade, os exemplos visuais, a especificação pedagógica e o guia do professor em conjunto.

### Integração e revisão

- Aplicar o ADR-0005: criar um novo Rascunho de atividade e um novo identificador para esta revisão, preservando a atividade publicada e o contexto dos trabalhos anteriores.
- Reutilizar as interfaces existentes de Realização da atividade, Autoavaliação da realização e Acontecimento de sessão. Não alterar os nomes congelados na ponte, conforme ADR-0002.
- Emitir tentativas reais e correções através do contrato existente, sem tratar a passagem de página como prova de acerto. Abrir a atividade ou desenhar um exemplo inicial não produz uma tentativa da criança.
- Distinguir o percurso do aluno da exploração pelo professor ou Quadro. A demonstração pode abrir páginas; isso não atribui respostas a alunos. Esta distinção não amplia as permissões do papel Quadro.
- O modo de revisão continua excluído dos relatórios de alunos. A publicação usa o fluxo existente e o Catálogo continua derivado dos metadados.

## Testes propostos

A confirmação pedida ao professor é sobre os resultados a verificar, não sobre a escolha de bibliotecas.

- Testar principalmente o comportamento público no browser: abrir o rascunho, manipular, responder, receber feedback e navegar. Evitar testes que apenas repetem a estrutura do código ou comparam HTML como texto.
- Cobrir página vazia, resposta parcial, resposta errada completa, correção, regresso e mudança do objeto ou nível. Verificar todos os caminhos de avanço e as respostas dependentes.
- Percorrer todos os pedidos obrigatórios das cinco unidades em cada nível e a construção externa. A conclusão com erros deve funcionar; a conclusão com pedidos em falta deve falhar.
- Verificar os desenhos das frações contra o valor matemático esperado, incluindo um quarto da unidade Minecraft e comparação de unidades do mesmo tamanho.
- Exercitar o browser pelo Agent Browser Hub, com toque e teclado, nas larguras já usadas no protótipo: 390, 768 e 1280 px. Verificar foco, ordem das vinhetas, pistas visíveis e ausência de transbordamento horizontal.
- Usar as interfaces HTTP e da ponte já testadas no projeto para comprovar que tentativas e correções chegam ao professor, a demonstração não cria respostas do aluno e ensaios de rascunhos não entram nos relatórios. Os testes de realizações, publicação e vocabulário de acontecimentos são o precedente.
- Confirmar que a atividade antiga permanece disponível e que a revisão só entra no Catálogo depois do fluxo de publicação. Não é necessário alterar a base de dados para a lógica de Página respondida.

## Fora deste recorte

- Identificação e atribuição de evidências a todos os membros de um par ou grupo. O problema permanece aberto e exige definir esse percurso; «Turma» continua distinto de grupo de trabalho.
- Conversão em lote das restantes atividades ou alteração geral do gerador. A atividade revista será a referência para esse trabalho posterior.
- Novas políticas de acesso ou nova correção do emparelhamento do quadro, já tratado nesta conversa.
- Verificação automática da construção real no Minecraft ou avaliação automática de desenhos livres.
- Publicação automática para os alunos sem a revisão prevista no fluxo existente.

## Fontes e continuidade

- [Decisões confirmadas e ensaio remoto](usabilidade-infantil.md).
- Protótipo primário: branch `prototype/fracoes-visuais`, commit `58331ac`, variante B. Escolha do professor em 29/09/2026.
- [Etapas propostas](fracoes-banda-desenhada-etapas.md).
- ADR-0002 sobre nomes na ponte, ADR-0003 sobre Catálogo derivado e ADR-0005 sobre revisões e realizações.
- A preferência do professor decide a direção visual. Observar crianças em aula continua necessário para avaliar se a revisão lhes permite trabalhar com mais autonomia.
