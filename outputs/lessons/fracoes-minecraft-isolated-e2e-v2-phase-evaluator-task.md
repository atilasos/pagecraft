# PageCraft Isolated Phase Task

## Identidade
Evaluator/Judge

## Contexto mínimo
- Slug: `fracoes-minecraft-isolated-e2e-v2`
- Tema: Frações equivalentes com Minecraft
- Ano: 2.º ano
- Duração: 35 minutos
- Repo PageCraft: `/Users/igor/dev/pagecraft`

## Fonte de verdade
Não uses conversa anterior como fonte de verdade. Usa apenas este enunciado, a identidade da tua fase e os ficheiros listados em Inputs.

## Inputs permitidos
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-docspec.json`
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-design-brief.md`
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-design-spec.json`
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-proofread-v1.json`
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2.html`

## Outputs obrigatórios
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-evaluation-v1.json`

## Contrato de output da fase
Criar `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-evaluation-v1.json` depois de executar `validate_lesson.py`:

- JSON object, sem markdown.
- Campos obrigatórios: `"pass"` boolean, `"acp_ok"` boolean, `"artifact_pass"` boolean, `"evidence"` object, `"blockers"` list.
- Usar o relatório `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-programmatic-validation.json` como evidência primária.
- Se `validate_lesson.py` falhar, não publicar e explicar os blockers.


## Comandos permitidos
- `python3 skills/pagecraft-openclaw/scripts/validate_lesson.py`
- `python3 -m json.tool`

## Limites
- usar conversa anterior como fonte de verdade
- ler artefactos de fases futuras
- alterar ficheiros fora de outputs/lessons
- publicar no catálogo
- declarar pass/fail final fora do Evaluator

## Critério de saída
- todos os writes declarados existem
- JSON produzido é válido quando aplicável
- bloqueios são registados explicitamente em vez de contornados

Se não conseguires cumprir a tarefa por falta de input, permissão ou informação, escreve o bloqueio no output da tua fase quando existir formato JSON, ou responde com `PHASE_BLOCKED` e a razão concreta.
