# Brief comum — protótipos de redesign do catálogo PageCraft

## Contexto
PageCraft é um catálogo público de atividades HTML interativas para o 1.º ciclo (crianças 6-10 anos), produzidas por um pipeline multi-agente. Quem usa o catálogo é o **professor** (encontrar e abrir rapidamente a atividade certa para a aula), mas a página é por vezes projetada no quadro interativo e tocada por crianças. A UI atual é um «dashboard azul Inter» genérico — anti-referência explícita do projeto.

## O trabalho da página
1. Professor encontra a atividade certa em segundos (pesquisa + filtros reais, a funcionar).
2. **Problema central de UX**: 90 das 103 atividades são da coleção «Método das 28 Palavras» (M28P) — cada palavra (casa, menina, sapato, árvore…) tem uma atividade principal + variantes («Sílaba intrusa», «Frase baralhada», «Onde está?», etc.). NÃO mostrar 103 cards planos: agrupar o M28P por palavra, com as variantes acessíveis a partir da palavra. As restantes ~13 atividades (matemática, Canva, projetos MEM, digital) merecem destaque próprio.
3. Cada card/linha mostra: título, faixa etária, duração, e ações «Abrir» + «Guia do professor».

## Dados reais
`catalog-data.js` nesta pasta define `window.CATALOG` (array de {slug, title, year, duration, maker, tags, url}). Inclui `<script src="./catalog-data.js"></script>` e renderiza a partir daí. Heurística M28P: tag `m28p`; a palavra extrai-se do slug (ex.: `arvore-cacador-silabas` → palavra «arvore»; a atividade principal é o slug igual à palavra). O título contém «Palavra N — X» de onde podes extrair o número da palavra.

## Regras duras (DESIGN.md do projeto — obrigatórias)
- Sem fontes remotas nem CDN nem qualquer pedido externo. Pilha local: `Atkinson Hyperlegible, Lexend, Nunito, "Comic Sans MS", "Chalkboard SE", system-ui` (escolhe e ordena por papel tipográfico).
- Cores declaradas em OKLCH. Contraste WCAG AA no texto.
- Proibido: glassmorphism, gradient text, semáforo verde/amarelo/vermelho para dificuldade, vermelho punitivo, side-stripe borders nos cards, modais como primeira solução, dark patterns de SaaS.
- Radius padrão 14px; alvos tocáveis ≥48px; foco de teclado visível; `prefers-reduced-motion` respeitado; responsivo até 360px de largura.
- pt-PT com AO90 em toda a copy. Tom: convite, nunca punitivo.
- North star do projeto: «O Tapete de Exploração da Sala» — oficina pedagógica serena com calor de sala MEM, não SaaS.

## Entregável
Um único ficheiro HTML (nome indicado no teu prompt) em `/home/proteu/pagecraft/outputs/ui-prototypes/`, CSS/JS inline (única exceção: o script local `catalog-data.js`). Estrutura mínima: header com identidade PageCraft + pesquisa; navegação/filtros; secção M28P agrupada; secção das outras atividades; footer discreto com contagem real. Links de atividades usam o campo `url` tal como está (não precisam de resolver). A pesquisa filtra em tempo real e mostra estado vazio simpático.
