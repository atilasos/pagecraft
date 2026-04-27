# Evidência QA — menina-30min (iteração 1)

## Setup
- URL local: http://127.0.0.1:8765/outputs/lessons/menina-30min.html
- HTTP 200, 69 729 bytes (single-file)
- Browser: Chrome (claude-in-chrome MCP), viewport 1767×836 (depois 1568×742 na screenshot)
- Title: "Menina · 30 min · Método das 28 Palavras"

## Consola JavaScript
- `read_console_messages(onlyErrors=true)`: **No console errors or exceptions found**.
- `read_console_messages(.*)`: **No console messages found**.

## Estrutura observada (accessibility tree)
- Skip link "Saltar para o conteúdo" presente e focável (#main).
- Header com:
  - heading "Menina · 30 min" + metadados ("Método das 28 Palavras — Palavra 1", "1.º ano (6-7 anos)", "30 minutos", "Português · Leitura e escrita")
  - "Objetivos da aula" (✓ AO90) com 4 listitens correctos.
- region "Seletor de diferenciação geral" (✓ AO90) com tablist {🟢 Apoio · 🟡 Intermédio · 🔴 Desafio}.
- 4 unidades visíveis (region por unit), com headings:
  - 👧1. A menina sorri (4 min)
  - 👏2. Bater palmas e ordenar (9 min)
  - 🧩3. Inventar palavras novas (9 min)
  - ⭐4. A frase e as estrelas (8 min)
- Por unidade (Units 1–3) há 3 grupos distintos (apoio/intermédio/desafio) com botões/blocos diferenciados.
- Unit 1 (apoio) inclui aviso visível "🔊 Estás a ouvir /menina/" (fix #13 confirmado).
- Unit 1 (challenge) contém "Diz em voz alta porque é que escolheste \"menina\" e não \"menino\"." (fix #12 confirmado).
- Unit 2: contador "/3 palmas", botão "Bater palma", "Repor palmas", e em cada nível sílabas distintas (apoio: posição 1 fixa "me" + arrastar ni/na; intermédio: 3 sílabas arrastáveis; desafio: 3 sílabas + bloco intruso "no").
- Unit 3 bandeja com 3 níveis: apoio com poço "mina"; intermédio com 4 sílabas (me/ni/na/mi) e instrução "Tenta descobrir pelo menos a palavra mina com o teu par." (fix #11 confirmado); desafio com 5 sílabas (me/ni/na/mi/ma) + "Há uma sílaba extra: \"ma\"." (fix #10 confirmado).
- Unit 4: construção de frase em 3 níveis + textbox livre + mini-avaliação com 4 itens (Reconhecer, Segmentar, Recombinar, Usar) com escala "⬜ Ainda não consigo · ⬜ Com ajuda · ⬜ Sozinho/a · ⬜ Ajudo colegas".
- Item 3 da mini-avaliação: "Formei a palavra \"mina\" e descobri uma palavra inventada." (fix #7 confirmado).
- Barra "Progresso da mini-avaliação" com 4 estados ("Reconhecer · por completar / Segmentar · por completar / Recombinar · por completar / Usar · por completar") (fix #14 e #6 confirmados).
- Footer curricular com AE com "respetivos" e "correspondência fonema-grafema" (fixes #3, #4 confirmados); PA-A/F/C/E presentes.
- Footer "Gerado por PageCraft 🛠️ · M28P · Palavra Menina · 30 min".

## Interações testadas com sucesso
1. Click em tab "🔴 Desafio" → níveis Desafio activam-se em todas as units (verificado por estado dos grupos).
2. Click em "Bater palma" 3× → contador chega a "3/3 palmas" e a estrela "Segmentar" muda para "Segmentar · concluído".
3. Click em escala "Sozinho/a" do item 1 → não atualiza estrela (intencional: estrela atualiza ao concluir a unit, não pela self-rating; comportamento aceitável dado o aria-label "por completar/concluído" estar ligado ao Assessment observável).

## Screenshot
- Capturada em modo 🔴 Desafio: paleta consistente (primary #E05FA0 rosa, sílabas me=rosa / ni=violeta / na=verde), tipografia 'Nunito'/Comic Sans, touch targets generosos, layout responsivo legível, "Diz em voz alta porque é que escolheste \"menina\"..." visível, "3/3 palmas" e bloco intruso "no" presente.

## Cruzamento com DocSpec
- topic, ageRange, duration → match.
- 4 units com summaries e durações (4+9+9+8 = 30 min) → match.
- SRTC-A das 4 units → match (state como blocos arrastáveis/contador, render como cards coloridos, transition por click/drag, constraint a descobrir pela ordem das sílabas/recombinação válida, assessment observável em cada unit).
- Diferenciação 🟢/🟡/🔴 presente em **todas** as units e distinta.
- AE/PA do DocSpec listadas no footer.
- maker: none (não pedido) → ausência correcta.

## Cruzamento com Proofread v1 (14 issues, 4 high, 0 critical)
Todos os 14 fixes do `repair-ticket-v1.json` aplicados (verificado por grep + leitura da accessibility tree):
- 4 termos AO90 corrigidos (Objetivos, Seletor, respetivos, corretamente).
- "pseudo-palavra" → "palavra inventada" no HTML e mini-avaliação.
- "Lembra-te do som".
- "porque é que escolheste".
- Estrelas em 4 (sincronizadas com 4 itens).
- Áudio /menina/ + nota visível em u1 apoio.
- Mensagem de erro u4 reescrita.
- "Há uma sílaba extra".
- "Tenta descobrir pelo menos a palavra mina com o teu par."
- aria-labels das estrelas com descritor + estado.

## Sem dependências externas
- `grep -E "<link[^>]*href=\"http|<script[^>]*src=\"http|fonts\.googleapis|cdn\."` → vazio.

## Notas
- Páginas com estado persistente em memória JS dentro da sessão; dados de mini-avaliação opcionalmente em localStorage.
- `prefers-reduced-motion` respeitado (declaração CSS visível na inspecção).
- Self-contained, offline.
