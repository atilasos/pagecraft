# PageCraft — Regras de Design para o Builder (Claude Code)

> Este ficheiro é lido automaticamente pelo Claude Code em qualquer sessão dentro deste repositório.
> Aplica estas regras a todas as páginas HTML geradas.

---

## Contexto do projeto

**PageCraft** é uma coleção de páginas de aula interativas para crianças de 4–10 anos (pré-escolar e 1.º CEB), publicada como GitHub Pages em https://atilasos.github.io/pagecraft/.

**Método das 28 Palavras (M28P)** — série de 28 atividades para iniciação à leitura e escrita, com exploração silábica, reconhecimento global de palavras e recombinação de sílabas.

---

## Regras absolutas (nunca violar)

1. **Self-contained** — zero dependências externas. Sem CDN, sem imports de JS/CSS externos, sem Google Fonts via URL (embedda o @font-face inline se necessário). O ficheiro deve funcionar offline.
2. **Título canónico** — `<title>M28P #N — palavra | PageCraft</title>`. Os valores N e palavra vêm do `docspec.json`. Nenhum outro formato é aceite.
3. **Sem frameworks** — sem React, Vue, Tailwind, Bootstrap. HTML5 + CSS3 + JS vanilla únicos.
4. **Touch-first** — todos os elementos interativos com `min-height: 48px` e `min-width: 48px` (WCAG 2.5.8).
5. **lang="pt-PT"** — o HTML deve ter `<html lang="pt-PT">` e todo o texto em português europeu (AO90).

---

## Design para crianças

### Tipografia
- Fonte principal: `'Nunito', 'Comic Sans MS', 'Chalkboard SE', sans-serif`
- Tamanho base body: **20px** (mínimo 18px)
- Headings: 32–48px, `font-weight: 800`
- Sílabas em destaque: **36–48px, font-weight: 800**
- Nunca usar Inter, Roboto, Arial, system-ui como fonte principal

### Cores
- Cada palavra M28P tem uma paleta própria definida no `design-spec.json` — usá-la rigorosamente
- Cada sílaba tem uma cor própria (`syllableColors` no design-spec) — aplicar de forma consistente em todos os blocos draggable e referências textuais
- Contraste mínimo: **WCAG-AA** (4.5:1 texto normal, 3:1 texto grande)
- Fundo: tons quentes suaves (nunca branco puro #fff — usar #FFF8F0 ou equivalente da paleta)

### Componentes padrão

**Botões:**
- Forma pill (`border-radius: 9999px`)
- Padding: `0.75rem 2rem`
- Font-weight: 700
- min-height: 48px
- Hover: `transform: scale(1.05)` + sombra mais intensa
- Active: `transform: scale(0.97)`

**Cards:**
- Background: `var(--surface)` (#fff)
- Border: `2px solid var(--primary)`
- Border-radius: 16px
- Sombra: `0 4px 12px rgba(0,0,0,0.08)`

**Blocos de sílabas (draggable):**
- Cada sílaba num bloco colorido com a cor do `syllableColors`
- Font-size: 36px, font-weight: 800
- Padding: `0.5rem 1.2rem`, border-radius: 12px
- Texto branco, cursor: grab
- Durante drag: `transform: scale(1.1)` + sombra

**Feedback:**
- Correto: fundo `#f0fdf4`, borda `#22c55e`, ícone ✓, mensagem encorajadora
- Incorreto: fundo `#fffbeb`, borda `#F59E0B`, ícone ~, mensagem de tentativa (nunca negativa)

**Palavra em destaque:**
- Maiúsculas, font-size: 48px, font-weight: 800, `color: var(--primary)`, `letter-spacing: 0.05em`

### Indicadores de diferenciação
- 🟢 **Com ajuda** (nível base)
- 🟡 **Objetivo** (nível intermédio)
- 🔴 **Desafio** (extensão)

---

## Estrutura obrigatória de cada página M28P

1. **Header** — gradiente com paleta da palavra, título, metadados (ano, duração, emoji da palavra), objetivos como pills
2. **Navegação** — âncoras para cada unidade/secção da página
3. **Unidades de aprendizagem** (a partir do docspec.json):
   - Ativação (história/contexto da palavra)
   - Apresentação global (imagem + palavra completa)
   - Exploração silábica (blocos coloridos, drag & drop)
   - Recombinação (formar novas palavras com as sílabas)
   - Frases simples (completar/ler)
   - Mini-avaliação formativa
4. **Guia do professor** (colapsável) — objetivos, diferenciação, notas
5. **Footer** — crédito PageCraft

---

## Acessibilidade

- `aria-label` em todos os controlos interativos sem texto visível
- Focus ring: `outline: 3px solid var(--primary); outline-offset: 2px`
- Skip link no início: `<a href="#main" class="skip-link">Ir para o conteúdo</a>`
- Imagens decorativas: `aria-hidden="true"`
- Drag & drop: alternativa de clique/teclado obrigatória

---

## Motion / Animações

- Transições: `200ms ease` (subtis, não distractivas)
- Page load: stagger suave nas cards (animation-delay escalonado)
- Feedback correto: pulse verde 0.3s
- Sem animações que pisquem mais de 3x/segundo (WCAG 2.3.1)
- Respeitar `prefers-reduced-motion`

---

## CSS — tokens obrigatórios

```css
:root {
  /* Definidos pelo design-spec.json da palavra */
  --bg: /* fundo quente suave */;
  --surface: #FFFFFF;
  --primary: /* cor principal da palavra */;
  --accent: /* cor de destaque */;
  --text: #1E1B18;

  /* Fixos */
  --correct: #22c55e;
  --correct-bg: #f0fdf4;
  --incorrect: #F59E0B;
  --incorrect-bg: #fffbeb;
  --radius: 16px;
  --shadow: 0 4px 12px rgba(0,0,0,0.08);
  --font: 'Nunito', 'Comic Sans MS', 'Chalkboard SE', sans-serif;
}
```

---

## Skill de design activa

Este projeto usa a skill **anthropics-frontend-design** instalada no Claude Code (`~/.claude/plugins/anthropics-frontend-design/SKILL.md`). Aplica os princípios de design thinking e estética da skill adaptados ao contexto infantil:

- **Tone:** Playful/toy-like, warm, energetic — nunca neutro ou corporativo
- **Differentiator:** Cada página deve ter uma identidade visual única baseada na paleta da palavra, não um template genérico
- **Motion:** Animações de carregamento com stagger; feedback imediato e satisfatório em interações
- Ignora as sugestões da skill que violem as regras absolutas acima (sem CDN, sem frameworks)
