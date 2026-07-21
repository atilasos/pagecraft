# PageCraft Isolated Phase Task

## Identidade
Proofreader

## Contexto mínimo
- Slug: `fracoes-minecraft-maker-e2e-20260524`
- Tema: Frações com maker Minecraft
- Ano: 2.º ano
- Duração: 45 minutos
- Repo PageCraft: `/Users/igor/dev/pagecraft`

## Fonte de verdade
Não uses conversa anterior como fonte de verdade. Usa apenas este enunciado, a identidade da tua fase e os ficheiros listados em Inputs.

## Inputs permitidos
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-docspec.json`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524.html`

## Outputs obrigatórios
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-proofread-v1.json`

## Contrato de output da fase
Criar `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-proofread-v1.json`:

- JSON object, sem markdown.
- Campos obrigatórios: `"pass"` boolean, `"severity"` string, `"issues"` list, `"recommendations"` list.
- Rever pt-PT/AO90, clareza para 2.º ano, adequação pedagógica e se há instruções que revelem o constraint cedo demais.
- `"severity"` deve ser `"none"`, `"low"`, `"minor"`, `"medium"` ou `"high"`.


## Comandos permitidos
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
