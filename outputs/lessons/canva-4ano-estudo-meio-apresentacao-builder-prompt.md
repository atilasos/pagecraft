# PageCraft Builder — Gerar página HTML interactiva

## Tarefa
Gera um ficheiro `page.html` com uma página de aula interactiva completa, self-contained.

## Tópico: Canva + Estudo do Meio — Apresentação em grupo
- Ano: 9-10 anos (4.º ano do 1.º CEB)
- Duração: 45 minutos
- Objectivos: ["Escolher, em grupo, um tema de Estudo do Meio do 4.º ano e transformá-lo numa pergunta de investigação clara.", "Planear uma apresentação curta no Canva com capa, pergunta, 2–3 descobertas com evidências e conclusão.", "Usar ferramentas básicas do Canva — modelos, texto, elementos/imagens, comentários/partilha e modo de apresentação — para comunicar melhor, não apenas para decorar.", "Colaborar com papéis definidos no grupo, respeitando a conta escolar, as fontes de informação e o tempo de palavra dos colegas.", "Preencher uma autoavaliação final que gera um ficheiro Markdown e uma mensagem de email para o professor."]

## Estrutura da página

1. **Header** com gradiente colorido, título, metadados (ano, duração), objectivos
2. **Units interactivas** (ver especificações abaixo)
3. **Secção Maker** (🛠️) com desafios maker em cards verdes
4. **Mini-avaliação** (📝) com 4-5 itens observáveis, fundo laranja
5. **Footer curricular** com AE e Perfil do Aluno, fundo roxo
6. **Footer** "Gerado por PageCraft 🛠️"


## Unit 1: Missão, segurança e papéis da equipa (5 min)

### Texto
Os alunos identificam a missão: criar uma pequena apresentação sobre um tema escolhido de Estudo do Meio e trabalhar com papéis de grupo.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "roles",
    "type": "multi-select",
    "default": []
  }
]
```

**Render:** Cartões de papéis — coordenador/a, investigador/a, designer, escritor/a, porta-voz — e regras de segurança digital.

**Transition:** Clique/teclado seleciona papéis e mostra responsabilidades; checklist desbloqueia a fase seguinte.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A equipa trabalha melhor quando cada aluno tem uma responsabilidade visível e ninguém partilha a palavra-passe.

**Assessment (observável):** Grupo escolhe papéis e confirma duas regras de segurança/respeito.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: escolher 3 papéis essenciais com cartões já explicados por ícones.
- 🟡 **Intermédio:** 🟡 Intermédio: distribuir papéis e dizer uma responsabilidade de cada um.
- 🔴 **Desafio:** 🔴 Desafio: acrescentar um papel de revisor/a de fontes e combinar como ajudar outro grupo sem fazer por ele.

## Unit 2: Do tema à pergunta de investigação (8 min)

### Texto
Os grupos escolhem um tema de Estudo do Meio e transformam o tema numa pergunta que pode ser respondida numa apresentação curta.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "theme",
    "type": "choice",
    "default": ""
  },
  {
    "name": "question",
    "type": "text",
    "default": ""
  }
]
```

**Render:** Galeria de temas possíveis e construtor de pergunta com modelo 'Como/Por que/Que mudanças…?'.

**Transition:** Selecionar tema → aparecem pistas; escrever pergunta → feedback de clareza e tamanho.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Um tema fica mais fácil de apresentar quando vira uma pergunta investigável, não apenas um título bonito.

**Assessment (observável):** Grupo regista um tema e uma pergunta com pelo menos uma palavra de investigação.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: escolher entre temas sugeridos e completar uma frase com lacunas.
- 🟡 **Intermédio:** 🟡 Intermédio: escrever pergunta própria e verificar se cabe em 5 diapositivos.
- 🔴 **Desafio:** 🔴 Desafio: formular uma pergunta que compare dois aspetos ou peça uma explicação com evidências.

## Unit 3: Roteiro de 5 diapositivos (10 min)

### Texto
Os alunos organizam a apresentação em cinco diapositivos: capa, pergunta, descoberta 1, descoberta 2/evidência e conclusão/convite ao público.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "slidePlan",
    "type": "sorting",
    "default": []
  }
]
```

**Render:** Cartões arrastáveis/clicáveis de diapositivos e pré-visualização numerada.

**Transition:** Tocar num cartão e depois numa posição; verificar mostra se há começo, meio e fim.

**Constraint (o aluno DESCOBRE — NÃO revelar):** Uma apresentação clara tem uma sequência: pergunta primeiro, evidências no meio e conclusão no fim.

**Assessment (observável):** Grupo monta uma sequência de 5 diapositivos e justifica uma escolha.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: usar modelo de 4 diapositivos com títulos prontos.
- 🟡 **Intermédio:** 🟡 Intermédio: completar 5 diapositivos com título curto para cada um.
- 🔴 **Desafio:** 🔴 Desafio: acrescentar uma pergunta para o público ou um dado comparativo no diapositivo de evidência.

## Unit 4: Canva: escolher a ferramenta certa (12 min)

### Texto
Os grupos consultam cartões visuais inspirados no fluxo do Canva para decidir quando usar modelos, texto, elementos/imagens, comentários, notas e apresentar.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "toolMatches",
    "type": "matching",
    "default": []
  }
]
```

**Render:** Mini-ecrãs ilustrados e desafios 'Preciso de…' para associar a ferramenta adequada.

**Transition:** Clique numa necessidade e depois numa ferramenta; feedback explica a decisão.

**Constraint (o aluno DESCOBRE — NÃO revelar):** No Canva, a ferramenta deve resolver um problema de comunicação; enfeites só ajudam quando tornam a ideia mais clara.

**Assessment (observável):** Grupo liga pelo menos quatro necessidades a ferramentas e aplica uma no seu trabalho real.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: trabalhar com quatro ferramentas principais — Modelo, Texto, Imagem/Elementos, Partilhar.
- 🟡 **Intermédio:** 🟡 Intermédio: escolher seis ferramentas e justificar uma escolha para o tema.
- 🔴 **Desafio:** 🔴 Desafio: usar comentários ou notas do apresentador para preparar a comunicação oral.

## Unit 5: Revisão rápida e autoavaliação Markdown (10 min)

### Texto
Os alunos verificam se a apresentação comunica o tema de Estudo do Meio e preenchem uma autoavaliação que gera ficheiro Markdown/email.

### SRTC-A (Interaction Specification)

**State variables:**
```json
[
  {
    "name": "selfAssessment",
    "type": "form",
    "default": {}
  }
]
```

**Render:** Checklist de revisão, campos do grupo, tema, contributo e escala de autonomia; pré-visualização Markdown.

**Transition:** Preencher formulário → gerar Markdown → copiar, descarregar ficheiro .md ou abrir email para o professor.

**Constraint (o aluno DESCOBRE — NÃO revelar):** A autoavaliação só é útil quando descreve evidências do trabalho e uma próxima melhoria, não apenas 'correu bem'.

**Assessment (observável):** Cada grupo gera um Markdown com tema, papéis, evidências, nível de autonomia e próxima melhoria.

### Diferenciação (implementar como tabs seleccionáveis)

- 🟢 **Apoio:** 🟢 Apoio: selecionar frases de evidência já sugeridas e escrever uma melhoria curta.
- 🟡 **Intermédio:** 🟡 Intermédio: escrever uma evidência própria e uma melhoria realista.
- 🔴 **Desafio:** 🔴 Desafio: comparar o produto final com o plano inicial e indicar uma decisão de design que ajudou a comunicar melhor.




## Mini-avaliação (📝)
Gerar 4-5 perguntas/desafios observáveis baseados nos Assessment de cada unit.
Incluir escala: ⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas

## Referências curriculares (footer)
### Aprendizagens Essenciais
- Estudo do Meio (4.º ano): Pesquisar e partilhar informação sobre temáticas de interesse do aluno ou relacionadas com os temas em estudo, comunicando aprendizagens com recurso às TIC.
- Estudo do Meio (4.º ano): Utilizar as tecnologias de informação e comunicação com segurança, respeito e responsabilidade; reconhecer que o conhecimento se constrói colocando questões, levantando hipóteses, comprovando resultados e comunicando-os.
- Português (4.º ano): Planear, produzir e avaliar discursos orais breves, individualmente ou em grupo, e selecionar informação relevante para uma finalidade comunicativa.

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

