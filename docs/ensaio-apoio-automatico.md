# Ensaio do apoio automático

Verificação técnica de 22 de outubro de 2026, neste ramo. Não houve publicação, alterações aos dados da turma ou chamadas a um fornecedor real de IA.

## Comportamento

O componente comum pede ajuda após três confirmações incorretas consecutivas da mesma tarefa, com respostas ou estados diferentes entre confirmações. O plano pode escolher entre dois e cinco ou desativar com `support.automaticAfterFailures: 0`. Acertar, mudar de tarefa ou declarar outro local de trabalho reinicia a contagem. Repetir um clique na mesma resposta não cria outra tentativa. Edição, autoavaliação e ausência de cliques não disparam pedidos.

O contexto inclui `ageRange` da atividade, objetivos, descrição da interação, etapa, produto, critérios, língua, participantes, respostas incorretas observadas e pistas anteriores. Sem faixa etária declarada, regista «não indicada». Contextos extensos são abreviados e assinalados como tal para caber no contrato de acontecimentos. O pedido mantém correlação com a tentativa; uma resposta atrasada não abre um modal noutra etapa.

O modal comum cobre a janela do host, incluindo o exterior do iframe, no Studio e nas atividades permanentes. Mostra uma pista e oferece «Ouvir», «Outra pista», «Ainda estou preso», «Pedir ajuda ao professor» e «Vou experimentar», com formas para pares. A leitura só começa por escolha. O modal exige uma escolha explícita para retomar; Escape não o fecha. Não há espera imposta nem áudio automático.

`hint_acknowledged` regista a escolha no modal. Não demonstra leitura, compreensão ou utilidade. «Outra pista» conserva essa distinção; só a indicação explícita de bloqueio regista `not_helped`. A síntese mantém apresentação, utilidade declarada e revisão separadas. Uma falha do fornecedor usa as pistas revistas do guião. Texto aberto e trabalho externo não recebem um veredicto inventado.

## Reproduzir sem dados escolares

```sh
uv run python scripts/render_automatic_support_demo.py --output /tmp/pagecraft-automatic-support
python3 -m http.server 18877 --bind 127.0.0.1 --directory /tmp/pagecraft-automatic-support
```

Abrir `http://127.0.0.1:18877/`, confirmar respostas 1, 2 e 3 e observar o modal após a resposta simulada. O acerto 4 permite verificar o reinício da contagem. O exemplo é técnico, não uma atividade completa para publicação.

`/?route=studio&offline` ensaia o tratamento a pares e a contingência. O seletor muda os mesmos cenários. A página mostra os registos apenas em memória e não contém API, credenciais ou gravação. Ao fechar o servidor, termina o ensaio. Para limpar os ficheiros gerados, retirar apenas a pasta temporária criada por este comando.

## Evidência recolhida

- 315 testes Python passaram, excluindo `tests/browser`. Incluem entrada por código, trabalho a pares, APIs de feedback e síntese, com fornecedores simulados.
- 21 testes JavaScript passaram. Cobrem limiares, duplicação, acertos, tarefas, trabalho externo, contexto etário, correlação, respostas atrasadas, contingência, modal, indicações de utilidade e indisponibilidade da voz.
- Skill Codex e Claude passaram `quick_validate.py`; schema documentado, cópias da skill e artefactos gerados sem divergências.
- Browser real pelo Agent Browser Hub em `127.0.0.1:18877`: confirmações por teclado, modal no host acima do iframe, Escape, outra pista, pedido ao professor e retoma. Foram usados cenários de atividade permanente individual e Studio a pares com fornecedor indisponível, ambos simulados na página de ensaio. As APIs reais dos dois percursos foram verificadas separadamente nos testes Python.

Capturas locais:

- [Página de ensaio antes do modal](/home/proteu/agent-browser-hub/screenshots/apoio-automatico-antes.png).
- [Modal individual](/home/proteu/agent-browser-hub/screenshots/apoio-automatico-modal.png).
- [Modal a pares com pista de contingência](/home/proteu/agent-browser-hub/screenshots/apoio-automatico-pares-contingencia.png).

A pronúncia das vozes, a qualidade de um fornecedor real, tamanhos de tablet/telemóvel e a utilização pelos alunos não foram avaliados neste ensaio. O piloto em turma deve verificar se reconhecem a ajuda, se a usam para continuar com sentido e se o professor consegue preparar a aula seguinte com a síntese. Contar menos pedidos ou mais cliques no modal não demonstra esse resultado.

As fontes da skill e o pipeline foram alterados neste ramo. Não foi substituída a instalação ligada ao checkout principal nem atualizada qualquer atividade já publicada.
