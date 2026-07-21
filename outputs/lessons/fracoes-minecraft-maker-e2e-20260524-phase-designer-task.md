# PageCraft Isolated Phase Task

## Identidade
Designer

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

## Outputs obrigatórios
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-design-brief.md`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-design-spec.json`

## Contrato de output da fase
Criar dois outputs:

- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-design-brief.md`: síntese curta de intenção visual, hierarquia, ritmo e adequação ao 2.º ano.
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-design-spec.json`: JSON object que mencione explicitamente acessibilidade, contraste, responsive/tablet/mobile, cores, tipografia, estados de feedback e layout.

O design deve ser específico para frações/Minecraft, não genérico.


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
