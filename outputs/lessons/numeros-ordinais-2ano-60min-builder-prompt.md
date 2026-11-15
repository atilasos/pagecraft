# PageCraft Builder

Gera o HTML autocontido em `outputs/lessons/numeros-ordinais-2ano-60min.html` a partir deste DocSpec. Segue o design-spec produzido pelo Designer; planeia o percurso conforme as unidades, sem impor uma estrutura fixa.

Tema: Números ordinais (até ao 20.º) em contextos do quotidiano
Idade: 7-8 anos (2.º ano)
Duração: 60 minutos
Objetivos: ["Distinguir o número que diz quantos (cardinal) do número que diz em que lugar (ordinal), em filas, prédios e corridas", "Ler e escrever os numerais ordinais do 1.º ao 20.º e associá-los ao nome por extenso (primeiro… décimo, décimo primeiro… vigésimo)", "Descobrir que a posição de uma pessoa ou de um andar depende do ponto de partida e do sentido da contagem (frente/trás da fila, de baixo para cima no prédio)", "Explicar oralmente a um colega como encontrou um lugar e formular uma pergunta com ordinais sobre a sua realidade próxima"]

## Regras do repositório
Este projeto tem regras de repo em `/home/proteu/pagecraft/AGENTS.md`. Lê-as e cumpre-as antes de implementar.

## Experiência aprovada
# Experiência da atividade PageCraft

Decisões do professor consolidadas em 01/10/2026. Esta referência é comum à skill de criação e ao pipeline do Studio. O pedido da atividade define tema, idade, duração e recursos; as regras abaixo orientam a conceção, implementação e revisão.

## Conceber cada atividade

Planear a divisão de páginas caso a caso, conforme objetivos, interações e atenção exigida. Registar no DocSpec os pedidos obrigatórios de cada etapa e como a criança lhes responde. A banda desenhada «Imagina / Experimenta / Repara» foi aprovada para Frações com Minecraft do 2.º ano; outras atividades podem usar outra organização.

A ação deve perceber-se ao olhar: mostrar o objeto, o local onde tocar ou colocar e uma pista visual junto da ação. Usar instruções curtas, uma ação principal por momento e texto adicional apenas quando ajuda a criança. Escolher representações do tema e estados visíveis de seleção, evitando longas explicações e decoração sem função. A pista apoia a descoberta sem antecipar a resposta.

## Apoio durante o trabalho

Cada atividade nova tem um plano de apoio no DocSpec, com objetivo e critérios da etapa, obstáculos previsíveis e pistas progressivas escritas para essa tarefa. Segue [apoio contextual](contextual-support.md) na conceção, implementação e revisão. Usa o componente comum para apresentar uma ação por vez junto da tarefa, ouvir por pedido, indicar utilidade, tentar outra abordagem e pedir ajuda ao professor. A edição do trabalho atualiza o contexto e invalida respostas antigas; só confirmações relevantes ou pedidos explícitos oferecem feedback. A aplicação externa, quando existir, vem do pedido da atividade.

## Respostas e avanço

Uma Página respondida tem resposta a todos os pedidos obrigatórios, mesmo com erros. O acerto não é condição para avançar. Se houver páginas sequenciais, bloquear «Seguinte» e saltos para etapas futuras enquanto faltar uma resposta; indicar junto do controlo o pedido em falta. Permitir voltar e corrigir.

Distinguir uma resposta vazia de uma confirmação intencional de uma representação vazia. Quando pintar, construir ou manipular exige confirmação, oferecer uma ação explícita para confirmar. Respostas erradas recebem feedback automático imediato, começando por uma pista visual que permite corrigir; acrescentar uma frase curta quando necessário. Manter a mesma regra de avanço por respostas após a correção.

Nos pedidos em Minecraft ou noutra aplicação externa, pedir «Já fizemos» e uma resposta curta sobre o trabalho. Registar essa construção como declaração da criança. A página não observa automaticamente a aplicação externa.

Definir o que acontece às respostas ao mudar de apoio: conservar as compatíveis, invalidar só as que deixam de corresponder ao pedido e atualizar a indicação de conclusão. Na recuperação de trabalho, restaurar respostas e etapa sem emitir novas tentativas.

## Representações e diferenciação

Mostrar Com pistas, Passo a passo e Mais desafios, sem paleta semáforo. Usar `support`, `intermediate` e `challenge` nos valores da ponte; no DocSpec o campo intermédio continua `standard`. Os apoios mudam as pistas, a complexidade e a forma de explicar; não classificam a criança.

Nas atividades de frações, apresentar numerador sobre denominador, separados por uma barra horizontal, também nas escolhas, instruções, comparações e feedback. Conservar valores internos `n/d` e rótulos acessíveis. As representações visuais devem respeitar partes iguais da mesma unidade.

Aplicar a preferência Century Gothic com alternativa Didact Gothic incorporada e os mínimos por idade definidos em [adaptação à idade](age-adaptation.md). Incorporar a fonte real antes da revisão, conforme o percurso Studio ou CLI aí descrito. Usar alvos cómodos para toque, foco visível e alternativa por teclado às manipulações.

## Trabalho conjunto e reflexão

Nas Sessões de aula, o host permite Sozinho, A pares ou Em grupo e os alunos escolhem os participantes da turma. O HTML utiliza a mesma ponte sem criar autenticação, reservar nomes ou atribuir acontecimentos a alunos. O servidor identifica a produção conjunta; só o professor altera participantes depois de começar e as respostas antigas conservam a autoria original.

A reflexão é individual, à vez, com o nome da criança visível e as respostas dos colegas preservadas. É facultativa e retoma critérios conhecidos. Usar a reflexão do host quando integrado; em modo autónomo, oferecer reflexão local sem afirmar gravação no professor. O endereço permanente ainda tem entrada individual: não prometer seleção de grupos nesse percurso.

## Evidência para revisão

O Evaluator regista os percursos e resultados reais, por apoio:

- Pedido por responder bloqueia avanço e saltos; todas as respostas, mesmo erradas, permitem continuar.
- Erro mostra pista visual; a criança consegue corrigir e voltar às respostas.
- Mudança de apoio e recuperação conservam o trabalho compatível e atualizam a conclusão.
- Tipografia, símbolos e alvos funcionam em computador, tablet e telemóvel, com toque ou teclado e sem transbordamento.
- Em Sessões de aula, grupo e reflexão individual são identificados pelo host; a demonstração do Quadro não regista tentativas de alunos.
- HTML funciona offline; registos sincronizados são confirmados pelo servidor e não presumidos pela interface.

A análise estática do pipeline do Studio é uma verificação distinta do ensaio no browser. Registar como não verificado o que não foi executado; a revisão visual e de interação deve preceder a entrega da atividade ao professor como pronta para usar.


## Adaptação à idade
# Age Adaptation — PageCraft

Guia operacional para o Architect, Designer e Builder traduzirem **faixa etária** em decisões concretas. Esta é a fonte de verdade dos mínimos por idade e da tipografia. Para conceção das etapas, respostas e reflexão, consultar `activity-experience.md`.

## Princípios

1. **Idade não é só vocabulário** — afeta tipografia, motricidade, tempo de atenção, formato de instruções e modalidade (texto/áudio/visual).
2. **Redundância de canais** — para 4–7 anos, qualquer informação importante deve estar em pelo menos dois canais (texto + ícone, texto + áudio, cor + texto).
3. **Cor nunca é semântica única** — daltonismo afeta ~8% dos rapazes; em sala de aula é certo que existe.
4. **Sem feedback punitivo** — vermelho de erro está banido. Use âmbar com mensagem do tipo "quase! tenta outra vez" e ícone ↻.

## Mínimos por faixa

| Critério | 4–5 anos (pré-escolar) | 6–7 anos (1.º/2.º ano) | 8–10 anos (3.º/4.º ano) |
|---|---|---|---|
| Corpo de texto | ≥24px | ≥22px | ≥20px |
| Título de unidade | ≥34px | ≥30px | ≥28px |
| Microcopy / rodapé | ≥18px | ≥18px | ≥16px |
| Comprimento de linha | ≤40ch | ≤50ch | ≤55ch |
| Frase típica | ≤6 palavras | ≤10 palavras | ≤14 palavras |
| Itálico em corpo | proibido | proibido | desencorajado |
| ALL CAPS em corpo | proibido | proibido | proibido |
| Tap target | ≥64px | ≥56px | ≥48px |
| Slider thumb | n/a (use tap-cycle) | ≥48px com snapping | ≥40px |
| Decisões por ecrã | 1 | 1–2 | 2–3 |
| Vocabulário | concreto, próximo | concreto | concreto + jargão pontual com gloss |
| Instruções | áudio + ícone redundantes | ícone redundante ao texto | texto |
| Tempo por atividade | 3–5 min | 5–8 min | 8–12 min |

## Padrões recomendados por idade

| Pattern | 4–5 | 6–7 | 8–10 |
|---|---|---|---|
| `tap-to-cycle` | ✅ ideal | ✅ ideal | ⚠️ só se simplifica |
| `tap-to-place` | ✅ ideal | ✅ ideal | ✅ ok |
| `audio-first` | ✅ obrigatório | ✅ ideal | ⚠️ opcional |
| `toggle` | ✅ | ✅ | ✅ |
| `dropdown` | ⚠️ evitar | ⚠️ se botão grande | ✅ |
| `slider` | ⚠️ só com snap a 2–3 valores | ✅ com snap | ✅ contínuo |
| `drag` | ❌ frustrante | ⚠️ tentar `tap-to-place` antes | ✅ |
| `sorting` (drag) | ❌ | ⚠️ | ✅ |
| `matching` (linhas) | ❌ | ⚠️ | ✅ |
| `quiz-inline` | ✅ com áudio | ✅ | ✅ |
| `canvas-draw` | ✅ livre | ✅ guiado | ✅ guiado |
| `quiz` com texto longo | ❌ | ⚠️ | ✅ |

## Tipografia

Preferência confirmada pelo professor: `"Century Gothic", "Didact Gothic", "URW Gothic", "Avant Garde", sans-serif`, em texto, títulos e controlos. Century Gothic é usada quando está instalada no dispositivo que abre a página.

Para dispositivos sem Century Gothic, o pipeline do Studio incorpora automaticamente a Didact Gothic e a licença OFL no HTML antes de o enviar ao Proofreader e ao Evaluator, em cada ronda de construção ou reparação. O Builder deve usar a família acima no CSS e não deve inventar data URLs nem tentar ler ficheiros de fontes: a incorporação é responsabilidade do servidor. O artefacto final inclui o WOFF2 real, sem ligações externas ou dependências de rede.

Fora do pipeline do Studio, depois de guardar ou reparar o rascunho e antes da revisão, executar no repositório PageCraft `python3 scripts/embed_gothic_font.py --activity drafts/<slug>.html`. Este comando incorpora a mesma fonte e licença; pode ser repetido sem duplicar o bloco.

## Cor

- Usar **OKLCH**, com chroma reduzido perto dos extremos de lightness.
- **Identidade**: 4–5 *hues*. **Funcional**: `ok` (verde 150°), `warn` (âmbar 85°), `focus` (azul 255°).
- **Proibido**: usar `verde/amarelo/vermelho` como níveis de dificuldade — colide com feedback de acerto/erro e ativa carga emocional de "errado". Use três *hues* distintos sem semântica de semáforo (template usa Com pistas / Passo a passo / Mais desafios).

## Movimento

- Respeitar `prefers-reduced-motion`.
- *Easing* `ease-out`, **sem** bounce/elastic.
- Animações de feedback ≤200ms; transições de estado ≤300ms.
- Nunca animar propriedades de *layout* (`width`, `height`, `top`, `left`) — usar `transform` e `opacity`.

## Som

- **Sempre opt-in**: a página começa muda; um botão 🔊 visível liga o áudio.
- **Nunca** o som é o único portador de significado.
- Tons curtos (~120 ms, volume ≤0.05) para confirmação; síntese de voz em `pt-PT` para narração.

## Comunicação com o aluno

- Tratamento por **tu**.
- Microcopy de erro **convida a tentar de novo** e nunca culpa. Ex.: *"Quase! Que tal experimentar outra peça?"* — nunca *"Errado"*.
- Microcopy de acerto **celebra a descoberta**, não o desempenho. Ex.: *"Encontraste! Já sabes que…"* — preferir descrever o que se descobriu a só *"Correto!"*.
- Em ações destrutivas (reiniciar/limpar), pedir confirmação curta e visual.


## Apoio contextual da atividade
# Apoio contextual nas atividades geradas

Aplica a cada atividade nova, em qualquer área. O pedido do professor define tema, objetivos, etapas, produtos e recursos. Os exemplos de software, Matemática ou escrita não impõem um formato ou um banco de pistas às restantes atividades.

## Architect: escrever o plano da atividade

Acrescenta `support.version` ao DocSpec e `support` a cada unidade. Usa o schema JSON canónico em `server/pipeline/schemas/docspec.schema.json`.

- Em `support`, indica uma versão do conteúdo e as línguas pedidas. `automaticAfterFailures` usa três tentativas por defeito, aceita limiares de dois a cinco ou `0` para desativar. A faixa etária vem de `ageRange`, sem inferir características pessoais. Inclui `externalWork` apenas quando o trabalho decorrer também fora do PageCraft; o valor é o nome dessa aplicação ou contexto.
- Em cada unidade, define `objective`, `criteria` relevantes e `obstacles` previsíveis para aquela tarefa. Escolhe categorias reconhecíveis pelas crianças, próprias do tema e do que estão a fazer.
- Cada obstáculo tem um `id`, `label` por língua e duas ou três pistas progressivas. A primeira indica uma ação curta. A seguinte propõe outra abordagem, comparação ou pergunta que ajude a distinguir a causa. Cada pista tem `id` e `text.pt.individual`/`text.pt.group`; quando houver inglês, acrescenta os mesmos modos em `text.en`.
- Escreve as duas formas de tratamento; não confies numa troca automática de verbos. Uma pista mostra um próximo passo sem entregar a solução. A revisão docente da atividade inclui estas pistas.

Exemplo parcial para uma atividade de escrita:

```json
{
  "ageRange": "8-9 anos",
  "support": {"version": "convite-v1", "languages": ["pt"], "automaticAfterFailures": 3},
  "units": [{
    "summary": "Rever o convite",
    "support": {
      "objective": "Rever se o destinatário sabe onde acontece o encontro.",
      "criteria": ["Inclui a informação de que o destinatário precisa."],
      "obstacles": [{
        "id": "rever", "label": {"pt": "Perceber o que falta ao convite"},
        "hints": [
          {"id": "local", "text": {"pt": {
            "individual": "Sublinha a indicação do local. O destinatário sabe onde ir?",
            "group": "Sublinhem a indicação do local. O destinatário sabe onde ir?"
          }}},
          {"id": "destinatario", "text": {"pt": {
            "individual": "Lê o convite como se o recebesses. Que pergunta ainda terias de fazer?",
            "group": "Leiam o convite como se o recebessem. Que pergunta ainda teriam de fazer?"
          }}}
        ]
      }]
    }
  }]
}
```

O exemplo omite os outros campos obrigatórios do DocSpec e SRTC-A. As atividades arquivadas sem plano mantêm o contrato anterior; as atividades novas têm plano próprio.

## Builder: ligar o trabalho ao componente comum

Coloca `<aside data-pagecraft-support="u1"></aside>` junto da tarefa da unidade. Usa a mesma convenção `uN` do DocSpec e da ponte. O componente incorpora as pistas do plano, apresenta uma ação por vez e oferece leitura opcional, outra pista, indicação de utilidade, esclarecimento por IA e pedido ao professor. O botão de trabalho externo só existe quando o plano o declara.

Em cada mudança de etapa, resposta, manipulação relevante, produto ou nível, atualiza o contexto local. Faz esta atualização também durante a edição para invalidar uma resposta antiga; isso não pede feedback ao modelo:

```js
if (window.PageCraftSupport) PageCraftSupport.update({
  unit_id: currentUnitId,
  question: currentTask,
  answer: recentAttempt,
  product: chosenProduct || '',
  level: currentLevel,
  revision: attemptRevision
});
```

`revision` muda quando a tentativa muda. Se a interação tem um estado composto, pode transmitir `attempt` com os valores relevantes. Uma resposta só pode ser mostrada enquanto o contexto do pedido continua atual. O template sinaliza confirmações da ponte ao componente; as transições próprias da atividade continuam a precisar desta atualização explícita.

O `PageCraftSupport` pode ainda não existir durante a execução inicial do script. Atualiza o contexto ao receber `document` → `pagecraft-support-ready` e depois de cada transição. Não reimplementes a fila, a leitura ou o progresso das pistas em cada HTML. Ao substituir o DOM de uma etapa, conserva o atributo do painel; o componente volta a ligá-lo.

Para associar uma revisão a uma pista, conserva `PageCraftSupport.currentHintId()` antes de alterar a resposta e envia-o em `assessment_result.payload.detail.after_hint_id`. Uma alteração declarada sobre trabalho externo usa `detail.external_change: true`; continua a ser uma declaração. Nas sessões em grupo, os campos conjuntos usam `detail.activity` igual ao slug e `detail.field` estável, conforme o contrato do host.

O pedido ao modelo é explícito ou automático após respostas incorretas consecutivas e distintas na mesma tarefa. Atualiza o contexto antes de confirmar uma tentativa. Mantém `task_id` e `question` estáveis para esse pedido; muda-os quando começa outra questão:

```js
PageCraftBridge.attempt(currentUnitId, correct, {
  value: recentAnswer,
  question: currentQuestion,
  task_id: currentQuestionId
});
```

Emite `attempt` apenas depois de confirmar uma resposta relevante com um critério verificável. `correct` é um booleano. Campos vazios, autoavaliação, texto aberto sem critério e declarações de conclusão externa não recebem um veredicto inventado. `detail` pode ter `value`, `question` e `task_id`; uma mensagem de feedback em `detail` nunca é a resposta da criança. Atividades com integração própria podem usar `PageCraftSupport.recordAttempt({unit_id, correct, answer, question, task_id, attempt_id})`; escolhe uma via por confirmação, para evitar duplicação.

O componente conta respostas diferentes, reinicia após acerto ou mudança de tarefa e mantém um intervalo de novas tentativas antes de outro pedido automático. O limiar não bloqueia o avanço. Não o dispares por tecla, por perda de foco ou por tempo sem cliques. As pistas locais continuam disponíveis sem modelo. Não acrescentes um recetor genérico que apresente `ai_feedback` sem conferir `request_id` e contexto; o componente comum faz essa verificação.

O pedido automático inclui faixa etária, características da atividade, etapa, critérios, tentativas incorretas observadas e pistas anteriores. Quando a resposta chega para o contexto ainda atual, o componente apresenta uma única ação num modal de ecrã inteiro. O host cobre também os controlos exteriores ao iframe. Não implementes outro modal no Builder. A leitura só começa ao escolher «Ouvir». A criança escolhe «Vou experimentar», «Outra pista», «Ainda estou preso» ou «Pedir ajuda ao professor» para prosseguir. Pedir outra pista não declara que a anterior foi inútil; apenas «Ainda estou preso» regista essa indicação. O fecho regista `hint_acknowledged`; não comprova leitura, compreensão ou utilidade. Uma falha do fornecedor usa a próxima pista revista do guião. Sem ligação ao host, a página autónoma mantém pistas locais e o mesmo modal, sem afirmar uma chamada à IA.

Antes do Proofreader e Evaluator, incorpora o plano e o código comum no HTML:

```sh
python3 scripts/embed_activity_support.py --activity drafts/<slug>.html --docspec drafts/<slug>-docspec.json
python3 scripts/embed_gothic_font.py --activity drafts/<slug>.html
```

Repete após reparações. O pipeline Studio faz a incorporação automaticamente antes da revisão. O HTML final mantém CSS/JS inline, sem rede nem credenciais; pedidos e resultados passam pelo host.

## Evaluator: verificar o apoio próprio da atividade

Verifica pelo menos um obstáculo de cada unidade: primeira pista visível junto da tarefa; outra abordagem após «não ajudou»; encaminhamento ao professor; leitura só ao carregar. Confirma a ligação entre pistas e critérios do DocSpec, incluindo as duas formas de tratamento e as línguas pedidas.

Confirma tentativas diferentes até ao limiar nos dois percursos com código. Confirma o reinício após acerto ou mudança de questão e que cliques repetidos na mesma resposta não contam como novas tentativas. Verifica modal em todo o ecrã, foco no seu interior, retoma explícita, outra pista, professor e ausência de áudio automático.

Muda a resposta, etapa e produto enquanto um pedido demora. A resposta anterior deve ser ignorada. Confirma também trabalho externo declarado, retorno ao guião e registos na realização ou sessão. Distingue pista apresentada, utilidade declarada e revisão observada. O PageCraft não valida um produto noutra aplicação a partir de uma declaração. Preserva a autoria do grupo e a reflexão de cada participante.

O resumo posterior deriva dos mesmos registos de qualquer atividade e liga as conclusões às fontes. Propostas de melhoria ficam para revisão antes de mudar uma versão usada na turma. Regista como não verificado o que depender de um fornecedor ou browser que não tenha sido exercitado.


## Ao alterar o componente comum

Executa `uv run pytest tests/test_activity_support.py` e `node --test tests/js/activity_support.test.cjs`. Os exemplos em `tests/fixtures/support-examples.json` verificam planos distintos de Matemática, escrita e Scratch, não a qualidade de aulas completas.

Para inspecionar o componente num browser, gera HTML autocontido com `uv run python scripts/render_support_examples.py --output /tmp/pagecraft-support-examples`. Estes ficheiros de ensaio não publicam atividades nem contactam IA. A avaliação de uma atividade gerada continua a exigir o seu próprio percurso, contexto e fontes.

Para ensaiar a intervenção automática no host, usa `uv run python scripts/render_automatic_support_demo.py --output /tmp/pagecraft-automatic-support` e serve essa pasta apenas em localhost. O cenário simula respostas do fornecedor e falhas; não guarda dados. O procedimento e a evidência estão em `docs/ensaio-apoio-automatico.md`.


```json
{
  "support": {
    "version": "numeros-ordinais-2ano-v1",
    "languages": [
      "pt"
    ],
    "automaticAfterFailures": 3
  },
  "units": [
    {
      "objective": "Distinguir perguntas que pedem uma quantidade de perguntas que pedem um lugar na fila.",
      "criteria": [
        "Escolhe um número para as perguntas «quantos?» e um ordinal para as perguntas «em que lugar?».",
        "Conta a partir da porta da cantina quando procura um lugar."
      ],
      "obstacles": [
        {
          "id": "quantos-ou-lugar",
          "label": {
            "pt": "Não sei se a pergunta pede quantos ou o lugar"
          },
          "hints": [
            {
              "id": "palavra-chave",
              "text": {
                "pt": {
                  "individual": "Lê só o começo da pergunta. Começa por «Quantos» ou por «Em que lugar»?",
                  "group": "Leiam só o começo da pergunta. Começa por «Quantos» ou por «Em que lugar»?"
                }
              }
            },
            {
              "id": "olhar-icone",
              "text": {
                "pt": {
                  "individual": "Olha para o ícone ao lado da pergunta. É a mão a contar ou a bandeira de lugar?",
                  "group": "Olhem para o ícone ao lado da pergunta. É a mão a contar ou a bandeira de lugar?"
                }
              }
            },
            {
              "id": "dizer-resposta",
              "text": {
                "pt": {
                  "individual": "Diz a resposta em voz baixa numa frase: «Estão … crianças» ou «Está em … lugar». Qual soa bem?",
                  "group": "Digam a resposta numa frase: «Estão … crianças» ou «Está em … lugar». Qual soa bem?"
                }
              }
            }
          ]
        },
        {
          "id": "a-frente-de",
          "label": {
            "pt": "Conto mal as crianças à frente de alguém"
          },
          "hints": [
            {
              "id": "tapar-crianca",
              "text": {
                "pt": {
                  "individual": "Toca na Rita. Agora conta só as crianças entre a porta e ela. Contaste a Rita?",
                  "group": "Toquem na Rita. Contem só as crianças entre a porta e ela. Contaram a Rita?"
                }
              }
            },
            {
              "id": "fila-real",
              "text": {
                "pt": {
                  "individual": "Pensa na fila da sala. Quem estava à frente da Inês? A Inês estava à frente dela própria?",
                  "group": "Lembrem-se da fila da sala. Quem estava à frente da Inês? Ela estava à frente dela própria?"
                }
              }
            }
          ]
        }
      ]
    },
    {
      "objective": "Colocar os ordinais do 1.º ao 10.º na fila, contando a partir da porta, e ligá-los ao nome por extenso.",
      "criteria": [
        "Começa a contar na criança junto à porta.",
        "Conta a própria criança quando procura o seu lugar.",
        "Liga cada numeral ao nome que diz o mesmo lugar."
      ],
      "obstacles": [
        {
          "id": "onde-comecar",
          "label": {
            "pt": "Não sei por onde começar a contar"
          },
          "hints": [
            {
              "id": "porta",
              "text": {
                "pt": {
                  "individual": "Procura a porta da cantina. Quem vai entrar primeiro?",
                  "group": "Procurem a porta da cantina. Quem vai entrar primeiro?"
                }
              }
            },
            {
              "id": "pegadas",
              "text": {
                "pt": {
                  "individual": "Põe o dedo na criança junto à porta e anda uma criança de cada vez, a dizer os lugares.",
                  "group": "Um de vocês põe o dedo junto à porta e avança uma criança de cada vez; o outro diz os lugares."
                }
              }
            }
          ]
        },
        {
          "id": "salto-na-contagem",
          "label": {
            "pt": "O cartão ficou num lugar ao lado"
          },
          "hints": [
            {
              "id": "contar-de-novo",
              "text": {
                "pt": {
                  "individual": "Volta à porta e conta devagar, tocando em cada criança. Saltaste alguma?",
                  "group": "Voltem à porta e contem devagar, tocando em cada criança. Saltaram alguma?"
                }
              }
            },
            {
              "id": "vizinhos",
              "text": {
                "pt": {
                  "individual": "Olha para os cartões dos vizinhos. Que lugar vem antes e qual vem depois deste?",
                  "group": "Olhem para os cartões dos vizinhos. Que lugar vem antes e qual vem depois deste?"
                }
              }
            }
          ]
        },
        {
          "id": "nome-por-extenso",
          "label": {
            "pt": "Não sei ler o nome do lugar"
          },
          "hints": [
            {
              "id": "ouvir-nome",
              "text": {
                "pt": {
                  "individual": "Carrega em 🔊 no cartão do nome e ouve-o. Já disseste este nome numa fila?",
                  "group": "Carreguem em 🔊 no cartão do nome e ouçam-no. Já disseram este nome numa fila?"
                }
              }
            },
            {
              "id": "recitar",
              "text": {
                "pt": {
                  "individual": "Diz os lugares em voz alta desde «primeiro». Em que dedo chegas a este nome?",
                  "group": "Digam os lugares em coro desde «primeiro». Em que dedo chegam a este nome?"
                }
              }
            }
          ]
        }
      ]
    },
    {
      "objective": "Construir e ler os nomes dos lugares do 11.º ao 20.º e escrever o seu numeral.",
      "criteria": [
        "Usa a peça «décimo» para os lugares do 11.º ao 19.º.",
        "Escolhe a segunda peça pelos passageiros que estão depois do 10.º.",
        "Escreve o numeral com o sinal «.º»."
      ],
      "obstacles": [
        {
          "id": "segunda-peca",
          "label": {
            "pt": "Não sei que peça vai na segunda casa"
          },
          "hints": [
            {
              "id": "depois-do-decimo",
              "text": {
                "pt": {
                  "individual": "Toca no passageiro que tem o cartão 10.º. Quantos passageiros há depois dele até ao que pisca?",
                  "group": "Toquem no passageiro com o cartão 10.º. Quantos passageiros há depois dele até ao que pisca?"
                }
              }
            },
            {
              "id": "nome-da-primeira-fila",
              "text": {
                "pt": {
                  "individual": "Na primeira fila, que nome tinha o passageiro nesse lugar? Procura-o nos cartões esbatidos.",
                  "group": "Na primeira fila, que nome tinha o passageiro nesse lugar? Procurem-no nos cartões esbatidos."
                }
              }
            }
          ]
        },
        {
          "id": "vigesimo",
          "label": {
            "pt": "O último passageiro não encaixa"
          },
          "hints": [
            {
              "id": "contar-grupos",
              "text": {
                "pt": {
                  "individual": "Conta quantos grupos de 10 passageiros vês até ao último. Uma peça chega?",
                  "group": "Contem quantos grupos de 10 passageiros há até ao último. Uma peça chega?"
                }
              }
            },
            {
              "id": "procurar-peca-nova",
              "text": {
                "pt": {
                  "individual": "Há uma peça que ainda não usaste. Experimenta-a sozinha numa casa.",
                  "group": "Há uma peça que ainda não usaram. Experimentem-na sozinha numa casa."
                }
              }
            }
          ]
        },
        {
          "id": "esquecer-sinal",
          "label": {
            "pt": "O meu numeral parece um número normal"
          },
          "hints": [
            {
              "id": "comparar-cartoes",
              "text": {
                "pt": {
                  "individual": "Compara o que escreveste com os cartões da fila. O que têm os cartões a mais?",
                  "group": "Comparem o que escreveram com os cartões da fila. O que têm os cartões a mais?"
                }
              }
            },
            {
              "id": "quantos-lugar",
              "text": {
                "pt": {
                  "individual": "Lembra-te da cantina: um número dizia quantos, o outro dizia o lugar. Qual queres aqui?",
                  "group": "Lembrem-se da cantina: um número dizia quantos, o outro dizia o lugar. Qual querem aqui?"
                }
              }
            }
          ]
        }
      ]
    },
    {
      "objective": "Indicar o lugar de uma criança a partir de cada porta e explicar porque é que o lugar muda.",
      "criteria": [
        "Começa a contar na criança junto à porta aberta.",
        "Explica que a criança ficou no mesmo sítio e que mudou o ponto de partida."
      ],
      "obstacles": [
        {
          "id": "porta-errada",
          "label": {
            "pt": "Continuo a contar pela porta da frente"
          },
          "hints": [
            {
              "id": "seta-aberta",
              "text": {
                "pt": {
                  "individual": "Procura a seta «entra-se aqui». Qual é a criança que entra primeiro agora?",
                  "group": "Procurem a seta «entra-se aqui». Qual é a criança que entra primeiro agora?"
                }
              }
            },
            {
              "id": "dramatizar",
              "text": {
                "pt": {
                  "individual": "Imagina que és o motorista à porta de trás. Que criança cumprimentas primeiro?",
                  "group": "Um de vocês faz de motorista à porta de trás. Que criança cumprimenta primeiro?"
                }
              }
            }
          ]
        },
        {
          "id": "lugar-igual",
          "label": {
            "pt": "Acho que o lugar devia ser o mesmo"
          },
          "hints": [
            {
              "id": "comparar-cartoes",
              "text": {
                "pt": {
                  "individual": "Olha para os dois espaços por baixo do Tomás. De que porta veio cada contagem?",
                  "group": "Olhem para os dois espaços por baixo do Tomás. De que porta veio cada contagem?"
                }
              }
            },
            {
              "id": "fila-real",
              "text": {
                "pt": {
                  "individual": "Lembra-te da fila na sala. Se o professor fosse para o fim, quem seria o primeiro?",
                  "group": "Lembrem-se da fila na sala. Se o professor fosse para o fim, quem seria o primeiro?"
                }
              }
            }
          ]
        }
      ]
    },
    {
      "objective": "Entregar cartas no andar pedido, contando de baixo para cima a partir do rés-do-chão.",
      "criteria": [
        "Começa a contar os andares acima do rés-do-chão.",
        "Lê o andar escrito com numeral ou por extenso."
      ],
      "obstacles": [
        {
          "id": "contar-rc",
          "label": {
            "pt": "A carta ficou um andar abaixo"
          },
          "hints": [
            {
              "id": "olhar-painel",
              "text": {
                "pt": {
                  "individual": "Olha para o painel do elevador. Que botão está antes do 1?",
                  "group": "Olhem para o painel do elevador. Que botão está antes do 1?"
                }
              }
            },
            {
              "id": "porta-entrada",
              "text": {
                "pt": {
                  "individual": "Entra pela porta do prédio. Já subiste algum andar? Começa a contar quando subires.",
                  "group": "Imaginem que entram pela porta do prédio. Já subiram algum andar? Contem quando subirem."
                }
              }
            },
            {
              "id": "casa-real",
              "text": {
                "pt": {
                  "individual": "Pensa num prédio que conheças. Onde fica a porta da rua: no rés-do-chão ou no 1.º andar?",
                  "group": "Pensem num prédio que conheçam. Onde fica a porta da rua: no rés-do-chão ou no 1.º andar?"
                }
              }
            }
          ]
        },
        {
          "id": "sentido-contagem",
          "label": {
            "pt": "Contei os andares a partir do telhado"
          },
          "hints": [
            {
              "id": "elevador-sobe",
              "text": {
                "pt": {
                  "individual": "Toca no R/C e vê para onde o elevador vai quando sobe um andar.",
                  "group": "Toquem no R/C e vejam para onde vai o elevador quando sobe um andar."
                }
              }
            },
            {
              "id": "comparar-fila",
              "text": {
                "pt": {
                  "individual": "Na fila contavas a partir da porta. No prédio, onde está a porta da rua?",
                  "group": "Na fila contavam a partir da porta. No prédio, onde está a porta da rua?"
                }
              }
            }
          ]
        }
      ]
    },
    {
      "objective": "Mostrar o que já sei sobre ordinais em várias situações e criar com o par uma pergunta com um lugar e um ponto de partida.",
      "criteria": [
        "Lê e escreve ordinais até ao 20.º, com numeral ou por extenso.",
        "Responde com um lugar quando a pergunta pede um lugar.",
        "A pergunta do par diz de onde se começa a contar."
      ],
      "obstacles": [
        {
          "id": "trocar-representacao",
          "label": {
            "pt": "Não consigo passar do nome para o numeral"
          },
          "hints": [
            {
              "id": "partir-nome",
              "text": {
                "pt": {
                  "individual": "Divide o nome em duas partes. O que diz a primeira parte? E a segunda?",
                  "group": "Dividam o nome em duas partes. O que diz a primeira parte? E a segunda?"
                }
              }
            },
            {
              "id": "lembrar-autocarro",
              "text": {
                "pt": {
                  "individual": "Lembra-te da fila do autocarro: os primeiros 10 e mais alguns. Quantos a mais?",
                  "group": "Lembrem-se da fila do autocarro: os primeiros 10 e mais alguns. Quantos a mais?"
                }
              }
            }
          ]
        },
        {
          "id": "pergunta-sem-partida",
          "label": {
            "pt": "A nossa pergunta tem mais do que uma resposta"
          },
          "hints": [
            {
              "id": "testar-colega",
              "text": {
                "pt": {
                  "individual": "Lê a tua pergunta a um colega. Ele sabe por onde começar a contar?",
                  "group": "Leiam a vossa pergunta a outro par. Eles sabem por onde começar a contar?"
                }
              }
            },
            {
              "id": "porta-ou-chao",
              "text": {
                "pt": {
                  "individual": "Pensa onde está a porta, a meta ou o rés-do-chão no teu exemplo. Escreve isso no fim.",
                  "group": "Pensem onde está a porta, a meta ou o rés-do-chão no vosso exemplo. Escrevam isso no fim."
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## Unidades SRTC-A

## Unit 1: Quantos? ou Em que lugar? — o mesmo número pode dizer uma quantidade ou uma posição. (8 min)

### Texto
Ativação. O professor chama cinco crianças para formarem uma fila real à porta da sala e pergunta «Quantos estão na fila?» e «Em que lugar está a Inês?», recolhendo as respostas sem as corrigir (3 min). Na página, uma fila de 8 crianças espera à porta da cantina; a porta, à esquerda, marca a frente da fila com uma seta. Surgem 6 perguntas curtas, uma de cada vez, cada uma com um ícone (mão a contar para «quantos?», bandeira de lugar para «em que lugar?»). O aluno responde escolhendo entre dois cartões, por exemplo «8» e «8.º». O aluno deve perceber, pela própria resposta, que «quantos?» pede uma quantidade e «em que lugar?» pede uma posição, e que estar em 4.º lugar não é o mesmo que ter 4 crianças à frente.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "perguntaAtual",
    "type": "derived",
    "derivedFrom": "índice 0-5 sobre a lista fixa de perguntas: quantas crianças na fila (8); em que lugar está o menino de boné (3.º); quantas crianças de mochila (2); em que lugar está a Rita (4.º); quantas crianças estão à frente da Rita (3); em que lugar está a última criança (8.º)"
  },
  {
    "name": "resposta",
    "type": "quiz",
    "options": [
      "cartão com número (ex.: 3)",
      "cartão com ordinal (ex.: 3.º)"
    ],
    "default": null
  },
  {
    "name": "tipoPergunta",
    "type": "derived",
    "derivedFrom": "perguntaAtual.tipo ∈ {'quantos', 'lugar'}"
  }
]
```

**Render:** Fila horizontal de 8 crianças ilustradas, cada uma com um traço visual distinto (boné, mochila, laço…), à porta da cantina; a porta e uma seta «frente» à esquerda. Por cima, a pergunta numa frase de até 10 palavras, com ícone redundante. Dois cartões grandes (≥56px) lado a lado, com o número e o ordinal escritos em tamanho grande (o «.º» bem visível). Ao tocar numa criança, esta fica com contorno de seleção, sem revelar a posição. Botão 🔊 opcional lê a pergunta em pt-PT. Navegação por teclado: Tab entre cartões, Enter confirma.

**Transition:** Tocar num cartão confirma a resposta. Acerto: a fila mostra a evidência da descoberta (para «quantos?», cada criança recebe um ponto e o total aparece; para «em que lugar?», a contagem ilumina-se a partir da porta até à criança) e a frase «Encontraste! Contaste até à Rita.». Erro: contorno âmbar e ícone ↻ no cartão, a fila mostra a pista visual correspondente ao tipo de pergunta, sem dizer qual é o cartão certo, e o aluno pode tentar outra vez. A pergunta seguinte fica disponível depois de qualquer resposta.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: a pergunta «quantos?» responde-se com um número que diz a quantidade de um conjunto; a pergunta «em que lugar?» responde-se com um ordinal que diz a posição de um elemento numa ordem. O último lugar tem o mesmo número do total, mas a criança em 4.º lugar tem só 3 crianças à frente.

**Assessment (observável):** O aluno escolhe o cartão adequado em pelo menos 5 das 6 perguntas, incluindo a pergunta «quantas crianças estão à frente da Rita?» (3 e não 4.º), e, quando o professor pergunta «8 e 8.º dizem a mesma coisa?», responde com uma frase do tipo «8 diz quantos são; 8.º diz o lugar».

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** Fila de 5 crianças e 4 perguntas sem a pergunta «à frente de»; a criança referida na pergunta pisca levemente; o aluno pode usar os cartões físicos e contar com o dedo no ecrã, com leitura áudio opcional.
- **Passo a passo — Intermédio:** Fila de 8 crianças e as 6 perguntas, incluindo «quantas crianças estão à frente da Rita?».
- **Mais desafios — Desafio:** Fila de 12 crianças e 8 perguntas, com duas perguntas inversas («Se a Rita é a 7.ª, quantas crianças estão à frente dela?» e «Quantas estão atrás?»); no fim, o aluno inventa oralmente uma pergunta «quantos?» e outra «em que lugar?» para o colega.

## Unit 2: A fila da cantina: cada lugar, do 1.º ao 10.º, tem um numeral e um nome. (11 min)

### Texto
As crianças chegam à cantina uma a uma (animação curta). O aluno coloca um cartão de lugar (1.º a 10.º) em cada criança da fila, usando tocar no cartão e depois tocar na criança. Depois liga cada numeral ao seu nome por extenso (primeiro, segundo, terceiro, quarto, quinto, sexto, sétimo, oitavo, nono, décimo). Por fim, a cozinheira pede «Dá o tabuleiro azul ao sétimo» e o aluno toca na criança certa. O aluno deve descobrir que a contagem começa na porta, que a própria criança conta quando se encontra o seu lugar e que «7.º» e «sétimo» são duas formas de escrever o mesmo lugar.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "cartoesColocados",
    "type": "matching",
    "options": [
      "1.º",
      "2.º",
      "3.º",
      "4.º",
      "5.º",
      "6.º",
      "7.º",
      "8.º",
      "9.º",
      "10.º"
    ],
    "default": null
  },
  {
    "name": "paresNomeNumeral",
    "type": "matching",
    "options": [
      "primeiro",
      "segundo",
      "terceiro",
      "quarto",
      "quinto",
      "sexto",
      "sétimo",
      "oitavo",
      "nono",
      "décimo"
    ],
    "default": null
  },
  {
    "name": "pedidoTabuleiro",
    "type": "quiz",
    "options": [
      "sétimo",
      "quarto",
      "décimo"
    ],
    "default": "sétimo"
  },
  {
    "name": "cartoesCorretos",
    "type": "derived",
    "derivedFrom": "contagem de cartões cuja posição = índice da criança a partir da porta (1 = junto à porta)"
  }
]
```

**Render:** Página em três passos, um por ecrã. Passo 1: fila horizontal de 10 crianças junto à porta da cantina (à esquerda, com seta «frente»); por baixo, os cartões 1.º–10.º baralhados em botões grandes. Passo 2: duas colunas de cartões grandes — numerais à esquerda, nomes à direita; o par ligado fica com a mesma cor de fundo e um ícone de ligação (não depende só da cor). Passo 3: a cozinheira com balão curto («Dá o tabuleiro azul ao sétimo») e a fila com os cartões já colocados escondidos, para obrigar a contar. Painel de apoio contextual junto da tarefa. Alternativa por teclado: setas escolhem cartão/criança, Enter coloca.

**Transition:** Tocar num cartão seleciona-o (contorno de foco); tocar numa criança coloca-o por cima dela. Um cartão no lugar errado fica com contorno âmbar e a pista visual mostra passos numerados a partir da porta até essa criança, sem colocar o cartão certo; o aluno pode retirar e recolocar. No passo 2, um par errado desfaz-se suavemente e as duas peças ficam disponíveis. No passo 3, tocar na criança entrega o tabuleiro; se for outra criança, os pés da fila acendem-se a partir da porta como pista. «Seguinte» só fica ativo quando todos os pedidos do passo têm resposta, mesmo com erros.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: numa fila, o lugar de cada pessoa obtém-se contando a partir da frente e incluindo a própria pessoa; cada lugar tem um só ordinal e cada ordinal corresponde a um só lugar; o numeral (7.º) e o nome por extenso (sétimo) representam o mesmo lugar.

**Assessment (observável):** O aluno coloca corretamente pelo menos 8 dos 10 cartões, liga pelo menos 8 dos 10 pares numeral–nome e entrega pelo menos 2 dos 3 tabuleiros à criança certa; ao entregar um tabuleiro, aponta para a porta e conta em voz alta «primeiro, segundo, …» até à criança.

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** Fila de 5 crianças (1.º a 5.º); os cartões aparecem por ordem, um de cada vez; pegadas pontilhadas no chão (1 ponto, 2 pontos…) a partir da porta; os nomes por extenso têm leitura áudio opcional; cartões físicos ao lado do computador.
- **Passo a passo — Intermédio:** Fila de 10 crianças com cartões baralhados; ligação dos 10 numerais aos nomes; 3 pedidos da cozinheira por nome por extenso.
- **Mais desafios — Desafio:** Fila de 10 crianças em que 3 cartões estão em falta e o aluno escreve o ordinal num teclado numérico com tecla «.º»; pedidos da cozinheira combinados («Dá o tabuleiro à criança que está logo a seguir à sexta»); pergunta final «Se chegar mais uma criança, em que lugar fica?».

## Unit 3: A fila do autocarro: os lugares do 11.º ao 20.º constroem-se a partir do décimo. (11 min)

### Texto
Na paragem, 20 passageiros esperam o autocarro. Os 10 primeiros já têm o seu cartão (recuperados da unidade anterior, em tom esbatido). O aluno constrói o nome dos passageiros do 11.º ao 20.º juntando peças de palavra num quadro de duas casas: uma peça «décimo» e peças «primeiro» a «nono», além de uma peça isolada «vigésimo». Depois lê pedidos do motorista por extenso («O décimo oitavo leva o bilhete verde») e toca no passageiro certo, e escreve o numeral de dois passageiros apontados (ex.: 13.º). O aluno deve descobrir que do 11.º ao 19.º o nome junta «décimo» ao nome de um lugar de 1 a 9 e que o 20.º tem um nome novo.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "passageiroAlvo",
    "type": "derived",
    "derivedFrom": "sequência fixa de 5 posições: 11, 14, 17, 19, 20 (Passo a passo)"
  },
  {
    "name": "pecaDezena",
    "type": "drag",
    "options": [
      "décimo",
      "vigésimo",
      "(vazio)"
    ],
    "default": "(vazio)"
  },
  {
    "name": "pecaUnidade",
    "type": "drag",
    "options": [
      "primeiro",
      "segundo",
      "terceiro",
      "quarto",
      "quinto",
      "sexto",
      "sétimo",
      "oitavo",
      "nono",
      "(vazio)"
    ],
    "default": "(vazio)"
  },
  {
    "name": "pedidoMotorista",
    "type": "quiz",
    "options": [
      "décimo oitavo",
      "décimo segundo"
    ],
    "default": "décimo oitavo"
  },
  {
    "name": "numeralEscrito",
    "type": "quiz",
    "options": [
      "teclado 0–9 + tecla «.º»"
    ],
    "default": ""
  },
  {
    "name": "nomeCorreto",
    "type": "derived",
    "derivedFrom": "posição == 20 ? (pecaDezena == 'vigésimo' && pecaUnidade == '(vazio)') : (pecaDezena == 'décimo' && pecaUnidade == nome(posição - 10))"
  }
]
```

**Render:** Paragem de autocarro com 20 passageiros em duas filas de 10 para caber no ecrã sem transbordar (a segunda fila continua a primeira, ligada por uma seta curva); o autocarro e a porta de entrada à esquerda marcam a frente. Os 10 primeiros têm o cartão esbatido; o passageiro alvo pisca. Por baixo, um quadro com duas casas grandes e, ao lado, as peças de palavra como botões (≥56px). Ao completar um nome certo, o grupo dos 10 primeiros acende ao mesmo tempo que a peça «décimo», e os passageiros a mais acendem com a segunda peça — mostrando a ligação sem a dizer. Teclado próprio com dígitos e a tecla «.º» para escrever numerais.

**Transition:** Tocar numa peça e depois numa casa coloca-a (alternativa por teclado: Tab + Enter); tocar numa peça colocada retira-a. «Confirmar» verifica o nome. Erro: as casas ficam com contorno âmbar e a pista visual mostra, na fila, o grupo dos 10 primeiros e os passageiros que faltam até ao alvo, sem mostrar a peça em falta. No pedido do motorista, tocar no passageiro confirma; se errar, a fila conta em silêncio, acendendo um a um, a partir da porta até onde o aluno tocou. Ao escrever o numeral, a falta do «.º» é sinalizada com o cartão «13» ao lado de «13.º» e a pergunta «Diz quantos ou diz o lugar?».

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: do 11.º ao 19.º, o nome do ordinal forma-se juntando «décimo» ao nome do ordinal das unidades (décimo terceiro = dez lugares + mais três); o 20.º não segue esse padrão e tem nome próprio, «vigésimo»; o numeral ordinal escreve-se com os mesmos algarismos do número e o sinal «.º».

**Assessment (observável):** O aluno constrói corretamente pelo menos 4 dos 5 nomes (incluindo o vigésimo), encontra os 2 passageiros pedidos por extenso e escreve os 2 numerais com o sinal «.º»; perante a pergunta «Porque é que o 14.º se chama décimo quarto?», aponta para os 10 primeiros e para os 4 seguintes ou diz «são dez e mais quatro».

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** Fila até ao 15.º; a peça «décimo» já está colocada na primeira casa e o aluno só escolhe a segunda; os 10 primeiros passageiros ficam dentro de uma moldura com a etiqueta «10»; o numeral é escolhido entre dois cartões («13» e «13.º») em vez de escrito.
- **Passo a passo — Intermédio:** Fila até ao 20.º; o aluno escolhe as duas peças, constrói 5 nomes, lê 2 pedidos e escreve 2 numerais.
- **Mais desafios — Desafio:** Fila até ao 20.º com peças-armadilha («décimo décimo», «segundo décimo»); o aluno constrói 7 nomes por ordem salteada e responde «Quem está entre o décimo sexto e o décimo oitavo?»; no fim prevê como se chamará o 21.º passageiro e explica a ideia ao par (resposta aberta, sem veredicto automático).

## Unit 4: De onde começas a contar? — o lugar muda quando muda o ponto de partida. (10 min)

### Texto
Uma fila de 12 crianças espera para entrar no autocarro da visita de estudo. O aluno responde, para uma criança destacada, «Em que lugar está o Tomás?», contando a partir da porta da frente. Depois acontece uma surpresa: «Hoje a porta da frente avariou! Entra-se por trás.» A porta muda para a outra ponta e a mesma pergunta repete-se para a mesma criança. O aluno repete o par de perguntas para 3 crianças e, no fim, responde «O Tomás mudou de lugar na fila?». Deve descobrir que a criança não se mexeu, mas o ordinal muda quando muda o ponto de partida da contagem.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "portaAberta",
    "type": "toggle",
    "options": [
      "porta da frente",
      "porta de trás"
    ],
    "default": "porta da frente"
  },
  {
    "name": "criancaAlvo",
    "type": "derived",
    "derivedFrom": "sequência fixa: Tomás (posição 3 a partir da frente), Duarte (posição 8), Pedro (posição 11), numa fila de 12"
  },
  {
    "name": "ordinalEscolhido",
    "type": "quiz",
    "options": [
      "3 cartões de ordinal próximos, ex.: 9.º, 10.º, 11.º"
    ],
    "default": null
  },
  {
    "name": "ordinalEsperado",
    "type": "derived",
    "derivedFrom": "portaAberta == 'porta da frente' ? posicao : 12 - posicao + 1"
  },
  {
    "name": "mudouDeLugar",
    "type": "quiz",
    "options": [
      "Sim, mudou",
      "Não, ficou no mesmo sítio"
    ],
    "default": null
  }
]
```

**Render:** Autocarro ao longo do ecrã com duas portas; a porta aberta tem uma seta grande «entra-se aqui» e a fechada um sinal de proibido. A fila de 12 crianças fica sempre no mesmo sítio, com as mesmas cores e acessórios, para que se veja que ninguém se mexe. A criança alvo tem um balão com o nome. Três cartões de ordinal grandes por baixo. Depois de responder pela porta da frente, o cartão escolhido fica preso por baixo da criança, à esquerda; ao abrir a porta de trás, aparece um segundo espaço à direita para o novo cartão, permitindo comparar os dois. O professor pode mostrar este ecrã no Quadro para a discussão final.

**Transition:** Tocar num cartão confirma o lugar a contar da porta aberta. Depois da primeira resposta, a mudança de porta é animada (≤300 ms, respeita prefers-reduced-motion) e a mesma criança volta a ser perguntada. Erro: contorno âmbar e a fila acende uma a uma a partir da porta aberta até à criança, sem dizer o número. As respostas da porta da frente mantêm-se visíveis enquanto o aluno responde pela porta de trás. A pergunta «mudou de lugar?» aparece no fim; a escolha regista-se e a explicação é oral, sem veredicto automático.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: o ordinal de um elemento depende do ponto de partida e do sentido da contagem; a mesma criança, sem se mover, pode ser a 3.ª a contar da frente e a 10.ª a contar de trás; por isso, dizer um lugar exige dizer de onde se conta.

**Assessment (observável):** O aluno indica corretamente o ordinal a partir das duas portas para pelo menos 2 das 3 crianças, escolhe «Não, ficou no mesmo sítio» e justifica oralmente com uma frase do tipo «ela não mexeu, nós é que começámos a contar do outro lado».

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** Fila de 6 crianças e só 2 crianças alvo; pegadas numeradas acendem a partir da porta aberta quando o aluno toca na fila; o aluno pode reproduzir a situação com 6 cartões físicos na mesa, virando-os.
- **Passo a passo — Intermédio:** Fila de 12 crianças e 3 crianças alvo, com escolha entre três cartões próximos.
- **Mais desafios — Desafio:** Fila de 16 crianças; o aluno escreve o ordinal em vez de o escolher; problema final «A Leonor é a 4.ª a contar da frente e a 9.ª a contar de trás. Quantas crianças há na fila?», verificável na página construindo a fila com o botão «+ criança»; uso do feminino (4.ª, quarta) assinalado no cartão.

## Unit 5: O prédio da Rua do Carteiro: os andares contam-se de baixo para cima, a partir do rés-do-chão. (10 min)

### Texto
O carteiro tem 5 cartas para entregar num prédio com rés-do-chão e 12 andares. Cada carta tem o andar escrito com numeral ou por extenso («Família Costa — 5.º andar», «Avó Lurdes — nono andar»). O aluno toca na carta e depois no andar certo do prédio; o elevador sobe até lá. Uma das cartas é para o rés-do-chão. O aluno deve descobrir, pelo feedback do elevador, que no prédio se conta de baixo para cima e que o rés-do-chão não é o 1.º andar: o 1.º andar é o primeiro acima do rés-do-chão. Antes de começar, o professor pergunta à turma «Em que andar moras?» e regista algumas respostas no cartaz (casas térreas também contam: moram no rés-do-chão).

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "cartaAtual",
    "type": "derived",
    "derivedFrom": "sequência fixa: 5.º andar; nono andar; rés-do-chão; 1.º andar; décimo segundo andar"
  },
  {
    "name": "andarTocado",
    "type": "quiz",
    "options": [
      "R/C",
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12"
    ],
    "default": null
  },
  {
    "name": "nomePorExtenso",
    "type": "quiz",
    "options": [
      "3 cartões de nome próximos, ex.: quarto, quinto, sexto"
    ],
    "default": null
  },
  {
    "name": "elevador",
    "type": "derived",
    "derivedFrom": "posição vertical do elevador = andarTocado; painel acende do R/C até andarTocado"
  }
]
```

**Render:** Prédio alto e estreito no centro, com 13 pisos visíveis sem deslocar a página: porta de entrada e etiqueta «R/C» no piso térreo, janelas com caixas de correio em cada andar. À direita, um painel de elevador com botões grandes (≥56px): R/C, 1, 2… 12. A carta atual aparece em grande, com o destinatário ilustrado e o andar escrito. O andar ainda não tem etiqueta visível no prédio, para obrigar a contar. Alternativa por teclado: setas para cima e para baixo percorrem os andares, Enter entrega.

**Transition:** Tocar no andar (no prédio ou no painel) entrega a carta: o elevador sobe com animação curta e os botões do painel acendem do R/C até ao andar tocado. Acerto: a caixa de correio abre e a etiqueta do andar aparece. Erro: contorno âmbar na caixa de correio, o painel volta a acender lentamente desde o R/C, com o botão R/C destacado, e a carta volta para a mão do carteiro para nova tentativa. Depois de cada entrega com numeral, aparece a pergunta «Como se diz este andar?» com três cartões de nome.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: num prédio, os andares ordenam-se de baixo para cima, a partir do rés-do-chão; o rés-do-chão é o ponto de partida e não é o 1.º andar, pelo que o 5.º andar é o quinto acima do rés-do-chão e não o quinto piso a contar do chão.

**Assessment (observável):** O aluno entrega corretamente pelo menos 4 das 5 cartas, incluindo a do rés-do-chão e a do 1.º andar, escolhe o nome por extenso correto em 2 de 2 perguntas e, ao professor que pergunta «Onde fica o 1.º andar?», aponta para o primeiro piso acima da porta de entrada.

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** Prédio com R/C e 6 andares; as cartas usam só numerais até 6.º; o painel do elevador mostra os números e, ao lado de cada botão, pontos (1 ponto, 2 pontos…); o R/C tem uma porta grande e um tapete para tornar visível o ponto de partida.
- **Passo a passo — Intermédio:** Prédio com R/C e 12 andares; 5 cartas com numerais e nomes por extenso, incluindo rés-do-chão e 1.º andar.
- **Mais desafios — Desafio:** Prédio com R/C e 20 andares; cartas com pistas relativas («O Sr. Rui mora três andares acima do 15.º», «A Sara mora no andar logo abaixo do vigésimo»); no fim, o aluno responde «Num prédio com R/C e 20 andares, quantos pisos há ao todo?» e explica a resposta ao par.

## Unit 6: Pódio e perguntas da turma: os ordinais dizem lugares em qualquer contexto. (10 min)

### Texto
Mini-avaliação e comunicação. Primeiro, 6 itens curtos em contextos variados — a chegada à meta da corrida da escola, a fila da cantina e o prédio — misturando: ler um numeral e escolher o nome (17.º → décimo sétimo), ler um nome e escrever o numeral (décimo segundo → 12.º), distinguir «quantos?» de «em que lugar?» e indicar um lugar a partir de um ponto de partida dado. Depois, a pares, os alunos criam uma pergunta com ordinais sobre a sua realidade (fila do recreio, prédio, corrida, cadeiras na sala) completando a moldura «O/A ___ está em ___ lugar, a contar ___.» ou escrevendo livremente. No circuito de comunicação, dois ou três pares leem a pergunta à turma no Quadro e a turma responde; as descobertas vão para o cartaz «Descobrimos que…» e cada aluno regista no PIT até onde já sabe ler e escrever os ordinais. Reflexão individual facultativa: «O que te ajudou a encontrar o lugar certo?».

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "itemAtual",
    "type": "derived",
    "derivedFrom": "índice 0-5: corrida 17.º→nome; cantina «décimo segundo»→numeral; corrida «quantos chegaram antes do 5.º?»; prédio «3.º andar» com R/C; fila «2.º a contar de trás numa fila de 9»; pódio «quem ganhou a medalha de prata?» (2.º)"
  },
  {
    "name": "respostaItem",
    "type": "quiz",
    "options": [
      "cartões de escolha (3) ou teclado 0–9 + «.º», conforme o item"
    ],
    "default": null
  },
  {
    "name": "perguntaDoPar",
    "type": "canvas",
    "options": [
      "moldura com três espaços (quem / lugar / de onde se conta)",
      "texto livre"
    ],
    "default": "moldura com três espaços (quem / lugar / de onde se conta)"
  },
  {
    "name": "itensCorretos",
    "type": "derived",
    "derivedFrom": "contagem de respostas certas nos 6 itens"
  }
]
```

**Render:** Passo 1: um item por ecrã, com a cena do contexto (meta com bandeira de xadrez e pódio de três degraus; fila da cantina; prédio com R/C) e a pergunta numa frase curta com ícone. Barra de progresso com 6 marcas. Passo 2: moldura de frase em cartões grandes com três espaços; o espaço «lugar» oferece teclado com «.º» e cartões de nome; o espaço «de onde se conta» oferece «da frente», «de trás», «de baixo», «de cima» e escrita livre. Botão «Já está» confirma a pergunta do par. Mensagem final que descreve a descoberta: «Já sabes dizer lugares até ao 20.º!».

**Transition:** Em cada item, confirmar regista a resposta; erro mostra a pista visual do contexto (contagem a acender a partir da porta, da meta ou do R/C) e permite uma nova tentativa; o item seguinte fica disponível depois de qualquer resposta. No passo 2, completar os espaços e carregar em «Já está» guarda a pergunta como produção do par, sem veredicto automático; editar depois invalida a confirmação anterior e pede nova confirmação.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Invariante interno, não apresentado ao aluno: em qualquer contexto (fila, prédio, corrida), um ordinal responde a «em que lugar?» numa ordem com ponto de partida definido; o numeral (17.º) e o nome (décimo sétimo) são duas representações do mesmo lugar, e uma pergunta sobre lugares só tem uma resposta quando diz de onde se conta.

**Assessment (observável):** O aluno acerta pelo menos 5 dos 6 itens (registo automático por item); o par produz uma pergunta que contém um ordinal e indica o ponto de partida (ex.: «O Rui está em 6.º lugar, a contar da porta.»), e, no circuito de comunicação, pelo menos um elemento do par explica à turma como se encontra a resposta (observação do professor na lista de verificação).

### Diferenciação (implementar como tabs seleccionáveis)

- **Com pistas — Apoio:** 4 itens, só até ao 10.º, todos com escolha entre cartões; moldura de frase com cartões de palavras para tocar, incluindo «da frente» já sugerido; o par pode ditar a pergunta ao professor.
- **Passo a passo — Intermédio:** 6 itens até ao 20.º, com um item de escrita do numeral; pergunta do par na moldura de três espaços.
- **Mais desafios — Desafio:** 8 itens, incluindo dois com feminino (a 3.ª classificada, terceira) e um item inverso («A Ana chegou em 12.º lugar e o Rui 5 lugares depois. Em que lugar chegou o Rui?»); o par escreve a pergunta livremente e acrescenta uma segunda pergunta em que o ponto de partida mude a resposta.


## Referências curriculares para o guia do professor
- Matemática (2.º ano): Reconhecer os numerais ordinais até ao 20.º, em contextos diversos. Ação estratégica: propor a exploração dos números ordinais a partir de situações da realidade próxima dos alunos (ordem dos alunos na fila da cantina; andar em que habitam; ordem dos passageiros na fila do autocarro).
- Matemática (2.º ano): Comparar e ordenar números naturais, de forma crescente e decrescente (mobilizado na contagem a partir da frente e a partir de trás da fila).
- Matemática (2.º ano): Descrever a sua forma de pensar acerca de ideias e processos matemáticos, oralmente e por escrito; ouvir os outros, questionar e discutir as ideias de forma fundamentada.
- Matemática (2.º ano): Ler e interpretar ideias e processos matemáticos expressos por representações diversas; usar representações múltiplas, em especial linguagem verbal e diagramas (numeral 13.º, nome «décimo terceiro» e posição na fila).
- PA-A: Linguagens e textos
- PA-C: Raciocínio e resolução de problemas
- PA-D: Pensamento crítico e pensamento criativo
- PA-E: Relacionamento interpessoal
- PA-F: Desenvolvimento pessoal e autonomia

## Artefacto e verificação

HTML5, CSS e JavaScript inline, sem dependências de rede. Implementa as interações e os estados definidos nas unidades, incluindo alternativa por teclado. Usa o template da skill como referência técnica e conserva os nomes da ponte. O ficheiro deve passar pela incorporação da fonte, Proofreader e Evaluator antes de ser entregue para revisão do professor.

