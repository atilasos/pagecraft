# Renovação das 28 palavras para TIC

A revisão de 23/10/2026 substitui o desenho v2 por minijogos para crianças dos 1.º e 2.º anos que trabalham praticamente sozinhas no computador. O professor acompanha a turma e presta ajuda pontual. Os percursos v2 exigiam leitura e mediação frequentes; por isso, deixam de ser a proposta para utilização ou aprovação neste contexto. Os seus ficheiros permanecem como histórico, sem serem reutilizados como experiência infantil v3.

## Proposta atual para revisão

São 28 palavras e seis minijogos independentes por palavra, num total de 168 atividades. Cada jogo tem quatro rondas e dura aproximadamente três a seis minutos. A mesma palavra pode ser retomada em vários dias, com jogos e apoios diferentes. O professor confirma o repertório e escolhe o que propor; não há uma sequência anual automática imposta à criança.

As operações são associar, encontrar pares, procurar a igual, reconstruir com modelo, completar e reconstruir sem modelo inicial. Há imagem original, áudio PT-PT incorporado, demonstração recuperável e pistas junto da ação. A entrada não exige ler critérios nem conversar com um adulto. A posição 14 continua a ser gema; flor mantém a sua única sílaba e usa letras móveis nos jogos de reconstrução.

- [Princípios revistos](m28p-principios-implementacao.md).
- [Contrato de dados e interação v3](m28p-contrato-percursos.md).
- [Pesquisa sobre manuais, Drive, Sebenta e autonomia](research/m28p-tic-autonomia-2026.md).
- [Desenho comum dos jogos](../drafts/m28p-v3/collection-design.json).
- [Investigação histórica e lexical anterior](research/metodo-28-palavras-2026.md), útil como enquadramento, sem validar os pressupostos de utilização do v2.

## Construir e verificar

A fonte lexical revista é `drafts/m28p-v3/words.json`. O gerador `scripts/build_m28p_tic.py` e o template `scripts/templates/m28p-tic.html` produzem os artefactos autocontidos. Consultar `python3 scripts/build_m28p_tic.py --help` para opções e destinos exatos da versão instalada.

A validação verifica os dados de toda a coleção e a presença real dos recursos incorporados. A revisão de browser deve incluir entrada de menina sem leitura adulta, os seis jogos, erro e reparação, demonstração, áudio, teclado/toque, mudança de apoio e recuperação; acrescentar dígrafos e o caso monossilábico de flor. Os relatórios de execução e de revisão distinguem verificações concluídas de limitações por resolver. Este documento descreve os critérios; não declara testes ainda não executados.

## Site e aprovação

Os novos materiais são rascunhos para revisão do professor. O registo canónico cria códigos estáveis e pré-visualizações privadas no Studio. O catálogo de revisão permite encontrar palavra e jogo. As atividades inadequadas são retiradas dessa proposta ativa, preservando os endereços e os registos históricos necessários.

Integrar PRs em main coloca o trabalho no repositório. É também necessário confirmar que o serviço do site usa a versão integrada e que as pré-visualizações abrem os novos conteúdos. A entrega deve indicar as ligações reais, o número de rascunhos disponíveis e eventuais limitações verificadas. Não basta entregar ficheiros locais.

A aprovação docente continua a ser individual por atividade. A presença no Studio permite essa aprovação; não equivale a publicação para os alunos. Depois da aprovação explícita, usar o publicador canónico com `--approved`, sem editar `catalog.json` à mão.

## Histórico preservado

O [inventário de arquivo](archives/m28p-2026-10-23.json) conserva a coleção anterior de 90 atividades. O diretório `drafts/m28p-v2/`, os seus relatórios e o [registo anterior de fontes](../drafts/m28p-renovacao-sources.md) documentam a primeira tentativa de renovação. Os documentos operacionais presentes foram reescritos porque essa tentativa interpretou mal a disponibilidade de mediação em TIC. Nenhuma alteração à Sebenta é pressuposta por esta revisão.

A revisão documental e os ensaios técnicos não demonstram aquisição de leitura. O professor verificará em sala a clareza das imagens, a autonomia de utilização e a adequação dos apoios. Os registos digitais descrevem ações, respostas e ajuda, sem certificar fluência ou domínio do método.
