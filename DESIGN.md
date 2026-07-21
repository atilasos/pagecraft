---
name: PageCraft
description: Atividades HTML interativas, offline e acessíveis para crianças do 1.º ciclo.
colors:
  bg: "oklch(0.985 0.005 250)"
  surface: "oklch(0.995 0.003 250)"
  activity-surface: "oklch(0.980 0.005 260)"
  ink: "oklch(0.220 0.020 260)"
  ink-soft: "oklch(0.400 0.020 260)"
  primary: "oklch(0.620 0.120 255)"
  primary-ink: "oklch(0.980 0.010 255)"
  accent: "oklch(0.780 0.130 85)"
  tint-info: "oklch(0.960 0.030 255)"
  tint-warm: "oklch(0.960 0.040 85)"
  tint-grow: "oklch(0.960 0.050 150)"
  ok: "oklch(0.680 0.160 150)"
  ok-tint: "oklch(0.950 0.050 150)"
  warn: "oklch(0.750 0.140 85)"
  warn-tint: "oklch(0.960 0.060 85)"
  focus: "oklch(0.700 0.200 255)"
  border: "oklch(0.880 0.010 260)"
typography:
  display:
    fontFamily: "Atkinson Hyperlegible, Lexend, Nunito, Comic Sans MS, Chalkboard SE, system-ui, -apple-system, sans-serif"
    fontSize: "clamp(1.6rem, 4vw, 2.2rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Atkinson Hyperlegible, Lexend, Nunito, Comic Sans MS, Chalkboard SE, system-ui, -apple-system, sans-serif"
    fontSize: "clamp(1.3rem, 3vw, 1.6rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Atkinson Hyperlegible, Lexend, Nunito, Comic Sans MS, Chalkboard SE, system-ui, -apple-system, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 800
    lineHeight: 1.25
  body:
    fontFamily: "Atkinson Hyperlegible, Lexend, Nunito, Comic Sans MS, Chalkboard SE, system-ui, -apple-system, sans-serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Atkinson Hyperlegible, Lexend, Nunito, Comic Sans MS, Chalkboard SE, system-ui, -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.3
rounded:
  focus: "6px"
  md: "10px"
  lg: "14px"
  xl: "16px"
  pill: "999px"
spacing:
  xs: "0.4rem"
  sm: "0.6rem"
  md: "1rem"
  lg: "1.25rem"
  xl: "1.5rem"
  tap: "48px"
  maxw: "960px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.md}"
    padding: "0.55rem 1.1rem"
    height: "48px"
    typography: "{typography.label}"
  button-ghost:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: "0.55rem 1.1rem"
    height: "48px"
    typography: "{typography.label}"
  card-unit:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "1.25rem 1.5rem"
  diff-tab-selected:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.pill}"
    padding: "0.6rem 1rem"
    height: "48px"
  feedback-correct:
    backgroundColor: "{colors.ok-tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "1rem 1.25rem"
  feedback-try-again:
    backgroundColor: "{colors.warn-tint}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "1rem 1.25rem"
---

# Design System: PageCraft

## 1. Overview

**Creative North Star: "O Tapete de Exploração da Sala"**

PageCraft deve parecer uma atividade pousada na mesa da sala: limpa, táctil, pronta a tocar, com materiais suficientemente grandes para mãos pequenas e informação suficientemente calma para um quadro interativo. A estética central é uma oficina pedagógica serena: superfície clara tintada, contornos sólidos, botões honestos e feedback que convida a experimentar de novo.

O sistema visual é de produto, não de campanha. A identidade não deve competir com o objetivo pedagógico. Cada atividade pode ter uma cor de tema, mas a gramática mantém-se: fundo claro tintado, superfície quase branca tintada, tinta escura azulada, foco azul, sucesso verde funcional e tentativa âmbar. A variação vive no `primary` e no `accent`, nunca em padrões aleatórios.

**Direção do catálogo: «O Ficheiro da Biblioteca Escolar».** O catálogo público e as páginas de apoio do professor usam a materialidade de um ficheiro escolar: papel branco-quente, tinta quase preta, um único acento verde-azulado de carimbo, separadores manila, fichas com furos de arquivo e dados em numerais tabulares. Esta gramática dá densidade e velocidade ao professor sem regressar ao dashboard SaaS; as atividades infantis continuam a seguir «O Tapete de Exploração da Sala».

Rejeita explicitamente SaaS educativo genérico, paleta semáforo para níveis de dificuldade, vermelho de erro, fontes remotas, glassmorphism decorativo, gradient text, side-stripe borders e modais como primeira solução. Se a interface parece uma landing page de IA com cartões repetidos, falhou.

**Key Characteristics:**

- Touch-first: alvos de 48px no mínimo, 56px para 6–7 anos e 64px para 4–5 anos.
- Offline por defeito: sem CDN, sem Google Fonts, sem dependências remotas.
- Tipografia grande, familiar e legível para leitores em formação.
- Feedback não punitivo: sucesso celebra descoberta; tentativa usa âmbar e sugestão concreta.
- Cores funcionais separadas de níveis de dificuldade.

## 2. Colors

A paleta é clara, tintada e funcional. PageCraft usa OKLCH como fonte de verdade para reduzir garishness, manter contraste previsível e permitir variações temáticas sem perder a gramática visual.

### Primary

- **Azul Oficina** (`primary`): ação principal, tabs selecionadas, títulos de unidade e controlos interativos. Deve carregar identidade suficiente para orientar a criança, mas nunca dominar a superfície.
- **Tinta Sobre Azul** (`primary-ink`): texto dentro de botões e estados selecionados. É quase claro, mas tintado, nunca branco puro.

### Secondary

- **Âmbar Descoberta** (`accent`): momentos de avaliação, atenção e atividade manipulável. Não é erro. Quando a criança precisa de tentar de novo, usar `warn` e `warn-tint` com microcopy específico.
- **Verde Crescimento** (`tint-grow`): blocos maker, descoberta e progresso construtivo. Não deve ser usado para codificar nível “fácil”.

### Tertiary

- **Azul Pergunta** (`tint-info`): perguntas de ativação, zonas de exploração e contexto de instrução.
- **Calor de Síntese** (`tint-warm`): assessment, síntese e reflexão final.

### Neutral

- **Papel Frio** (`bg`): fundo global. Claro, mas ligeiramente azul para evitar branco clínico.
- **Cartão de Sala** (`surface`): superfície de cards e controlos. Quase branco tintado, não `#fff`.
- **Tinta de Lápis** (`ink`): texto principal. Escuro, azul-violeta, não `#000`.
- **Tinta Suave** (`ink-soft`): metadados, instruções secundárias e rodapé.
- **Linha Baixa** (`border`): contornos de containers, inputs e tabs inativos.

### Named Rules

**The Functional Split Rule.** `ok`, `warn` e `focus` são funções de interface, não cores de dificuldade. Níveis Apoio, Intermédio e Desafio usam marcadores neutros ou botânicos, nunca verde, amarelo e vermelho como semáforo.

**The Tinted Neutral Rule.** Fundo, superfície e texto nunca usam branco ou preto puros. A neutralidade PageCraft é sempre levemente tintada para parecer papel, não ecrã clínico.

**The One Theme Color Rule.** Cada atividade pode trocar `primary` para se aproximar do tema curricular, mas mantém `bg`, `surface`, `ink`, `focus`, `ok` e `warn` estáveis.

## 3. Typography

A tipografia privilegia leitores em formação. A pilha normativa é `Atkinson Hyperlegible`, `Lexend`, `Nunito`, `Comic Sans MS`, `Chalkboard SE`, `system-ui`, `-apple-system`, `sans-serif`. Todas são locais ou fallbacks do sistema. Fontes remotas são proibidas.

### Scale

- **Display**: títulos de página e unidade principal (`clamp(1.6rem, 4vw, 2.2rem)`, peso 800, linha 1.2).
- **Headline**: títulos de secção (`clamp(1.3rem, 3vw, 1.6rem)`, peso 800, linha 1.2).
- **Title**: subtítulos e labels fortes (`1.15rem`, peso 800).
- **Body**: corpo base para 8–10 anos (`20px`, linha 1.55).
- **Young Body**: corpo para 6–7 anos (`22px`, linha 1.6).
- **Pre-reader Body**: corpo para 4–5 anos (`24px`, com instruções em canais redundantes).
- **Microcopy infantil**: nunca abaixo de `16px`; microcopy crítico deve manter contraste AAA.
- **Shell do professor**: corpo base de `16px`, ações de `14–16px`, metadados funcionais de `13px` e small caps decorativas de `12px` no mínimo. Esta escala adulta só se aplica ao catálogo, viewer e Studio; quando projetados ou usados com apontador coarse, ações sobem para `16px` e alvos para `56px`.

### Rules

**The Early Reader Rule.** O texto de criança não usa itálico, ALL CAPS nem linhas acima de 55ch. Para 6–7 anos, limitar a 50ch; para 4–5 anos, 40ch.

**The Local Font Rule.** A página corre offline. Se Atkinson, Lexend ou Nunito não existirem no dispositivo, `Comic Sans MS` e `Chalkboard SE` são aceitáveis neste contexto porque ajudam o reconhecimento de letras.

## 4. Elevation

A elevação PageCraft é baixa, estrutural e tátil. Cards e zonas interativas usam contorno real, raio generoso e sombra suave apenas para separar camadas. A sombra não é decoração e nunca deve substituir hierarquia, contraste ou espaçamento.

- **Flat Base:** fundo global sem sombra.
- **Surface Low:** cards de unidade com borda de 1px e sombra leve (`0 1px 2px` + `0 4px 14px`, opacidade baixa).
- **Interactive Raised:** botões, blocos manipuláveis e sliders podem ganhar feedback por `filter`, contorno ou sombra curta.
- **No Glass:** blur, transparência e glassmorphism são proibidos por defeito.

**The Chalk Tray Rule.** Uma superfície só levanta quando precisa de ser tocada, lida ou distinguida numa sala. Se a sombra chama mais atenção do que a tarefa, está demasiado forte.

## 5. Components

### Buttons

- **Shape:** retângulo suavemente arredondado (`10px`) ou pill quando a ação é curta e repetida.
- **Primary:** `primary` sobre `primary-ink`, altura mínima `48px`, padding `0.55rem 1.1rem`, peso 700.
- **Hover / Focus:** hover por `filter: brightness(1.06)`, active por `brightness(0.94)`, foco com outline `3px` em `focus` e `outline-offset: 3px`.
- **Ghost:** fundo `surface`, texto `primary`, borda de 2px, mesmo tamanho do primary.
- **Forbidden:** hover com `scale()`, bounce, elastic ou gradientes decorativos.

### Chips

- **Style:** pills com fundo tintado, texto escuro e ícone redundante quando houver semântica.
- **State:** selecionado usa fundo sólido `primary`; não selecionado usa `surface` + `border`.
- **Difficulty:** Apoio, Intermédio e Desafio podem usar marcador botânico pequeno, mas a cor não é o único significado.

### Cards / Containers

- **Corner Style:** raio principal `14px` em atividades, catálogo e páginas do professor; variações exigem motivo funcional ou pedagógico.
- **Background:** `surface` para unidades, `activity-surface` para zonas interativas, tints funcionais para feedback.
- **Shadow Strategy:** sombra baixa e borda visível. Não usar side-stripe borders.
- **Internal Padding:** `1.25rem 1.5rem` em desktop; reduzir para `1rem` em mobile sem comprimir alvos.

### Inputs / Fields

- **Style:** fundo `surface`, borda `2px` em `border`, raio `10px`, texto em `ink`.
- **Focus:** outline `3px` em `focus`, não trocar apenas a cor da borda.
- **Error / Try Again:** PageCraft não usa vermelho de erro. Usar `warn-tint`, ícone ↻ e sugestão concreta em pt-PT.
- **Disabled:** reduzir contraste com cuidado, nunca abaixo de legibilidade confortável para crianças.

### Navigation

- **Catalogue Navigation:** pode ser mais denso, mas deve herdar tintas e foco PageCraft. Evitar que o catálogo pareça outro produto.
- **Activity Navigation:** tabs ARIA com `role=tablist`, `role=tab`, `aria-selected` e navegação por setas quando aplicável.
- **Mobile:** tabs empilham e ocupam a largura disponível. Alvo de toque continua a mandar.

### Discovery Message

Mensagem de descoberta usa `ok-tint`, borda `ok`, texto escuro e `aria-live="polite"`. A cópia celebra a descoberta: “Encontraste! Já sabes que…” é melhor do que “Correto!”.

### Differentiation Tabs

Apoio, Intermédio e Desafio existem sempre quando a atividade inclui diferenciação. A interface usa labels explícitas e marcadores botânicos — Broto/Apoio, Árvore jovem/Intermédio e Árvore robusta/Desafio — ou símbolos neutros equivalentes. Não usar 🟢, 🟡 e 🔴 nestes níveis: mesmo acompanhados por texto, reintroduzem a leitura de semáforo emocional que o sistema rejeita.

### Audio Toggle

O som começa desligado. O botão de áudio é visível, tem label acessível e nunca transporta significado sozinho. Feedback sonoro, quando ligado, é curto, baixo e redundante ao visual/texto.

## 6. Do's and Don'ts

### Do:

- **Do** usar OKLCH como fonte de verdade das cores nas atividades novas.
- **Do** manter fundo, superfície e texto tintados; nunca usar `#fff` ou `#000` puros em trabalho novo.
- **Do** separar cores de identidade (`primary`, `accent`) de cores funcionais (`ok`, `warn`, `focus`).
- **Do** garantir corpo mínimo de `20px` para 8–10, `22px` para 6–7 e `24px` para 4–5.
- **Do** usar alvos de toque mínimos de `48px`, `56px` e `64px` conforme idade.
- **Do** escrever feedback que convida a tentar de novo: “Quase! Tenta outra peça.”
- **Do** manter atividades self-contained: CSS e JS inline, sem internet, sem CDN e sem fontes remotas.
- **Do** usar `:focus-visible` com outline de `3px` e `outline-offset: 3px`.
- **Do** traduzir qualquer emoji semântico em texto ou `aria-label`; emoji decorativo recebe `aria-hidden="true"`.

### Don't:

- **Don't** usar “vermelho de erro”, mensagens como “Errado” ou feedback punitivo.
- **Don't** usar paleta semáforo para níveis de dificuldade. Apoio, Intermédio e Desafio não são verde, amarelo e vermelho visuais.
- **Don't** usar side-stripe borders, incluindo `border-left` ou `border-right` maior que 1px como acento em cards, alerts ou callouts.
- **Don't** usar gradient text, glassmorphism decorativo ou gradientes em headers como decoração.
- **Don't** carregar Google Fonts, scripts remotos, frameworks, jQuery ou assets de internet.
- **Don't** usar Inter azul de dashboard como identidade das atividades infantis. O catálogo pode migrar para a gramática PageCraft, mas as atividades mandam no sistema.
- **Don't** usar itálico em corpo, ALL CAPS em instruções ou linhas longas para crianças.
- **Don't** animar `width`, `height`, `top`, `left`, `padding` ou `margin`. Usar `transform`, `opacity`, `filter` ou cor.
- **Don't** usar modais como primeira solução para explicar, confirmar ou corrigir. Preferir feedback inline, estados progressivos e zonas de descoberta.
