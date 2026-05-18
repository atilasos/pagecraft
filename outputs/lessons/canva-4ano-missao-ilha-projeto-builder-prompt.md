# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Canva na escola — Missão Ilha do Projeto
- Ano: 9-10 anos (4.º ano do 1.º CEB)
- Duração: 45 minutos
- Objectivos: ["Entrar no Canva com a conta escolar @edu.madeira.gov.pt através da opção Microsoft/conta da escola, sem partilhar a palavra-passe.", "Criar uma apresentação nova a partir de um modelo ou de uma página em branco, escolhendo tema, título e sequência de diapositivos.", "Editar uma imagem para apoiar uma ideia: recortar/enquadrar, ajustar brilho/contraste e escrever uma legenda ou texto alternativo simples.", "Usar funcionalidades úteis para projetos: elementos/ícones, gráficos simples, notas do apresentador, comentários/colaboração e modo de apresentação.", "Descobrir que uma boa apresentação não é “muitos enfeites”: cada elemento deve ajudar o público a compreender o projeto."]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Entrada segura com conta Microsoft da escola (8 min)

### Texto
Os alunos ordenam os passos de entrada no Canva, reconhecendo que usam a conta escolar @edu.madeira.gov.pt e que a palavra-passe é pessoal.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "ordemLogin",
    "type": "interactive",
    "default": "por_iniciar"
  }
]
```

**Render:** Cartões clicáveis com passos de entrada e zona “A minha ordem”.

**Transition:** Clique/teclado nos cartões para construir a ordem; botão “Verificar”.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A conta da escola identifica o aluno e protege o trabalho; partilhar palavra-passe nunca é necessário para colaborar.

**Assessment (observável):** Aluno ordena os passos e explica uma regra de segurança.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: usa pistas visuais e trabalha com colega-tutor; pode escolher entre menos cartões.
- 🟡 **Intermédio:** 🟡 Intermédio: completa a tarefa principal com feedback e explica a escolha em voz alta.
- 🔴 **Desafio:** 🔴 Desafio: acrescenta uma justificação, melhora a clareza para o público e ajuda outro grupo sem fazer por ele.

## Unit 2: Criar uma apresentação com começo, meio e fim (12 min)

### Texto
Os alunos escolhem os diapositivos essenciais para iniciar uma apresentação de projeto: capa, pergunta, descoberta, evidência/imagem e conclusão.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "estruturaSlides",
    "type": "interactive",
    "default": "por_iniciar"
  }
]
```

**Render:** Cartões de diapositivos e pré-visualização numerada.

**Transition:** Seleção por clique; o sistema mostra progresso e feedback.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Uma apresentação clara tem sequência: não começa pelos detalhes nem termina sem uma ideia final.

**Assessment (observável):** Aluno monta uma sequência com pelo menos quatro diapositivos e justifica uma escolha.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: usa pistas visuais e trabalha com colega-tutor; pode escolher entre menos cartões.
- 🟡 **Intermédio:** 🟡 Intermédio: completa a tarefa principal com feedback e explica a escolha em voz alta.
- 🔴 **Desafio:** 🔴 Desafio: acrescenta uma justificação, melhora a clareza para o público e ajuda outro grupo sem fazer por ele.

## Unit 3: Editar uma imagem para explicar melhor (12 min)

### Texto
Os alunos simulam edição de imagem: enquadrar, ajustar brilho/contraste e escrever legenda/texto alternativo para tornar a informação compreensível.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "edicaoImagem",
    "type": "interactive",
    "default": "por_iniciar"
  }
]
```

**Render:** Imagem ilustrada local em CSS/SVG, controlos de zoom/brilho/contraste, campo de legenda.

**Transition:** Sliders e botões alteram a pré-visualização; guardar valida legenda.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Editar imagem não é só decorar: o enquadramento e a legenda devem tornar a ideia mais clara e respeitar a fonte/contexto.

**Assessment (observável):** Aluno melhora a imagem e escreve uma legenda informativa.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: usa pistas visuais e trabalha com colega-tutor; pode escolher entre menos cartões.
- 🟡 **Intermédio:** 🟡 Intermédio: completa a tarefa principal com feedback e explica a escolha em voz alta.
- 🔴 **Desafio:** 🔴 Desafio: acrescenta uma justificação, melhora a clareza para o público e ajuda outro grupo sem fazer por ele.

## Unit 4: Ferramentas úteis para apresentar projetos (10 min)

### Texto
Os alunos associam ferramentas do Canva a necessidades de projeto: modelos, elementos, gráficos, comentários, notas do apresentador e modo de apresentação.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "ferramentasProjeto",
    "type": "interactive",
    "default": "por_iniciar"
  }
]
```

**Render:** Cartões de ferramentas e desafios “Preciso de…”.

**Transition:** Matching por clique com feedback imediato.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A melhor ferramenta depende do problema de comunicação; nem todos os elementos decorativos melhoram a apresentação.

**Assessment (observável):** Aluno faz correspondências e verbaliza quando usaria uma ferramenta.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: usa pistas visuais e trabalha com colega-tutor; pode escolher entre menos cartões.
- 🟡 **Intermédio:** 🟡 Intermédio: completa a tarefa principal com feedback e explica a escolha em voz alta.
- 🔴 **Desafio:** 🔴 Desafio: acrescenta uma justificação, melhora a clareza para o público e ajuda outro grupo sem fazer por ele.




## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Português (4.º ano): Produzir discursos preparados para apresentação a público restrito; usar a escrita para informar, explicar e defender uma opinião pessoal.
- Estudo do Meio (4.º ano): Utilizar as TIC no desenvolvimento de pesquisas e na apresentação de trabalhos; relacionar objetos tecnológicos com a evolução da sociedade.
- TIC (1.º ciclo): Criar artefactos digitais criativos para exprimir ideias e conhecimentos; colaborar e partilhar produtos desenvolvidos em espaços preparados pela escola.

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
13. **Linguagem** — pt-PT (AO90), frases curtas, adequada a 9-10 anos (4.º ano do 1.º CEB)

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

