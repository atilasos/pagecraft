# Catálogo com anos destinatários explícitos

Implementação da proposta 1 da auditoria `/tmp/pagecraft-audit-04.md`.
Base `4c6ba90476a498a03b08fd88dea96c432ba767cd`, branch
`feat/catalog-years-index-api`, worktree
`/home/proteu/.t3/worktrees/pagecraft/t3-960f9147`.

## Problema reproduzido

A função pública `itemYears` convertia idades em anos e perdia o primeiro
ano em `3.º e 4.º anos`. A API preferia o ano da primeira AE e devolvia um
escalar. O seletor docente comparava esse escalar por igualdade.

Na base, Tinkercad resultava em `[4]` no catálogo e `year: null` na API.
As cinco variantes `m28p-*-blocos`, com `6–8 anos, ajustável`, resultavam em
`[1,2,3]` no catálogo e `year: 1` na API. O número sintético `3` resultava em
`[]` no catálogo público.

## Implementação

O [contrato de anos](../catalog-years.md) descreve a precedência e os
formatos aceites. `server/catalog_years.py` concentra a interpretação
histórica e a validação. Índice, API e publicação usam esse módulo.

`years` explícito prevalece, incluindo `[]`. Na sua ausência, o sistema lê
escolaridade explícita em `meta.year` e depois em `docspec.ageRange`.
Não atribui destinos por idade, etiquetas ou referências curriculares.
A API preserva `yearLabel` e só expõe um `year` escalar para conjuntos
unitários. As facetas usam a união de `years`.

O catálogo público e os dois clientes docentes usam `years`. Tinkercad
surge nos filtros dos dois anos. Variantes conservam filtragem, abertura e
contagem independentes da base. O carimbo acompanha os resultados visíveis.
Sem declaração, a atividade continua encontrável em **Todos**.

A publicação valida `docspec.years` opcional antes de escrever artefactos.
Sem nova declaração, preserva o destino explícito ou histórico existente.
O esquema e os prompts de geração ficaram intactos.

Inspecionei os escritores do catálogo. `publish_to_catalog.py` partilhado e
as suas cópias delegam em `server.publish`. O gerador de variantes e o
script de reparação M28P já chamavam `regenerate_catalog`. O gerador passou
a preservar o `years` próprio de uma variante, com o validador comum.
O teste desse script confirma também a projeção no índice.

A regeneração neste worktree encontrou 107 atividades. O índice e a API
agora concordam para todas elas. Tinkercad dá `[3,4]`; as cinco variantes
que só declaram idade dão `[]`. `git diff 4c6ba90 -- activities` está vazio.
Não houve alteração de HTML, DocSpecs ou metadados publicados, nem acesso
a dados de produção.

## Fundamentação pedagógica

Consultei `health` e li integralmente `Diferenciação Pedagógica` pela API
local da Sebenta em 22-10-2026, através de `sebenta_api.py`.
A página está em `review`, com confiança `medium`.

A síntese da wiki defende vias e apoios diferentes com metas comuns e
organização cooperativa da heterogeneidade. A decisão de separar idade,
escolaridade e apoios é uma proposta de produto. A síntese não demonstra
adequação de uma atividade a um ano nem autoriza preencher destinos ausentes.

## Prova e comandos

Testes do contrato, API, publicação, CLI e escritores:

```bash
uv run --project /home/proteu/pagecraft python -m pytest \
  tests/test_catalog.py tests/test_publish.py tests/test_publish_cli.py \
  tests/test_catalog_batches.py -q
```

Resultado final deste conjunto: 76 testes passam. Os casos cobrem número
isolado, ordinais, vários anos, intervalos, duplicados, precedência, vazio
explícito, idades sem escolaridade, booleanos e valores inválidos.
A API é exercitada por HTTP, com verificação de 401 sem acesso docente,
facetas e concordância com `/api/meta`. A publicação e a CLI verificam que
uma declaração inválida não altera ficheiros, incluindo na republicação.

Suite geral:

```bash
uv run --project /home/proteu/pagecraft python -m pytest -q
```

Resultado: **399 passed, 35 skipped**. A suite geral omite browser sem CDP.
Os testes de browser desta alteração foram executados separadamente.

Abri a sessão própria `pagecraft-catalog-years`, perfil `temporary`, pelo
Agent Browser Hub. Playwright ligou-se apenas ao CDP dessa sessão. Os testes
usam servidores locais e turmas descartáveis, sem dados de produção:

```bash
PAGECRAFT_TEST_CDP=http://127.0.0.1:9333 \
PAGECRAFT_CATALOG_PROOF_DIR=/tmp/pagecraft-catalog-years-proof \
uv run --project /home/proteu/pagecraft --with playwright python -m pytest \
  tests/browser/test_catalog_years.py -q
```

Resultado: **5 passed**. Inclui Tinkercad em 3.º e 4.º, exclusão em 2.º,
ano numérico, rótulos dos dois clientes docentes, variante de 4.º com base
de 1.º, abertura da variante, contagens, ausência de ano e limpeza da
seleção escondida. O botão de lançamento fica ativo com uma turma e uma
atividade selecionadas, e volta a ficar desativado quando o filtro as separa.
Os testes públicos correm em larguras de 1280 e 390 px.

Antes da adaptação dos clientes, os quatro testes originais falharam.
Depois da correção passaram, com uma quinta execução para ecrã estreito.

Uma segunda comparação no browser usou os ficheiros reais `index.html` e
`catalog.json` de `4c6ba90` e os deste checkout, cada par num servidor
estático temporário. Nos dois tamanhos de ecrã, os resultados foram:

- Base: filtro 3.º com zero Tinkercad, filtro 4.º com uma, filtro 2.º com zero.
- Implementação: filtros 3.º e 4.º com uma Tinkercad cada, filtro 2.º com zero.

O script desta prova está em `/tmp/pagecraft-delegate/check-catalog-years-proof.py`.
Pode repetir-se enquanto a sessão própria do Hub estiver aberta:

```bash
uv run --project /home/proteu/pagecraft --with playwright python \
  /tmp/pagecraft-delegate/check-catalog-years-proof.py
```

Artefactos locais, fora do repositório:

- `/tmp/pagecraft-catalog-years-proof/before-after.json`
- `/tmp/pagecraft-catalog-years-proof/4c6ba90-tinkercad-3-1280.png`
- `/tmp/pagecraft-catalog-years-proof/after-tinkercad-3-1280.png`
- `/tmp/pagecraft-catalog-years-proof/after-tinkercad-4-1280.png`
- `/tmp/pagecraft-catalog-years-proof/after-tinkercad-3-390.png`

A comparação mediu uma largura de página de 726 px no viewport de 390 px,
tanto na base como depois da alteração. Esse transbordo preexistente fica
fora desta correção. O carimbo novo apresenta os dois anos sem cortar texto.

Verificações adicionais:

```bash
node --check server/static/teacher/common.js
node --check server/static/teacher/class.js
node --check server/static/teacher/app.js
bash skills/sync-from-canonical.sh --check
git diff --check
git diff 4c6ba90 -- activities
```

Sem erros de sintaxe ou whitespace, sem drift dos conteúdos canónicos e
sem alterações nas atividades. A sessão própria do Hub foi fechada no fim.
Nenhuma PR foi aberta e não houve merge.

## Commits de implementação

- `a2b3ebb`: normalização comum, índice, API e testes.
- `c2472b9`: pertença e rótulos nos clientes, com testes de browser.
- `c5d86e4`: preservação do destino histórico na republicação e prova da CLI.
- `d2272e3`: preservação de anos explícitos no gerador de variantes.
- `bb7dc23`: rótulos normalizados nas fichas gerais.

A documentação segue num commit próprio. A branch local fica pronta para a
revisão independente e criação de PR pelo agente principal.
