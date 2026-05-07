# Tarefa: Gerar DocSpec-AM para PageCraft

## Tópico
treino de verbos no modo indicativo: presente, pretérito perfeito e futuro

## Contexto
- Ano: 3.º ano (8-9 anos)
- Duração: 30 minutos
- Ciclo: 1.º ciclo

## Instruções

Gera um DocSpec-AM completo em JSON válido para o tópico acima.

### Requisitos obrigatórios:
1. Consulta as Aprendizagens Essenciais abaixo e referencia descritores específicos
2. Mapeia para áreas de competência do Perfil do Aluno (PA-A a PA-J)
3. Alinha com módulos MEM (TEA, projecto cooperativo, comunicação, conselho)
4. Cada knowledge unit tem SRTC-A completo (State, Render, Transition, Constraint, Assessment)
5. Diferenciação obrigatória em 3 níveis (apoio/intermédio/desafio)
6. Linguagem adequada à faixa etária: 8-9 anos
7. O Constraint (C) é algo que o aluno DESCOBRE, não que lhe é dito
8. O Assessment (A) é observável: o que o aluno FAZ/DIZ/PRODUZ
9. Duration total das units deve somar ≤ 30 minutos
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



## Maker
Não incluir maker challenges nesta página (--no-maker). Focar apenas na interacção digital.


## Aprendizagens Essenciais relevantes:


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
