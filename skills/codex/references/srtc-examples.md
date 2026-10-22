# Exemplos SRTC-A por Tópico e Idade

## Pré-escolar (4-5 anos)

### Cores primárias e secundárias

```yaml
Unit: Misturar cores
S:
  - cor1: dropdown ["Vermelho","Amarelo","Azul"], default "Vermelho"
  - cor2: dropdown ["Vermelho","Amarelo","Azul"], default "Amarelo"
  - resultado: derived (tabela de mistura)
R: "Dois baldes de tinta arrastáveis; ao juntar, balde central mostra cor resultante com animação de mistura"
T: "Seleccionar cor1 e cor2 → animação de mistura → resultado aparece"
C: "Duas cores primárias misturadas produzem sempre a mesma cor secundária"
A: "O aluno prevê a cor resultante antes de misturar"
Diferenciação:
  Com pistas: apenas 2 combinações possíveis, feedback visual e som opt-in
  Passo a passo: todas as combinações, label com nome da cor
  Mais desafios: inclui "o que acontece se misturares as 3?"
```

### Contagem até 10

```yaml
Unit: Contar objectos
S:
  - quantidade: slider [1, 10], step 1, default 3
R: "Maçãs animadas aparecem/desaparecem; número grande actualiza; barra de progresso visual"
T: "Arrastar slider → maçãs aparecem uma a uma com som opt-in"
C: "O número representa a quantidade de objectos"
A: "O aluno coloca o slider no 7 quando pedido 'mostra-me 7 maçãs'"
Diferenciação:
  Com pistas: range [1,5], maçãs grandes, contagem oral automática
  Passo a passo: range [1,10], aluno conta sozinho
  Mais desafios: range [1,10], pergunta "quantas faltam para 10?"
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
  Com pistas: formas simples pré-desenhadas para completar
  Passo a passo: desenho livre com eixo visível
  Mais desafios: eixo escondido, aluno tenta desenhar simétrico sem ajuda
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
  Com pistas: apenas 3 posições (frio/morno/quente), estados pré-definidos
  Passo a passo: slider contínuo, aluno descobre os pontos de transição
  Mais desafios: inclui pressão como segunda variável (panela de pressão)
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
  Com pistas: denominador fixo, só muda numerador
  Passo a passo: ambos ajustáveis, referência visível
  Mais desafios: referência visual disponível, aluno encontra outra representação e explica a equivalência
```
