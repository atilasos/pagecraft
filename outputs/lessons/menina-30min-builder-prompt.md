# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Método das 28 Palavras — Palavra 1: Menina (sessão de 30 min)
- Ano: 6-7 anos (1.º ano)
- Duração: 30 minutos
- Objectivos: ["Reconhecer globalmente a palavra 'menina' associando-a à imagem e ao som correspondentes", "Segmentar a palavra 'menina' nas sílabas me-ni-na e reconstruí-la a partir de sílabas desordenadas", "Recombinar as sílabas me, ni, na para formar uma palavra nova (ex: 'mina'), distinguindo palavras reais de pseudo-palavras", "Construir oralmente e por escrito uma frase simples utilizando a palavra 'menina'"]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Apresentação global da palavra 'menina' em micro-frase com imagem (4 min)

### Texto
O aluno encontra a palavra 'menina' em contexto significativo: vê uma ilustração e lê/ouve uma micro-frase ('A menina sorri.'). Reconhece globalmente a palavra associando imagem, som e forma escrita, antes de qualquer trabalho silábico isolado.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "cenaVisivel",
    "type": "toggle",
    "options": [
      "oculta",
      "visível"
    ],
    "default": "oculta"
  },
  {
    "name": "palavraSeleccionada",
    "type": "quiz",
    "options": [
      "menina",
      "boneca",
      "janela"
    ]
  },
  {
    "name": "tentativas",
    "type": "derived",
    "derivedFrom": "count(cliques)"
  }
]
```

**Render:** Painel superior com ilustração de uma menina a sorrir e a micro-frase 'A menina sorri.' com a palavra 'menina' destacada a rosa (#E05FA0) sobre as sílabas; em baixo, 3 cartões-palavra (menina, boneca, janela) com áudio individual; botão de play que narra a frase

**Transition:** Clicar na imagem revela a cena → ouvir a frase narrada → clicar num cartão-palavra: se 'menina', borda verde + ampliação + áudio /menina/; se outro, borda âmbar + áudio neutro + nova tentativa permitida

**Constraint (o aluno DESCOBRE — NÃO revelar):** A mesma sequência de letras/sons corresponde sempre à mesma imagem e à mesma palavra ouvida — o aluno descobre a tripla correspondência imagem ↔ palavra escrita ↔ palavra falada

**Assessment (observável):** O aluno seleciona o cartão 'menina' entre 3 opções em até 2 tentativas e repete a palavra em voz alta de forma audível

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 2 opções apenas (menina vs. boneca); imagem com seta a apontar para a palavra na frase; áudio de 'menina' tocado antes da escolha
- 🟡 **Intermédio:** 3 opções com imagem visível; uma tentativa adicional permitida; áudio só após clicar
- 🔴 **Desafio:** 4 opções incluindo distrator visualmente próximo ('menino'); responde à 1.ª tentativa e justifica oralmente porque é 'menina' e não 'menino'

## Unit 2: Descoberta das sílabas me-ni-na por palmas e separação visual (9 min)

### Texto
O aluno descobre que a palavra 'menina' tem 3 partes (sílabas) batendo palmas ao mesmo tempo que ouve, e depois reconstrói a palavra ordenando as sílabas me, ni, na. Cada sílaba tem cor própria (me=rosa, ni=violeta, na=verde) que servirá de pista nas units seguintes.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "modo",
    "type": "toggle",
    "options": [
      "bater palmas",
      "ordenar sílabas"
    ],
    "default": "bater palmas"
  },
  {
    "name": "contadorPalmas",
    "type": "slider",
    "range": [
      0,
      4
    ],
    "step": 1,
    "default": 0,
    "unit": "palmas"
  },
  {
    "name": "silabaActiva",
    "type": "derived",
    "derivedFrom": "contadorPalmas"
  },
  {
    "name": "ordemSilabas",
    "type": "sorting",
    "options": [
      "na",
      "me",
      "ni"
    ]
  },
  {
    "name": "palavraFormada",
    "type": "derived",
    "derivedFrom": "join(ordemSilabas)"
  }
]
```

**Render:** Modo 'bater palmas': palavra 'menina' centrada em grande; ao clicar no botão 'palma' incrementa contador, destaca uma sílaba de cada vez (me rosa → ni violeta → na verde) com áudio sincronizado e mãos animadas. Modo 'ordenar sílabas': 3 blocos arrastáveis coloridos (na/me/ni) e zona-alvo com 3 posições; a palavra parcial actualiza em tempo real; imagem da menina visível como apoio.

**Transition:** Em 'bater palmas', cada clique destaca a próxima sílaba; ao chegar a 3, a palavra divide-se visualmente em me-ni-na e o toggle muda para 'ordenar sílabas'. Em 'ordenar', arrastar para zona correcta forma 'menina' → áudio /menina/ + animação de celebração; ordem errada → borda âmbar e sugestão.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A palavra 'menina' tem exactamente 3 sílabas e só uma sequência (me-ni-na) reproduz a palavra ouvida — o aluno descobre simultaneamente o número de partes e a ordem invariante

**Assessment (observável):** O aluno bate 3 palmas sincronizadas com as sílabas, indica oralmente que 'menina' tem 3 partes, e ordena os 3 blocos na sequência me-ni-na em até 2 tentativas

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Modo 'palmas' com animação automática de modelagem (auto-play 1x); na ordenação, a sílaba 'me' já está colocada na 1.ª posição; cores das sílabas correspondem às posições marcadas
- 🟡 **Intermédio:** Aluno bate as 3 palmas autonomamente e ordena os 3 blocos com a imagem como apoio e cores nas sílabas mas sem posições pré-preenchidas
- 🔴 **Desafio:** Sílabas todas a preto (sem cor); inclui um bloco distrator extra ('no') que tem de ser identificado e descartado; verbaliza após ordenar 'menina tem três sílabas: me, ni, na'

## Unit 3: Recombinação silábica — formar palavras novas com me, ni, na (descobrir 'mina') (9 min)

### Texto
O aluno experimenta combinações livres das sílabas me, ni, na (e descarta uma) para formar palavras novas. Descobre que 'mina' é uma palavra real (formada com mi+na — usando a sílaba 'ni' lida como 'mi' não funciona, mas reaproveitando 'na' e mudando a 1.ª letra com 'mi' apresentada como nova sílaba) e classifica combinações como palavra real ou pseudo-palavra. Generaliza a ideia de que sílabas são peças reutilizáveis.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "silabasDisponiveis",
    "type": "drag",
    "options": [
      "me",
      "ni",
      "na",
      "mi"
    ]
  },
  {
    "name": "combinacaoActual",
    "type": "derived",
    "derivedFrom": "join(silabasDisponiveis_zona)"
  },
  {
    "name": "classificacao",
    "type": "quiz",
    "options": [
      "é palavra",
      "não é palavra"
    ]
  },
  {
    "name": "listaDescobertas",
    "type": "derived",
    "derivedFrom": "palavras_classificadas_correctamente"
  }
]
```

**Render:** Bancada superior com 4 sílabas arrastáveis coloridas (me rosa, ni violeta, na verde, mi azul-claro); zona de construção central com 2 posições (depois 3); palavra formada lida em áudio ao soltar; dois botões grandes 'é palavra' e 'não é palavra'; lista lateral 'já descobri:' que vai acumulando as palavras correctamente classificadas (alvo seguro: 'mina'); imagem aparece quando a palavra real é classificada correctamente

**Transition:** Arrastar 2-3 sílabas para a zona → áudio lê a combinação → aluno classifica como palavra ou não → se acertar a classificação, palavra entra na lista 'já descobri:'; se errar, feedback âmbar com áudio repetido para nova tentativa; botão 'limpar' devolve sílabas para nova combinação

**Constraint (o aluno DESCOBRE — NÃO revelar):** Nem toda a combinação de sílabas forma uma palavra com significado — só algumas sequências (como 'mi-na') correspondem a palavras reais que o aluno já ouviu

**Assessment (observável):** O aluno forma e classifica correctamente pelo menos a palavra 'mina' como palavra real, e pelo menos uma pseudo-palavra (ex: 'nime') como 'não é palavra', verbalizando ao colega de par o que descobriu

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Apenas 3 sílabas (me, na, mi); zona com 2 posições fixas; 'mina' surge como exemplo guiado e o aluno tem de a classificar como palavra real; imagem de mina (poço) visível como pista
- 🟡 **Intermédio:** 4 sílabas (me, ni, na, mi); zona com 2-3 posições; sem exemplo prévio; deve descobrir e classificar 'mina' por iniciativa própria com o par
- 🔴 **Desafio:** Inclui sílaba extra ('ma'); deve descobrir 2+ palavras reais (mina, nana) e identificar pelo menos 2 pseudo-palavras; escreve as palavras descobertas no campo de texto

## Unit 4: Construção de frase com 'menina' e mini-avaliação observável (8 min)

### Texto
O aluno aplica a palavra 'menina' numa frase simples ('A menina sorri.') ordenando cartões-palavra, e depois realiza uma mini-avaliação de 3 micro-tarefas que cobrem reconhecimento, segmentação e uso. O resultado é registado no ficheiro individual e partilhado em circuito de comunicação curto.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "fase",
    "type": "dropdown",
    "options": [
      "construir frase",
      "mini-avaliação"
    ],
    "default": "construir frase"
  },
  {
    "name": "palavrasDaFrase",
    "type": "sorting",
    "options": [
      "A",
      "menina",
      "sorri",
      "."
    ]
  },
  {
    "name": "fraseFormada",
    "type": "derived",
    "derivedFrom": "join(palavrasDaFrase, ' ')"
  },
  {
    "name": "tarefaAvaliacao",
    "type": "dropdown",
    "options": [
      "reconhecer",
      "segmentar",
      "usar"
    ],
    "default": "reconhecer"
  },
  {
    "name": "estrelas",
    "type": "derived",
    "derivedFrom": "count(tarefas_correctas)"
  }
]
```

**Render:** Fase 'construir frase': 4 cartões-palavra arrastáveis (A, menina, sorri, .) fora de ordem, com 'menina' destacada nas cores silábicas; linha de construção em baixo com 4 posições; ao completar, áudio lê a frase com entoação e a imagem da menina a sorrir aparece. Fase 'mini-avaliação': 3 micro-ecrãs sequenciais — (1) escolher 'menina' entre 3 palavras; (2) indicar nº de sílabas com botões 1/2/3; (3) completar 'A ___ sorri.' com a sílaba/palavra correta. Barra com 3 estrelas no topo acende verde/âmbar.

**Transition:** Construir frase: arrastar cartões → frase actualiza → ordem correcta acende verde + lê em voz alta + revela imagem; ordem errada → borda âmbar e sugestão. Mini-avaliação: completar tarefa → estrela acende → avança automaticamente; ao fim, ecrã de resumo com as 3 estrelas e botão 'partilhar com a turma' que abre o registo final.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Uma frase simples em português segue a ordem artigo-sujeito-verbo e termina com ponto final; as competências treinadas (reconhecer, segmentar, usar) são complementares e cada uma pode ser observada de forma independente

**Assessment (observável):** O aluno (1) ordena os 4 elementos da frase 'A menina sorri.' correctamente e lê-a em voz alta; (2) acerta nas 3 micro-tarefas da avaliação ou identifica em qual precisa de mais prática; (3) partilha com um colega ou com a turma a frase construída

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Frase com 'A' e '.' já colocados; só ordenar 'menina' e 'sorri'; mini-avaliação com 2 opções por tarefa e imagem de apoio; partilha em par
- 🟡 **Intermédio:** 4 elementos para ordenar sem pistas; mini-avaliação com 3 opções por tarefa; partilha à turma de 1 frase
- 🔴 **Desafio:** Cria uma frase própria com 'menina' (campo de texto livre, ex: 'A menina canta uma canção.'); mini-avaliação inclui tarefa bónus de escrita autónoma da palavra 'mina'; comunica à turma a frase própria




## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Português (1.º ano): Pronunciar segmentos fónicos a partir dos respectivos grafemas e dígrafos, incluindo os casos que dependem de diferentes posições dos fonemas ou grafemas na palavra
- Português (1.º ano): Reconhecer palavras globalmente, associando a forma escrita à forma oral e ao significado, integrando-as progressivamente num léxico visual alargado
- Português (1.º ano): Fazer a correspondência entre letra/dígrafo e fonema/som; ler sílabas e palavras constituídas por essas correspondências
- Português (1.º ano): Escrever palavras e frases simples, respeitando as regras de correspondência fonema-grafema e utilizando correctamente as marcas do género e do número

### Perfil do Aluno
- PA-A: Linguagens e textos
- PA-F: Desenvolvimento pessoal e autonomia
- PA-C: Raciocínio e resolução de problemas
- PA-E: Relacionamento interpessoal

## Requisitos técnicos OBRIGATÓRIOS

1. **HTML5 + CSS3 + JavaScript vanilla** — ZERO dependências externas, ZERO CDNs
2. **Self-contained** — TODO o CSS e JS inline no ficheiro HTML
3. **Responsive** — funcionar em tablet (768px) e quadro interactivo (1920px)
4. **Touch-friendly** — áreas clicáveis mínimo 44x44px, suporte touch events + mouse
5. **Acessibilidade** — aria-labels, contraste WCAG AA, font-size mínimo 16px
6. **Cores vivas** — amigáveis para crianças, feedback visual claro
7. **Animações** — CSS transitions + requestAnimationFrame para partículas/canvas
8. **Diferenciação** — 3 níveis como tabs/botões (🟢 Apoio, 🟡 Intermédio, 🔴 Desafio)
9. **Constraint** — NÃO revelar directamente; a interacção leva à descoberta
10. **Feedback** — visual+sonoro quando o aluno descobre algo (confetti, cor, mensagem)
11. **Drag-and-drop** — funcional com touch events E mouse events
12. **Offline** — funcionar sem internet
13. **Linguagem** — pt-PT (AO90), frases curtas, adequada a 6-7 anos (1.º ano)

## Guardar como
`page.html` — ficheiro único, completo, pronto a abrir no browser.

## IMPORTANTE
- Usar `template.html` como referência de estilo CSS (se existir no directório)
- Implementar TODAS as interacções descritas nas specs SRTC-A
- Cada slider, matching, sorting, toggle deve ser FUNCIONAL, não placeholder
- Canvas com partículas animadas quando especificado
- Testar mentalmente que a página funciona antes de gravar

## Design obrigatório (PageCraft)
Este projeto tem um `CLAUDE.md` em `/Users/igor/.openclaw/workspace/pagecraft/CLAUDE.md` com as regras de design.
Resumo das regras críticas:
- Fonte: 'Nunito', 'Comic Sans MS', 'Chalkboard SE' — nunca Inter/Roboto/Arial
- Tamanho base body: 20px; sílabas: 36-48px, font-weight 800
- Touch targets mínimo 48px em todos os eixos
- Cada sílaba com cor própria do design-spec.json (syllableColors)
- Botões pill, border-radius 16px nos cards, feedback correto/incorreto conforme spec
- Aplicar a skill de design `anthropics-frontend-design`: página única, identidade visual
  baseada na paleta da palavra, playful/toy-like, animações de stagger no load
- Respeitar `prefers-reduced-motion` nas animações
- Focus ring: outline 3px solid var(--primary), outline-offset 2px

