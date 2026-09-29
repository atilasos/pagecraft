# Fontes da revisão de Frações com Minecraft

Consulta em 29/09/2026 para o ticket #41. A API local da Sebenta respondeu a `health`, pesquisa e leitura integral. O trabalho foi apenas de leitura; não houve alterações no vault, na fila ou nos serviços. As fontes orientam a revisão já aprovada em `docs/design/fracoes-banda-desenhada-spec.md` e a divisão de `docs/design/fracoes-banda-desenhada-etapas.md`.

## Sínteses da wiki lidas integralmente

Os caminhos são relativos a `/home/proteu/obsidian-vault/`. Estas páginas estão em estado editorial `review`; são sínteses, não documentos curriculares originais.

| Título | Caminho | Uso nesta revisão |
| --- | --- | --- |
| PageCraft | `20_Wiki/PageCraft.md` | Sequência de exploração, SRTC-A, diferenciação, construção ligada ao conceito e critérios observáveis. O pedido e o repositório atuais resolvem a referência antiga a cores semáforo. |
| Avaliação Formativa | `20_Wiki/Avaliação Formativa.md` | Mostrar critérios, permitir correção e usar a informação para ajustar apoios. Distinguir resposta, acerto e reflexão da criança. |
| TIC no Ensino Básico | `20_Wiki/TIC no Ensino Básico.md` | Articular Matemática e TIC com o titular de turma. A atualização de 08/09/2026 descreve o contexto de CTIC do professor; não se reproduzem dados pessoais na atividade. |
| Ensino da Matemática | `20_Wiki/Ensino da Matemática.md` | Conversa entre colegas, representações visuais e explicação de estratégias. Desenho livre como comunicação, sem correção automática. |

Pesquisas efetuadas: `PageCraft`, `avaliação formativa`, `TIC no Ensino Básico`, `frações` e `Matemática 2.º`. A pesquisa geral de frações devolveu sobretudo textos pedagógicos; a fonte curricular do ano foi localizada na coleção oficial local. Não se atribui leitura integral aos artigos apontados pelas páginas da wiki.

## Fontes curriculares originais

Foi lido o excerto de frações na cópia local e conferido o PDF disponibilizado pela DGE. As formulações abaixo são sínteses, não citações literais.

### Matemática, 2.º ano

- Cópia local: `documentos-oficiais/aprendizagens-essenciais/matematica-2-ano-1-ciclo.md`.
- Original: [Aprendizagens Essenciais de Matemática, 2.º ano, DGE](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/ae_mat_2.o_ano.pdf), páginas 24–26, secção Frações. PDF consultado em 29/09/2026.

O referencial trabalha a relação parte-todo com uma unidade contínua, a interpretação do numerador e denominador, diferentes representações, metades e quartos, unidade inteira e comparação de frações unitárias. As estratégias incluem partilhas desiguais para contraste, manipuláveis e papel; partem de duas e quatro partes e admitem outros denominadores, de preferência até dez. O exemplo de duas partes em cinco surge nas estratégias.

Limites do alinhamento: comparar frações não unitárias é uma extensão visual desta atividade. Não se apresenta como descritor obrigatório de comparação do 2.º ano. Os 20 blocos são uma escolha didática para construir uma superfície contínua com grupos inteiros, não uma exigência do documento. Não se faz aqui uma auditoria de alterações legislativas ou de todo o currículo.

### TIC, 1.º ciclo

- Cópia local: `documentos-oficiais/aprendizagens-essenciais/tic-1-ano-1-ciclo.md`.
- Original: [Orientações Curriculares de TIC para o 1.º ciclo, DGE](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/oc_1_tic_1.pdf), introdução e páginas 7–8. PDF consultado em 29/09/2026.

O documento orienta comunicação, colaboração, criação de artefactos e resolução de problemas matemáticos apoiada por ferramentas digitais. O cabeçalho da cópia local diz AE do 1.º ano; o corpo do original identifica Orientações Curriculares para o ciclo. A planificação por ano cabe ao professor. O DocSpec usa esta designação e não inventa AE de TIC específicas do 2.º ano.

A wiki distingue a proposta de revisão de março de 2026 do documento anterior. Não foi verificada a eventual homologação posterior dessa proposta. Por isso, nenhuma obrigação da atividade é fundamentada na proposta de 2026, nem se afirma que a sua situação continua igual à consulta da wiki.

## Decisões desta atividade

Estas decisões pertencem à especificação aceite pelo professor e à concretização do ticket, não são conclusões atribuídas aos documentos curriculares:

- Manter a variante B, com Imagina, Experimenta e Repara, e as cinco unidades implementadas nos tickets #39 e #40.
- Trabalhar 45 minutos: 30 de exploração, 10 de construção e 5 de reflexão/partilha.
- Usar Com pistas, Passo a passo e Mais desafios; permitir mudança e preservar respostas independentes.
- Na construção, representar 1/2, 1/4, 2/5 ou 1/10 numa unidade de 20 blocos. Os números pintados são, respetivamente, 10, 5, 8 e 2.
- Exigir declaração Já fizemos e resposta numérica, incluindo resposta errada. Trocar fração ou material invalida ambas.
- Um colega constrói e o outro verifica; depois trocam. Não há identificação técnica do par nem atribuição automática de evidências aos dois membros.
- A página observa escolhas e respostas. A realização externa e a reflexão são declarações da criança; o professor observa a construção real.
- Reutilizar a Autoavaliação da realização; fora desse contexto, disponibilizar reflexão facultativa sem prometer envio. A voz do aluno fica separada da evidência observada.

O guião e os dois JSON são especificações para revisão. A evidência de execução, browser e persistência fica nos artefactos de avaliação da entrega; este registo de fontes não declara esses testes realizados.
