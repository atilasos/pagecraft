# PageCraft Fresh Builder Repair Task

## Identidade
Builder novo, isolado, em sessão fresca.

## Contexto mínimo
- Slug: `fracoes-minecraft-maker-e2e-20260524`
- Tema: Frações com maker Minecraft
- Ano: 2.º ano
- Duração: 45 minutos
- Repo PageCraft: `/Users/igor/dev/pagecraft`
- Repair attempt: `1`

## Fonte de verdade
Usa apenas os ficheiros listados em Inputs. Não uses conversa anterior, memória de
outras fases, nem o HTML anterior como fonte de verdade.

## Inputs permitidos
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-docspec.json`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-design-spec.json`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-builder-clarification-v1.md`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-repair-ticket-v1.json`
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524-proofread-v1.json`

## Inputs proibidos
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524.html` existente, se existir.
- Conversas, mensagens ou conclusões de Builders anteriores.
- Artefactos de fases futuras.

## Output obrigatório
- `outputs/lessons/fracoes-minecraft-maker-e2e-20260524.html`

## Tarefa
Reconstrói a página HTML de raiz a partir do DocSpec-AM, design-spec e nota de
clarificação. Não faças patch incremental ao HTML anterior. O objectivo é remover
a falha pedagógica indicada no repair ticket sem alterar a intenção do DocSpec ou
do design.

## Critério de aceitação específico
- A regra, resposta ou equivalência não aparece no enunciado inicial.
- O primeiro feedback promove observação/comparação/teste, não explicação formal.
- A explicação formal aparece apenas depois de uma ação significativa do aluno.
- A interação principal funciona e deixa evidência observável para avaliação formativa.
- O HTML é self-contained, responsivo, acessível e em pt-PT.

Se não conseguires cumprir por falta de input ou permissão, responde com
`PHASE_BLOCKED` e a razão concreta.
