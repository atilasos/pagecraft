# Verificação da construção e reflexão de Frações

Em 29/09/2026, o ticket #41 completa o rascunho `fracoes-banda-desenhada-2ano`: cinco explorações, construção e reflexão, em 45 minutos. A atividade publicada `fracoes-2-minecraft` permanece intacta. A revisão ainda não foi publicada para alunos.

## Comportamento verificado

- A construção apresenta exatamente 20 blocos iguais. Os exemplos 1/2, 1/4, 2/5 e 1/10 correspondem a 10, 5, 8 e 2 blocos, com grupos iguais.
- «Já fizemos» e a resposta numérica são pedidos independentes e obrigatórios. Responder com erro permite avançar e dá pista visual; mudar o material ou a fração invalida os pedidos dependentes.
- Minecraft e papel/cubos conservam os papéis de construir e conferir. A declaração não simula observação do mundo externo nem identificação dos membros do grupo.
- Na realização, a reflexão usa o anfitrião e a API existentes. O metadado `requires_completion` impede conclusão antecipada mesmo durante carregamento lento; atividades anteriores sem esse metadado conservam o comportamento anterior.
- Na página direta, a reflexão é local e facultativa, sem alegar envio ao professor. A demonstração permite explorar livremente e não envia acontecimentos de alunos.
- O desenho livre continua recuperável. A compactação de até 1000 pontos impede ultrapassar o limite da ponte e perder os registos posteriores de construção.
- Os critérios do guia, DocSpec e registo coincidem. A publicação foi ensaiada numa cópia descartável: preservou código da revisão, atividade anterior, realização e respostas anteriores. Não publicou esta revisão em produção.

## Testes e limites da evidência

Browser do Agent Browser Hub, sessão `fracoes-minecraft-41`, perfil `research`, com contextos isolados por teste. Servidores Studio e dados de integração descartáveis.

```sh
PAGECRAFT_TEST_CDP=http://127.0.0.1:9330 uv run --with playwright pytest -q
```

Resultado final: **291 testes passaram em 79,37 s**.

As páginas finais foram verificadas nos três níveis, nas larguras 390, 768 e 1280 px, com foco, alvos de toque e geometria dos grupos. As cinco explorações continuam cobertas pelos testes anteriores. O ensaio de realização percorre respostas erradas, reflexão facultativa, conclusão idempotente e exclusão dos relatórios de alunos.

A primeira suite teve 290 testes aprovados e uma falha intermitente de clique após recarregar. A repetição confirmou o trabalho restaurado, mas o browser entregou `pointerdown`, `pointerup` e `click` ao elemento iframe do pai; nenhum chegou ao botão do documento filho. A origem profunda desse encaminhamento não foi demonstrada. O teste específico de retoma passou a usar foco e Enter reais, verificando seleção e desbloqueio antes de avançar. Não usa repetição de cliques nem chama handlers artificialmente. Os restantes testes conservam interação por ponteiro. Esta alteração estabiliza a verificação de retoma; não prova a eliminação daquela falha de input automatizado.

## Revisão de código

Base fixa: `71f0d0dd05ff19d47bac2578f1e000ab73bcef20`.

### Standards

Sem achados pendentes após corrigir foco e tamanho do texto da reflexão. A sugestão anterior de reunir definições das páginas num registo continua não bloqueante; não foi introduzida uma abstração nova neste recorte.

### Spec

Sem achados pendentes após corrigir o bloqueio inicial da reflexão no anfitrião e o foco no título ao abrir a autoavaliação. A publicação para alunos e a identificação de grupos não integram esta entrega.

## Pré-visualização

- [Percurso do aluno](https://graham-collaboration-exemption-contacting.trycloudflare.com/pao/).
- [Demonstração com navegação livre](https://graham-collaboration-exemption-contacting.trycloudflare.com/pao/?presentation=1).

O HTTPS respondeu 200 e os 44201 bytes coincidiram com o HTML revisto. SHA-256: `5e6f12d34837f6df0eb23ebb619ebfa1fec7668156563c8409164676eb98d0b3`. O túnel serve a cópia isolada em `/home/proteu/.cache/pagecraft/fracoes-preview/pao/index.html`; não expõe o Studio nem os dados de alunos. A reflexão neste endereço fica apenas na página. A integração com o Studio foi ensaiada localmente em instâncias descartáveis, não implantada em produção.

Capturas inspecionadas do endereço público: `/home/proteu/agent-browser-hub/screenshots/fracoes-minecraft-final-desktop.png` (1280 px) e `/home/proteu/agent-browser-hub/screenshots/fracoes-minecraft-final-mobile.png` (390 px). As vinhetas conservam a ordem e os controlos não transbordam. No percurso público de construção, correção e reflexão não foram observados erros JavaScript. Foi também concluído o percurso público sem modo de demonstração: cinco explorações, bloqueio com pedidos em falta, avanço após declaração e resposta errada e reflexão facultativa, sem erros JavaScript. A sessão do Hub foi fechada.

A avaliação técnica e a revisão linguística acompanham o rascunho. A adequação do ritmo e das pistas à turma continua a exigir observação pelo professor.
