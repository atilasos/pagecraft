# Bilhete de regresso no Studio

Implementação da proposta 1 de `/tmp/pagecraft-audit-01.md`, a partir de
`4c6ba90476a498a03b08fd88dea96c432ba767cd`. Worktree atribuído e confirmado antes
das alterações: `/home/proteu/.t3/worktrees/pagecraft/t3-a5b93f12`, branch
`feat/bilhete-regresso`, inicialmente sem alterações locais.

## Problema e resultado

Antes, recarregar ou retomar a atividade não oferecia a intenção anterior. Era
preciso abrir a reflexão, onde o próximo passo guardado preenchia o campo editável.

Agora, o Studio consulta o endpoint autorizado de reflexões ao montar o grupo.
Quando há texto guardado, oferece o botão opcional "O meu próximo passo". A criança
escolhe explicitamente o nome e vê apenas a intenção desse nome. "Voltar ao
trabalho" fecha o cartão e devolve o foco ao botão. A atividade mantém-se acessível;
não há modal automático nem pergunta obrigatória.

Ao abrir a reflexão, as intenções recebidas do servidor ficam congeladas para
essa abertura, incluindo trocas de criança, gravações e revisão de rascunhos.
A intenção anterior aparece separada do novo próximo passo. Esse campo começa
vazio, salvo se existir um rascunho da própria criança. As respostas aos critérios,
a estratégia, a autoria, as revisões e os identificadores mantêm o contrato existente.

A consulta e a seleção do nome não emitem acontecimentos, concluem trabalho nem
alteram respostas. O teste compara o histórico completo antes e depois da consulta.
Não foram criados endpoints, modelos ou fontes de evidência. `app.js`, incluindo
o transporte da fila, ficou sem alterações.

## Fronteiras verificadas

- O cartão usa exclusivamente `reflections` recebido do servidor ou a resposta
  confirmada de uma gravação. Rascunhos locais não alimentam o cartão nem a referência.
- Intenções vazias, só com espaços ou omitidas não oferecem cartão nem nome selecionável.
- Mudanças de grupo, composição, acesso ou identidade limpam seleção, texto e
  referência. Participantes removidos deixam de aparecer. A API existente continua
  responsável pela autorização do dispositivo e dos participantes atuais.
- As gerações do contexto e a ordem das leituras descartam respostas antigas.
  Uma leitura iniciada antes de uma gravação não substitui o valor confirmado.
- Uma falha de leitura opcional deixa a atividade disponível. A reflexão permite
  tentar novamente. Uma resposta 401 continua a invalidar a identidade revogada.
- Abrir o cartão não ultrapassa o bloqueio existente durante a recuperação do trabalho.

## Fundamentação pedagógica

A API da Sebenta foi consultada com `health`, pesquisa de "plano individual
trabalho avaliação cooperada" e leitura integral de `Plano Individual de Trabalho`
e `Avaliação Cooperada`. Ambas as páginas estavam em `review`, com confiança
`medium`, atualizadas em 09/07/2026.

Síntese da wiki: previsão, execução e confronto ajudam a orientar o plano seguinte;
a participação na avaliação liga-se à participação na planificação. O bilhete é
uma proposta de aplicação ao PageCraft, não uma funcionalidade prescrita pelas
fontes nem uma demonstração de eficácia. Mantém-se opcional para apoiar uma
decisão da criança. Há fontes e passagens de OCR ainda por verificar na wiki.

## Prova antes e depois

O primeiro teste foi executado antes da implementação, com os dois próximos passos
guardados por controlos reais. Falhou em
`test_saved_intentions_are_read_only_and_separate_from_new_step`, porque o botão
"O meu próximo passo" não existia. Resultado: `1 failed in 7.24s`.
Esse teste está no commit `7cd9487`, anterior às alterações da interface.

Capturas locais, produzidas pelo browser da sessão própria do Agent Browser Hub:

- Antes: `/tmp/pagecraft-bilhete-proof/antes.png`.
- Depois do reload, acesso opcional: `/tmp/pagecraft-bilhete-proof/atividade.png`.
- Bruno selecionado, intenção própria: `/tmp/pagecraft-bilhete-proof/bilhete-bruno.png`.
- Nova reflexão de Ana, referência separada e novo campo vazio:
  `/tmp/pagecraft-bilhete-proof/reflexao.png`.

Foram inspecionadas as capturas do cartão e da reflexão. Os testes usam apenas
Studio, turmas, sessões e ficheiros de dados descartáveis, sem produção.
Playwright liga-se por CDP à sessão `pagecraft-bilhete-regresso`, perfil `temporary`,
aberta pelo Hub para esta tarefa. Os contextos de cada teste fecham no final.
A sessão própria do Hub foi fechada depois da ronda final, com confirmação
`{"ok":true,"closed":"pagecraft-bilhete-regresso"}`.

## Reprodução e resultados

Com uma sessão própria do Hub aberta, obter o CDP com
`abh --json session show NOME_DA_SESSAO` e executar no worktree:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9331 PAGECRAFT_TICKET_PROOF=/tmp/pagecraft-bilhete-proof uv run --project /home/proteu/pagecraft --with playwright pytest tests/browser/test_return_ticket.py tests/browser/test_group_reflections.py tests/browser/test_group_continuation_ui.py -q
uv run --project /home/proteu/pagecraft pytest tests/test_group_continuation.py tests/test_work_groups.py -q
node --check server/static/student/reflection.js
git diff --check
```

A porta `9331` é a da sessão desta execução; substituí-la pela da nova sessão.
Criar o diretório de capturas antes de definir `PAGECRAFT_TICKET_PROOF`, ou omitir
essa variável para executar sem capturas. Não é necessário lançar outro browser.

- Browser: 11 testes passaram em 34,80 s, cobrindo as quatro provas novas, cinco regressões
  de reflexão e duas de continuação do trabalho. Log local:
  `/tmp/pagecraft-bilhete-proof/browser-final.txt`.
- API de grupos e continuação: 28 testes passaram em 1,92 s.
- Sintaxe JavaScript e `git diff --check`: sem erros.

Os quatro testes novos cobrem duas crianças com textos distintos, reload,
retoma noutro contexto de browser, referência congelada, campo novo vazio,
ausência de intenção, falha de leitura, composição alterada durante uma leitura,
revogação de identidade, resposta atrasada depois de nova gravação, rascunho
separado e recuperação do trabalho com falha e repetição.

## Commits de implementação

- `7cd9487` — Testa contrato do bilhete de regresso.
- `cba680a` — Mostra intenção guardada no regresso ao grupo.
- `5f548bd` — Protege o bilhete de leituras e rascunhos antigos.

Os ficheiros de produção alterados são apenas `server/static/student/index.html`
e `server/static/student/reflection.js`. A prova reproduzível está em
`tests/browser/test_return_ticket.py`. Este relatório completa a entrega para
revisão independente do agente principal.
