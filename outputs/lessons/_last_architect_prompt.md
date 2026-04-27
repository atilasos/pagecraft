# Tarefa: Gerar DocSpec-AM para PageCraft

## Tópico
Texto melhorado: O Pedro recebeu o Espírito Santo

## Contexto
- Ano: 1.º ano (6-7 anos)
- Duração: 45 minutos
- Ciclo: 1.º ciclo

## Instruções

Gera um DocSpec-AM completo em JSON válido para o tópico acima.

### Requisitos obrigatórios:
1. Consulta as Aprendizagens Essenciais abaixo e referencia descritores específicos
2. Mapeia para áreas de competência do Perfil do Aluno (PA-A a PA-J)
3. Alinha com módulos MEM (TEA, projecto cooperativo, comunicação, conselho)
4. Cada knowledge unit tem SRTC-A completo (State, Render, Transition, Constraint, Assessment)
5. Diferenciação obrigatória em 3 níveis (apoio/intermédio/desafio)
6. Linguagem adequada à faixa etária: 6-7 anos
7. O Constraint (C) é algo que o aluno DESCOBRE, não que lhe é dito
8. O Assessment (A) é observável: o que o aluno FAZ/DIZ/PRODUZ
9. Duration total das units deve somar ≤ 45 minutos
10. Incluir sessionFlow descrevendo o encadeamento temporal

### Interaction Patterns disponíveis:
# Interaction Patterns — PageCraft

Biblioteca de patterns reutilizáveis para interacções pedagógicas. Cada pattern inclui SRTC-A template.

## slider

Exploração de parâmetros contínuos.

**Quando usar:** O aluno precisa observar como uma variável afecta um resultado.

```yaml
S: { var: "velocidade", type: "slider", range: [1, 20], step: 1, default: 5 }
R: "Carro animado cuja velocidade reflecte o valor; label mostra km/h"
T: "Arrastar slider → velocidade actualiza → animação acelera/desacelera"
C: "Quanto maior a velocidade, menor o tempo para percorrer a mesma distância"
A: "O aluno ajusta o slider para fazer o carro chegar em exactamente 10 segundos"
```

**Adaptação por idade:**
- 🟢 Apoio (4-6): range pequeno [1,5], feedback visual exagerado (cores, sons)
- 🟡 Intermédio (7-8): range médio, label numérico visível
- 🔴 Desafio (9-10): range largo, cálculo mental envolvido

---

## dropdown

Selecção de opções discretas.

**Quando usar:** O aluno escolhe entre categorias/opções e observa o efeito.

```yaml
S: { var: "estacao", type: "dropdown", options: ["Primavera","Verão","Outono","Inverno"], default: "Primavera" }
R: "Paisagem ilustrada que muda conforme a estação; árvore central muda folhagem"
T: "Seleccionar estação → paisagem actualiza com transição suave"
C: "Cada estação tem características visuais distintas (cores, folhas, clima)"
A: "O aluno identifica a estação correcta a partir de uma descrição"
```

---

## drag

Manipulação directa de elementos.

**Quando usar:** O aluno precisa organizar, mover ou posicionar elementos.

```yaml
S: { var: "posicao_planeta", type: "drag", targets: ["orbita1","orbita2","orbita3"] }
R: "Sistema solar simplificado; planetas arrastáveis para órbitas"
T: "Arrastar planeta → encaixa na órbita mais próxima → label actualiza"
C: "Os planetas têm órbitas específicas ordenadas por distância ao Sol"
A: "O aluno coloca 3 planetas nas órbitas correctas"
```

---

## toggle

Alternância entre dois modos/estados.

**Quando usar:** Comparação directa entre duas condições (dia/noite, com/sem, antes/depois).

```yaml
S: { var: "modo", type: "toggle", options: ["Dia","Noite"], default: "Dia" }
R: "Cena com céu, sol/lua, animais diurnos/nocturnos"
T: "Clicar toggle → transição animada dia↔noite"
C: "Animais diferentes estão activos de dia e de noite"
A: "O aluno classifica 4 animais como diurnos ou nocturnos"
```

---

## quiz-inline

Pergunta integrada no fluxo da exploração.

**Quando usar:** Verificação de compreensão no momento, sem interromper a experiência.

```yaml
S: { var: "resposta", type: "quiz", question: "Quantas patas tem o insecto?", options: [4,6,8], correct: 6 }
R: "Pergunta aparece após exploração; feedback visual imediato (✓/✗ com cor)"
T: "Seleccionar opção → feedback instantâneo → explicação breve se errado"
C: "Insectos têm sempre 6 patas"
A: "O aluno responde correctamente ou lê a explicação e corrige"
```

---

## sorting

Ordenação por arrasto.

**Quando usar:** O aluno precisa sequenciar ou ordenar elementos (cronologia, tamanho, etc.).

```yaml
S: { var: "ordem", type: "sorting", items: ["ovo","larva","casulo","borboleta"], correct_order: [0,1,2,3] }
R: "Cards arrastáveis com imagens; zona de ordenação horizontal"
T: "Arrastar cards → reordenar → feedback quando ordem correcta"
C: "O ciclo de vida da borboleta segue uma sequência fixa"
A: "O aluno ordena as 4 fases correctamente"
```

---

## matching

Correspondência entre pares (ligar).

**Quando usar:** Associar conceitos, vocabulário, imagens a descrições.

```yaml
S: { var: "pares", type: "matching", left: ["🐶","🐱","🐰"], right: ["ladra","mia","salta"], correct: [[0,0],[1,1],[2,2]] }
R: "Duas colunas; linhas desenhadas quando o aluno liga pares"
T: "Clicar item esquerdo → clicar item direito → linha aparece; reset se errado"
C: "Cada animal tem um comportamento característico"
A: "O aluno liga correctamente os 3 pares"
```

---

## canvas-draw

Desenho livre ou guiado em canvas HTML5.

**Quando usar:** Expressão criativa, desenho de formas geométricas, escrita.

```yaml
S: { var: "desenho", type: "canvas", tools: ["lápis","borracha"], colors: ["preto","vermelho","azul"] }
R: "Canvas branco com barra de ferramentas simples; área de desenho responsiva"
T: "Tocar/arrastar → desenha; seleccionar ferramenta/cor → muda modo"
C: "Formas geométricas têm propriedades específicas (lados, ângulos)"
A: "O aluno desenha um triângulo com 3 lados rectos"
```



## Extensões Maker
Recursos disponíveis: whiteboard
Incluir maker challenges adequados para cada knowledge unit (ou para as units onde faz sentido).
Cada maker challenge deve ter: type, challenge, materials, groupSize, connection, communication, alternatives.

# Maker Patterns — PageCraft

Biblioteca de extensões Maker que ligam a exploração digital ao mundo tangível.
Cada pattern define como um recurso físico estende uma knowledge unit da página interactiva.

## Princípio

A página interactiva é o **ponto de partida**, não o fim. O ciclo completo:

```
1. Explorar (página interactiva — individual/pares)
2. Construir (desafio maker — grupo 2-4)
3. Comunicar (apresentação — circuito MEM)
4. Reflectir (conselho de cooperação)
```

## Recursos disponíveis

| Recurso | Tipo | Contexto |
|---|---|---|
| Minecraft Education | Digital/3D | Construção, simulação, escala, exploração espacial |
| Lego / Lego Technic | Físico | Estruturas, mecanismos, contagem, padrões |
| Impressão 3D | Digital→Físico | Prototipagem, formas geométricas, design |
| Robótica (robot educativo) | Físico/Programação | Sequências, ciclos, sensores, movimento |
| Quadro interactivo | Digital/Colectivo | Apresentação, manipulação colectiva, votação |
| Computadores/tablets | Digital | Exploração individual, pesquisa, produção |

---

## minecraft

**Quando usar:** Tópicos que envolvem espaço, escala, construção, simulação de ambientes, geografia.

### Templates de desafio

#### Construção com restrições
```yaml
maker:
  type: minecraft
  challenge: "Constrói uma casa com exactamente {X} blocos de largura e {Y} de altura. Calcula a área da fachada."
  materials: ["Minecraft Education Edition", "conta escola"]
  groupSize: 2
  connection: "O slider da página controla as dimensões → o aluno replica no Minecraft"
  mem_module: "projecto cooperativo"
  communication: "Screenshot + apresentação no quadro: 'A nossa casa tem área de...'"
```

#### Simulação de ambientes
```yaml
maker:
  type: minecraft
  challenge: "Reconstrói o ciclo da água: rio → evaporação → nuvem → chuva. Usa blocos azuis, brancos e transparentes."
  materials: ["Minecraft Education Edition"]
  groupSize: 3-4
  connection: "Depois de explorar o ciclo na página (toggle entre fases), construir no Minecraft"
  mem_module: "projecto cooperativo"
  communication: "Visita guiada ao mundo Minecraft da turma"
```

#### Escala e proporção
```yaml
maker:
  type: minecraft
  challenge: "O sistema solar: se o Sol tem 10 blocos de diâmetro, quantos blocos tem a Terra? E Júpiter?"
  materials: ["Minecraft Education Edition", "tabela de proporções (da página)"]
  groupSize: 2-3
  connection: "Slider da página mostra proporções → aluno calcula e constrói"
```

---

## lego

**Quando usar:** Tópicos que envolvem contagem, padrões, estruturas, mecanismos, classificação.

### Templates de desafio

#### Padrões e sequências
```yaml
maker:
  type: lego
  challenge: "Cria um padrão com 3 cores que se repete 4 vezes. Quantas peças usaste no total?"
  materials: ["Peças Lego variadas (mínimo 3 cores)"]
  groupSize: 2
  connection: "Página mostra padrões com sorting → aluno replica com Lego"
  mem_module: "TEA + comunicação"
  communication: "Expõe o padrão e explica a regra à turma"
```

#### Frações concretas
```yaml
maker:
  type: lego
  challenge: "Constrói uma barra com 12 peças. Separa em 1/2, 1/3 e 1/4. Quantas peças em cada parte?"
  materials: ["Peças Lego (mínimo 12 iguais por grupo)"]
  groupSize: 2
  connection: "Slider da página divide visualmente → aluno divide fisicamente"
```

#### Estruturas e resistência
```yaml
maker:
  type: lego
  challenge: "Constrói a ponte mais comprida que conseguires que aguente um lápis. Mede o comprimento."
  materials: ["Peças Lego Technic", "lápis para teste", "régua"]
  groupSize: 3-4
  connection: "Página explora formas resistentes (triângulo vs quadrado) → aluno testa"
```

---

## 3d-print

**Quando usar:** Tópicos que envolvem formas geométricas, design, prototipagem, visualização de objectos 3D.

### Templates de desafio

#### Formas geométricas
```yaml
maker:
  type: 3d-print
  challenge: "Desenha no TinkerCAD um sólido geométrico à tua escolha. Identifica faces, arestas e vértices."
  materials: ["TinkerCAD (browser)", "impressora 3D"]
  groupSize: 2
  connection: "Canvas-draw na página → modelação 3D → impressão → manipulação"
  mem_module: "projecto cooperativo"
  communication: "Exposição de sólidos impressos com ficha técnica"
```

#### Design funcional
```yaml
maker:
  type: 3d-print
  challenge: "Desenha um porta-lápis para a tua mesa. Tem de ter pelo menos 3 compartimentos de tamanhos diferentes."
  materials: ["TinkerCAD", "impressora 3D", "régua"]
  groupSize: 2
  connection: "Página explora medidas e proporções → aluno aplica no design"
```

#### Relevo e mapas
```yaml
maker:
  type: 3d-print
  challenge: "Modela a ilha da Madeira em 3D. Marca o pico mais alto e o teu concelho."
  materials: ["TinkerCAD ou Cura", "impressora 3D", "mapa topográfico (da página)"]
  groupSize: 3-4
  connection: "Página mostra mapa interactivo com altitudes → aluno traduz para 3D"
```

---

## robotics

**Quando usar:** Tópicos que envolvem sequências, algoritmos, causa-efeito, medição, movimento.

### Templates de desafio

#### Sequências e algoritmos
```yaml
maker:
  type: robotics
  challenge: "Programa o robot para percorrer o ciclo de vida da borboleta: ovo → larva → casulo → borboleta (4 estações marcadas no chão)"
  materials: ["Robot educativo (Bee-Bot/Blue-Bot/mBot)", "tapete com estações"]
  groupSize: 2-3
  connection: "Sorting na página (ordenar fases) → programar sequência no robot"
  mem_module: "projecto cooperativo"
  communication: "Demonstração ao vivo para a turma"
```

#### Medição e comparação
```yaml
maker:
  type: robotics
  challenge: "Faz o robot percorrer 50cm, 1m e 2m. Mede o tempo de cada percurso. O que descobres?"
  materials: ["Robot educativo", "fita métrica", "cronómetro"]
  groupSize: 2
  connection: "Slider da página explora velocidade/distância → aluno verifica com robot"
```

#### Sensores e condições
```yaml
maker:
  type: robotics
  challenge: "Programa o robot para parar quando detectar um obstáculo. Testa com objectos a diferentes distâncias."
  materials: ["mBot com sensor ultrassónico", "objectos variados"]
  groupSize: 2-3
  connection: "Toggle na página (com obstáculo / sem obstáculo) → aluno replica no mundo real"
```

---

## whiteboard

**Quando usar:** Momento de comunicação colectiva — apresentação, discussão, votação, síntese.

### Templates

#### Apresentação de descoberta
```yaml
maker:
  type: whiteboard
  challenge: "Apresenta à turma o que descobriste. Mostra a página no quadro e explica o que acontece quando moves o slider."
  materials: ["Quadro interactivo", "página PageCraft"]
  groupSize: 1-2 (apresentadores) + turma
  connection: "Exploração individual → comunicação colectiva"
  mem_module: "circuitos de comunicação"
```

#### Síntese colectiva
```yaml
maker:
  type: whiteboard
  challenge: "Em turma, completem o mapa de conceitos no quadro. Cada grupo adiciona o que aprendeu."
  materials: ["Quadro interactivo", "template de mapa de conceitos"]
  groupSize: turma
  connection: "Cada grupo traz a sua descoberta (constraint C) → turma constrói mapa completo"
  mem_module: "trabalho curricular comparticipado"
```

---

## Alinhamento MEM

| Módulo MEM | Momento PageCraft | Recurso típico |
|---|---|---|
| **TEA** (Trabalho Estudo Autónomo) | Exploração individual na página | Tablet/computador |
| **Projecto cooperativo** | Desafio maker em grupo | Minecraft/Lego/3D/Robot |
| **Trabalho curricular comparticipado** | Síntese colectiva | Quadro interactivo |
| **Circuitos de comunicação** | Apresentação de descobertas | Quadro interactivo + produções |
| **Conselho de cooperação** | Reflexão: "O que aprendemos? O que correu bem/mal?" | Diário de turma |

## Regras

1. O desafio maker é **sempre opcional** — a página funciona sozinha
2. Cada desafio indica **groupSize** — nunca individual (construção social)
3. Cada desafio tem **connection** — liga explicitamente ao digital
4. Cada desafio culmina em **comunicação** — nunca fica só no grupo
5. Materiais devem ser **acessíveis** — indicar alternativas quando possível



## Aprendizagens Essenciais relevantes:
### estudo-do-meio-1-ano-1-ciclo
---
title: "AE – Estudo do Meio – 1.º Ano"
disciplina: "Estudo do Meio"
ciclo: "1.º Ciclo"
ano: "1.º Ano"
fonte: "https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/1_estudo_do_meio.pdf"
tipo: "aprendizagens-essenciais"
nivel: "ensino-basico"
data_ingestao: "2026-03-03"
tags:
  - aprendizagens-essenciais
  - dge
  - estudo-do-meio
  - 1-ciclo
---
# Aprendizagens Essenciais – Estudo do Meio – 1.º Ano (1.º Ciclo)

> Fonte: [1_estudo_do_meio.pdf](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/1_estudo_do_meio.pdf)

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
JULHO DE 2018 
 
 
 
 
 
 
 
 
 
 
1.º ANO | 1.º CICLO DO ENSINO BÁSICO 
ESTUDO DO MEIO 
INTRODUÇÃO 
As Aprendizagens Essenciais (AE) de Estudo do Meio visam desenvolver um conjunto de competências de diferentes áreas do 
saber, nomeadamente Biologia, Física, Geografia, Geologia, História, Química e Tecnologia. 
Considerando que o Estudo do Meio tem um vasto objeto de estudo, a sua abordagem alicerça-se em conceitos e métodos das 
várias disciplinas enunciadas, contribuindo para a compreensão progressiva da Sociedade, da Natureza e da Tecnologia, bem 
como das inter-relações entre estes domínios. Nesta perspetiva, organizaram-se as presentes AE tendo por base as três áreas 
Ciência-Tecnologia-Sociedade (CTS).

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
1.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 2 
O documento AE estrutura-se de acordo com os domínios mencionados, sendo que, em cada um são identificados os 
conhecimentos a adquirir, as capacidades e as atitudes a desenvolver indispensáveis, relevantes e significativos. Também são 
indicadas, a título exemplificativo, ações estratégicas de ensino orientadas para as áreas de competências definidas no Perfil 
dos Alunos à Saída da Escolaridade Obrigatória (PA). 
Assim, ao longo do 1.º ciclo do ensino básico, o aluno deve: 
a) Adquirir um conhecimento de si próprio, desenvolvendo atitudes de autoestima e de autoconfiança; 
b) Valorizar a sua identidade e raízes, respeitando o território e o seu ordenamento, outros povos e outras culturas, 
reconhecendo a diversidade como fonte de aprendizagem para todos; 
c) Identificar elementos naturais, sociais e tecnológicos do meio envolvente e suas inter-relações;  
d) Identificar acontecimentos relacionados com a história pessoal e familiar, local e nacional, localizando-os no espaço e 
no tempo, utilizando diferentes representações cartográficas e unidades de referência temporal; 
e) Utilizar processos científicos simples na realização de atividades experimentais; 
f) Reconhecer o contributo da ciência para o progresso tecnológico e para a melhoria da qualidade de vida; 
g) Manipular, imaginar, criar ou transformar objetos técnicos simples; 
h) Mobilizar saberes culturais, científicos e tecnológicos para compreender a realidade e para resolver situações e 
problemas do quotidiano; 
i) Assumir atitudes e valores que promovam uma participação cívica de forma responsável, solidária e crítica; 
j) Utilizar as Tecnologias de Informação e Comunicação no desenvolvimento de pesquisas e na apresentação de trabalhos; 
k) Comunicar adequadamente as suas ideias, através da utilização de diferentes linguagens (oral, escrita, iconográfica, 
gráfica, matemática, cartográfica, etc.), fundamentando-as e argumentando face às ideias dos outros. 
Ao iniciar a escolaridade obrigatória, a criança já vivenciou um conjunto de experiências nos diversos contextos em que esteve 
inserida. A assunção desta realidade significa que a criança traz para a escola ideias, representações e preconceções 
referentes ao Meio Social, Natural e à Tecnologia, fruto da interação com os pares ou adultos que com ela convivem e da 
exploração dos espaços, dos objetos e dos materiais, conhecimento que importa aprofundar e estruturar.

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
1.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 3 
A operacionalização das aprendizagens do Estudo do Meio implica a contextualização dos temas a tratar. Para tal, considera-se 
importante que os professores conheçam os contextos locais, que identifiquem situações a partir das quais possam emergir 
questões-problema que sirvam de base para as aprendizagens a realizar e considerem as aprendizagens previstas nas áreas de 
conteúdo “Formação Pessoal e Social” e “Conhecimento do Mundo” das Orientações Curriculares para a Educação Pré-Escolar 
(ME, 2016), privilegiando-se a consolidação de processos de transição entre a educação pré-escolar e o 1.º ciclo. As AE de 
Estudo do Meio estão associadas a dinâmicas interdisciplinares pela natureza dos temas e conteúdos abrangidos, pelo que a 
articulação destes saberes com outros, de outras componentes do currículo, potencia a construção de novas aprendizagens. 
No processo de ensino, devem ser implementadas as ações estratégicas que melhor promovam o desenvolvimento das AE 
explicitadas neste documento. Neste sentido, revela-se importante: 
a) Centrar os processos de ensino nos alunos, enquanto agentes ativos na construção do seu próprio conhecimento; 
b) Tomar como referência o conhecimento prévio dos alunos, os seus interesses e necessidades, valorizando situações do 
dia a dia e questões de âmbito local, enquanto instrumentos facilitadores da aprendizagem; 
c) Privilegiar atividades práticas como parte integrante e fundamental do processo de aprendizagem; 
d) Promover uma abordagem integradora dos conhecimentos, valorizando a compreensão e a interpretação dos processos 
naturais, sociais e tecnológicos, numa perspetiva Ciência-Tecnologia-Sociedade-Ambiente (CTSA); 
e) Valorizar a natureza da Ciência, dando continuidade ao desenvolvimento da metodologia científica nas suas diferentes 
etapas. 
A gestão deste documento deve promover uma abordagem interdisciplinar, respeitando os temas e o respetivo 
desenvolvimento e ter em conta a atualidade dos assuntos, os interesses e as características dos alunos, ou ainda questões de 
âmbito local.

---

### estudo-do-meio-2-ano-1-ciclo
---
title: "AE – Estudo do Meio – 2.º Ano"
disciplina: "Estudo do Meio"
ciclo: "1.º Ciclo"
ano: "2.º Ano"
fonte: "https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/2_estudo_do_meio.pdf"
tipo: "aprendizagens-essenciais"
nivel: "ensino-basico"
data_ingestao: "2026-03-03"
tags:
  - aprendizagens-essenciais
  - dge
  - estudo-do-meio
  - 1-ciclo
---
# Aprendizagens Essenciais – Estudo do Meio – 2.º Ano (1.º Ciclo)

> Fonte: [2_estudo_do_meio.pdf](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/2_estudo_do_meio.pdf)

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
JULHO DE 2018 
 
 
 
 
 
 
 
 
 
2.º ANO | 1.º CICLO DO ENSINO BÁSICO 
ESTUDO DO MEIO 
INTRODUÇÃO 
As Aprendizagens Essenciais (AE) de Estudo do Meio visam desenvolver um conjunto de competências de diferentes áreas do 
saber, nomeadamente Biologia, Física, Geografia, Geologia, História, Química e Tecnologia. 
Considerando que o Estudo do Meio tem um vasto objeto de estudo, a sua abordagem alicerça-se em conceitos e métodos das 
várias disciplinas enunciadas, contribuindo para a compreensão progressiva da Sociedade, da Natureza e da Tecnologia, bem 
como das inter-relações entre estes domínios. Nesta perspetiva, organizaram-se as presentes AE tendo por base as três áreas 
Ciência-Tecnologia-Sociedade (CTS).

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
2.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 2 
O documento AE estrutura-se de acordo com os domínios mencionados, sendo que, em cada um são identificados os 
conhecimentos a adquirir, as capacidades e as atitudes a desenvolver indispensáveis, relevantes e significativos. Também são 
indicadas, a título exemplificativo, ações estratégicas de ensino orientadas para as áreas de competências definidas no Perfil 
dos Alunos à Saída da Escolaridade Obrigatória (PA). 
Assim, ao longo do 1.º ciclo do ensino básico, o aluno deve: 
a) Adquirir um conhecimento de si próprio, desenvolvendo atitudes de autoestima e de autoconfiança;  
b) Valorizar a sua identidade e raízes, respeitando o território e o seu ordenamento, outros povos e outras culturas, 
reconhecendo a diversidade como fonte de aprendizagem para todos; 
c) Identificar elementos naturais, sociais e tecnológicos do meio envolvente e suas inter-relações;  
d) Identificar acontecimentos relacionados com a história pessoal e familiar, local e nacional, localizando-os no espaço e 
no tempo, utilizando diferentes representações cartográficas e unidades de referência temporal; 
e) Utilizar processos científicos simples na realização de atividades experimentais; 
f) Reconhecer o contributo da ciência para o progresso tecnológico e para a melhoria da qualidade de vida;  
g) Manipular, imaginar, criar ou transformar objetos técnicos simples; 
h) Mobilizar saberes culturais, científicos e tecnológicos para compreender a realidade e para resolver situações e 
problemas do quotidiano; 
i) Assumir atitudes e valores que promovam uma participação cívica de forma responsável, solidária e crítica; 
j) Utilizar as Tecnologias de Informação e Comunicação no desenvolvimento de pesquisas e na apresentação de trabalhos; 
k) Comunicar adequadamente as suas ideias, através da utilização de diferentes linguagens (oral, escrita, iconográfica, 
gráfica, matemática, cartográfica,etc.), fundamentando-as e argumentando face às ideias dos outros.

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
2.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 3 
No 2.º ano de escolaridade são trabalhados conteúdos relacionados com o conhecimento de si próprio, dos outros e das 
instituições, do ambiente natural, do seu território de vivência, do tempo histórico pessoal, dos materiais e objetos e das 
inter-relações entre espaços. Neste ano de escolaridade optou-se por dar continuidade às temáticas previstas para o 1.º ano, 
sendo que algumas aprendizagens apresentam um grau de complexidade superior. 
A operacionalização das aprendizagens do Estudo do Meio implica a contextualização dos temas a tratar. Para tal, considera-se 
importante que os professores conheçam os contextos locais, e que identifiquem situações a partir das quais possam emergir 
questões-problema que sirvam de base para as aprendizagens a realizar. As AE de Estudo do Meio estão associadas a dinâmicas 
interdisciplinares pela natureza dos temas e conteúdos abrangidos, pelo que a articulação destes saberes com outros, de outras 
componentes do currículo, potencia a construção de novas aprendizagens. 
No processo de ensino, devem ser implementadas as ações estratégicas que melhor promovam o desenvolvimento das AE 
explicitadas neste documento. Neste sentido, revela-se importante: 
a) Centrar os processos de ensino nos alunos, enquanto agentes ativos na construção do seu próprio conhecimento; 
b) Tomar como referência o conhecimento prévio dos alunos, os seus interesses e necessidades, valorizando situações do 
dia a dia e questões de âmbito local, enquanto instrumentos facilitadores da aprendizagem; 
c) Privilegiar atividades práticas como parte integrante e fundamental do processo de aprendizagem; 
d) Promover uma abordagem integradora dos conhecimentos, valorizando a compreensão e a interpretação dos processos 
naturais, sociais e tecnológicos, numa perspetiva Ciência-Tecnologia-Sociedade-Ambiente (CTSA); 
e) Valorizar a natureza da Ciência, dando continuidade ao desenvolvimento da metodologia científica nas suas diferentes 
etapas.  
A gestão deste documento deve promover uma abordagem interdisciplinar, respeitando os temas e o respetivo 
desenvolvimento e ter em conta a atualidade dos assuntos, os interesses e as características dos alunos, ou ainda questões de 
âmbito local.

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
2.º ANO | 1.º CICLO | ESTUDO DO MEIO

### estudo-do-meio-3-ano-1-ciclo
---
title: "AE – Estudo do Meio – 3.º Ano"
disciplina: "Estudo do Meio"
ciclo: "1.º Ciclo"
ano: "3.º Ano"
fonte: "https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/3_estudo_do_meio.pdf"
tipo: "aprendizagens-essenciais"
nivel: "ensino-basico"
data_ingestao: "2026-03-03"
tags:
  - aprendizagens-essenciais
  - dge
  - estudo-do-meio
  - 1-ciclo
---
# Aprendizagens Essenciais – Estudo do Meio – 3.º Ano (1.º Ciclo)

> Fonte: [3_estudo_do_meio.pdf](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/3_estudo_do_meio.pdf)

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
JULHO DE 2018 
 
 
 
 
 
 
 
 
3.º ANO | 1.º CICLO DO ENSINO BÁSICO 
ESTUDO DO MEIO 
INTRODUÇÃO 
As Aprendizagens Essenciais (AE) de Estudo do Meio visam desenvolver um conjunto de competências de diferentes áreas do 
saber, nomeadamente Biologia, Física, Geografia, Geologia, História, Química e Tecnologia. 
Considerando que o Estudo do Meio tem um vasto objeto de estudo, a sua abordagem alicerça-se em conceitos e métodos das 
várias disciplinas enunciadas, contribuindo para a compreensão progressiva da Sociedade, da Natureza e da Tecnologia, bem 
como das inter-relações entre estes domínios. Nesta perspetiva, organizaram-se as presentes AE tendo por base as três áreas 
Ciência-Tecnologia-Sociedade (CTS). 
O documento AE estrutura-se de acordo com os domínios mencionados, sendo que, em cada um são identificados os 
conhecimentos a adquirir, as capacidades e as atitudes a desenvolver indispensáveis, relevantes e significativos. Também são

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
3.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 2 
indicadas, a título exemplificativo, ações estratégicas de ensino orientadas para as áreas de competências definidas no Perfil 
dos Alunos à Saída da Escolaridade Obrigatória (PA). 
Assim, ao longo do 1.º ciclo do ensino básico, o aluno deve: 
a) Adquirir um conhecimento de si próprio, desenvolvendo atitudes de autoestima e de autoconfiança;  
b) Valorizar a sua identidade e raízes, respeitando o território e o seu ordenamento, outros povos e outras culturas, 
reconhecendo a diversidade como fonte de aprendizagem para todos; 
c) Identificar elementos naturais, sociais e tecnológicos do meio envolvente e suas inter-relações;  
d) Identificar acontecimentos relacionados com a história pessoal e familiar, local e nacional, localizando-os no espaço e 
no tempo, utilizando diferentes representações cartográficas e unidades de referência temporal; 
e) Utilizar processos científicos simples na realização de atividades experimentais; 
f) Reconhecer o contributo da ciência para o progresso tecnológico e para a melhoria da qualidade de vida;  
g) Manipular, imaginar, criar ou transformar objetos técnicos simples; 
h) Mobilizar saberes culturais, científicos e tecnológicos para compreender a realidade e para resolver situações e 
problemas do quotidiano; 
i) Assumir atitudes e valores que promovam uma participação cívica de forma responsável, solidária e crítica; 
j) Utilizar as Tecnologias de Informação e Comunicação no desenvolvimento de pesquisas e na apresentação de trabalhos; 
k) Comunicar adequadamente as suas ideias, através da utilização de diferentes linguagens (oral, escrita, iconográfica, 
gráfica, matemática, cartográfica, etc.), fundamentando-as e argumentando face às ideias dos outros. 
No 3.º ano de escolaridade dá-se continuidade a algumas das temáticas propostas para os 1.º e 2.º anos, apresentando as 
aprendizagens um maior grau de complexidade. Houve, também, a preocupação de integrar temas atuais, como as questões 
ambientais e sociais, a importância dos media e os Direitos da Criança. Neste ano de escolaridade, privilegia-se ainda o 
aprofundamento do ensino experimental das ciências e das produções/utilizações tecnológicas.

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
3.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 3 
A operacionalização das aprendizagens do Estudo do Meio implica a contextualização dos temas a tratar. Para tal, considera-se 
importante que os professores conheçam os contextos locais, e que identifiquem situações a partir das quais possam emergir 
questões-problema que sirvam de base para as aprendizagens a realizar. As AE de Estudo do Meio estão associadas a dinâmicas 
interdisciplinares pela natureza dos temas e conteúdos abrangidos, pelo que a articulação destes saberes com outros, de outras 
componentes do currículo, potencia a construção de novas aprendizagens. 
No processo de ensino, devem ser implementadas as ações estratégicas que melhor promovam o desenvolvimento das AE 
explicitadas neste documento. Neste sentido, revela-se importante: 
a) Centrar os processos de ensino nos alunos, enquanto agentes ativos na construção do seu próprio conhecimento; 
b) Tomar como referência o conhecimento prévio dos alunos, os seus interesses e necessidades, valorizando situações do 
dia a dia e questões de âmbito local, enquanto instrumentos facilitadores da aprendizagem; 
c) Privilegiar atividades práticas como parte integrante e fundamental do processo de aprendizagem; 
d) Promover uma abordagem integradora dos conhecimentos, valorizando a compreensão e a interpretação dos processos 
naturais, sociais e tecnológicos, numa perspetiva Ciência-Tecnologia-Sociedade-Ambiente (CTSA); 
e) Valorizar a natureza da Ciência, dando continuidade ao desenvolvimento da metodologia científica nas suas diferentes 
etapas.  
A gestão deste documento deve promover uma abordagem interdisciplinar, respeitando os temas e o respetivo 
desenvolvimento e ter em conta a atualidade dos assuntos, os interesses e as características dos alunos, ou ainda questões de 
âmbito local.

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
3.º ANO | 1.º CICLO | ESTUDO DO MEIO
 

### estudo-do-meio-4-ano-1-ciclo
---
title: "AE – Estudo do Meio – 4.º Ano"
disciplina: "Estudo do Meio"
ciclo: "1.º Ciclo"
ano: "4.º Ano"
fonte: "https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/4_estudo_do_meio.pdf"
tipo: "aprendizagens-essenciais"
nivel: "ensino-basico"
data_ingestao: "2026-03-03"
tags:
  - aprendizagens-essenciais
  - dge
  - estudo-do-meio
  - 1-ciclo
---
# Aprendizagens Essenciais – Estudo do Meio – 4.º Ano (1.º Ciclo)

> Fonte: [4_estudo_do_meio.pdf](https://www.dge.mec.pt/sites/default/files/Curriculo/Aprendizagens_Essenciais/1_ciclo/4_estudo_do_meio.pdf)

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
JULHO DE 2018 
 
 
 
 
 
 
 
 
4.º ANO | 1.º CICLO DO ENSINO BÁSICO 
ESTUDO DO MEIO 
INTRODUÇÃO 
As Aprendizagens Essenciais (AE) de Estudo do Meio visam desenvolver um conjunto de competências de diferentes áreas do 
saber, nomeadamente Biologia, Física, Geografia, Geologia, História, Química e Tecnologia. 
Considerando que o Estudo do Meio tem um vasto objeto de estudo, a sua abordagem alicerça-se em conceitos e métodos das 
várias disciplinas enunciadas, contribuindo para a compreensão progressiva da Sociedade, da Natureza e da Tecnologia, bem 
como das inter-relações entre estes domínios. Nesta perspetiva, organizaram-se as presentes AE tendo por base as três áreas 
Ciência-Tecnologia-Sociedade (CTS).

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
4.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 2 
O documento AE estrutura-se de acordo com os domínios mencionados, sendo que, em cada um são identificados os 
conhecimentos a adquirir, as capacidades e as atitudes a desenvolver indispensáveis, relevantes e significativos. Também são 
indicadas, a título exemplificativo, ações estratégicas de ensino orientadas para as áreas de competências definidas no Perfil 
dos Alunos à Saída da Escolaridade Obrigatória (PA). 
Assim, ao longo do 1.º ciclo do ensino básico, o aluno deve: 
a) Adquirir um conhecimento de si próprio, desenvolvendo atitudes de autoestima e de autoconfiança;  
b) Valorizar a sua identidade e raízes, respeitando o território e o seu ordenamento, outros povos e outras culturas, 
reconhecendo a diversidade como fonte de aprendizagem para todos; 
c) Identificar elementos naturais, sociais e tecnológicos analógicos e digitais, do meio envolvente e suas inter-relações;  
d) Identificar acontecimentos relacionados com a história pessoal e familiar, local e nacional, localizando-os no espaço e 
no tempo, utilizando diferentes representações cartográficas e unidades de referência temporal; 
e) Utilizar processos científicos simples na realização de atividades experimentais; 
f) Reconhecer o contributo da ciência para o progresso tecnológico e para a melhoria da qualidade de vida;  
g) Manipular, imaginar, criar ou transformar objetos técnicos simples; 
h) Mobilizar saberes culturais, científicos e tecnológicos para compreender a realidade e para resolver situações e 
problemas do quotidiano; 
i) Assumir atitudes e valores que promovam uma participação cívica de forma responsável, solidária e crítica;

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
4.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 3 
j) Utilizar as Tecnologias de Informação e Comunicação no desenvolvimento de pesquisas e na apresentação de trabalhos; 
k) Comunicar adequadamente as suas ideias, através da utilização de diferentes linguagens (oral, escrita, iconográfica, 
gráfica, matemática, cartográfica, etc.), fundamentando-as e argumentando face às ideias dos outros. 
Neste ano de escolaridade, para além de se dar continuidade a algumas das temáticas trabalhadas no 3.º ano, prioriza-se a 
abordagem de fenómenos naturais, factos e datas relevantes da História de Portugal e elementos relativos à sua Geografia, o 
património natural e cultural, diferentes tipos de uso do solo, as migrações, contributos da ciência e da tecnologia que 
concorrem para a qualidade de vida das populações, bem como para a sustentabilidade.  
A operacionalização das aprendizagens do Estudo do Meio implica a contextualização dos temas a tratar. Para tal, considera-se 
importante que os professores conheçam os contextos locais, que identifiquem situações a partir das quais possam emergir 
questões-problema que sirvam de base para as aprendizagens a realizar. As AE de Estudo do Meio estão associadas a dinâmicas 
interdisciplinares pela natureza dos temas e conteúdos abrangidos, pelo que a articulação destes saberes com outros, de outras 
componentes do currículo, potencia a construção de novas aprendizagens. 
No processo de ensino, devem ser implementadas as ações estratégicas que melhor promovam o desenvolvimento das AE 
explicitadas neste documento. Neste sentido, revela-se importante: 
a) Centrar os processos de ensino nos alunos, enquanto agentes ativos na construção do seu próprio conhecimento; 
b) Tomar como referência o conhecimento prévio dos alunos, os seus interesses e necessidades, valorizando situações do 
dia a dia e questões de âmbito local, enquanto instrumentos facilitadores da aprendizagem; 
c) Privilegiar atividades práticas como parte integrante e fundamental do processo de aprendizagem;

---

APRENDIZAGENS ESSENCIAIS | ARTICULAÇÃO COM O PERFIL DOS ALUNOS 
4.º ANO | 1.º CICLO | ESTUDO DO MEIO
 
PÁG. 4 
d) Promover uma abordagem integradora dos conhecimentos, valorizando a compreensão e a interpretação dos processos 
naturais, sociais e tecnológicos, numa perspetiva Ciência-Tecnologia-Sociedade-Ambiente (CTSA); 
e) Valorizar a natureza da Ciência, dando continuidade ao desenvolvimento da metodologia científica nas suas diferentes 
etapas.  
A gestão deste documento deve promover uma abordagem interdisciplinar, respeitando os temas e o respetivo 
desenvolvimento e ter em conta a atualidade dos assuntos, os interesses e as características dos alunos, ou ainda questões de 

## Schema DocSpec-AM:
# DocSpec-AM Schema — PageCraft

Schema JSON para o Document Specification with Assessment + Maker.

## Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DocSpec-AM",
  "description": "PageCraft Document Specification with Assessment + Maker",
  "type": "object",
  "required": ["topic", "ageRange", "duration", "objectives", "curriculum", "units"],
  "properties": {
    "topic": {
      "type": "string",
      "description": "Tópico da aula"
    },
    "ageRange": {
      "type": "string",
      "description": "Faixa etária alvo (ex: '8-9 anos', 'pré-escolar', '3.º ano')"
    },
    "duration": {
      "type": "integer",
      "description": "Duração em minutos (15-50)",
      "minimum": 15,
      "maximum": 50
    },
    "objectives": {
      "type": "array",
      "description": "Objectivos de aprendizagem (2-4)",
      "items": { "type": "string" },
      "minItems": 2,
      "maxItems": 4
    },
    "curriculum": { "$ref": "#/$defs/CurriculumRef" },
    "memAlignment": { "$ref": "#/$defs/MEMAlignment" },
    "materials": {
      "type": "array",
      "description": "Materiais necessários (digitais + físicos)",
      "items": { "type": "string" }
    },
    "units": {
      "type": "array",
      "description": "Knowledge units ordenadas",
      "items": { "$ref": "#/$defs/KnowledgeUnit" },
      "minItems": 1
    },
    "sessionFlow": {
      "type": "string",
      "description": "Descrição do fluxo da sessão: como as units se encadeiam no tempo"
    }
  },
  "$defs": {
    "CurriculumRef": {
      "type": "object",
      "description": "Referências curriculares",
      "required": ["ae", "competencies"],
      "properties": {
        "ae": {
          "type": "array",
          "description": "Aprendizagens Essenciais referenciadas (disciplina + ano + descritor)",
          "items": {
            "type": "object",
            "required": ["subject", "year", "descriptor"],
            "properties": {
              "subject": { "type": "string", "description": "Disciplina (ex: 'Estudo do Meio')" },
              "year": { "type": "string", "description": "Ano (ex: '3.º ano')" },
              "domain": { "type": "string", "description": "Domínio (ex: 'Natureza')" },
              "descriptor": { "type": "string", "description": "Descritor específico das AE" },
              "source": { "type": "string", "description": "Ficheiro fonte no vault" }
            }
          }
        },
        "competencies": {
          "type": "array",
          "description": "Áreas de competência do Perfil do Aluno trabalhadas",
          "items": {
            "type": "string",
            "enum": [
              "PA-A: Linguagens e textos",
              "PA-B: Informação e comunicação",
              "PA-C: Raciocínio e resolução de problemas",
              "PA-D: Pensamento crítico e pensamento criativo",
              "PA-E: Relacionamento interpessoal",
              "PA-F: Desenvolvimento pessoal e autonomia",
              "PA-G: Bem-estar, saúde e ambiente",
              "PA-H: Sensibilidade estética e artística",
              "PA-I: Saber científico, técnico e tecnológico",
              "PA-J: Consciência e domínio do corpo"
            ]
          }
        }
      }
    },
    "MEMAlignment": {
      "type": "object",
      "description": "Alinhamento com os módulos do Modelo Pedagógico MEM",
      "properties": {
        "modules": {
          "type": "array",
          "description": "Módulos MEM envolvidos na sessão",
          "items": {
            "type": "string",
            "enum": [
              "TEA (Trabalho de Estudo Autónomo)",
              "Projecto cooperativo",
              "Trabalho curricular comparticipado",
              "Circuitos de comunicação",
              "Conselho de cooperação educativa"
            ]
          }
        },
        "instruments": {
          "type": "array",
          "description": "Instrumentos de pilotagem MEM usados (PIT, mapa de tarefas, diário de turma...)",
          "items": { "type": "string" }
        },
        "socialOrganization": {
          "type": "string",
          "description": "Como o trabalho se organiza socialmente (individual → pares → grupo → turma)"
        }
      }
    },
    "KnowledgeUnit": {
      "type": "object",
      "required": ["summary", "textDescription", "interaction", "differentiation"],
      "properties": {
        "summary": {
          "type": "string",
          "description": "Conceito coberto (1 frase)"
        },
        "textDescription": {
          "type": "string",
          "description": "Guia para geração de texto: o que o aluno deve compreender"
        },
        "interaction": { "$ref": "#/$defs/SRTCA" },
        "maker": { "$ref": "#/$defs/MakerChallenge" },
        "differentiation": { "$ref": "#/$defs/Differentiation" },
        "duration": {
          "type": "integer",
          "description": "Duração estimada desta unit em minutos"
        }
      }
    },
    "SRTCA": {
      "type": "object",
      "required": ["state", "render", "transition", "constraint", "assessment"],
      "properties": {
        "state": {
          "type": "array",
          "description": "Variáveis da visualização",
          "items": { "$ref": "#/$defs/StateVar" }
        },
        "render": {
          "type": "string",
          "description": "Como o estado se mapeia para elementos visuais"
        },
        "transition": {
          "type": "string",
          "description": "Como acções do utilizador modificam o estado"
        },
        "constraint": {
          "type": "string",
          "description": "Invariante pedagógico — o que o aluno deve descobrir"
        },
        "assessment": {
          "type": "string",
          "description": "O que o aluno deve demonstrar; critério observável"
        }
      }
    },
    "StateVar": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string" },
        "type": {
          "type": "string",
          "enum": ["slider", "dropdown", "drag", "toggle", "quiz", "sorting", "matching", "canvas", "derived"]
        },
        "range": {
          "type": "array",
          "items": { "type": "number" },
          "minItems": 2,
          "maxItems": 2
        },
        "step": { "type": "number" },
        "default": {},
        "options": {
          "type": "array",
          "items": { "type": "string" }
        },
        "unit": {
          "type": "string",
          "description": "Unidade de medida (ex: 'cm', '°C', 'blocos')"
        },
        "derivedFrom": {
          "type": "string",
          "description": "Fórmula ou expressão (ex: '2 * pi * raio')"
        }
      }
    },
    "MakerChallenge": {
      "type": "object",
      "description": "Extensão maker — liga o digital ao mundo tangível (opcional)",
      "required": ["type", "challenge", "connection"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["minecraft", "lego", "3d-print", "robotics", "whiteboard", "unplugged"],
          "description": "Recurso maker a utilizar"
        },
        "challenge": {
          "type": "string",
          "description": "Descrição do desafio em linguagem acessível"
        },
        "materials": {
          "type": "array",
          "items": { "type": "string" }
        },
        "groupSize": {
          "type": "string",
          "description": "Tamanho do grupo (ex: '2', '2-3', '3-4', 'turma')"
        },
        "connection": {
          "type": "string",
          "description": "Como o desafio maker se liga à exploração digital"
        },
        "communication": {
          "type": "string",
          "description": "Como o grupo comunica/partilha o resultado (circuito MEM)"
        },
        "alternatives": {
          "type": "array",
          "description": "Alternativas se o recurso principal não estiver disponível",
          "items": { "type": "string" }
        }
      }
    },
    "Differentiation": {
      "type": "object",
      "required": ["support", "standard", "challenge"],
      "properties": {
        "support": {
          "type": "string",
          "description": "🟢 Apoio — versão simplificada (menos variáveis, mais guia visual)"
        },
        "standard": {
          "type": "string",
          "description": "🟡 Intermédio — objectivo esperado"
        },
        "challenge": {
          "type": "string",
          "description": "🔴 Desafio — extensão (mais variáveis, raciocínio abstracto)"
        }
      }
    }
  }
}
```

## Exemplo completo: "Estados da água" (3.º ano, 40 min)

```json
{
  "topic": "Estados físicos da água e mudanças de estado",
  "ageRange": "8-9 anos (3.º ano)",
  "duration": 40,
  "objectives": [
    "Identificar os três estados físicos da água (sólido, líquido, gasoso)",
    "Relacionar a temperatura com as mudanças de estado",
    "Descobrir que as mudanças de estado ocorrem a temperaturas específicas (0°C e 100°C)"
  ],
  "curriculum": {
    "ae": [
      {
        "subject": "Estudo do Meio",
        "year": "3.º ano",
        "domain": "Natureza",
        "descriptor": "Identificar propriedades físicas da água (estados físicos, mudanças de estado)",
        "source": "estudo-do-meio-3-ano-1-ciclo.md"
      },
      {
        "subject": "Matemática",
        "year": "3.º ano",
        "domain": "Números e Operações",
        "descriptor": "Ler e interpretar informação em tabelas e gráficos",
        "source": "matematica-3-ano-1-ciclo.md"
      }
    ],
    "competencies": [
      "PA-C: Raciocínio e resolução de problemas",
      "PA-I: Saber científico, técnico e tecnológico",
      "PA-D: Pensamento crítico e pensamento criativo"
    ]
  },
  "memAlignment": {
    "modules": [
      "TEA (Trabalho de Estudo Autónomo)",
      "Projecto cooperativo",
      "Circuitos de comunicação"
    ],
    "instruments": ["PIT", "mapa de tarefas"],
    "socialOrganization": "individual (exploração 10min) → pares (desafio digital 10min) → grupo 3-4 (maker 15min) → turma (comunicação 5min)"
  },
  "materials": [
    "Tablet ou computador com browser (1 por aluno ou par)",
    "Minecraft Education Edition (1 conta por grupo)",
    "Quadro interactivo para apresentação final"
  ],
  "units": [
    {
      "summary": "Os três estados da água dependem da temperatura",
      "textDescription": "O aluno deve compreender que a água existe em três estados — gelo (sólido), água líquida e vapor (gasoso) — e que a temperatura determina em que estado se encontra. As moléculas movem-se de forma diferente em cada estado.",
      "interaction": {
        "state": [
          { "name": "temperatura", "type": "slider", "range": [-20, 120], "step": 1, "default": 20, "unit": "°C" },
          { "name": "estado", "type": "derived", "derivedFrom": "temperatura < 0 ? 'sólido' : temperatura > 100 ? 'gasoso' : 'líquido'" },
          { "name": "velocidadeMoleculas", "type": "derived", "derivedFrom": "(temperatura + 20) / 140" }
        ],
        "render": "Termómetro visual à esquerda; recipiente central com moléculas animadas (círculos azuis) cuja velocidade e disposição reflectem o estado; label grande com nome do estado e temperatura; fundo muda de cor (azul gelado → azul normal → vermelho quente)",
        "transition": "Arrastar slider de temperatura → moléculas ajustam velocidade e padrão (agrupadas/lentas para sólido, médias para líquido, dispersas/rápidas para gasoso) → label e fundo actualizam",
        "constraint": "A água muda de estado a exactamente 0°C (fusão/solidificação) e 100°C (ebulição/condensação)",
        "assessment": "O aluno ajusta o slider para encontrar as duas temperaturas de mudança de estado e regista-as"
      },
      "maker": {
        "type": "minecraft",
        "challenge": "Constrói o ciclo da água no Minecraft: usa blocos de gelo (estado sólido), água (líquido) e partículas de fumo (gasoso). Coloca placas com a temperatura de cada mudança.",
        "materials": ["Minecraft Education Edition", "blocos: gelo, água, soul fire (vapor)"],
        "groupSize": "3-4",
        "connection": "Depois de descobrir as temperaturas de mudança na página, o grupo reconstrói o ciclo em 3D",
        "communication": "Tour guiado ao mundo Minecraft: cada grupo explica o seu ciclo à turma via quadro interactivo",
        "alternatives": ["Sem Minecraft: construir com Lego (azul=gelo, transparente=água, branco=vapor) e etiquetas"]
      },
      "differentiation": {
        "support": "Slider com apenas 3 posições (-10°C, 50°C, 110°C); estado indicado automaticamente com ícone grande; no Minecraft, modelo pré-construído para completar",
        "standard": "Slider contínuo, aluno descobre os pontos de transição; Minecraft: construção livre com orientação",
        "challenge": "Slider inclui gráfico de energia das moléculas; pergunta: 'O que acontece a 100°C numa panela de pressão?'; Minecraft: adicionar o ciclo da água completo (evaporação→nuvem→chuva→rio)"
      },
      "duration": 20
    },
    {
      "summary": "O ciclo da água na natureza liga os três estados",
      "textDescription": "O aluno deve compreender que na natureza a água circula entre os três estados: o sol aquece a água (evaporação), o vapor sobe e arrefece (condensação em nuvens), e a água volta à terra (precipitação). Este ciclo é contínuo.",
      "interaction": {
        "state": [
          { "name": "fase", "type": "dropdown", "options": ["Evaporação", "Condensação", "Precipitação", "Escorrência"], "default": "Evaporação" },
          { "name": "animacao", "type": "derived", "derivedFrom": "fase" },
          { "name": "verTudo", "type": "toggle", "options": ["Uma fase", "Ciclo completo"], "default": "Uma fase" }
        ],
        "render": "Paisagem com mar, montanha e céu; setas animadas mostram o movimento da água; quando 'Uma fase', destaca apenas a fase seleccionada com cor e animação; quando 'Ciclo completo', todas as fases animam em sequência",
        "transition": "Seleccionar fase → paisagem destaca essa parte do ciclo com animação; toggle ciclo completo → animação contínua de todas as fases em loop",
        "constraint": "O ciclo da água é contínuo — cada fase alimenta a seguinte, sem princípio nem fim",
        "assessment": "O aluno descreve as 4 fases pela ordem correcta e explica o que acontece em cada uma"
      },
      "maker": {
        "type": "whiteboard",
        "challenge": "Cada grupo apresenta uma fase do ciclo no quadro interactivo, usando a página. No fim, a turma junta tudo num mapa de conceitos colectivo.",
        "materials": ["Quadro interactivo", "página PageCraft"],
        "groupSize": "turma (4 grupos, 1 fase cada)",
        "connection": "Cada grupo explora 1 fase em profundidade na página → apresenta à turma",
        "communication": "Mapa de conceitos colectivo no quadro: cada grupo adiciona a sua fase com setas",
        "alternatives": ["Sem quadro: cartolinas A3 por grupo, coladas na parede em sequência circular"]
      },
      "differentiation": {
        "support": "Apenas 2 fases (evaporação + chuva), com imagens descritivas; apresentação com guião",
        "standard": "4 fases, exploração livre; apresentação com pontos-chave",
        "challenge": "Inclui infiltração e lençóis freáticos; pergunta: 'O que acontece ao ciclo se não chover durante 3 meses?'"
      },
      "duration": 20
    }
  ],
  "sessionFlow": "0-5min: activação (pergunta: 'De onde vem a chuva?') → 5-25min: Unit 1 exploração + maker → 25-35min: Unit 2 exploração + comunicação → 35-40min: síntese colectiva no quadro"
}
```


## Output
Responde APENAS com o JSON do DocSpec-AM válido. Sem explicações antes ou depois.
