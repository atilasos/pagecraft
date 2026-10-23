# Auditoria 04: catálogo e atividades com vários anos

Base `4c6ba90`, verificada em 22-10-2026. Investigação só de leitura; o único artefacto criado é este relatório. Não alterei `catalog.json` nem as duas atividades locais do utilizador. Li AGENTS, CONTEXT, ADR-0002, ADR-0003, ADR-0005 e a avaliação anterior. As propostas abaixo não repetem os PRs #51–55, já integrados: evidência exportada, cache de feedback, retoma, nomes dos apoios e entrega da escolha de apoio.

## Fundamentação e estado existente

Consultei a API local da Sebenta com `health`, `search` e `read --content` de duas páginas integrais:

- **Síntese da wiki:** “Diferenciação Pedagógica”, `20_Wiki/Diferenciação Pedagógica.md`, estado `review`, confiança `medium`. Defende vias e apoios distintos com metas comuns, grupos móveis e organização cooperativa da heterogeneidade.
- **Síntese da wiki:** “Aprendizagem Cooperativa”, `20_Wiki/Aprendizagem Cooperativa.md`, estado `review`, confiança `medium`. Distingue estar em grupo de cooperar; pede objetivo comum, responsabilidade individual, explicação e papéis que evitem dependência.

As decisões de produto seguintes são propostas minhas. Estas sínteses não demonstram eficácia do PageCraft nem justificam deduzir competências a partir da idade.

Já existem pesquisa, filtros por ano, agrupamento M28P e variantes (`index.html:565`, `index.html:675`). O seletor de aula combina disciplina, ano e pesquisa (`server/static/teacher/class.js:314`). A ponte Tinkercad já prevê critérios comuns, apoios livres e troca de papéis (`activities/tinkercad-pontes-3e4/teacher.md:53`, `:59`). Não proponho reconstruir estes mecanismos.

## 1. Um contrato explícito de anos destinatários

**Problema e prova.** `index.html:565` interpreta textos por regex e converte idades em anos; `server/api/catalog.py:52` aceita apenas um ano e prefere a primeira referência curricular em `:83`. A ponte declara “3.º e 4.º anos” no `meta.json:7`, mas distingue enquadramento de ciclo e destinatários no `docspec.json:20`, `:40`.

Executei a função real `itemYears` em Node e `_parse_year`/`list_activities` em Python, sem servidor: a ponte resulta em `[4]` na página pública e `year: null` na API. Desaparece no filtro público do 3.º e nos filtros docentes dos dois anos. O cliente docente exige igualdade escalar em `server/static/teacher/class.js:315`.

Há outra divergência real: cinco variantes `m28p-*-blocos` têm `year: "6–8 anos, ajustável"`; a página interpreta `[1,2,3]`, enquanto a API apresenta `1`, obtido do currículo. Um valor numérico `3` também produz `[]` na função pública, embora a API o aceite; este último caso é sintético.

**Comportamento proposto.** Adotar `years: number[]`, ordenado, sem duplicados, com inteiros 1–4; `[]` significa ano destinatário não declarado. O `meta.json` é a autoridade publicada; `catalog.json` continua derivado, conforme ADR-0003. O DocSpec novo declara `years`, validado na publicação e copiado para os metadados. Preservar `ageRange`, texto histórico `year`, referências curriculares e HTML publicado.

Um normalizador Python comum serve publicação e API. Para metadados antigos sem `years`, reconhecer apenas escolaridade explícita em `meta.year`, depois `docspec.ageRange`, incluindo “3.º e 4.º anos” e números isolados. Não deduzir escolaridade de idades, etiquetas ou abrangência curricular. Campo explícito inválido bloqueia publicação; ausência histórica dá `[]`. As cinco variantes exigem confirmação docente do destino; até lá ficam em “Todos” e “Sem ano indicado”.

API e índice expõem o mesmo `years`; facetas usam a união desses conjuntos. Clientes testam pertença e mostram “3.º e 4.º anos”. O `year` escalar da API permanece definido apenas para conjuntos unitários durante a migração dos consumidores conhecidos; nunca escolher o menor ano de um conjunto. O carimbo público também deve deixar de transformar qualquer conjunto múltiplo em “1.º CEB” (`index.html:689`).

**Benefício pedagógico esperado.** Encontrar trabalho comum sem equiparar idade, escolaridade e apoio necessário.

**Risco e esforço.** Médio, 2–3 dias estimados. A correção reduz resultados antes inferidos por idade; exige revisão das cinco variantes e comunicação clara do estado desconhecido.

**Regressão concreta.** A mesma fixture da ponte produz `[3,4]` no índice e API; pesquisar “Tinkercad” com 3.º ou 4.º apresenta uma atividade, com 2.º apresenta zero. Testar idades isoladas → `[]`, número 3 → `[3]`, duplicados, booleanos e valores fora de 1–4. Testar variante cujo ano difere da base, preservando abertura, contagens e impossibilidade de lançar seleção escondida.

**Fronteira.** Novo `server/catalog_years.py`; `server/publish.py`, `server/api/catalog.py`, schema/prompt canónicos do DocSpec e distribuições sincronizadas; `index.html`, clientes docentes `class.js` e `app.js`; testes de catálogo/publicação/cliente. Regeneração futura do índice pela publicação, sem edição direta.

## 2. Encontrar uma atividade comum para dois anos

**Problema e evidência.** Ambos os seletores aceitam um único ano (`index.html:550`, `server/static/teacher/class.js:13`). A ponte oferece trabalho comum com apoios distintos, mas o catálogo não permite procurar explicitamente esse cruzamento.

**Proposta criativa.** Depois da proposta 1, permitir selecionar vários anos e escolher “Qualquer ano selecionado” ou “Comum aos anos selecionados”. Para `{3,4}`, o segundo modo exige que ambos pertençam a `activity.years`. A interface explica “Anos declarados; consulta o guia para adaptar”. Não atribui papéis ou apoios por ano nem necessita de nomes de alunos.

**Benefício esperado.** Preparar experiências partilhadas numa turma heterogénea, com diferenciação decidida pelo professor.

**Risco e esforço.** Médio, 1–2 dias. Cobertura declarada não prova adequação a cada criança; a ausência de metadados não deve parecer inadequação pedagógica.

**Teste concreto.** Com fixtures `[3]`, `[4]`, `[3,4]`, `[]`, a união mostra três atividades e o modo comum uma; limpar filtros recupera quatro, sem duplicação nem contagens inflacionadas.

**Fronteira.** `index.html`, `server/static/teacher/class.js`, marcação dos filtros em `class.html` e testes dos clientes. Sem alterar turmas, sessões, evidências ou apoios.

A melhor proposta recomendada é a **1**: resolve uma exclusão reproduzida e estabelece o contrato necessário para avaliar a proposta 2.
