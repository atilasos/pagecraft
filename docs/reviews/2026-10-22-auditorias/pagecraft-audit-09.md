# Avaliação 09 · Decidir e preparar com menos esforço

Investigação só de leitura sobre `4c6ba90`, em 22-10-2026. Li AGENTS, CONTEXT, PRODUCT, DESIGN, ADRs 0002–0005 e 0007, a avaliação anterior e os clientes/serviços de preparação, acompanhamento e relatórios. Não executei browser nem testes dinâmicos. Não alterei o repositório, incluindo `catalog.json` e as duas atividades locais. As estimativas abaixo são de implementação e validação, não medições de utilização.

Consultei a API local da Sebenta com `health`, `search "avaliação formativa regulação aprendizagem" --kind wiki` e `read --content` de duas páginas. **Síntese da wiki:** "Avaliação Formativa", `20_Wiki/Avaliação Formativa.md`, estado `review`, confiança `medium`, liga recolha, interpretação e ajuste efetivo de tarefas/apoios; pede atenção às estratégias, além do acerto. "Tempo de Estudo Autónomo", `20_Wiki/Tempo de Estudo Autónomo.md`, estado `review`, confiança `medium`, descreve autonomia organizada por planos, materiais e parcerias, permitindo acompanhamento docente individual. Ambas revistas em 09-07-2026. As propostas seguintes são minhas; estas sínteses não demonstram eficácia do produto.

Já existem triagem com espera, local de trabalho declarado, resolução de ajuda declarada pelo grupo, PIT, reflexão individual, continuação de sessões e observação docente nas realizações permanentes. O resumo já apresenta recorrências, pistas pouco úteis, revisões e propostas com referências (`server/support_summary.py:62`, `:70`, `:73`; `server/static/learning/teacher.js:185`). Não proponho refazê-lo. Também excluo checkpoints dos relatórios, cache, recuperação, nomes dos apoios e corrida de nível, tratados por #51–55.

**1. Abrir o contexto do pedido de ajuda no primeiro toque**

O professor sabe a quem ir, mas precisa de reconstituir o problema. O cartão destaca contagens (`server/static/teacher/class.js:734`); a tentativa aparece apenas como "acertou" ou "fez uma tentativa" e o pedido omite a nota (`:27`, `:32`). O percurso repete essas descrições (`:844`). Contudo, o contrato admite detalhe e nota (`server/classroom/event_types.py:184`, `:232`) e há um descritor mais rico nas realizações (`server/learning_reports.py:24`).

Ao abrir o aluno/grupo, mostrar primeiro o pedido pendente, etapa, nota, resposta disponível, última pista e utilidade declarada, cada elemento com data e referência. Manter a cronologia abaixo. Onde falta contexto, escrever "não registado"; conservar autoria conjunta e reflexão individual separadas. Usar texto legível, sem exigir leitura de JSON. Abrir o painel nunca resolve o pedido.

O benefício esperado é reduzir a procura e permitir uma pergunta pedagógica pertinente antes de explicar tudo novamente. Risco: associar uma pista ou resposta de outra etapa/composição ao pedido; ligar por identificadores e não apenas por proximidade temporal. Esforço pequeno/médio, 2–3 dias.

Teste concreto: dois grupos fictícios, três etapas e duas pistas; verificar que cada painel mostra apenas o contexto correspondente, incluindo "não registado", e que abrir/fechar preserva a ajuda pendente. Fronteira: `server/static/teacher/class.js`, `class.html`, novo descritor em `server/static/teacher/evidence.js` e teste em `tests/browser/`. O histórico já entrega os dados autorizados em `server/api/classroom.py:519`; não exige nova persistência. Sem alterações a atividades publicadas ou nomes da ponte.

**2. Levar uma decisão do balanço para o Plano de aula**

Há sugestões de revisão, mas não uma ação para as guardar como decisão (`server/static/learning/support-summary.js:39`). "Preparar" abre geração de atividades (`server/static/teacher/index.html:25`); lançar exige nova seleção (`server/static/teacher/class.js:348`). O Plano de aula está definido em `CONTEXT.md:23`, mas não encontrei fila persistente correspondente nos percursos inspecionados. A navegação da aula também omite "Atividades e progressos" (`server/static/teacher/class.html:17`).

Acrescentar "Preparar próximo passo" ao balanço: professor escolhe atividade existente ou continuação, escreve o ajuste e conserva ligações aos registos que motivaram a decisão. Guardar numa fila ordenada por turma, sem calendário. "Começar" usa os comandos atuais de lançar/continuar. Mostrar a mesma navegação nas três páginas. Primeiro incremento limitado a sessões de turma, sem reunir crianças automaticamente pelo nome.

Benefício: evitar copiar notas e procurar novamente recursos; tornar verificável a passagem de evidência a intervenção. Risco: transformar sugestões em decisões automáticas ou criar trabalho administrativo. Campos opcionais e confirmação explícita do professor; fila distinta do PIT. Esforço médio, 4–6 dias.

Teste: guardar uma continuação motivada por dois registos, recarregar noutro contexto, reordenar e começar; confirmar identidade da sessão e referências preservadas, sem duplicação por duplo toque. Fronteira: novos `server/lesson_plans.py` e `server/api/lesson_plans.py`, integração em `server/app.py`, clientes `server/static/teacher/`, `server/static/learning/support-summary.js` e testes de persistência/acesso.

**3. Comparar duas estratégias antes de escolher uma intervenção**

Proposta criativa: uma mesa privada de comparação. O relatório da turma privilegia contagens (`server/static/teacher/class.js:233`), embora as reflexões guardem estratégia e próximo passo (`server/classroom/event_types.py:212`) e o resumo encontre alterações antes/depois (`server/support_summary.py:35`).

O professor seleciona manualmente dois excertos da mesma tarefa e coloca-os lado a lado, com pergunta orientadora: "Que diferença merece ser explorada com estes grupos?". Pode guardar a pergunta no plano da proposta 2. Sem classificação, seleção automática de "melhores" ou divulgação no quadro. Quando só há resposta conjunta, identificá-la como tal; nenhuma compreensão individual é presumida.

Benefício: apoiar decisões sobre estratégias e preparar diálogo entre pares, em vez de decidir apenas por acertos. Risco: comparar tarefas distintas ou tomar declarações como observação; mostrar tarefa, versão e origem, recusando comparação automática sem contexto. Esforço médio, 3–4 dias após a proposta 1.

Teste: comparar respostas com igual acerto e estratégias diferentes; conferir autoria, separação das vozes e ausência de acesso por aluno/quadro. Fronteira: novo `server/static/teacher/compare.js`, painel em `class.html`, descritor da proposta 1 e testes de autorização/apresentação, reutilizando os históricos autorizados existentes.

Recomendo começar pela proposta 1: corrige uma perda concreta de contexto no momento de intervir, reaproveita informação existente e exige menos mudanças do que introduzir planeamento persistente.
