# Usabilidade infantil: decisões para a atividade

## Confirmado pelo professor

- A divisão aprovada aplica-se a esta atividade. Nas restantes, rever caso a caso o número e o conteúdo das páginas, os pedidos obrigatórios e as etapas de implementação, de acordo com os objetivos e as interações. A banda desenhada e o percurso das frações não são um molde obrigatório para todas as atividades.

- Em 29/09/2026, o professor escolheu a opção **B, Banda desenhada**, depois de experimentar os exemplos remotos. Esta disposição passa a ser a referência para a atividade completa de Frações com Minecraft, do 2.º ano.

- Primeiro protótipo: Frações com Minecraft, 2.º ano. A unidade inicial da [atividade de frações](../../activities/fracoes-2-minecraft/index.html) permite explorar uma baguete dividida em partes iguais ou diferentes.
- A criança precisa de responder a todos os pedidos obrigatórios antes de avançar. O critério é uma **Página respondida**, conforme [CONTEXT.md](../../CONTEXT.md), e não acertar em todas as respostas.
- Dar feedback automático e permitir corrigir as respostas erradas.
- Reduzir explicações textuais e aumentar as pistas visuais, tornando mais claro o que fazer em cada página.

- Perante uma resposta errada, começar por uma pista visual, permitindo tentar novamente; a primeira ajuda não revela logo a solução.
- Nos pedidos realizados fora da página, a criança confirma «Já fizemos» e responde a uma pergunta curta sobre a construção. Esta confirmação é declarada pela criança, não uma verificação automática do trabalho no Minecraft.

## Trabalho relacionado ainda pendente

- Permitir identificar todos os participantes quando trabalham a pares ou em grupo num dispositivo. O campo atual «Turma» não representa os membros de um grupo.
- Depois de experimentar o protótipo, definir como aplicar as melhorias às atividades existentes e à geração de novas atividades.

## Protótipo para revisão

A branch `prototype/fracoes-visuais`, commit `58331ac`, conserva o ensaio e as instruções em `activities/fracoes-2-minecraft/PROTOTYPE.md`. O worktree está em `/home/proteu/.t3/worktrees/pagecraft/prototype-fracoes-visuais`. O protótipo usa a rota da atividade com `?variant=A`, `B` ou `C`, mantendo as respostas em memória ao trocar de disposição.

- [A — Mesa de exploração](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=A)
- [B — Banda desenhada](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=B)
- [C — Oficina de blocos](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=C)

O servidor local de revisão está na unidade transitória `pagecraft-fracoes-prototype.service`. Para o fechar: `systemctl --user stop pagecraft-fracoes-prototype.service`. O README do protótipo explica como voltar a servi-lo.

Verificado em browser real: respostas obrigatórias, avanço mesmo com erros, pistas visuais, correção, bloqueio de saltos, declaração do trabalho externo e troca de versões. Percorridos os três passos das três versões em larguras de 1280, 768 e 390 px, sem erros JavaScript nem transbordamento horizontal.

Capturas: [A](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-A.png), [B](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-B.png), [C](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-C.png) e [telemóvel](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-mobile.png).

A escolha da disposição está concluída: opção B. O ensaio contém três passos representativos; a atividade completa, a diferenciação e a identificação de grupos continuam por implementar.

## Aplicação da opção B

Usar a sequência visual do protótipo: «Imagina» apresenta a situação, «Experimenta» contém a ação da criança e «Repara» reúne a pergunta e o feedback. Manter as vinhetas lado a lado quando há espaço e pela mesma ordem vertical nos ecrãs estreitos. As instruções devem ser curtas e estar junto do objeto ou botão a que se referem.

O avanço depende de todas as respostas obrigatórias da página, mesmo com erros. O feedback começa por uma pista visual e permite corrigir. Nos passos realizados no Minecraft, pedir «Já fizemos» e uma resposta curta sobre a construção. Preservar a possibilidade de voltar às respostas.

A implementação deve conservar o percurso completo e a diferenciação da atividade existente. O protótipo na branch separada é a referência visual; a barra de comparação e o estado de diagnóstico pertencem apenas ao ensaio. A preferência do professor estabelece a direção visual; a facilidade de uso pelas crianças ainda precisa de ser observada em aula.

## Revisão remota temporária

Publicada a pedido do professor em 28/09/2026, através de um Quick Tunnel público, sem login:

- [A — Mesa de exploração](https://graham-collaboration-exemption-contacting.trycloudflare.com/?variant=A)
- [B — Banda desenhada](https://graham-collaboration-exemption-contacting.trycloudflare.com/?variant=B)
- [C — Oficina de blocos](https://graham-collaboration-exemption-contacting.trycloudflare.com/?variant=C)

A origem é `http://127.0.0.1:18779`, servindo apenas a cópia de `index.html` em `/home/proteu/.cache/pagecraft/fracoes-preview/`. O repositório, os dados do Studio e o túnel partilhado não fazem parte desta publicação. O protótipo não guarda respostas. A barra de comparação também funciona no endereço temporário.

Unidades transitórias de utilizador: `pagecraft-fracoes-preview-origin.service` e `pagecraft-fracoes-preview-tunnel.service`. O endereço depende destes processos e do computador ligados; reiniciar o Quick Tunnel pode gerar outro endereço. Não há publicação permanente nem arranque configurado após reiniciar o computador.

Para atualizar esta cópia a partir da branch do protótipo:

```sh
cp /home/proteu/.t3/worktrees/pagecraft/prototype-fracoes-visuais/activities/fracoes-2-minecraft/index.html /home/proteu/.cache/pagecraft/fracoes-preview/index.html
```

Para retirar apenas esta publicação:

```sh
systemctl --user stop pagecraft-fracoes-preview-tunnel.service
systemctl --user stop pagecraft-fracoes-preview-origin.service
```

Verificação externa: HTTPS 200 nas três variantes, conteúdo idêntico ao HTML exportado, e 404 em `/AGENTS.md`, `/.git` e `/server/data/`. No browser do Agent Browser Hub, percorridos os três passos em cada versão; confirmados bloqueio por falta de respostas, pistas e avanço com erros, confirmação obrigatória do Minecraft e conservação das respostas ao trocar de versão. Zero erros JavaScript.

## Preparação da implementação

Em 29/09/2026 ficaram preparadas a [especificação da atividade completa](fracoes-banda-desenhada-spec.md) e as [três etapas propostas](fracoes-banda-desenhada-etapas.md). O professor confirmou esta divisão para Frações com Minecraft, ressalvando a revisão caso a caso nas outras atividades. A especificação e os tickets seguem para publicação no GitHub. O código da atividade completa ainda não foi alterado.
