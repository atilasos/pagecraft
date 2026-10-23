# Auditoria 05: gravação, autoria e retoma

Base `4c6ba90`, 22/10/2026. Investigação só de leitura; nenhum ficheiro do repositório alterado. Mantidas as alterações locais de `catalog.json` e das duas atividades. Li `AGENTS.md`, `CONTEXT.md`, ADRs 0002, 0004, 0005 e 0007, avaliação anterior, clientes, APIs e testes. Verificação dinâmica com API ASGI em diretório temporário e transporte JavaScript extraído do ficheiro real, sem browser nem dados reais. Não executei a suíte completa.

## Fundamentação pedagógica

Consultei `health`, `search` e `read --content` da API local da Sebenta, pela skill obrigatória.

Síntese da wiki: **Avaliação Formativa**, `20_Wiki/Avaliação Formativa.md`, estado `review`, confiança `medium`, revista em 09/07/2026, associa a função formativa às decisões que ajustam o trabalho e à apropriação dos critérios e erros pela criança. **Avaliação Cooperada**, `20_Wiki/Avaliação Cooperada.md`, mesmo estado, confiança e data, liga avaliação à participação na planificação e à discussão dos registos pelo grupo. As páginas admitem lacunas documentais e OCR incerto. As propostas seguintes são minhas aplicações ao produto, não prescrições literais da wiki nem eficácia demonstrada.

## O que já existe

Os PRs #51–55 estão integrados: checkpoints separados da evidência; cache contextual e pedidos de feedback serializados; recuperação de realizações permanentes após rede/503; nomes neutros; escolha de apoio entregue no final da retoma. Não proponho refazer essas correções.

Também existem deduplicação, autoria conjunta com versões de composição/acesso, recuperação por código do grupo e reflexão individual revisível. `server/classroom/service.py:615` protege revisão e autoria da reflexão; `server/static/student/reflection.js:182` conserva o mesmo envio pendente para repetição. São bases a preservar.

## 1. Impedir gravação na realização de outro separador

**Problema demonstrado, prioridade crítica.** O cookie `pagecraft_realization` é único, emitido com `path='/'`, em `server/api/learning.py:173`. O cliente conserva a realização A em memória, mas envia acontecimentos para `/me/events` sem identificar A, em `server/static/learning/activity.js:217`; terminar faz o mesmo em `:409`. O servidor escolhe o destino exclusivamente pelo cookie em `server/api/learning.py:179` e `:195`. Abrir outra realização no mesmo browser substitui esse cookie.

Reprodução ASGI com o mesmo cookie jar, simulando pedidos de dois separadores: iniciar A, iniciar B, enviar resposta de A, terminar com reflexão de A. Resultado: HTTP 200 em ambos; A ficou com zero acontecimentos; B recebeu `from-tab-A` e terminou com `strategy='reflexão A'`. Não é a falha de rede corrigida em #53.

**Comportamento proposto.** Cada mutação declara o identificador esperado da realização. O servidor compara-o com a identidade autenticada antes de gravar, pedir feedback, terminar ou sair. Divergência devolve conflito; o cliente conserva o pendente e explica que outra realização foi aberta. O identificador não concede acesso e os cookies continuam HttpOnly.

**Benefício pedagógico.** Impede atribuir respostas e voz de uma criança a outra. **Risco:** incompatibilidade entre cliente antigo e API nova; exige atualização coordenada e recusa explícita. **Esforço:** 1–2 dias. **Teste concreto:** dois separadores do mesmo contexto, A/B distintos; pedidos antigos nunca alteram B nem apagam a fila A, incluindo finish e leave.

**Fronteira:** `server/api/learning.py`, `server/static/learning/activity.js`, `tests/test_learning.py` e novo teste de browser. Sem mexer nas atividades publicadas.

## 2. Dar ao trabalho individual a mesma proteção da fila dos grupos

**Problema demonstrado, prioridade alta.** `server/static/student/app.js:617` só define chave persistente quando existe grupo; `:452` não grava sem chave. Assim, trabalho individual sem rede vive apenas em memória e desaparece num reload. A fila recusa acontecimentos após 200 em `:436`; o recetor ignora essa recusa em `:500`, podendo apresentar respostas que nunca serão enviadas.

Ensaio Node do transporte real: 201 chamadas aceitaram 200 tanto individualmente como em grupo. A sessão individual escreveu zero chaves; o grupo escreveu `pc-group-outbox:…`. Esta proteção pertence ao Studio, distinto do cliente permanente corrigido em #53.

**Comportamento proposto.** Persistir a fila individual por sessão e identidade; restaurar e deduplicar antes de aceitar trabalho. Tornar a recusa visível e impedir confirmação de gravação integral enquanto houver trabalho recusado. Preservar as regras existentes para composição antiga.

**Benefício pedagógico.** A evidência disponível deixa de depender de trabalhar sozinho ou acompanhado. **Risco:** recuperar dados para identidade errada; chave e invalidação devem seguir a credencial. `sessionStorage` continua limitado ao separador. **Esforço:** 2–3 dias. **Teste concreto:** rede cortada, resposta individual, reload, reconexão e uma única evidência; repetir com grupo e 201 acontecimentos, exigindo aviso explícito sem falso “Guardado”.

**Fronteira:** `server/static/student/app.js`, `server/static/student/index.html`, `tests/browser/test_group_continuation_ui.py` e teste equivalente individual.

## 3. Retoma com um compromisso escolhido pela criança

**Oportunidade criativa, prioridade posterior.** Já se guarda `next_step` individual e o formulário permite revê-lo, em `server/static/student/reflection.js:119` e `:151`. Contudo, retomar apenas restaura acontecimentos e abre o trabalho em `server/static/student/app.js:237`. Falta trazer essa intenção para a decisão de hoje.

**Comportamento proposto.** Acrescentar um acesso opcional “O que queria experimentar?” na retoma do grupo. Cada criança escolhe o próprio nome e pode manter ou reformular o próximo passo, consultando a reflexão anterior. Guardar usa a revisão existente; nenhuma resposta ou apoio muda automaticamente. Primeira versão restrita ao mesmo grupo autorizado.

**Benefício pedagógico.** Liga balanço a planificação sem impor um formulário de entrada. **Risco:** ritualizar a reflexão; preservar opção de passar. **Esforço:** 2 dias. **Teste concreto:** retomar com duas reflexões diferentes, escolher uma, editar e guardar; a outra mantém conteúdo e revisão. **Fronteira:** `server/static/student/reflection.js`, `app.js`, `index.html` e `tests/browser/test_group_reflections.py`; reutilizar API e vocabulário existentes.

Melhor proposta recomendada: **1**, porque a corrupção de autoria foi reproduzida e compromete simultaneamente evidência, reflexão e confiança no registo.
