# Usabilidade infantil: decisões para o protótipo

## Confirmado pelo professor

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

A branch `prototype/fracoes-visuais`, commit `f905b2b`, conserva o ensaio e as instruções em `activities/fracoes-2-minecraft/PROTOTYPE.md`. O worktree está em `/home/proteu/.t3/worktrees/pagecraft/prototype-fracoes-visuais`. O protótipo usa a rota da atividade com `?variant=A`, `B` ou `C`, mantendo as respostas em memória ao trocar de disposição.

- [A — Mesa de exploração](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=A)
- [B — Banda desenhada](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=B)
- [C — Oficina de blocos](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=C)

O servidor local de revisão está na unidade transitória `pagecraft-fracoes-prototype.service`, sem publicação externa. Para o fechar: `systemctl --user stop pagecraft-fracoes-prototype.service`. O README do protótipo explica como voltar a servi-lo.

Verificado em browser real: respostas obrigatórias, avanço mesmo com erros, pistas visuais, correção, bloqueio de saltos, declaração do trabalho externo e troca de versões. Percorridos os três passos das três versões em larguras de 1280, 768 e 390 px, sem erros JavaScript nem transbordamento horizontal.

Capturas: [A](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-A.png), [B](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-B.png), [C](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-C.png) e [telemóvel](/home/proteu/agent-browser-hub/screenshots/fracoes-prototype-mobile.png).

A escolha da disposição pelo professor continua pendente. O ensaio contém três passos representativos; a atividade completa, a diferenciação e a identificação de grupos serão tratadas na especificação posterior.
