# Auditoria 10: investigação, erro produtivo e comunicação

Base `4c6ba90`, 22/10/2026. Investigação só de leitura: AGENTS.md, CONTEXT.md, avaliação anterior, ADRs 0002–0005 e 0007, atividades, template e referências comuns. Sem browser, execução de atividades, alterações ao repositório, commits ou PR. As conclusões de interação resultam do código; os testes abaixo são propostas de validação. `catalog.json` e as duas atividades locais do utilizador ficaram intactos.

## Fundamentação consultada

API local da Sebenta disponível. Executei `search --kind wiki` e `read --content` para duas páginas:

- **Trabalho de Projeto**, `20_Wiki/Trabalho de Projeto.md`, estado `review`, confiança `medium`. Síntese da wiki: transformar um tema em pergunta investigável exige apoio; confrontar hipóteses e variar um fator de cada vez ajuda a estudar uma questão; comunicar implica explicar evidências a destinatários que podem interrogar os autores. Instrumentos demasiado densos prejudicam o envolvimento.
- **Circuitos de Comunicação**, `20_Wiki/Circuitos de Comunicação.md`, estado `review`, confiança `medium`. Síntese da wiki: a comunicação tem funções cognitiva e social; colegas perguntam, criticam e propõem melhorias; o professor medeia a explicitação. A página assinala fontes por verificar e limites da síntese.

As propostas seguintes são minhas. A wiki fundamenta os objetivos; não demonstra a eficácia destas interfaces nem prescreve estes mecanismos.

## O que já existe

A ponte já tem previsão, manipulação, feedback visual, registo de configurações, teste e revisão entre pares: `activities/tinkercad-pontes-3e4/index.html:141`, `:188`, `:189`, `:213`; `teacher.md:28`. Canva Animais já inclui plano negociado, alternância, sugestão, decisão de revisão e ensaio com perguntas: `activities/canva-animais-4ano/index.html:119`, `:122`, `:124`, `:166`.

O template já fornece ponte e feedback; o contrato disponibiliza `assessment_result`, checkpoints e pedidos de partilha: `server/pipeline/prompts/template-base.html:324`, `:432`; `references/bridge-contract.md:21`, `:26`, `:35`, relativamente a `server/pipeline/prompts/`. Portanto, acrescentar genericamente “trabalho em grupo”, “pistas” ou “partilhar” repetiria capacidades existentes. Também ficam excluídos os temas dos PRs #51–55: exports, cache, recuperação, rótulos dos guias e entrega da escolha de apoio.

## 1. Duas pontes iguais de cima: investigar um contraexemplo

**Problema e evidência.** A simulação já conserva tentativas no histórico, mas a interface mostra o resultado da configuração atual (`activities/tinkercad-pontes-3e4/index.html:185`). O estado guarda configuração atual e uma anterior para desfazer (`:158`), sem uma comparação escolhida pela criança. A vista superior desenha os apoios sem representar alturas (`:179`); a regra de travessia depende precisamente delas (`:173`). Existe aqui uma pergunta investigável muito concreta.

**Comportamento proposto.** Novo rascunho opcional de 10–15 minutos: “Olhar de cima chega para decidir se a personagem atravessa?” O par antecipa uma resposta, guarda um ensaio A, altera uma altura e guarda B. Compara duas miniaturas superiores e laterais, os resultados e a variável alterada. Pode manter ou rever a hipótese, explicando oralmente ou numa frase. Um colega procura um contraexemplo à explicação. Guardar apenas dois ensaios limita o registo. Respostas incorretas continuam a permitir avançar.

**Benefício pedagógico esperado.** Transformar tentativa e erro em confronto entre previsão, observação e explicação. O erro torna-se material escolhido para comunicar; a cooperação tem uma tarefa intelectual partilhada. Esta é a proposta mais criativa da ronda.

**Risco e esforço.** A criança pode generalizar a regra artificial a pontes reais. Manter “neste modelo” nas perguntas e na comunicação, como exige `teacher.md:32`. Evitar formulários longos e pontuação das hipóteses. Esforço médio, estimativa de 2–3 dias incluindo validação e revisão docente.

**Teste concreto.** Com apoios nas margens e tabuleiro presente, A tem alturas 2/2 e B 2/1. Confirmar vistas superiores iguais, laterais diferentes e resultados distintos. Rever a hipótese, mudar apoio e recarregar: conservar A/B e explicação sem duplicar tentativas; manter checkpoint abaixo de 4096 bytes (`:161`). Ensaiar teclado e toque e observar se um par consegue explicar qual variável mudou.

**Fronteira de ficheiros.** Novos `drafts/pontes-duas-vistas.{html,md}`, respetivo DocSpec e teste de browser dedicado. Reutilizar o contrato existente. Conteúdo revisto recebe slug próprio, conforme ADR-0005:9; publicação fica fora deste recorte.

## 2. A imagem explicou o que queríamos? Teste com um leitor

**Problema e evidência.** `activities/canva-4ano-laboratorio-apresentacao/index.html:38` afirma que edição e legenda ajudam a compreender quando há qualquer ajuste e pelo menos 18 caracteres. O código verifica manipulação e comprimento, sem testar a mensagem comunicada. A tarefa promete “editar para explicar melhor” (`:21`).

**Comportamento proposto.** Microatividade autónoma com uma ilustração incorporada da escola. O autor escolhe a mensagem pretendida, enquadra e legenda. Passa o dispositivo ao colega, que indica o que percebeu antes de conhecer a intenção. Ambos comparam intenção e interpretação e podem rever uma escolha. O professor pode registar a resposta oral. Guardar as duas declarações como trabalho conjunto, sem inferir competências individuais.

**Benefício pedagógico esperado.** Dar ao destinatário uma função verificável na revisão. Complementa a revisão por sugestões já existente em Canva Animais: aqui compara-se uma intenção concreta com a interpretação do leitor.

**Risco e esforço.** Constrangimento por discordância e confusão entre relato e observação. Usar linguagem descritiva, revisão facultativa e feedback sem juízo automático de clareza. Esforço médio, 2–3 dias; sem contas Canva, uploads ou comunicação entre dispositivos.

**Teste concreto.** Introduzir uma legenda longa irrelevante: deve guardar como edição declarada, sem elogiar a clareza. Registar interpretação diferente, rever enquadramento e retomar: preservar ambas as versões. Verificar acessibilidade da imagem e observar se a revisão responde ao que o colega percebeu.

**Fronteira de ficheiros.** Novos `drafts/imagem-para-um-leitor.{html,md}`, DocSpec e teste dedicado; ilustração SVG incorporada. Usar os nomes neutros e o apoio comum atuais. Sem alterações ao catálogo, template distribuído ou atividades entregues.

Recomendo primeiro **Duas pontes iguais de cima**: aproveita uma simulação existente, oferece um contraexemplo observável e acrescenta investigação com alcance pequeno.
