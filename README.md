# PageCraft

Catálogo público de atividades interativas criadas para contexto educativo.

## Objetivo
Este repositório agrega atividades HTML self-contained (funcionam offline no browser) e materiais de apoio para o professor.

Cada atividade vive em `activities/<slug>/`.

## Estrutura
```text
pagecraft/
  index.html               # landing page do catálogo
  catalog.json             # índice das atividades
  activities/
    <slug>/
      index.html           # atividade para alunos
      teacher.md           # guia rápido para professor
      docspec.json         # especificação estruturada (DocSpec)
      meta.json            # metadados (título, ano, tags, etc.)
  skills/                  # skills e variantes por harness (opcional)
  ATTRIBUTION.md           # regras e template de atribuição
  CONTRIBUTING.md          # como contribuir
  LICENSE                  # CC BY-SA 4.0 (texto integral)
```

## Como adicionar uma atividade
1. Criar pasta `activities/<slug>/`.
2. Adicionar `index.html`, `teacher.md`, `docspec.json` e `meta.json`.
3. Atualizar `catalog.json` com a nova entrada.
4. Validar se `index.html` abre localmente sem dependências externas.
5. Garantir que o conteúdo respeita as regras de atribuição em `ATTRIBUTION.md`.

## Licenciamento
Este projeto está licenciado sob **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.

- Podes partilhar e adaptar os materiais.
- Tens de dar atribuição adequada.
- Derivados devem manter a mesma licença (ShareAlike).

Texto completo: ver [`LICENSE`](./LICENSE).
