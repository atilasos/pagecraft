# Auditoria 08: papéis, quadro e exposição pública

Base verificada: `4c6ba90476a498a03b08fd88dea96c432ba767cd`. Investigação só de leitura do repositório. Li `AGENTS.md`, `CONTEXT.md`, ADRs 0004–0007 e a avaliação de 22/10. Não alterei o catálogo nem as duas atividades locais, não fiz commits, PRs ou delegações. Sem browser, dados reais ou pedidos a produção. As reproduções usaram ASGI e armazenamento temporário descartável.

## Fundamentação pedagógica

API local da Sebenta disponível. Executei `search` e `read --content` para duas páginas integrais:

- **Avaliação Cooperada**, `20_Wiki/Avaliação Cooperada.md`, estado `review`, confiança `medium`. Síntese da wiki: os alunos participam na gestão dos instrumentos e na planificação; os registos apoiam regulação coletiva e entreajuda.
- **Circuitos de Comunicação**, `20_Wiki/Circuitos de Comunicação.md`, estado `review`, confiança `medium`. Síntese da wiki: comunicar produções ajuda a explicitar conhecimento; professor e alunos preparam a comunicação, e os colegas perguntam e propõem melhorias. A página assinala fontes ainda por verificar.

As decisões de autorização e os comportamentos abaixo são propostas minhas. As páginas não especificam controlos técnicos nem demonstram eficácia destes desenhos.

## O que já existe

Há políticas obrigatórias nas rotas, cookies HttpOnly, identidade própria do Quadro, filtragem de acontecimentos por papel, expiração e revogação. As realizações permanentes guardam hash da credencial e escrever o mesmo nome não recupera históricos (`server/learning.py:96`, `:117`). Relatórios e observações docentes exigem Professor. A retoma usa códigos consumíveis e conserva autoria. Não repito as correções #51–55 sobre checkpoints, cache, recuperação, nomes de apoio ou corrida do nível.

## 1. Vincular também o stream do Quadro à sessão atual

**Problema demonstrado.** O conteúdo exige a sessão atual (`server/api/board.py:108`), mas o stream delega diretamente (`:102`); a autorização interna verifica apenas que a sessão pedida está viva (`server/api/classroom.py:579`). Criar uma nova sessão não fecha as anteriores (`server/classroom/service.py:316`). A sessão atual é a viva mais recente (`:423`).

Reproduzi com duas sessões sintéticas: `/api/board/session` indicava B; o HTML de A devolvia **404**, mas o handler do stream de A, após resolução real do papel Quadro, devolvia **200** e um snapshot com nomes e código de grupo de oito caracteres. Estes códigos dão entrada no trabalho guardado (`server/classroom/service.py:517`). A condição exige um quadro emparelhado que conheça o identificador de A; não é acesso anónimo.

**Comportamento proposto.** Aplicar a mesma seleção de sessão ao conteúdo e ao stream, antes do primeiro frame e durante a ligação. Quando muda a sessão projetada, terminar o stream anterior e reconduzir o Quadro à atual. Conservar sessões anteriores para os seus próprios alunos e para o Professor.

**Benefício pedagógico.** Evitar que códigos e nomes de outro trabalho reapareçam no ecrã coletivo; manter previsível quem tem acesso às produções e reflexões.

**Risco e esforço.** A troca deve conservar o trabalho em curso nos tablets. Esforço pequeno a médio, cerca de 1 dia.

**Teste concreto.** Abrir A, gerar código de retoma, começar B; exigir 404 no stream de A e ausência dos seus nomes/códigos. Abrir primeiro o stream de A e depois B; comprovar que nenhum novo frame de A chega. Professor e alunos de A conservam acesso autorizado.

**Fronteira.** `server/api/board.py`, ramo Quadro em `server/api/classroom.py`, `server/static/board/app.js` e testes de acesso/stream do Quadro.

## 2. Fazer a aprovação valer também para os artefactos do pipeline

**Problema demonstrado.** `/outputs` é um mount público (`server/app.py:276`). O pipeline grava HTML antes da revisão (`server/pipeline/runner.py:290`) e só depois chega a `awaiting_review`, anunciando precisamente `/outputs/<slug>.html` (`:323`). Um ficheiro sintético nesse diretório foi servido **200 sem papel**. O mount também abrange DocSpecs e avaliações gravados ali (`:183`). Não encontrei nem alego dados reais de crianças nesses artefactos.

O ADR-0004 tornou `/outputs` público deliberadamente. Porém, o domínio atual define rascunho como indisponível aos alunos (`CONTEXT.md:95`), e o ADR-0006 pretende proteger pré-visualizações. Há uma decisão de produto por reconciliar.

**Comportamento proposto.** Reservar os artefactos de geração ao Professor; disponibilizar aos alunos o HTML aprovado em `/activities`. Atualizar explicitamente a decisão antiga sobre `/outputs`.

**Benefício pedagógico.** A revisão docente passa a controlar efetivamente os materiais acessíveis à turma.

**Risco e esforço.** Endereços históricos de demonstração usam `/outputs`; inventariar os que precisam de publicação aprovada. Esforço pequeno, cerca de meio dia a 1 dia.

**Teste concreto.** Antes da aprovação, HTML e JSON recusados a anónimo, Aluno e Quadro; Professor vê a pré-visualização. Depois, `/activities/<slug>/` continua público.

**Fronteira.** `server/app.py`, referências de pré-visualização do pipeline, testes de acesso e ADR correspondente.

## 3. Criativa: preparar um recorte para o Momento de comunicação

**Problema demonstrado.** Existe pedido de partilha (`server/classroom/event_types.py:249`), mas o drawer só oferece mensagem e destaque (`server/static/teacher/class.html:208`). O Quadro carrega a atividade genérica (`server/static/board/app.js:150`). O Momento descrito em `CONTEXT.md:62` ainda não tem esse percurso.

**Comportamento proposto.** A criança escolhe uma produção e uma pergunta para os colegas; o Professor pré-visualiza e mostra apenas esse recorte ao Quadro, podendo retirá-lo. Começar com uma declaração textual guardada, ampliando depois para estados de atividades compatíveis. Reflexões individuais e histórico completo ficam fora do recorte.

**Benefício pedagógico.** Dar consequência ao pedido de partilha e criar interlocução sobre estratégias reais, com escolha do aluno.

**Risco e esforço.** Confundir recorte com reprodução integral ou expor campos adicionais. Esforço médio, 2–4 dias para a primeira modalidade.

**Teste concreto.** Só o recorte aprovado chega ao Quadro; outro aluno não o recebe; retirar ou fechar a sessão limpa a apresentação. O original permanece intacto.

**Fronteira.** Vocabulário e projeção de sessão, API docente, drawer, cliente Quadro e testes de autorização.

Melhor proposta recomendada: **1, vincular o stream do Quadro à sessão atual**, porque corrige uma discrepância reproduzida que envolve nomes e credenciais de acesso ao trabalho, com alcance delimitado.
