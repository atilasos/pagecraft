# Exemplos SRTC-A por Tópico e Idade

Regra comum: os três níveis partilham o **Constraint** e o critério de **Assessment**. Variam a via e o andaime (menos variáveis, mais passos, mais pistas), nunca o ponto de chegada nem o invariante revelado. Cada unidade termina com um pedido de generalização («Acontece sempre? Porquê?»). Os controlos respeitam `age-adaptation.md`.

## Pré-escolar (4-5 anos)

### Cores primárias e secundárias

```yaml
Unit: Misturar cores
S:
  - cor1: tap-to-cycle ["Vermelho","Amarelo","Azul"], default "Vermelho"
  - cor2: tap-to-cycle ["Vermelho","Amarelo","Azul"], default "Amarelo"
  - resultado: derived (tabela de mistura)
R: "Dois baldes de tinta grandes (≥64px); ao tocar em «Misturar», balde central mostra cor resultante com animação de mistura"
T: "Tocar nos baldes para escolher cor1 e cor2 (ou tocar numa cor e colocá-la no balde) → tocar em «Misturar» → resultado aparece"
C: "Duas cores primárias misturadas produzem sempre a mesma cor secundária"
A: "O aluno prevê a cor resultante antes de misturar"
Diferenciação:
  Com pistas: as mesmas 3 cores, mas uma combinação de cada vez com a cor-alvo visível; feedback visual e som opt-in; o aluno acaba por testar todas as combinações
  Passo a passo: todas as combinações, label com nome da cor
  Mais desafios: todas as combinações sem label e "o que acontece se misturares as 3?"; todos terminam com «Acontece sempre? Porquê?»
```

### Contagem até 10

```yaml
Unit: Contar objectos
S:
  - quantidade: tap-to-place/botões «+1» e «−1» (1 a 10), default 3
R: "Maçãs animadas aparecem/desaparecem; número grande actualiza; barra de progresso visual"
T: "Tocar «+1»/«−1» → maçãs aparecem uma a uma; som só se a criança o ligar; botão «Ouvir» lê o número quando a criança o toca"
C: "O número representa a quantidade de objectos"
A: "O aluno mostra 7 maçãs quando pedido 'mostra-me 7 maçãs'"
Diferenciação:
  Com pistas: 1 a 10, maçãs grandes agrupadas de 5 em 5 (mão de cinco), botão «Ouvir» para a criança iniciar a contagem oral
  Passo a passo: 1 a 10, aluno conta sozinho
  Mais desafios: 1 a 10, pergunta "quantas faltam para 10?"; todos terminam com «Acontece sempre? Porquê?»
```

---

## 1.º/2.º ano (6-7 anos)

### Simetria

```yaml
Unit: Eixo de simetria
S:
  - metade: canvas-draw (metade esquerda)
  - espelho: derived (reflexão horizontal automática)
  - eixo_visivel: toggle [Sim, Não], default Sim
R: "Canvas dividido ao meio; lado esquerdo desenhável, lado direito espelha em tempo real; linha de eixo tracejada"
T: "Desenhar no lado esquerdo → espelho actualiza instantaneamente; toggle eixo → linha aparece/desaparece"
C: "Uma figura simétrica é igual dos dois lados do eixo"
A: "O aluno desenha metade de uma borboleta e verifica que o espelho completa"
Diferenciação:
  Com pistas: formas simples pré-desenhadas para completar, com o eixo visível; o critério final é o mesmo (a figura é igual dos dois lados)
  Passo a passo: desenho livre com eixo visível
  Mais desafios: eixo escondido, aluno tenta desenhar simétrico sem ajuda; todos terminam com «Acontece sempre? Porquê?»
```

---

## 3.º/4.º ano (8-10 anos)

### Estados da água

```yaml
Unit: Mudanças de estado
S:
  - temperatura: slider [-20, 120], step 1, default 20, unit "°C"
  - estado: derived (solid <0, liquid 0-100, gas >100)
  - moleculas_velocidade: derived (proporcional à temperatura)
R: "Termómetro visual; recipiente com moléculas animadas (lentas=gelo, médias=líquido, rápidas=vapor); label do estado"
T: "Arrastar temperatura → moléculas mudam velocidade e disposição → estado actualiza"
C: "A água muda de estado a 0°C e 100°C; as moléculas movem-se mais rápido com o calor"
A: "O aluno identifica a temperatura de fusão e ebulição ajustando o slider"
Diferenciação:
  Com pistas: slider com passos de 10°C e marcas visíveis; o aluno prevê o estado antes de mover e as pistas pedem "entre que valores muda?" sem indicar 0°C nem 100°C
  Passo a passo: slider contínuo, aluno descobre os pontos de transição
  Mais desafios: inclui pressão como segunda variável (panela de pressão); todos terminam com «Acontece sempre? Porquê?»
```

### Frações equivalentes

```yaml
Unit: Descobrir frações iguais
S:
  - numerador: slider [1, 8], step 1, default 1
  - denominador: slider [2, 12], step 1, default 2
  - barra_visual: derived (numerador/denominador da barra preenchida)
  - barra_referencia: toggle entre 1/2, 1/3, 1/4
R: "Duas barras horizontais: a de cima é a fração do aluno, a de baixo é a referência; sobreposição com transparência"
T: "Ajustar numerador/denominador → barra actualiza; quando fracções são equivalentes, destaque visual + som opt-in"
C: "Frações diferentes podem representar a mesma quantidade (ex: 2/4 = 1/2)"
A: "O aluno encontra 3 frações equivalentes a 1/2"
Diferenciação:
  Com pistas: denominador fixo em cada passo (primeiro 2, depois 4, depois 8), só muda o numerador; o aluno chega às mesmas 3 frações equivalentes a 1/2
  Passo a passo: ambos ajustáveis, referência visível
  Mais desafios: referência visual disponível, aluno encontra outra representação e explica a equivalência; todos terminam com «Acontece sempre? Porquê?»
```
