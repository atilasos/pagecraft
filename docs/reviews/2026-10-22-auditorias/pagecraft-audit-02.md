# Auditoria 02: participação na avaliação e evidência no quadro

Base inspecionada: `4c6ba90`, 22/10/2026. Investigação estática, só leitura, sem browser ou dados reais. Li `AGENTS.md`, `CONTEXT.md`, ADR-0002/0004/0005/0007 e `docs/reviews/2026-10-22-avaliacao-pagecraft.md`. As alterações locais em `catalog.json` e nas duas atividades ficaram intocadas. Não implementei nem executei testes; os testes abaixo são critérios de aceitação propostos.

## Fundamentação consultada

Apliquei a skill `sebenta-wiki`: API local saudável, `search "avaliação cooperada conselho critérios" --kind wiki`, seguida de `read --content` das duas páginas:

- **Avaliação Cooperada**, `20_Wiki/Avaliação Cooperada.md`, estado `review`, confiança `medium`, atualizada em 09/07/2026. Síntese da wiki: a participação efetiva inclui planificação e gestão dos instrumentos; critérios e instrumentos podem ser renegociados; os registos devem alimentar discussão e entreajuda. A página assinala fontes nucleares por ler e OCR frágil em algumas passagens.
- **Conselho de Cooperação Educativa**, `20_Wiki/Conselho de Cooperação Educativa.md`, estado `review`, confiança `low`, atualizada em 08/07/2026. Síntese da wiki: o conselho permite negociar planos, critérios e procedimentos, avaliar o trabalho e decidir alterações. A cobertura documental é incompleta; não tomo os seus pormenores operacionais como prescrição.

As propostas seguintes são minhas, inspiradas nessas sínteses. Não constam como funcionalidades prescritas pelas fontes nem demonstram eficácia em crianças.

## O que já existe

A reflexão do grupo é individual, pode ser omitida e revista, tem leitura por pedido e conserva autoria e versão: `server/static/student/reflection.js:114`, `server/static/student/reflection.js:182`, `server/classroom/service.py:615`. Os relatórios distinguem reflexão e trabalho conjunto, incluindo uma ressalva sobre desempenho individual: `server/classroom/reports.py:142`. O PIT tem estados até “para partilhar”, mas está oculto no percurso de grupo: `server/classroom/service.py:984`, `server/static/student/app.js:200`.

O quadro tem papel próprio e recebe apenas projeção coletiva: `server/classroom/live_state.py:144`, `server/api/classroom.py:634`. Preservar esta fronteira é requisito, não uma lacuna a remover. Estas propostas não repetem #51–55: checkpoints, cache de feedback, recuperação, nomes de apoios e corrida na retoma.

## 1. Critérios que a turma pode pôr à prova e rever

**Problema e evidência.** Os critérios chegam da atividade registada ou do DocSpec: `server/classroom/activity_content.py:52`. O contrato tem apenas identificador e textos PT/EN: `server/criteria.py:7`. O formulário apresenta opções de autoavaliação sobre esses critérios: `server/static/student/reflection.js:124`. Nestes percursos não encontrei propostas dos alunos, deliberação ou revisão coletiva. A revisão anterior já reconhece esta oportunidade. Acrescentar uma pergunta final não transfere poder de decisão.

**Comportamento proposto.** Antes do trabalho, apresentar os critérios em linguagem infantil e permitir sugerir alterações ou declarar dúvidas. A turma discute; o professor regista o acordo e a justificação de propostas adiadas, mantendo as metas curriculares explícitas. Uma ideia criativa é um “teste do critério”: usar dois exemplos fictícios, um deles ambíguo, e perguntar se a formulação permite explicar a diferença. A turma pode reformular após esse ensaio. Durante a atividade, os critérios acordados permanecem consultáveis. A reflexão referencia a versão efetivamente conhecida; revisões posteriores preservam a anterior.

**Benefício pedagógico esperado.** Apropriação dos critérios e participação na planificação. O desacordo passa a poder alterar o instrumento, em vez de terminar num comentário sem consequência.

**Risco e esforço.** Esforço grande. Pode criar uma cerimónia de aprovação ou substituir discussão por votação. Começar com um único critério em discussão, aceitar participação oral mediada e conservar razões e dissensos. Não transformar o acordo em regra automática de correção.

**Teste concreto.** Numa sessão fictícia, duas crianças propõem formulações diferentes; o professor regista uma decisão. Uma reflexão na versão 1 conserva o texto original depois da versão 2. Repetir o envio não duplica propostas; um grupo alheio não altera a decisão. Em ensaio pedagógico, verificar se uma sugestão infantil consegue efetivamente modificar o critério.

**Fronteira de ficheiros.** Novo módulo `server/classroom/criteria.py`; integração em `activity_content.py`, `service.py`, `event_types.py`, `server/api/classroom.py`; interfaces `server/static/student/` e `server/static/teacher/class.*`; testes dedicados de versões e autorização. Não alterar atividades publicadas nem a correção automática.

## 2. Momento de comunicação com escolha explícita e consequência

**Problema e evidência.** `CONTEXT.md:62` promete “Mostrar no quadro”, mas `server/static/teacher/class.html:210` oferece apenas chamar a atenção do aluno, com execução em `class.js:875`. O quadro abre o HTML da atividade: `server/api/board.py:108`. Não encontrei apresentação do trabalho guardado. `share_requested` guarda apenas `what`: `server/classroom/event_types.py:250`. O relatório para conselho começa por contagens individuais: `server/classroom/reports.py:132`.

**Comportamento proposto.** A criança escolhe uma produção ou excerto observado, explica “quero discutir isto” e confirma a prévia; trabalho conjunto requer acordo dos participantes. O professor lança e termina a apresentação. Os colegas podem formular uma pergunta ou oferecer ajuda, mediadas pelo professor. No conselho, registar uma decisão e um próximo passo aceites pela criança, distinguindo evidência, reflexão, comentário e acordo. O relatório coletivo inclui só itens deliberadamente levados à discussão.

**Benefício pedagógico esperado.** Autoria sobre a visibilidade e comunicação que conduz a revisão ou entreajuda.

**Risco e esforço.** Esforço grande; exposição involuntária e pressão para apresentar. Primeira versão limitada a cartões explícitos de evidência, sem histórico completo ou autoavaliação privada. Rever `CONTEXT.md:63`, que promete estado integral. Preservar ADR-0004 e nomes congelados do ADR-0002.

**Teste concreto.** Com duas sessões fictícias, projetar um único excerto autorizado; verificar respostas HTTP e SSE para garantir ausência de outras respostas, reflexões e contagens. Cancelar, reconectar e terminar a sessão devem retirar o cartão. Confirmar que pedir partilha nunca equivale a apresentação realizada.

**Fronteira de ficheiros.** Novo `server/classroom/communications.py`; APIs de quadro e sala, `live_state.py`, `event_types.py`, `reports.py`; clientes professor/aluno/quadro e testes de acesso. Sem reescrever HTML publicado ou abrir o histórico do aluno ao quadro.

Melhor proposta recomendada: **1, critérios revistos pela turma**, porque introduz uma decisão real dos alunos sobre o trabalho que vão realizar e permite avaliar essa participação antes de ampliar a exposição pública da evidência.
