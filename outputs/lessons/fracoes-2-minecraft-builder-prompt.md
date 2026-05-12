# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Frações: partes iguais de uma unidade
- Ano: 2.º ano (7-8 anos)
- Duração: 45 minutos
- Objectivos: ["Reconhecer a fração como uma quantidade não inteira numa relação parte-todo, quando uma unidade contínua é dividida em partes iguais.", "Distinguir partilhas equitativas e não equitativas, justificando que só há fração quando as partes da unidade têm o mesmo tamanho.", "Representar frações simples por desenhos, dobragens, materiais, palavras e símbolos, usando linguagem inicial de numerador e denominador.", "Comparar frações unitárias em contextos concretos e reconhecer que uma fração com numerador igual ao denominador representa a unidade inteira."]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Uma fração nasce de uma unidade inteira dividida em partes iguais. (8 min)

### Texto
A turma parte de uma situação concreta: uma baguete para duas crianças. O aluno observa a unidade inteira, experimenta cortes em partes iguais e não iguais, e constrói a ideia de que cada metade só é 1/2 quando as duas partes têm o mesmo tamanho.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "tipo_de_corte",
    "type": "toggle",
    "options": [
      "partes iguais",
      "partes diferentes"
    ],
    "default": "partes iguais"
  },
  {
    "name": "partes_baguete",
    "type": "derived",
    "derivedFrom": "tipo_de_corte define se a baguete aparece dividida em 2 partes do mesmo tamanho ou em 2 partes de tamanhos diferentes"
  }
]
```

**Render:** Mostra uma baguete inteira e, ao lado, a baguete cortada em duas partes. As partes iguais aparecem sobrepostas por contorno quando se comparam; as partes diferentes deixam uma marca visual de sobra/desigualdade. O símbolo 1/2 só aparece depois de o aluno escolher a divisão equitativa.

**Transition:** Tocar no alternador muda entre partilha igual e partilha desigual. O aluno toca na parte que acha que pode chamar 'uma metade'; se a divisão não for equitativa, a página pede para comparar os tamanhos antes de tentar de novo.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A mesma unidade só pode ser nomeada por frações quando está repartida em partes iguais; uma de duas partes iguais corresponde a 1/2.

**Assessment (observável):** O aluno seleciona a divisão correta da baguete, recusa a divisão desigual e diz ou escreve: 'é 1/2 porque a baguete inteira foi dividida em 2 partes iguais'.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Usa apenas a baguete em 2 partes, com contornos grandes e comparação por sobreposição visual; o adulto pode perguntar 'as duas partes tapam o mesmo espaço?'.
- 🟡 **Intermédio:** Compara duas imagens, uma equitativa e outra não equitativa, e justifica oralmente qual representa 1/2.
- 🔴 **Desafio:** Desenha uma nova partilha errada e explica a um colega porque não pode ser escrita como 1/2.

## Unit 2: O denominador indica em quantas partes iguais a unidade foi dividida; o numerador indica quantas dessas partes foram tomadas. (10 min)

### Texto
A unidade é dobrada ou repartida primeiro em metades e quartos, depois em 8, 5, 10, 3 e 6 partes iguais. O aluno liga palavras, símbolos e imagens: 1/2, 1/4, 2/5, 'uma de duas partes iguais', 'duas de cinco partes iguais'.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "denominador",
    "type": "dropdown",
    "options": [
      "2",
      "4",
      "8",
      "5",
      "10",
      "3",
      "6"
    ],
    "default": "2"
  },
  {
    "name": "numerador",
    "type": "slider",
    "range": [
      1,
      10
    ],
    "step": 1,
    "default": 1
  },
  {
    "name": "fracao_valida",
    "type": "derived",
    "derivedFrom": "numerador <= denominador"
  }
]
```

**Render:** Mostra uma barra, uma pizza e uma folha dobrada virtual com o número de partes definido pelo denominador. As partes escolhidas pelo numerador ficam coloridas. Ao lado aparecem frase curta, símbolo e vocabulário: '2/5 — duas de cinco partes iguais — dois quintos'. O slider do numerador fica limitado visualmente ao denominador escolhido.

**Transition:** Escolher o denominador reparte novamente a mesma unidade em partes iguais. Mover o numerador colore mais ou menos partes. A página começa com 2 e 4 destacados, e só depois desbloqueia 8, 5, 10, 3 e 6.

**Constraint (o aluno DESCOBRE — NÃO revelar):** O número de baixo conta todas as partes iguais da unidade; o número de cima conta apenas as partes escolhidas, sem mudar a unidade.

**Assessment (observável):** Dada uma imagem com 2 de 5 partes coloridas, o aluno monta 2/5, escolhe a frase 'duas de cinco partes iguais' e identifica oralmente qual é o numerador e qual é o denominador.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Trabalha apenas 1/2 e 1/4 com peças grandes e frases com lacunas: '1 de __ partes iguais'.
- 🟡 **Intermédio:** Representa 1/2, 1/4 e 2/5 alternando entre imagem, palavra e símbolo.
- 🔴 **Desafio:** Constrói uma representação para 3/6 e explica porque o denominador é 6 mesmo quando só 3 partes estão coloridas.

## Unit 3: A mesma fração pode aparecer em desenhos, dobragens, materiais, palavras e símbolos. (10 min)

### Texto
O aluno transforma uma fração simples entre representações. A ênfase está em partir, dobrar, colorir, construir com materiais e explicar com linguagem própria, sem cálculo abstrato.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "cartoes_imagem",
    "type": "matching",
    "options": [
      "barra 1/2",
      "folha dobrada em quartos com 1 parte pintada",
      "5 cubos com 2 destacados"
    ]
  },
  {
    "name": "cartoes_linguagem",
    "type": "matching",
    "options": [
      "1/2 — uma metade",
      "1/4 — um quarto",
      "2/5 — dois quintos"
    ]
  },
  {
    "name": "desenho_do_aluno",
    "type": "canvas",
    "default": "desenho livre de uma unidade repartida em partes iguais"
  }
]
```

**Render:** Apresenta cartões grandes com imagens concretas, cartões com palavras e símbolos, e uma área de desenho simples. As ligações corretas ficam verdes; ligações incorretas pedem nova observação da unidade e das partes.

**Transition:** O aluno liga imagem a palavra/símbolo e depois desenha uma representação equivalente. Pode apagar, dobrar virtualmente uma folha e voltar a tentar sem penalização.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Representações diferentes podem falar da mesma relação parte-todo se mantiverem a mesma unidade, o mesmo número de partes iguais e o mesmo número de partes escolhidas.

**Assessment (observável):** O aluno liga corretamente três pares de cartões e produz um desenho próprio para 1/2, 1/4 ou 2/5 com partes iguais assinaladas.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Recebe cartões com cores correspondentes e só precisa ligar imagem a palavra para 1/2 e 1/4.
- 🟡 **Intermédio:** Liga três representações e desenha uma unidade repartida com partes iguais claramente visíveis.
- 🔴 **Desafio:** Cria duas representações diferentes para a mesma fração e explica ao par porque são equivalentes na situação concreta.

## Unit 4: Quando o numerador é igual ao denominador, todas as partes da unidade foram tomadas e obtém-se a unidade inteira. (7 min)

### Texto
O aluno explora casos como 2/2, 4/4, 5/5 e 10/10 em unidades concretas. A página evita cálculo simbólico e mostra que a unidade está completa quando todas as partes iguais estão coloridas ou reunidas.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "denominador_unidade",
    "type": "dropdown",
    "options": [
      "2",
      "4",
      "5",
      "10"
    ],
    "default": "4"
  },
  {
    "name": "partes_reunidas",
    "type": "slider",
    "range": [
      0,
      10
    ],
    "step": 1,
    "default": 1
  },
  {
    "name": "unidade_completa",
    "type": "derived",
    "derivedFrom": "partes_reunidas == denominador_unidade"
  }
]
```

**Render:** Mostra uma unidade dividida em partes iguais e uma moldura de 'unidade completa'. À medida que as partes são reunidas, a moldura vai preenchendo. Quando todas as partes estão reunidas, a unidade fica inteira e aparece a equivalência em linguagem infantil: '4/4 é a unidade toda'.

**Transition:** Escolher o denominador muda o número de partes iguais. Mover o slider acrescenta ou retira partes reunidas. A página só celebra 'unidade inteira' quando o número de partes reunidas coincide com o número total de partes.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Tomar todas as partes iguais de uma unidade recompõe a unidade; por isso, numerador e denominador iguais indicam a unidade toda.

**Assessment (observável):** O aluno completa 4/4 ou 5/5, identifica que já não falta nenhuma parte e escolhe a frase 'é a unidade inteira'.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Usa 2/2 e 4/4 com encaixe visual tipo puzzle e feedback imediato quando a unidade fica completa.
- 🟡 **Intermédio:** Reconhece 2/2, 4/4 e 5/5 como unidade e distingue de 1/2 ou 3/4.
- 🔴 **Desafio:** Justifica por palavras porque 10/10 é a unidade inteira mesmo tendo mais partes pequenas do que 2/2.

## Unit 5: Frações unitárias podem ser comparadas observando o tamanho de uma parte quando a unidade é a mesma. (10 min)

### Texto
A turma compara 1/2, 1/3, 1/4, 1/5, 1/6, 1/8 e 1/10 em barras do mesmo tamanho. O foco é prático: quanto mais partes iguais fazemos na mesma unidade, menor fica cada parte. A exploração digital prepara uma construção cooperativa no Minecraft.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "fracao_A",
    "type": "dropdown",
    "options": [
      "1/2",
      "1/3",
      "1/4",
      "1/5",
      "1/6",
      "1/8",
      "1/10"
    ],
    "default": "1/2"
  },
  {
    "name": "fracao_B",
    "type": "dropdown",
    "options": [
      "1/2",
      "1/3",
      "1/4",
      "1/5",
      "1/6",
      "1/8",
      "1/10"
    ],
    "default": "1/4"
  },
  {
    "name": "resposta_comparacao",
    "type": "quiz",
    "options": [
      "A parte A é maior",
      "A parte B é maior",
      "São iguais"
    ],
    "default": "A parte A é maior"
  }
]
```

**Render:** Mostra duas barras do mesmo comprimento, cada uma dividida no número de partes indicado. Só uma parte de cada barra está colorida. Uma régua visual permite alinhar as partes coloridas para comparar tamanhos.

**Transition:** O aluno escolhe duas frações unitárias, observa as barras alinhadas e responde à comparação. O feedback pede uma justificação ligada ao número de partes iguais da mesma unidade.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Na mesma unidade, uma parte de uma divisão em menos partes iguais é maior do que uma parte de uma divisão em mais partes iguais.

**Assessment (observável):** O aluno compara corretamente 1/2 com 1/4 e 1/5 com 1/10, e justifica com uma frase do tipo: '1/2 é maior porque a unidade foi partida em menos partes iguais'.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Compara apenas 1/2 e 1/4, usando barras sobrepostas e uma parede Minecraft já marcada em 2 ou 4 secções iguais.
- 🟡 **Intermédio:** Compara pares de frações unitárias com denominadores até 10 e constrói no Minecraft paredes com partes iguais e placa correta.
- 🔴 **Desafio:** Inclui 1/8 ou 1/10 na galeria e explica por que a parte fica menor quando a mesma unidade é dividida em mais partes iguais.

### Maker Challenge (minecraft)
- Desafio: Em grupos de 3, construam no Minecraft uma 'Galeria das Frações' com 4 paredes iguais, cada uma com 10 blocos de comprimento. Em cada parede, mostrem uma fração diferente: 1/2, 1/4, 2/5 e uma fração à escolha com denominador até 10. Usem blocos de duas cores para mostrar a unidade, as partes iguais e as partes escolhidas. Incluam uma placa com palavras e símbolo, por exemplo: '2/5 — duas de cinco partes iguais'.
- Materiais: Minecraft Education Edition, mundo plano ou área delimitada pelo professor, blocos de duas cores contrastantes, placas/sinais do Minecraft, registo da exploração digital para consulta
- Grupo: 3
- Comunicação: Cada grupo faz uma visita guiada de 1 minuto à sua galeria, mostrando uma representação correta, uma comparação de frações unitárias e uma frase que explique porque as partes têm de ser iguais.



## Secção Maker (🛠️ Desafios Maker)
Incluir secção visual com fundo verde:
- **Minecraft:** Em grupos de 3, construam no Minecraft uma 'Galeria das Frações' com 4 paredes iguais, cada uma com 10 blocos de comprimento. Em cada parede, mostrem uma fração diferente: 1/2, 1/4, 2/5 e uma fração à escolha com denominador até 10. Usem blocos de duas cores para mostrar a unidade, as partes iguais e as partes escolhidas. Incluam uma placa com palavras e símbolo, por exemplo: '2/5 — duas de cinco partes iguais'.


## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Matemática (2.º ano): Reconhecer a fração como possibilidade de representar uma quantidade não inteira relativa a uma relação parte-todo, sendo o todo uma unidade contínua, e explicar o significado do numerador e do denominador, no contexto da resolução de problemas.
- Matemática (2.º ano): Representar uma fração de diversas formas, transitando de forma fluente entre as diferentes representações, recorrendo a materiais manipuláveis, dobragens, esquemas, palavras e símbolos.
- Matemática (2.º ano): Reconhecer frações que representam a metade e quartos da unidade, reconhecer que uma fração cujo numerador e denominador são iguais corresponde a uma unidade, e comparar e ordenar frações unitárias recorrendo a representações múltiplas.

### Perfil do Aluno
- PA-A: Linguagens e textos
- PA-B: Informação e comunicação
- PA-C: Raciocínio e resolução de problemas
- PA-D: Pensamento crítico e pensamento criativo
- PA-E: Relacionamento interpessoal
- PA-F: Desenvolvimento pessoal e autonomia
- PA-I: Saber científico, técnico e tecnológico

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
13. **Linguagem** — pt-PT (AO90), frases curtas, adequada a 2.º ano (7-8 anos)

## Guardar como
`page.html` — ficheiro único, completo, pronto a abrir no browser.

## IMPORTANTE
- Usar `template.html` como referência de estilo CSS (se existir no directório)
- Implementar TODAS as interacções descritas nas specs SRTC-A
- Cada slider, matching, sorting, toggle deve ser FUNCIONAL, não placeholder
- Canvas com partículas animadas quando especificado
- Testar mentalmente que a página funciona antes de gravar

## Design obrigatório (PageCraft)
Este projeto tem regras de repo em `/Users/igor/dev/pagecraft/README.md`. Lê-as e cumpre-as antes de implementar.

Resumo das regras críticas PageCraft:
- Fonte: 'Nunito', 'Comic Sans MS', 'Chalkboard SE' — nunca Inter/Roboto/Arial
- Tamanho base body: 20px; sílabas: 36-48px, font-weight 800
- Touch targets mínimo 48px em todos os eixos
- Cada sílaba com cor própria do design-spec.json (syllableColors)
- Botões pill, border-radius 16px nos cards, feedback correto/incorreto conforme spec
- Aplicar a skill de design `anthropics-frontend-design`: página única, identidade visual
  baseada na paleta da palavra, playful/toy-like, animações de stagger no load
- Respeitar `prefers-reduced-motion` nas animações
- Focus ring: outline 3px solid var(--primary), outline-offset 2px

