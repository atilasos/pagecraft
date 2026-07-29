# PageCraftBridge — contrato gerado de acontecimentos de sessão

<!-- Gerado por scripts/generate_bridge_artifacts.py a partir de SESSION_EVENT_TYPES. Não editar à mão. -->

A atividade é **sempre** um HTML self-contained e offline. A ponte é opcional e degrada silenciosamente: usa apenas `postMessage` para `window.parent`; `fetch`, XHR e WebSocket são proibidos dentro da atividade. Quando a página é aberta diretamente, os acontecimentos não têm ouvinte e nada acontece.

## Envelope

```json
{ "pagecraft": 1, "type": "<nome na ponte>", "unitId": "u1", "payload": {}, "ts": 1710000000000 }
```

O **nome interno** é o identificador canónico no servidor. O **nome na ponte** é o valor de `type` que fica incorporado nas atividades. Nos acontecimentos emitidos pela atividade os dois nomes coincidem. Nos recebidos, `bridge_name` é declarado separadamente no registo e é append-only: nunca se renomeia um nome publicado (ADR-0002), apenas se acrescenta outro durante uma migração deliberada.

## Emitidos pela atividade

| nome interno | nome na ponte (`type`) | emissor | payload declarado |
|---|---|---|---|
| `activity_loaded` | `activity_loaded` | automático pelo template | `title` — Título apresentado pela atividade carregada. |
| `heartbeat` | `heartbeat` | automático pelo template | — |
| `unit_started` | `unit_started` | `PageCraftBridge.unitStarted(unitId)` | — |
| `attempt` | `attempt` | `PageCraftBridge.attempt(unitId, correct, detail)` | `correct` — Indica se a tentativa corresponde à resposta esperada.<br>`detail` — Descrição curta e opcional da tentativa observada. |
| `discovery` | `discovery` | `PageCraftBridge.discovery(unitId, message)` | `message` — Descrição curta da descoberta feita pela criança. |
| `assessment_result` | `assessment_result` | `PageCraftBridge.assessment(unitId, result, detail)` | `result` — Resultado observável do item de avaliação.<br>`detail` — Contexto curto e opcional sobre o resultado. |
| `feedback_request` | `feedback_request` | `PageCraftBridge.askForFeedback(unitId, question, answer, expected)` | `question` — Pergunta ou tarefa apresentada à criança.<br>`answer` — Resposta dada pela criança.<br>`expected` — Resposta de referência indicada pela atividade. |
| `help_needed` | `help_needed` | `PageCraftBridge.helpNeeded(unitId, note)` | `note` — Contexto curto e opcional sobre o pedido de ajuda. |
| `share_requested` | `share_requested` | `PageCraftBridge.share(unitId, what)` | `what` — Trabalho que a criança quer levar ao momento de comunicação. |

`unitId` identifica a unidade no envelope e não faz parte de `payload`.

## Recebidos pela atividade

| nome interno | nome na ponte (`type`) | payload declarado | efeito |
|---|---|---|---|
| `ai_feedback` | `ai_feedback` | `text` — Feedback formativo apresentado à criança.<br>`unit_id` — Unidade da atividade a que o feedback diz respeito.<br>`source` — Origem do texto: assistente, cache ou resposta de contingência. | preenche `.ai-feedback` com `payload.text` (id `pagecraft-feedback` ou `targetId`) |
| `teacher_highlight` | `highlight` | `unit_id` — Unidade para a qual o professor chama a atenção.<br>`unit_label` — Nome legível da unidade apresentado à criança. | usa `unitId` do envelope para focar a unidade e aplicar `.pagecraft-attention` durante cerca de 6 s |

O host traduz o acontecimento interno para o envelope da ponte. Pode projetar apenas os campos necessários ao recetor; os campos acima documentam o payload canónico declarado no registo.

## Regras para o Builder

1. Usa os helpers listados na tabela e `PageCraftFeedback.show(...)` ou `showDiscovery(...)`; esses helpers já emitem os nomes normativos.
2. Dá `unitId` estável a cada unidade (`u1`, `u2`, … pela ordem do docspec), põe `id="u1"` (ou `data-unit="u1"`) no contentor DOM e chama `PageCraftBridge.unitStarted(unitId)` quando a unidade fica visível ou ativa pela primeira vez.
3. Em perguntas de texto livre, chama `PageCraftBridge.askForFeedback(unitId, pergunta, respostaDoAluno, respostaEsperada)` e inclui `<div class="ai-feedback" id="pagecraft-feedback"></div>` por baixo.
4. Inclui um botão «Preciso de ajuda» (`help-button`) por unidade ou global que chama `PageCraftBridge.helpNeeded(unitId)`.
5. O feedback local imediato continua a mandar; o feedback do assistente é uma camada extra e pode nunca chegar.
6. Nunca uses rede. A ponte usa exclusivamente `postMessage`.
