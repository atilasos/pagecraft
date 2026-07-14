# PageCraftBridge — contrato de telemetria da atividade

A atividade é **sempre** um HTML self-contained e offline. A telemetria é
opcional e degrada silenciosamente: `postMessage` para `window.parent`, sem
qualquer rede (`fetch`/XHR/WebSocket são proibidos dentro da atividade).
Quando a página é aberta diretamente (ficheiro local, catálogo), os eventos
não têm ouvinte e nada acontece.

## Mensagem

```json
{ "pagecraft": 1, "type": "<tipo>", "unitId": "u1", "payload": {}, "ts": 1710000000000 }
```

## Tipos emitidos pela atividade

| type | quando | payload |
|---|---|---|
| `activity_loaded` | no arranque, se embutida | `{title}` |
| `heartbeat` | a cada 30s com página visível | `{}` |
| `unit_started` | o aluno entra numa unidade | `{}` |
| `attempt` | tentativa numa interação/quiz | `{correct: bool, detail}` |
| `discovery` | o aluno descobriu o invariante | `{message}` |
| `assessment_result` | item de avaliação observável concluído | `{result, detail}` |
| `feedback_request` | resposta aberta que merece feedback IA | `{question, answer, expected}` |
| `help_needed` | o aluno pediu ajuda | `{note}` |
| `share_requested` | o aluno quer partilhar no circuito de comunicação | `{what}` |

## Tipos recebidos pela atividade

| type | efeito |
|---|---|
| `ai_feedback` | preenche a caixa `.ai-feedback` com `payload.text` (id `pagecraft-feedback` ou `targetId`) |
| `highlight` | faz scroll até à unidade `unitId` e aplica `.pagecraft-attention` (brilho âmbar ~6 s) — o professor está a chamar a atenção para essa parte |

## Regras para o Builder

1. Usa os helpers do template: `PageCraftBridge.attempt/discovery/assessment/askForFeedback/helpNeeded/share`, `PageCraftFeedback.show(...)` e `showDiscovery(...)` — já emitem os eventos certos.
2. Dá `unitId` estável a cada unidade (`u1`, `u2`, … pela ordem do docspec), põe `id="u1"` (ou `data-unit="u1"`) no contentor DOM dessa unidade, e chama `PageCraftBridge.unitStarted(unitId)` quando a unidade fica visível/ativa pela primeira vez.
3. Em perguntas de resposta aberta (texto livre), chama `askForFeedback(unitId, pergunta, respostaDoAluno, respostaEsperada)` e inclui uma caixa `<div class="ai-feedback" id="pagecraft-feedback"></div>` por baixo.
4. Inclui um botão «Preciso de ajuda» (classe `help-button`) por unidade ou global que chama `PageCraftBridge.helpNeeded(unitId)`.
5. O feedback local imediato continua a mandar (verde-suave/âmbar); o feedback IA é camada extra e pode nunca chegar — a atividade não pode depender dele.
6. Nunca uses rede. A telemetria é só `postMessage`.
