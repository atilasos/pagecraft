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
| `activity_state` | `activity_state` | `PageCraftBridge.activityState(unitId, state)` | `state` — Checkpoint para recuperar a etapa e as escolhas da atividade. |
| `unit_started` | `unit_started` | `PageCraftBridge.unitStarted(unitId)` | — |
| `level_changed` | `level_changed` | `PageCraftBridge.levelChanged(unitId, level)` | `level` — Nível de diferenciação escolhido: support, intermediate ou challenge. |
| `attempt` | `attempt` | `PageCraftBridge.attempt(unitId, correct, detail)` | `correct` — Indica se a tentativa corresponde à resposta esperada.<br>`detail` — Descrição curta e opcional da tentativa observada. |
| `discovery` | `discovery` | `PageCraftBridge.discovery(unitId, message)` | `message` — Descrição curta da descoberta feita pela criança. |
| `assessment_result` | `assessment_result` | `PageCraftBridge.assessment(unitId, result, detail)` | `result` — Resultado observável do item de avaliação.<br>`detail` — Contexto curto e opcional sobre o resultado. |
| `feedback_request` | `feedback_request` | `PageCraftBridge.askForFeedback(unitId, question, answer, expected)` | `question` — Pergunta ou tarefa apresentada à criança.<br>`answer` — Resposta dada pela criança.<br>`expected` — Resposta de referência indicada pela atividade. |
| `help_needed` | `help_needed` | `PageCraftBridge.helpNeeded(unitId, note)` | `note` — Contexto curto e opcional sobre o pedido de ajuda. |
| `hint_presented` | `hint_presented` | `PageCraftBridge.hintPresented(unitId, hintId, text, context)` | `hint_id` — Pista apresentada; não comprova leitura.<br>`text` — Ação mostrada.<br>`context` — Etapa, tentativa, critérios e versão do guião. |
| `hint_feedback` | `hint_feedback` | `PageCraftBridge.hintFeedback(unitId, hintId, usefulness)` | `hint_id` — Pista a que a declaração se refere.<br>`usefulness` — helped ou not_helped, segundo o grupo. |
| `hint_acknowledged` | `hint_acknowledged` | `PageCraftBridge.hintAcknowledged(unitId, hintId, action)` | `hint_id` — Pista do modal reconhecida por uma escolha explícita.<br>`action` — continue, next ou teacher; não comprova leitura ou compreensão. |
| `hint_listened` | `hint_listened` | `PageCraftBridge.hintListened(unitId, hintId)` | `hint_id` — O grupo pediu a leitura; não comprova que ouviu até ao fim. |
| `work_location` | `work_location` | `PageCraftBridge.workLocation(unitId, location, label)` | `location` — Local declarado: external, pagecraft, reading ou discussion.<br>`label` — Nome da aplicação ou contexto externo, quando aplicável. |
| `help_resolved` | `help_resolved` | `PageCraftBridge.helpResolved(unitId, note)` | `note` — O grupo declarou que já consegue continuar; não comprova intervenção docente. |
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
3. Para atividades novas, usa o plano do DocSpec e o componente comum de `references/contextual-support.md`. Atualiza a tentativa com `PageCraftSupport.update(...)`; pede uma pista só por confirmação relevante ou pedido explícito, com contexto e correlação.
4. O componente oferece ajuda ao professor e regista pistas apresentadas, utilidade declarada e trabalho externo. Conserva estes registos distintos.
5. O feedback local imediato continua a mandar; o feedback do assistente é uma camada extra e pode nunca chegar.
6. Nunca uses rede. A ponte usa exclusivamente `postMessage`.
