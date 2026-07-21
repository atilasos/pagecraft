# PageCraft Isolated Phase Task

## Identidade
Builder

## Contexto mínimo
- Slug: `pagecraft-isolated-smoke`
- Tema: Teste de pipeline isolado
- Ano: 2.º ano
- Duração: 20 minutos
- Repo PageCraft: `/Users/igor/dev/pagecraft`

## Fonte de verdade
Não uses conversa anterior como fonte de verdade. Usa apenas este enunciado, a identidade da tua fase e os ficheiros listados em Inputs.

## Inputs permitidos
- `outputs/lessons/pagecraft-isolated-smoke-docspec.json`
- `outputs/lessons/pagecraft-isolated-smoke-design-spec.json`

## Outputs obrigatórios
- `outputs/lessons/pagecraft-isolated-smoke.html`

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
