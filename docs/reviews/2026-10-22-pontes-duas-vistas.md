# Duas pontes iguais de cima, rascunho privado

## Âmbito e isolamento

Implementação da proposta 1 de `/tmp/pagecraft-audit-10.md`, autorizada para 3.º/4.º ano, 15 minutos, português europeu. Slug `pontes-duas-vistas`. Worktree `/home/proteu/.t3/worktrees/pagecraft/t3-4e77fc67`, branch `feat/pontes-duas-vistas`, base inicial `4c6ba90476a498a03b08fd88dea96c432ba767cd`, estado inicial limpo. A branch descritiva já existia no worktree atribuído.

O recorte só acrescenta rascunhos e provas. Não inclui registo de atividades em produção, publicação, catálogo, PR ou merge. Os cinco papéis da skill são executados por subagentes sequenciais no mesmo worktree, sem escrita concorrente das fases. O orquestrador integra e verifica.

## Antes

A atividade entregue `activities/tinkercad-pontes-3e4/index.html` conserva a configuração atual e uma anterior para desfazer. A função `outcome` depende das alturas, mas a vista superior não as representa. `renderTrial` substitui o resultado atual; não há um par de ensaios escolhidos conservado para comparação.

Confirmação no Hub, sessão própria `pagecraft-pontes-before`, perfil `temporary`, fechada após o ensaio. Servidor estático exclusivamente em loopback, porta 8837. No percurso real: apoios nas margens, tabuleiro presente, A 2/2 atravessa; mudar apenas altura direita para 1 e testar substitui o resultado pela pista das alturas. A interface não mostra os dois ensaios lado a lado.

Provas locais preservadas:

- `/tmp/pagecraft-pontes-proof/before.json`
- `/home/proteu/agent-browser-hub/screenshots/pontes-duas-vistas-before.png`

Leitura reproduzível da base: `git show 4c6ba90:activities/tinkercad-pontes-3e4/index.html`, funções `outcome`, `draw`, `renderTrial`, `changed` e `test`. A atividade existente não é alterada.

## Depois e validação

A preencher com os artefactos e resultados efetivamente executados.
