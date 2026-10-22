# Autoria das realizações entre separadores

Implementação da proposta 1 da auditoria `/tmp/pagecraft-audit-05.md`, em 22/10/2026.
Base `4c6ba90476a498a03b08fd88dea96c432ba767cd`, branch `fix/protect-learning-authorship`,
worktree `/home/proteu/.t3/worktrees/pagecraft/t3-ae3a563b`.

## Problema reproduzido antes da correção

O cookie HttpOnly `pagecraft_realization` é partilhado entre separadores. A página A
conservava a sua realização em memória, mas os pedidos não declaravam essa identidade.
Depois de iniciar B, o servidor atribuía a B uma resposta escrita em A.

Os testes introduzidos em `b98c1fe` falharam contra o servidor original:

- API: dois casos, aluno e pré-visualização do professor, devolveram HTTP 200 e
  acrescentaram a B o acontecimento `from-tab-A`, com `answer=Resposta A`.
- Browser real: A e B foram iniciados pela interface em separadores do mesmo contexto.
  Escrever `Resposta antiga A` em A devolveu HTTP 200 e alterou os acontecimentos de B.

Comandos executados antes da correção, no commit `b98c1fe`:

```bash
uv run --project /home/proteu/pagecraft pytest -q tests/test_learning_authorship.py -k 'stale and events'
PAGECRAFT_TEST_CDP=http://127.0.0.1:9332 uv run --project /home/proteu/pagecraft --with playwright pytest -q tests/browser/test_learning_authorship.py -k events
```

O teste de browser foi depois renomeado para `test_learning_authorship_ui.py`, para
evitar colisão com o módulo de testes API na recolha da suíte completa.

## Contrato implementado

`X-PageCraft-Realization` transporta o identificador esperado pelo separador.
`current_id` autentica primeiro o cookie e só depois compara os identificadores.
O header nunca seleciona um ficheiro nem concede acesso.

- `POST /me/events`, `/me/feedback`, `/me/finish` e `/me/leave` exigem o header.
  A ausência devolve HTTP 428, sem mutação nem alteração de cookie.
- Uma identidade autenticada diferente devolve HTTP 409 com
  `detail.code=realization_conflict`, antes de escrever, invocar feedback ou apagar o cookie.
  A resposta não revela o identificador da outra realização.
- Credenciais ausentes, falsas ou expiradas continuam a devolver HTTP 401,
  mesmo quando o header indica um identificador existente e o professor está autenticado.
- `GET /me` aceita descoberta inicial sem header. Um separador com identidade conhecida
  envia o header também na recuperação. O cliente conserva essa identidade em
  `sessionStorage`, na chave `pc-realization:<código da atividade>`.
- Recarregar A com o cookie de B devolve conflito e não carrega os dados de B.
  A fila `pc-queue:<id>` e a reflexão `pc-reflection:<id>` permanecem intactas.
  Um separador conhecido sem cookie também conserva os pendentes e não oferece nova entrada.
- O aviso de conflito em PT e EN permanece visível quando guardar, terminar ou sair falham.
  O cliente não apresenta a conclusão como guardada nem transforma o conflito de feedback
  numa pista de fallback entregue à atividade.

O HTML referencia uma nova versão do JavaScript para atualizar o contrato em páginas
reabertas. Clientes anteriores que continuem abertos recebem 428 ao tentar mutações.
IDs, credenciais, acontecimentos e autoria já persistidos mantêm-se.

## Prova depois da correção

Todos os servidores de teste usaram dados descartáveis. O browser foi lançado pelo
Agent Browser Hub, sessão própria `pagecraft-authorship`, perfil `temporary`, CDP na porta 9332.
O Playwright ligou-se apenas a essa sessão; cada teste criou o seu contexto isolado.

Resultados finais:

- 45 casos API dedicados passaram. Incluem todos os caminhos protegidos, aluno e professor,
  credenciais inválidas, clientes sem header, descoberta inicial, deduplicação,
  conclusão repetida e saída autorizada. A e B ficam intactos nos pedidos de A após iniciar B.
- 9 testes finais de browser de autoria e recuperação passaram. Incluem os quatro caminhos
  de mutação, recarga com fila e reflexão reais pendentes, ausência de cookie,
  falhas de rede e HTTP 503 na recuperação. Depois do conflito em A, B consegue guardar.
- A verificação alargada anterior passou com 52 testes de browser, incluindo frações,
  reflexão, retoma e integração com o Studio. Depois foram acrescentadas as verificações
  finais de credenciais ausentes e de pendentes, executadas nos 9 testes acima.
- A suíte final sem browser passou com 382 testes. A recolha global passou com 416 testes.
- `git diff --check` passou. `node --check server/static/learning/activity.js` passou.

Comandos finais, a executar neste worktree:

```bash
uv run --project /home/proteu/pagecraft pytest -q tests/test_learning_authorship.py
uv run --project /home/proteu/pagecraft pytest -q tests --ignore=tests/browser
uv run --project /home/proteu/pagecraft pytest --collect-only -q
PAGECRAFT_TEST_CDP=http://127.0.0.1:9332 uv run --project /home/proteu/pagecraft --with playwright pytest -q tests/browser/test_learning_authorship_ui.py tests/browser/test_learning_recovery.py
node --check server/static/learning/activity.js
git diff --check
```

Para repetir a verificação alargada, acrescentar ao comando de browser
`tests/browser/test_fraction_minecraft.py`, `tests/browser/test_fraction_units.py` e
`tests/browser/test_fraction_studio.py`. A porta CDP depende da nova sessão própria do Hub.
O ambiente instalado não contém Playwright; `--with playwright` fornece a dependência
temporariamente sem alterar o checkout original.

## Âmbito e limites

As alterações de produto pertencem a `server/api/learning.py` e
`server/static/learning/activity.js`, com atualização da versão no HTML anfitrião.
Os testes existentes foram adaptados para declarar a identidade esperada e remover
saídas anónimas usadas como limpeza em contextos que já são isolados.

O cliente Studio de grupos, as atividades publicadas e os dados de produção não foram alterados.
Não foi aberto PR nem feito merge. A branch fica local para revisão do agente principal.

A correção impede atribuição cruzada e conserva os pendentes no armazenamento do separador.
Não acrescenta recuperação de credenciais perdidas nem transfere pendentes de A para B.
Fechar definitivamente o separador continua sujeito aos limites de `sessionStorage` existentes.
Não houve ensaio com crianças nem alteração de critérios ou de comportamento pedagógico.
