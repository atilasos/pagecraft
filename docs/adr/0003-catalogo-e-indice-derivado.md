# O Catálogo é um índice derivado, nunca escrito diretamente

`catalog.json` não é um sítio onde se escreve. A verdade de cada atividade vive no `meta.json` da própria atividade, e o catálogo é **regenerado** por varredura a partir de todas elas, em ordem canónica por slug, sempre que se publica. Quem quiser corrigir o catálogo corrige o `meta.json` e regenera. Decidido em 2026-07-30, ao dar uma costura única ao ato de publicar.

## Considered Options

A alternativa era um *upsert* que preservasse campos desconhecidos: o catálogo continuaria a ser estado próprio, e o módulo defendê-lo-ia contra escritores que não conhecem todas as chaves. Foi rejeitada porque preservar campos desconhecidos é uma defesa contra a divergência entre dois sítios de verdade — e derivar remove a divergência por construção, em vez de a gerir.

À data da decisão, o catálogo já era de facto uma projeção fiel dos 103 `meta.json`: zero divergências campo a campo, nenhum item órfão em qualquer sentido. A decisão reconhece o que os dados já diziam.

## Consequences

- Publicar passa a exigir commitar `catalog.json` junto com a atividade. Um teste de frescura regenera o índice e compara com o ficheiro commitado, por isso esquecer-se disso fica vermelho em vez de ficar em silêncio — que é o que acontecia antes.
- Apagar a diretoria de uma atividade basta para a tirar do catálogo. Não há operação de remoção; há regeneração.
- A ordem do ficheiro é por slug, e é deliberadamente burra. A ordem pedagógica do método M28P vive nos campos `order` e `variantIndex` de cada atividade e é desenhada por quem apresenta — nenhum leitor depende da ordem do ficheiro. Uma ordem canónica que dependesse de `order` teria um caso especial permanente para as atividades que não pertencem ao método.
- Ninguém escreve no catálogo a partir de vários sítios, por isso deixa de ser possível que dois escritores discordem sobre o formato. O preço é que todo o caminho de publicação passa por um módulo só; um erro nesse módulo afeta tudo o que se publica.
- Reverter esta decisão depois de os escritores deixarem de saber compor o ficheiro obriga a reintroduzir a composição em cada um deles e a reconciliar o que entretanto divergiu.
