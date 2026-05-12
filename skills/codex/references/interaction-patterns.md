# Interaction Patterns — PageCraft

Biblioteca de patterns reutilizáveis para interações pedagógicas. Cada pattern inclui template SRTC-A.

> **Escolha por idade** (resumo; ver `age-adaptation.md`):
> - **4–7 anos**: preferir `tap-to-cycle`, `tap-to-place`, `audio-first`, `toggle`, `quiz-inline`. Evitar `drag` e `matching` por linhas em touch.
> - **8–10 anos**: todos os patterns são viáveis. `slider`, `drag`, `sorting` e `matching` funcionam bem em tablet.
> - **Sempre**: pelo menos uma alternativa **sem som** e uma alternativa **só por toque** disponível.

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

---

## tap-to-cycle

Avançar por opções com um único toque grande. Substitui o `dropdown` e o `slider` para idades em que a motricidade fina ainda está em formação.

**Quando usar:** crianças 4–7, qualquer escolha entre 2–6 estados discretos, ou qualquer ambiente onde teclado/precisão não estão disponíveis.

```yaml
S: { var: "estacao", type: "tap-cycle", options: ["Primavera","Verão","Outono","Inverno"], default: "Primavera" }
R: "Botão grande (≥56px alto) com o nome e um ícone da estação atual; seta visual indica que cicla"
T: "Tocar botão → próxima opção (com wrap-around) → cena actualiza"
C: "Cada estação tem características visuais distintas"
A: "O aluno passa pelas 4 estações e identifica a actual quando pedido"
```

**Adaptação por idade:**
- 🟢 Apoio (4–6): 2–3 opções, ícone + cor de fundo redundantes ao texto.
- 🟡 Intermédio (7–8): 3–4 opções, ícone + texto.
- 🔴 Desafio (9–10): tipicamente preferir `dropdown` ou `slider` para escolhas finas.

**Acessibilidade:** `aria-label="Mudar estação. Atual: <valor>"`. Anunciar mudança em `aria-live="polite"`.

---

## tap-to-place

Tocar na origem, depois tocar no destino. Substitui `drag` para 4–7 anos em touch.

**Quando usar:** organizar/categorizar/posicionar elementos quando o público é jovem ou o dispositivo é tablet escolar com calibração imperfeita.

```yaml
S: { var: "classificacao", type: "tap-place", sources: ["maçã","cenoura","pão"], buckets: ["fruta","legume","cereal"] }
R: "Cards grandes em cima; 'caixas' grandes em baixo; selecção realçada com contorno espesso"
T: "Tocar source (fica destacado) → tocar bucket → card 'voa' para a caixa com transição curta"
C: "Cada alimento pertence a uma categoria"
A: "O aluno coloca os 3 alimentos nas categorias certas"
```

**Adaptação por idade:**
- 🟢 Apoio (4–6): 2 categorias, ícones grandes, feedback sonoro/visual em cada acerto.
- 🟡 Intermédio (7–8): 3 categorias.
- 🔴 Desafio (9–10): também aceitar `drag` real como alternativa.

**Acessibilidade:** após seleção do source, focar primeira caixa; navegação por setas; `Enter` confirma. `aria-live` anuncia "X colocado em Y".

---

## audio-first

Instrução ou questão entregue por áudio antes de qualquer leitura. Para pré-leitores e leitores em formação.

**Quando usar:** sempre que a faixa etária inclua 4–7 anos, ou quando a leitura não é o objetivo de aprendizagem da unidade.

```yaml
S: { var: "resposta", type: "audio-quiz", audioRef: "audio:pergunta1", options: ["🐶","🐱","🐰"], correct: 1 }
R: "Botão grande 🔊 'Ouvir pergunta' (≥56px); opções como cards grandes com emoji semântico"
T: "Tocar 🔊 → áudio toca → tocar opção → feedback visual + áudio curto de confirmação"
C: "O aluno consegue responder mesmo sem ler"
A: "O aluno acerta sem suporte textual"
```

**Notas de implementação:**
- O áudio pode ser sintetizado em tempo real (`SpeechSynthesisUtterance` com `lang="pt-PT"`) ou pré-gravado em `data:audio` inline para garantir offline.
- **Sempre** redundante: texto presente, mesmo se opcional; emoji semântico com `aria-label`.
- **Som opt-in** continua a aplicar-se: o botão 🔊 é a forma do aluno ligar o áudio.
- Nunca o som é o único portador de significado.

**Acessibilidade:** botão 🔊 com `aria-label="Ouvir pergunta"`. Após resposta, `aria-live` anuncia o resultado em texto.
