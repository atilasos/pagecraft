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
