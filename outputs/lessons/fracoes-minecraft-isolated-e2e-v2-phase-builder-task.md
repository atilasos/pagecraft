# PageCraft Isolated Phase Task

## Identidade
Builder

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
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2-design-spec.json`

## Outputs obrigatórios
- `outputs/lessons/fracoes-minecraft-isolated-e2e-v2.html`

## Contrato de output da fase
Criar `outputs/lessons/fracoes-minecraft-isolated-e2e-v2.html`:

- HTML self-contained, com CSS e JavaScript inline.
- Sem URLs externas, CDN, imagens remotas ou dependências.
- Pelo menos uma interação real com `<button>` e atributos `aria-*`.
- Responsive para tablet e desktop.
- Texto em pt-PT, adequado ao 2.º ano.
- Diferenciação visível em apoio, intermédio e desafio.


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
