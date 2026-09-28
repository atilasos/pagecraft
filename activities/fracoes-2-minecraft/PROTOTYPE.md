# Protótipo de frações: pistas visuais e progressão

Pergunta: qual disposição ajuda uma criança do 2.º ano a perceber o que fazer e o que falta responder?

Branch `prototype/fracoes-visuais`. O HTML nesta branch é um ensaio descartável da atividade existente, com estado em memória, sem registos no Studio. O trabalho publicado permanece na branch `main`.

## Abrir

Na raiz deste worktree:

```sh
python3 -m http.server 18778 --bind 127.0.0.1
```

- [A — Mesa de exploração](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=A): material manipulável ao centro e pergunta ao lado.
- [B — Banda desenhada](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=B): vinhetas «Imagina», «Experimenta» e «Repara».
- [C — Oficina de blocos](http://127.0.0.1:18778/activities/fracoes-2-minecraft/?variant=C): percurso vertical e bancada de trabalho.

Também podes abrir `index.html` diretamente. A barra inferior permite mudar de versão sem perder as respostas. As setas do teclado fazem o mesmo fora dos campos de edição. Recarregar repõe as respostas; o URL conserva a versão. «Ver estado» mostra o estado do ensaio ao professor. A barra aparece em localhost, num ficheiro local ou nos endereços temporários `*.trycloudflare.com` usados para revisão remota. Para publicar um ensaio temporário, copiar apenas `index.html` para uma pasta isolada e servir essa pasta; nunca expor a raiz do repositório.

## Percurso e decisões aplicadas

1. Escolher um corte no pão e responder se formou duas metades.
2. Pintar blocos numa parede com oito blocos e verificar a resposta.
3. Construir no Minecraft, declarar «Já fizemos» e indicar quantos blocos foram pintados.

Todos os pedidos obrigatórios precisam de resposta. O acerto não bloqueia o avanço; um erro recebe primeiro uma pista visual e permite nova tentativa. Mudar o objeto de uma pergunta exige voltar a responder sobre esse objeto. A declaração de trabalho no Minecraft vem da criança: o protótipo não observa a construção externa.

Este recorte não substitui a atividade completa, os níveis de diferenciação, a avaliação final nem a futura identificação dos membros de um grupo. A escolha entre versões ainda depende da revisão do professor. A versão escolhida servirá de referência para implementação, não de código a publicar diretamente.

## Verificação realizada

Browser Chromium aberto pelo Agent Browser Hub; larguras de 1280, 768 e 390 px. Verificados respostas em falta, resposta errada com pista e avanço, correção, separadores bloqueados, confirmação do trabalho externo, regresso aos passos e conservação do estado ao trocar de versão. Sem erros JavaScript nem transbordamento horizontal nos três passos das três versões.
