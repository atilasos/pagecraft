# Guias do professor com diferenciação neutra

## Problema e requisito

Na base `480521e`, o exportador do Studio acrescenta semáforos aos níveis de
diferenciação do guia Markdown. A CLI canónica já remove os semáforos, mas mantém
os nomes antigos ao lado dos novos. `CONTEXT.md` pede nomes que descrevem o
trabalho; `PRODUCT.md` e `DESIGN.md` rejeitam a paleta semáforo nos níveis.

Reproduzir com o `DOCSPEC` sintético de `tests/test_markdown_export.py`: chamar
`server.markdown_export.docspec_to_markdown(DOCSPEC)` ou guardar o objeto como
JSON e executar `python3 skills/shared/scripts/build_markdown.py docspec.json`.

## Critérios de aceitação

- Os novos guias do Studio e da CLI usam `Com pistas`, `Passo a passo` e
  `Mais desafios`, sem semáforos acrescentados pelo exportador.
- Os textos continuam associados a `support`, `standard` e `challenge`, pela
  mesma ordem. Os identificadores internos permanecem iguais.
- As variantes Claude e Codex correspondem à fonte canónica.
- Nenhum artefacto publicado ou histórico é reescrito.

## Evidência antes e depois

Antes, o Studio produz `- 🟢 Apoio: Slider com 3 posições`,
`- 🟡 Intermédio: Slider contínuo` e `- 🔴 Desafio: Gráfico de energia`.
A CLI produz `Com pistas — Apoio`, `Passo a passo — Intermédio` e
`Mais desafios — Desafio`, com os mesmos conteúdos.

Depois, os quatro percursos produzem exatamente:

```markdown
- Com pistas: Slider com 3 posições
- Passo a passo: Slider contínuo
- Mais desafios: Gráfico de energia
```

Verificação em 2026-10-22:

- `uv run pytest tests/test_markdown_export.py -q`: 6 testes passaram. A cobertura
  inclui a função usada pelo Studio e subprocessos reais dos três scripts CLI,
  com verificação dos conteúdos e ausência dos três emojis semáforo na saída.
- `bash skills/sync-from-canonical.sh --check`: sem divergências.
- `git diff --check`: sem erros.

## Fundamento pedagógico e limites

O mandato do agente pai fornece a leitura integral da Sebenta por API de
[[Diferenciação Pedagógica]], [[Avaliação Formativa]] e [[Avaliação Cooperada]].
Estas páginas estão em revisão, com confiança média; não certificam a alteração.

Os nomes descrevem apoios e propostas de trabalho, em coerência com metas comuns,
apoios variados e livre escolha, sem rótulos pessoais nem grupos fixos. Retirar o
semáforo evita associar os percursos a uma classificação visual. A mudança de
vocabulário, por si só, não comprova avaliação formativa nem regulação pelo aluno.
Essas práticas exigem ajustar apoios a partir de evidências, trabalhar o erro e
manter a voz da criança distinta da interpretação docente.

A correção altera apenas os rótulos que os exportadores acrescentam. Texto livre
do DocSpec pode continuar a conter vocabulário antigo ou emojis. Os guias já
entregues mantêm o conteúdo original, respeitando o cuidado com artefactos
publicados expresso no ADR 0002.

## Oportunidades adiadas

Rever o conteúdo pedagógico livre dos futuros DocSpecs e recolher apreciação do
professor sobre os nomes. Migrar guias históricos exigiria uma decisão própria.
Não se alteram HTML, registos de alunos, acontecimentos da ponte nem publicação.
