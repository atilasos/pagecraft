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
