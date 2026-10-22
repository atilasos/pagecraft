# Integração em main e qualidade da skill PageCraft

Pedido do professor em 01/10/2026: integrar todas as modificações em main e preparar o percurso de criação da próxima atividade. Base remota fixa `291371cd3a08fb571307f3d4e7f1c5a61a901f2f`. Os recortes de frações e grupos já tinham revisão e aceitação; a confirmação por toque concluiu #42 e #45.

## Percurso de criação

A fonte comum `server/pipeline/prompts/references/activity-experience.md` reúne as decisões: divisão de páginas caso a caso, pistas visuais e texto curto, todas as respostas obrigatórias antes de avançar mesmo com erros, feedback corrigível, representações verticais de frações, tipografia offline e autoria conjunta com reflexão individual. O pipeline envia esta referência às cinco fases no system prompt; os recursos distribuídos são sincronizados a partir da mesma fonte.

A skill Codex e os papéis usam caminhos de rascunho consistentes e indicam a incorporação da fonte antes da revisão. O helper real do Builder foi executado com o DocSpec de Frações e `--output drafts/fracoes-banda-desenhada-2ano.html`: gerou o destino correto, a preferência Century Gothic e as regras de respostas/pistas, sem a fonte antiga nem uma estrutura de páginas universal. O gerador legado também recebe as referências comuns. Os mínimos por idade e a preferência tipográfica chegaram ao host de atividades permanentes.

## Verificações

- `uv run --with playwright pytest -q`: 269 aprovados, 59 omitidos, em 11,85 s. Os testes automáticos de browser exigem CDP e não foram executados. Foram corrigidas duas expectativas antigas identificadas pela revisão: feedback de fração vertical e confirmação da identidade antes de entrar na atividade.
- `bash skills/sync-from-canonical.sh --check`, `git diff --check`, compilação Python e sintaxe JavaScript passaram.
- Inspeção dos prompts reais confirmou que as cinco fases recebem as regras de resposta, numerador sobre denominador, reflexão individual e divisão de páginas caso a caso.
- Browser nativo do T3 Code em HTTPS, com o host real e dados descartáveis: Didact Gothic carregada, Century Gothic em primeiro lugar, ano 2 com corpo de 22 px e alvos mínimos de 56 px. Frame real de 390 px, conteúdo de 390 px, sem transbordamento. Ano 4 com corpo de 20 px e alvos mínimos de 48 px. Os ensaios técnicos de tipografia ficaram apenas na instância temporária, separados dos rascunhos reais e da produção.
- As verificações de frações, quadro e grupos, incluindo autoria antes/depois da troca e reflexão individual, permanecem nos relatórios de cada entrega. O professor confirmou por toque escolha dos participantes, reflexão de cada criança e gravação da troca no professor.

## Standards

Dois achados P2 corrigidos: helper de criação com fontes/tamanhos antigos e host permanente sem a fonte preferida ou os mínimos infantis. Foi também clarificada a nota P3 sobre recursos próprios de Codex no CANONICAL.md. Nenhum smell material ou bloqueador identificado na revisão final.

## Spec

Dois achados P2 corrigidos: expectativas de browser desatualizadas e helper auxiliar sem as regras aprovadas, impondo estrutura fixa. A documentação deixou de tratar grupos como pendentes. Revisão final: zero requisitos pendentes ou desvios de âmbito comprovados.

A integração do código e da skill não publica automaticamente os pilotos nem reinicia o serviço de produção. A próxima atividade mantém o percurso de rascunho, revisão do professor e publicação aprovada.
