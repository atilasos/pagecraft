# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Verbos no modo indicativo: presente, pretérito perfeito e futuro
- Ano: 8-9 anos (3.º ano)
- Duração: 30 minutos
- Objectivos: ["Identificar o tempo verbal (presente, pretérito perfeito, futuro do indicativo) de uma forma verbal dada", "Conjugar verbos regulares das três conjugações (-ar, -er, -ir) e irregulares de alta frequência no modo indicativo", "Descobrir as terminações características de cada tempo/pessoa por observação de paradigmas", "Aplicar correctamente os três tempos do indicativo em frases completas"]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Aquecimento: o tempo verbal situa a acção no passado, presente ou futuro (5 min)

### Texto
O aluno recebe frases curtas com verbos em destaque e tem de decidir se a acção aconteceu (passado), acontece agora (presente) ou vai acontecer (futuro). O objectivo é activar conhecimento implícito sobre temporalidade antes de nomear os tempos gramaticais. A página usa linguagem do dia-a-dia ('já aconteceu', 'está a acontecer', 'ainda vai acontecer') em vez de metalinguagem imediata.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "frase_atual",
    "type": "quiz",
    "options": [
      "Já aconteceu",
      "Está a acontecer agora",
      "Ainda vai acontecer"
    ],
    "default": null
  },
  {
    "name": "indice_frase",
    "type": "derived",
    "derivedFrom": "contador interno 0-4"
  }
]
```

**Render:** Uma frase por vez, centrada, com o verbo sublinhado e em cor diferente. Três botões grandes com etiquetas temporais ('Já aconteceu / Está a acontecer agora / Ainda vai acontecer'). Barra de progresso no topo (5 frases). Feedback visual imediato: fundo verde claro (acerto) ou vermelho claro (erro) com a forma verbal revelada. Frases exemplares: 'O João cantou uma música.' / 'A Ana come a sopa.' / 'Nós vamos partir amanhã.' / 'O cão bebeu água.' / 'Eu farei os trabalhos.'

**Transition:** Tocar num botão → feedback imediato → após 1,5s avança automaticamente para a frase seguinte

**Constraint (o aluno DESCOBRE — NÃO revelar):** A terminação do verbo e as palavras em redor da frase (ontem, agora, amanhã) são pistas que permitem situar a acção no tempo — sem precisar de decorar nomes técnicos

**Assessment (observável):** O aluno responde correctamente a pelo menos 4 das 5 frases, identificando o marcador temporal implícito ou explícito

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Frases acompanham ícone visual (relógio com agulhas no passado / presente / futuro) e a frase inclui sempre um marcador explícito ('ontem', 'agora', 'amanhã')
- 🟡 **Intermédio:** Nem todas as frases têm marcador temporal explícito; o aluno deve apoiar-se na forma verbal
- 🔴 **Desafio:** Duas frases ambíguas sem marcador temporal: o aluno toca no verbo para ver um tooltip pedindo justificação da escolha ('Como sabes?')

## Unit 2: Descoberta: as terminações dos verbos regulares mudam de forma previsível conforme o tempo e a pessoa (8 min)

### Texto
O aluno explora um paradigma interactivo de três verbos regulares — cantar (1.ª conjugação), comer (2.ª conjugação), partir (3.ª conjugação) — em tabela. Pode seleccionar qualquer célula (pessoa × tempo) e ver a forma verbal formada. O objectivo é que o aluno, pela manipulação, descubra que as terminações variam sistematicamente: a mesma pessoa no mesmo tempo tem terminações semelhantes dentro da mesma conjugação, e que o radical se mantém inalterado nos regulares. O Constraint é esta regularidade morfológica — nunca enunciada directamente.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "verbo_selecionado",
    "type": "dropdown",
    "options": [
      "cantar",
      "comer",
      "partir"
    ],
    "default": "cantar"
  },
  {
    "name": "tempo_selecionado",
    "type": "toggle",
    "options": [
      "Presente",
      "Pretérito Perfeito",
      "Futuro"
    ],
    "default": "Presente"
  },
  {
    "name": "pessoa_selecionada",
    "type": "sorting",
    "options": [
      "eu",
      "tu",
      "ele/ela",
      "nós",
      "vós",
      "eles/elas"
    ],
    "default": "eu"
  },
  {
    "name": "forma_verbal",
    "type": "derived",
    "derivedFrom": "conjugação(verbo_selecionado, tempo_selecionado, pessoa_selecionada)"
  }
]
```

**Render:** Tabela 6×3 (pessoas × tempos) com células tocáveis. A célula seleccionada fica destacada (cor primária). A forma verbal aparece grande no centro acima da tabela. Radical sublinhado a azul, terminação sublinhada a laranja — a mesma codificação de cor em todas as células. Quando o aluno troca de verbo, apenas a coluna de terminações muda de texto; o radical muda também mas mantém a cor azul. Minilegenda no canto: 'azul = radical | laranja = terminação'.

**Transition:** Tocar célula → forma verbal actualiza instantaneamente com animação de fade; trocar verbo/tempo → tabela toda actualiza mantendo a célula seleccionada

**Constraint (o aluno DESCOBRE — NÃO revelar):** Em verbos regulares, o radical não muda e as terminações de cada pessoa/tempo são fixas dentro da mesma conjugação. Verbos de conjugações diferentes têm terminações distintas, mas internamente consistentes.

**Assessment (observável):** O aluno consegue, sem ajuda, dizer a terminação correcta de 3 pessoas diferentes do mesmo tempo para o verbo 'cantar', antes de confirmar na tabela — demonstrado tocando 'Testar-me' que esconde as terminações e pede preenchimento

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Tabela reduzida: apenas 3 pessoas (eu, ele/ela, eles/elas) e 2 tempos (presente e pretérito perfeito); cores mais contrastadas; tooltip de ajuda em cada célula com a divisão radical+terminação explicitada em sílabas
- 🟡 **Intermédio:** Tabela completa 6×3 com os três verbos; o aluno compara colunas e regista no PIT a terminação de uma pessoa à sua escolha
- 🔴 **Desafio:** Após exploração, o aluno arrasta as terminações soltas (baralhadas) para as células correctas de um paradigma em branco de um novo verbo regular: 'andar' — sem ver a tabela de referência

## Unit 3: Verbos irregulares de alta frequência: ser, ter, ir, fazer — o radical muda, mas a lógica de tempo mantém-se (7 min)

### Texto
O aluno confronta os mesmos três tempos (presente, pretérito perfeito, futuro) com quatro verbos irregulares de uso quotidiano: ser, ter, ir, fazer. A página mostra dois paradigmas em paralelo: um verbo regular (cantar) e um irregular (à escolha do aluno). O aluno observa que as terminações de tempo são semelhantes em alguns casos mas o radical é imprevisível — daí serem 'irregulares'. O objectivo é que o aluno reconheça as formas sem as decorar sistematicamente nesta sessão, mas comece a distinguir a irregularidade do radical da regularidade da terminação.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "irregular_selecionado",
    "type": "dropdown",
    "options": [
      "ser",
      "ter",
      "ir",
      "fazer"
    ],
    "default": "ser"
  },
  {
    "name": "tempo_comparacao",
    "type": "toggle",
    "options": [
      "Presente",
      "Pretérito Perfeito",
      "Futuro"
    ],
    "default": "Presente"
  },
  {
    "name": "pessoa_comparacao",
    "type": "derived",
    "derivedFrom": "fixo em 'eu / tu / ele / nós / eles' para as duas colunas"
  }
]
```

**Render:** Duas colunas lado a lado: esquerda = 'cantar' (regular, cinzento claro), direita = verbo irregular seleccionado (fundo amarelo claro). Radical a azul, terminação a laranja — mesma codificação. Nas formas onde o radical muda radicalmente (ex: 'sou' em vez de 'ser+o'), o radical fica destacado com borda vermelha e um ponto de interrogação tocável que abre: 'Este verbo é irregular — o radical muda! Tens de memorizar esta forma.' Botão de toggle de tempo no topo para comparar os três tempos.

**Transition:** Seleccionar irregular → coluna direita actualiza; tocar ponto de interrogação → tooltip explicativo; toggle tempo → ambas as colunas actualizam em simultâneo

**Constraint (o aluno DESCOBRE — NÃO revelar):** Nos verbos irregulares o radical pode mudar completamente dependendo do tempo e da pessoa, mas as terminações de tempo seguem ainda algumas regularidades partilhadas com os verbos regulares (especialmente no futuro)

**Assessment (observável):** O aluno toca em 3 formas verbais de 'ir' (uma por tempo: presente, pretérito perfeito, futuro) e diz em voz alta ou escreve se o radical mudou ou não face ao infinitivo — critério: identifica correctamente a irregularidade em pelo menos 2 das 3 formas

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Apenas 1 verbo irregular ('ser') com tabela de 3 pessoas (eu/ele/eles) e 2 tempos; as formas irregulares têm ícone de 'surpresa' antes do texto
- 🟡 **Intermédio:** 4 verbos irregulares disponíveis; aluno explora pelo menos 2; compara as 3 pessoas de 1 tempo com o regular
- 🔴 **Desafio:** O aluno recebe uma frase com lacuna: 'Ontem eu ___ ao mercado.' e deve escolher entre 'fui / fiz / tive' — com justificação do tempo e do verbo correcto; 3 frases deste tipo com irregulares diferentes

## Unit 4: Prática guiada: conjugar e completar frases com o tempo correcto (7 min)

### Texto
O aluno recebe frases com lacunas que pedem a forma correcta de um verbo dado entre parêntesis. Cada frase inclui um indicador de tempo (marcador adverbial ou contexto narrativo). Esta unit activa a síntese: o aluno deve conjugar (não apenas reconhecer) e escolher o tempo adequado ao contexto. Verbos usados: cantar, comer, partir, ser, ter, ir — garantindo cobertura das três conjugações regulares e dos irregulares.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "frase_lacuna",
    "type": "quiz",
    "options": [],
    "default": null
  },
  {
    "name": "resposta_aluno",
    "type": "drag",
    "targets": [
      "lacuna_1",
      "lacuna_2",
      "lacuna_3",
      "lacuna_4",
      "lacuna_5",
      "lacuna_6"
    ]
  },
  {
    "name": "banco_formas",
    "type": "derived",
    "derivedFrom": "conjunto de 4 opções por frase: 1 correcta + 3 distratores (tempo errado ou pessoa errada)"
  }
]
```

**Render:** Uma frase por vez com lacuna assinalada por '___'. Abaixo da frase, 4 cards tocáveis com formas verbais possíveis — incluem sempre formas do mesmo verbo em tempos diferentes e/ou pessoas diferentes. Após selecção correcta, a lacuna preenche-se a verde e a frase completa é lida. Após erro, a forma errada fica vermelha e o aluno pode tentar novamente. Contador de acertos no topo. Frases: 1) 'Amanhã nós ___ (partir) para as férias.' 2) 'Ontem o Pedro ___ (comer) toda a sopa.' 3) 'Eu já ___ (ser) pequenino, mas agora cresci.' 4) 'A Mariana ___ (cantar) todos os dias.' 5) 'No ano que vem eles ___ (ter) um novo professor.' 6) 'Hoje de manhã eu ___ (ir) ao parque.'

**Transition:** Tocar card → lacuna preenche com animação; verde = correcto (avança após 1s); vermelho = incorrecto (card volta ao banco, aluno tenta outra opção)

**Constraint (o aluno DESCOBRE — NÃO revelar):** O marcador temporal da frase (amanhã, ontem, todos os dias, hoje) é a pista que determina qual tempo verbal é adequado — não é possível acertar sem ler o contexto da frase

**Assessment (observável):** O aluno completa correctamente pelo menos 5 das 6 frases; em caso de erro, identifica e corrige após 1 nova tentativa

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Apenas 4 frases; marcadores temporais sublinhados automaticamente; apenas 3 opções por lacuna (sem distratores de pessoa errada)
- 🟡 **Intermédio:** 6 frases, 4 opções, marcadores sem sublinhado; feedback apenas no acerto/erro
- 🔴 **Desafio:** 6 frases + 2 frases bónus onde o verbo não é dado: o aluno escreve livremente a forma correcta num campo de texto; o sistema valida a resposta contra uma lista de formas aceites

## Unit 5: Mini-avaliação: identificar tempo + conjugar numa frase nova (3 min)

### Texto
Tarefa de síntese em dois passos: primeiro o aluno identifica o tempo de 4 formas verbais apresentadas isoladamente (matching entre forma e etiqueta de tempo); depois recebe 2 frases para completar de forma autónoma, sem banco de opções — escrevendo a forma directamente. Esta unit serve de evidência de aprendizagem observável para o professor e o aluno.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "pares_avaliacao",
    "type": "matching",
    "default": null
  },
  {
    "name": "formas_a_identificar",
    "type": "derived",
    "derivedFrom": "['cantou', 'partiremos', 'comes', 'fui'] — colunas esquerda; ['Pretérito Perfeito', 'Futuro', 'Presente', 'Pretérito Perfeito (irreg.)'] — coluna direita"
  },
  {
    "name": "frase_livre_1",
    "type": "canvas",
    "tools": [
      "teclado"
    ],
    "default": ""
  },
  {
    "name": "frase_livre_2",
    "type": "canvas",
    "tools": [
      "teclado"
    ],
    "default": ""
  }
]
```

**Render:** Fase 1 — Matching: coluna esquerda com 4 formas verbais (cards azuis), coluna direita com 4 etiquetas de tempo (cards cinzentos). Linha tracejada liga quando o aluno toca par a par. Feedback no final: pares correctos ficam verdes, incorrectos ficam vermelhos com a ligação correcta revelada. Fase 2 — após matching, aparecem 2 frases com lacuna e campo de texto livre (teclado virtual ou físico). Botão 'Verificar' valida. Frases: a) 'No verão passado eu ___ (fazer) uma viagem.' b) 'Amanhã a turma ___ (cantar) uma canção.'

**Transition:** Fase 1: ligar pares → feedback imediato por par; após 4 pares, botão 'Continuar' activa fase 2. Fase 2: escrever no campo → 'Verificar' → feedback com forma correcta revelada se errado

**Constraint (o aluno DESCOBRE — NÃO revelar):** Identificar um tempo verbal exige reconhecer as terminações características — e conjugar correctamente exige aplicar essas terminações ao sujeito da frase

**Assessment (observável):** Critério 1 (identificação): o aluno liga correctamente pelo menos 3 dos 4 pares. Critério 2 (produção): o aluno escreve correctamente pelo menos 1 das 2 formas verbais livres. Evidência registável pelo professor no PIT do aluno.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Fase 1 com apenas 3 pares (presente/pretérito perfeito/futuro, verbos regulares); fase 2 com banco de 3 opções em vez de campo livre
- 🟡 **Intermédio:** 4 pares + 2 campos livres conforme descrito
- 🔴 **Desafio:** 4 pares + 2 campos livres + 1 tarefa de escrita: 'Escreve uma frase tua com o verbo IR no futuro e outra com o verbo SER no pretérito perfeito.' — avaliação por critério de adequação do tempo ao contexto criado




## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Português (3.º ano): Conjugar verbos regulares e irregulares no presente, no pretérito perfeito e no futuro do modo indicativo
- Português (3.º ano): Utilizar apropriadamente os tempos verbais para exprimir anterioridade, posterioridade e simultaneidade
- Português (3.º ano): Aquisição de conhecimento sobre regras de flexão de verbos regulares e irregulares (ação estratégica de ensino)
- Português (3.º ano): Descobrir regularidades na formação de palavras (manipulação de constituintes de palavras — aqui aplicada às terminações verbais)

### Perfil do Aluno
- PA-A: Linguagens e textos
- PA-C: Raciocínio e resolução de problemas
- PA-D: Pensamento crítico e pensamento criativo
- PA-F: Desenvolvimento pessoal e autonomia

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
13. **Linguagem** — pt-PT (AO90), frases curtas, adequada a 8-9 anos (3.º ano)

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

