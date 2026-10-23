# Anos destinatários do catálogo

O índice público `catalog.json`, `GET /api/activities` e as atividades de
`GET /api/meta` expõem `years: number[]`. O módulo `server/catalog_years.py`
resolve os anos para os três percursos.

## Declarações e precedência

`years` contém inteiros de 1 a 4, ordenados e sem duplicados. `[]` significa
que a atividade não declara anos destinatários. Estas atividades continuam
acessíveis em **Todos**, com o rótulo **Sem ano indicado**.

A resolução usa a primeira declaração disponível:

1. `meta.years`, incluindo uma lista vazia explícita.
2. Escolaridade explícita no campo histórico `meta.year`.
3. Escolaridade explícita em `docspec.ageRange`.
4. `[]` quando nenhum destes campos declara escolaridade.

Os formatos históricos incluem o número `3`, o texto `"3"`, `"3.º ano"`,
`"3.º e 4.º anos"`, `"3º e 4º anos"` e `"1.º ao 4.º ano"`.
Listas e intervalos exigem ordinais. `"3-4 anos"`, `"3 e 4 anos"` e
`"6–8 anos, ajustável"` são idades e não declaram escolaridade.

O normalizador ignora etiquetas, títulos, `meta.ageRange` isolado e anos das
referências curriculares. As AE continuam a fornecer a disciplina da API,
mas não os destinatários.

Uma declaração `years` inválida provoca `ValueError`, sem recorrer ao campo
histórico. São inválidos valores nulos, escalares, strings, booleanos,
números fracionários e inteiros fora de 1 a 4. A publicação valida os
metadados da atividade antes de escrever os seus artefactos. A regeneração
e a API também validam declarações explícitas dos metadados publicados.

## Publicação e republicação

O ato `server.publish.publish_activity` aceita `years` como propriedade
opcional do DocSpec. Valida e copia essa declaração para `meta.json` em
ordem canónica. Por exemplo, `"years": [4, 3, 4]` publica `[3, 4]`.
O esquema de geração já permite propriedades adicionais, por isso não muda.

Sem `docspec.years`, a republicação preserva a declaração explícita dos
metadados existentes. Se não existir, resolve a escolaridade histórica
com a precedência acima. Um DocSpec com apenas idades não apaga os anos
históricos já declarados. Para mudar o destino, o autor fornece `years`
explicitamente. A declaração `[]` permite remover uma atribuição anterior.

Os invólucros CLI das skills, o Studio e as atividades permanentes chamam o
mesmo ato de publicação. O gerador de variantes M28P preserva `years` da
própria variante, usando o mesmo validador. Não copia os anos da base para
uma declaração explícita da variante.

## Campos históricos e consumidores

`yearLabel` conserva a representação textual de `meta.year` na API e no
índice. O campo histórico `year` do índice mantém o valor original.
O `year` escalar da API fica definido apenas quando `years` contém um único
ano. Para vários anos ou nenhum, devolve `null`.

Os consumidores internos do catálogo usam pertença a `years`. Os rótulos
visíveis também usam essa lista. No agrupamento M28P, cada variante filtra
pelo seu próprio destino. O carimbo do grupo mostra a união dos destinos
dos resultados visíveis. Uma seleção escondida pelos filtros deixa de
poder lançar uma sessão.

Os anos das turmas, dos pedidos de geração e dos registos privados de
realizações são contratos distintos. Não consomem o ano escalar do catálogo.

O índice continua derivado segundo a ADR-0003. A regeneração lê apenas os
metadados e DocSpecs locais do checkout. Não reescreve atividades nem
preenche automaticamente `years` nos metadados existentes.
