# Auditoria 06: feedback automático, IA e regulação pelo aluno

Base `4c6ba90`, 22/10/2026. Investigação só de leitura; sem browser, dados reais, chamadas a modelos, alterações ao repositório, commits ou PRs. As propostas seguintes estão ordenadas por prioridade e destinam-se à seleção.

## Fundamento e limites

Consultei `AGENTS.md`, `CONTEXT.md`, ADRs 0002, 0004 e 0005, a avaliação `docs/reviews/2026-10-22-avaliacao-pagecraft.md`, implementação, testes e documentação do piloto.

**Síntese da wiki**, consultada pela API local com `search` e `read --content`:

- **Avaliação Formativa**, `20_Wiki/Avaliação Formativa.md`, estado `review`, confiança `medium`, revista em 09/07/2026. A informação recolhida torna-se formativa quando permite ajustar a ação; a apropriação dos critérios e a compreensão da estratégia usada sustentam a autorregulação.
- **Inteligência Artificial na Educação**, `20_Wiki/Inteligência Artificial na Educação.md`, estado `review`, confiança `medium`, revista em 09/07/2026. Propõe preservar o pensamento e autoria do aluno e a mediação docente. A própria página avisa que grande parte da fundamentação consiste em resumos gerados de artigos/preprints, sem leitura integral dos originais. Uso-a como orientação local, não como demonstração de eficácia no 1.º ciclo.

**Inferência desta auditoria:** uma pista útil deve permitir uma ação observável ligada a um critério, sem classificar a pessoa nem fornecer o produto final. As soluções abaixo são propostas minhas.

Já existem pistas progressivas revistas, áudio opcional, utilidade declarada, pedidos ao professor, rejeição de respostas atrasadas e contexto com idade, critérios e tentativas: `server/pipeline/prompts/activity-support.js:72`, `:119`, `:153`, `:176`. A síntese docente já distingue revisão observada e alteração externa declarada: `server/support_summary.py:28`. Os 21 testes JavaScript passaram nesta ronda.

A cobertura precisa de cuidado: uma leitura dos 107 DocSpecs versionados em `activities/` encontrou zero com `support`. O piloto contextual já existe, separado em rascunho: `scripts/build_canva_support_pilot.py:24`, `:27`; `docs/piloto-autonomia-canva.md:5`. Isto não significa ausência de feedback local nas atividades. As propostas incidem sobretudo no motor e em futuros rascunhos, sem presumir utilização generalizada em sala. Não repetem #51–55: exportação de checkpoints, cache, retoma, nomes dos apoios e entrega de nível.

## 1. Oferecer um modo de IA limitado a ações revistas

**Problema e evidência.** O prompt proíbe soluções e juízos pessoais em `server/feedback_context.py:31`, mas o schema só controla estrutura/comprimento e o filtro cobre poucas palavras, `:8`, `:17`. O texto livre passa diretamente para entrega em `server/learning_feedback.py:70` e `server/classroom/feedback.py:269`. Num ensaio em memória com fornecedor simulado, `_generate` aceitou "A resposta é 4." e "És preguiçoso.". É prova da aceitação técnica, não da frequência destas saídas num modelo real.

**Comportamento proposto.** Permitir que uma atividade escolha um modo em que a IA seleciona o identificador de uma pista ou pergunta discriminante previamente revista. O servidor resolve o texto no plano autorizado da atividade. Uma seleção inexistente ou contexto insuficiente oferece a próxima pista local ou ajuda docente. Exemplo de texto revisto: "Compara as duas representações. O que contaste em cada uma?".

**Benefício pedagógico.** Mantém uma ação executável e a investigação do erro nas mãos do aluno, com conteúdo verificável pelo professor.

**Risco e esforço.** Reduz a capacidade de responder a dificuldades imprevistas e exige curadoria; esforço médio/alto. Começar por um obstáculo num rascunho, sem presumir que todos os textos revistos são adequados.

**Teste concreto.** Nos dois percursos, simular resposta livre, ID inexistente e ID de outra etapa; nenhum texto livre chega ao aluno. Um ID autorizado apresenta exatamente o texto revisto, na língua e composição certas.

**Fronteira.** `server/feedback_context.py`, `server/learning_feedback.py`, `server/classroom/feedback.py`, schema/plano de apoio, resolução do conteúdo da atividade e testes correspondentes. Sem reescrever atividades publicadas.

## 2. Unir confirmação, resposta observada e feedback local

**Problema e evidência.** `PageCraftFeedback.show` emite a mensagem de feedback como `detail`, `server/pipeline/prompts/template-base.html:532`. O apoio comum só extrai resposta de `detail.value`, `activity-support.js:300`, e não conta tentativas sem resposta conhecida, `:82`. A integração exige atualização explícita adicional, `server/pipeline/prompts/references/contextual-support.md:49`. Assim, usar apenas o helper visual não fornece contexto suficiente; não afirmo que o piloto, que tem adaptador próprio, esteja afetado.

**Comportamento proposto.** Acrescentar ao helper um argumento opcional com `value`, `question` e `task_id`, emitindo uma única confirmação completa. Conservar a assinatura existente e os nomes da ponte do ADR-0002.

**Benefício pedagógico.** A pista responde ao trabalho efetivamente confirmado e evita interpretar a própria mensagem corretiva como resposta da criança.

**Risco e esforço.** Estados compostos exigem seleção explícita dos dados pertinentes; esforço médio.

**Teste concreto.** Três respostas distintas pelo helper ativam uma pista com os três valores; repetir uma resposta não incrementa; texto aberto e autoavaliação continuam sem veredicto automático.

**Fronteira.** Template canónico, distribuições sincronizadas, referência de integração e testes JS; um rascunho de demonstração.

## 3. Criar um "espelho de tentativas" opcional

**Problema e evidência.** Os critérios chegam à IA, `activity-support.js:123`, mas não aparecem no painel comum, `:221`. O antes/depois já aparece na síntese docente, `server/static/learning/support-summary.js:28`.

**Comportamento proposto.** A criança escolhe comparar duas respostas suas, vê um critério e pode responder "O que mudaste?" ou ignorar. Sem solução-modelo, nota ou conclusão automática. É uma extensão criativa da revisão existente.

**Benefício pedagógico.** Torna a estratégia discutível e permite explicar a revisão ao par ou professor.

**Risco e esforço.** Pode acrescentar leitura; esforço médio. Limitar a um critério e textos curtos. Associação temporal nunca prova efeito da pista.

**Teste concreto.** Comparar versões preserva ambas, autoria e privacidade; ignorar permite avançar; não aparece "melhorou" por comparação automática.

**Fronteira.** Componente de apoio, adaptador de um rascunho e testes JS; reutilizar acontecimentos existentes antes de acrescentar vocabulário.

**Melhor proposta recomendada: 1**, primeiro num único obstáculo do piloto existente, para tornar verificável o conteúdo entregue antes de ampliar a exposição à IA.
