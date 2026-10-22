Avaliação 01: intenção, trabalho e reflexão

Base inspecionada: `4c6ba90`, em 22/10/2026. Investigação estática, só de leitura, com AGENTS.md, CONTEXT.md, avaliação anterior, ADRs 0004, 0005 e 0007, código e testes existentes. Sem browser, execução de testes, alterações ao repositório, commits ou PRs. As alterações locais de `catalog.json` e das duas atividades ficaram intactas. Os testes citados foram lidos, não executados nesta ronda.

Fundamentação na Sebenta

API local consultada por `health`, `search "plano individual trabalho avaliação cooperada" --kind wiki` e `read --content` integral de duas páginas:

- **Plano Individual de Trabalho**, `20_Wiki/Plano Individual de Trabalho.md`, estado `review`, confiança `medium`, atualização 09/07/2026. Síntese da wiki: prever, executar e confrontar o realizado deve orientar o plano seguinte; o plano individual admite trabalho com pares e depende de critérios e regulação coletiva.
- **Avaliação Cooperada**, `20_Wiki/Avaliação Cooperada.md`, estado `review`, confiança `medium`, atualização 09/07/2026. Síntese da wiki: a participação na avaliação pressupõe participação na planificação; os instrumentos devem apoiar decisões sobre o percurso seguinte e ser revistos pelo grupo.

As propostas abaixo são minhas aplicações ao produto. Estas páginas têm fontes ainda por verificar, incluindo OCR; não demonstram eficácia das funcionalidades propostas.

O que já existe

O PIT é escrito pela criança e conservado por acontecimentos: `server/classroom/service.py:942` e `:211`. Os quatro estados existem, incluindo recuo seguro de “para partilhar” para “feito”, em `:985`; autoria alheia é recusada em `:981`. A interface recupera itens pelo estado recebido, em `server/static/student/app.js:333`.

A reflexão do grupo já é individual, facultativa e revisível, com estratégia e próximo passo: `server/static/student/index.html:87`, `server/classroom/service.py:615`. O endpoint limita as reflexões aos participantes atuais daquele dispositivo: `server/api/classroom.py:374`. A retoma conserva trabalho e credenciais delimitadas, conforme ADR-0007 e `tests/test_group_continuation.py:30`. Nas realizações permanentes, o próximo passo já aparece no ecrã final: `server/static/learning/activity.js:346`.

Estas oportunidades não repetem #51–55: não alteram exportação de checkpoints, cache de feedback, recuperação de rede das realizações, nomes dos apoios ou escolha de nível durante a retoma.

1. **Bilhete de regresso escrito pela criança. Prioridade alta; proposta criativa.**

Problema e evidência: no Studio em grupo, o próximo passo só reaparece quando se abre novamente a reflexão, preenchendo o campo editável, em `server/static/student/reflection.js:119` e `:151`. A montagem não consulta a reflexão guardada, em `:26`; a retoma termina mostrando a atividade, em `server/static/student/app.js:243`. Existe memória técnica, mas falta um lembrete da intenção antes de continuar.

Comportamento: depois da retoma autorizada, oferecer “O meu próximo passo”. Cada criança escolhe o nome e vê “Da última vez quiseste experimentar…” com o seu texto guardado. “Voltar ao trabalho” fecha o cartão. Ao refletir novamente, apresentar aquela intenção como referência separada do novo campo. Manter a referência da revisão anterior durante essa abertura. Não criar itens, conclusões ou evidência automaticamente. Sem texto anterior, não mostrar cartão.

Benefício pedagógico: torna a intenção anterior utilizável no trabalho e no balanço seguinte, sem exigir outra pergunta obrigatória. Risco: atribuir a intenção ao colega ou confundir rascunho com versão guardada; usar exclusivamente a resposta autorizada do servidor, invalidar o cartão em mudanças de composição e não bloquear a atividade se a consulta falhar.

Esforço estimado: 1–2 dias. Fronteira: `server/static/student/{app.js,reflection.js,index.html}` e `tests/browser/test_group_reflections.py`; reutilizar o endpoint existente. Teste concreto: Ana e Bruno guardam próximos passos diferentes; fechar, reativar e entrar noutro browser; cada nome mostra o texto correto; um participante removido desaparece; nenhum acontecimento adicional é criado por abrir o cartão.

2. **“Voltar a trabalhar” num item concluído. Prioridade média.**

Problema e evidência: a máquina de estados em `server/classroom/service.py:985` só alterna entre “feito” e “para partilhar” depois da conclusão. A interface oferece apenas avançar, em `server/static/student/app.js:808`. Uma criança que decidiu rever o trabalho não consegue declarar “a fazer” mantendo o mesmo item.

Comportamento: ação secundária explícita “Voltar a trabalhar”, de “feito” ou “para partilhar” para “a fazer”, conservando texto, identificador, autor e histórico. Preservar o toque principal atual.

Benefício pedagógico: legitima revisão após reflexão ou conversa com colegas. Risco: alteração involuntária e repetição de pedidos; usar transição explícita e idempotente. Esforço: cerca de 1 dia. Fronteira: `server/classroom/service.py`, `server/api/classroom.py`, `server/static/student/app.js`, `tests/test_api_integration.py`. Teste: concluir, partilhar, reabrir, repetir o pedido; obter “a fazer” sem duplicação e recusar outro autor.

3. **Plano individual no computador do par. Prioridade posterior.**

Problema e evidência: o botão desaparece em grupo, em `server/static/student/app.js:200`; a API recusa o PIT do grupo, em `server/api/classroom.py:470`, também documentado por `tests/test_work_groups.py:104`.

Comportamento: seleção explícita do nome para consultar e atualizar o próprio plano, aproveitando o padrão da reflexão individual. Benefício: preserva intenção pessoal durante cooperação. Risco: autoria e acesso; exige contrato próprio por participante, sem simplesmente retirar o 403. Esforço: 3–5 dias. Fronteira: `server/api/classroom.py`, `server/classroom/{service.py,live_state.py}`, `server/static/student/{app.js,index.html}` e `tests/test_work_groups.py`. Teste: Ana altera o plano de Ana; composição muda; os itens anteriores mantêm autoria e deixam de estar acessíveis a participantes removidos.

Recomendo selecionar primeiro o bilhete de regresso: reutiliza a voz já guardada e aproxima intenção, trabalho e reflexão com uma alteração pequena e verificável.
