# PageCraft Isolated Phase Task

## Identidade
Architect

## Contexto mínimo
- Slug: `fracoes-minecraft-isolated-e2e-v2`
- Tema: Frações equivalentes com Minecraft
- Ano: 2.º ano
- Duração: 35 minutos
- Repo PageCraft: `/Users/igor/dev/pagecraft`

## Fonte de verdade
Não uses conversa anterior como fonte de verdade. Usa apenas este enunciado, a identidade da tua fase e os ficheiros listados em Inputs.

## Inputs permitidos
- Nenhum artefacto prévio.

## Outputs obrigatórios
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-docspec.json`

## Contrato de output da fase
DocSpec-AM mínimo obrigatório para `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-docspec.json`:

- JSON object, sem markdown.
- `topic`: string.
- `duration`: inteiro positivo em minutos.
- `objectives`: lista não vazia.
- `curriculum.ae`: lista não vazia com objectos que incluam disciplina/descritor.
- `memAlignment.modules`: lista não vazia.
- `units`: lista não vazia.
- cada item de `units` deve incluir `summary`, `textDescription`, `duration`, `interaction` e `differentiation`.
- `interaction.state`, `interaction.render`, `interaction.transition`, `interaction.constraint` e `interaction.assessment` são obrigatórios.
- `differentiation.support`, `differentiation.standard` e `differentiation.challenge` são obrigatórios.
- O constraint deve ser descoberto pela criança, não revelado como regra pronta.
- O assessment deve ser observável: algo que a criança faz, diz ou produz.


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
