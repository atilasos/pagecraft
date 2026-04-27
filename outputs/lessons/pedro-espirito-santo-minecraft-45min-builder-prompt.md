# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Texto melhorado: O Pedro recebeu o Espírito Santo — leitura, compreensão e reconstrução no Minecraft Education
- Ano: 6-7 anos (1.º ano)
- Duração: 45 minutos
- Objectivos: ["Identificar no texto informação essencial: quem, quando, onde, quantas pessoas e o que aconteceu.", "Reconhecer que um texto melhorado fica mais claro quando junta frases completas, nomes próprios, tempos e detalhes verificáveis.", "Recontar oralmente o acontecimento respeitando a sequência do texto do colega.", "Planear em grupo uma representação no Minecraft Education que comunique as ideias principais do texto."]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Ler o texto melhorado como memória de turma. (5 min)

### Texto
O texto do colega é apresentado como produção valorizada e melhorada pela turma, mantendo respeito pela experiência familiar/religiosa.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "leitura_guiada",
    "type": "toggle",
    "options": [
      "Escutar",
      "Ler em eco"
    ],
    "default": "Escutar"
  }
]
```

**Render:** Cartão grande com o texto, palavras-chave destacáveis e modo eco para leitura em grupo.

**Transition:** Seleccionar palavras-chave ou modo de leitura muda o destaque visual.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Um texto fica mais fácil de compreender quando sabemos de quem fala, quando aconteceu e onde aconteceu.

**Assessment (observável):** A criança aponta pelo menos uma palavra-chave do texto e diz o que ela ajuda a saber.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Adulto lê em voz alta e a criança escolhe entre dois cartões visuais.
- 🟡 **Intermédio:** 
- 🔴 **Desafio:** Criança explica por que razão essa informação ajuda o leitor.

## Unit 2: Encontrar informação essencial no texto. (10 min)

### Texto
As crianças fazem correspondência entre perguntas simples e excertos do texto.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "pares_pergunta_resposta",
    "type": "matching",
    "options": [
      "Quem?",
      "Quando?",
      "Onde?",
      "Quantas pessoas?",
      "O que fizeram?"
    ]
  }
]
```

**Render:** Cartões pergunta/resposta com feedback visual; alternativa por clique sem arrastar.

**Transition:** Clicar numa pergunta e depois num cartão de resposta cria um par; o sistema confirma e conta pistas.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Cada pergunta importante tem uma pista no texto; não precisamos inventar para responder.

**Assessment (observável):** A criança forma 4 pares correctos e justifica oralmente um deles.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Três pares com pictogramas e leitura pelo adulto.
- 🟡 **Intermédio:** 
- 🔴 **Desafio:** Criar uma pergunta nova que também tenha resposta no texto.

## Unit 3: Recontar respeitando a sequência. (8 min)

### Texto
Ordenar acontecimentos ajuda a recontar com clareza.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "ordem_acontecimentos",
    "type": "sorting",
    "options": [
      "Domingo à tarde",
      "Recebeu o Espírito Santo em casa",
      "Vieram seis pessoas",
      "Duas saloias cantaram e benzeram a casa",
      "O Senhor Pe. Vítor fez uma oração"
    ]
  }
]
```

**Render:** Linha do tempo simples com cartões grandes e numeração automática.

**Transition:** Mover/clicar cartões para a linha do tempo; confirmar revela feedback e frase de recontagem.

**Constraint (o aluno DESCOBRE — NÃO revelar):** O recontar fica claro quando mantém a ordem das ideias do texto.

**Assessment (observável):** A criança ordena pelo menos 4 acontecimentos e reconta em frase oral.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Usar só 3 cartões principais.
- 🟡 **Intermédio:** 
- 🔴 **Desafio:** Acrescentar uma frase de ligação: depois, também, no fim.

## Unit 4: Transformar a compreensão em plano Minecraft. (17 min)

### Texto
O Minecraft é usado para comunicar o texto, não para brincar sem objectivo: cada construção deve representar uma pista textual.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "plano_minecraft",
    "type": "quiz",
    "options": [
      "Casa do Pedro",
      "6 visitantes",
      "2 saloias",
      "Espaço de oração",
      "Legenda/placa"
    ]
  }
]
```

**Render:** Checklist cooperativa com contador de evidências: texto → bloco/elemento → legenda.

**Transition:** Clicar em cada evidência activa uma missão e desbloqueia uma frase de orientação para construir no Minecraft.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Uma boa construção comunica o texto quando cada elemento tem uma razão ligada a uma frase.

**Assessment (observável):** Grupo apresenta 3 elementos do mundo Minecraft e aponta a frase do texto que lhes deu origem.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Modelo de casa já iniciado; grupo escolhe e coloca placas/pessoas.
- 🟡 **Intermédio:** 
- 🔴 **Desafio:** Adicionar percurso de visita com setas e uma placa de boas-vindas escrita pelo grupo.

### Maker Challenge (minecraft)
- Desafio: Em grupos de 3-4, construir uma pequena cena respeitosa da visita do Espírito Santo à casa do Pedro: casa, seis visitantes, duas saloias, zona de oração e pelo menos três placas com palavras do texto.
- Materiais: Minecraft Education, mundo plano preparado, contas da escola, cartão de funções do grupo
- Grupo: 3-4
- Comunicação: Screenshot ou visita guiada: cada grupo diz “Construímos ___ porque no texto diz ___”.

## Unit 5: Comunicar e verificar aprendizagem. (5 min)

### Texto
A turma fecha com observação formativa e compromisso de melhoria.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "bilhete_saida",
    "type": "quiz",
    "options": [
      "Sei uma pista do texto",
      "Sei explicar uma construção",
      "Preciso de ajuda numa parte"
    ]
  }
]
```

**Render:** Bilhete de saída digital com três botões e caixa curta para frase oral/escrita do professor.

**Transition:** Escolha regista estado; feedback sugere próximo passo.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Aprendemos melhor quando conseguimos mostrar onde está a evidência no texto.

**Assessment (observável):** Cada criança/grupo comunica uma evidência textual e um elemento construído.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** Responder apontando ou escolhendo pictograma.
- 🟡 **Intermédio:** 
- 🔴 **Desafio:** Sugerir uma melhoria respeitosa para o texto ou para a construção.



## Secção Maker (🛠️ Desafios Maker)
Incluir secção visual com fundo verde:
- **Minecraft:** Em grupos de 3-4, construir uma pequena cena respeitosa da visita do Espírito Santo à casa do Pedro: casa, seis visitantes, duas saloias, zona de oração e pelo menos três placas com palavras do texto.


## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Português (1.º ano): Saber escutar para interagir, responder a questões, exprimir opinião, pedir a palavra e falar de forma clara e audível.
- Português (1.º ano): Desenvolver a compreensão de textos, escrever pequenos textos, rever e melhorar texto próprio ou de colega com apoio.
- Estudo do Meio (1.º ano): Valorizar situações do dia a dia e do contexto local; comunicar ideias por diferentes linguagens e usar TIC na apresentação de trabalhos.

### Perfil do Aluno
- PA-A: Linguagens e textos
- PA-B: Informação e comunicação
- PA-D: Pensamento crítico e pensamento criativo
- PA-E: Relacionamento interpessoal
- PA-F: Desenvolvimento pessoal e autonomia
- PA-H: Sensibilidade estética e artística
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

