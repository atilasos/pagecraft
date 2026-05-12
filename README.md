# PageCraft

Atividades HTML interativas para o 1.º ciclo do ensino básico (6–10 anos), produzidas por um *pipeline* multi-agente e publicadas como catálogo público.

Cada atividade é um ficheiro `.html` único, *self-contained* (CSS + JS *inline*), que funciona offline, em tablet e em quadro interativo, sem dependências externas.

## O que está aqui

O repositório tem duas metades:

1. **Catálogo público** (`activities/`, `catalog.json`, `index.html`, `viewer.html`) — as atividades publicadas, prontas a usar em sala.
2. **Sistema de produção** (`skills/`, `outputs/lessons/`, `scripts/`) — *prompts*, identidades dos agentes, *template* base e artefactos das *runs* que dão origem às atividades.

## Quem é o público

Crianças do 1.º ciclo (6–10 anos), com tolerância para pré-escolar (4–5). O sistema de design força mínimos concretos por faixa etária (tipografia ≥18/20/22/24 px, áreas tocáveis ≥48/56/64 px, frases curtas, *feedback* nunca punitivo, *opt-in* de áudio, contraste WCAG AA e AAA em microcopy crítico). A fonte de verdade é [`skills/openclaw/references/age-adaptation.md`](skills/openclaw/references/age-adaptation.md).

## Pipeline de produção

Cada atividade passa por cinco papéis especializados, cada um com identidade própria em `skills/openclaw/identities/`:

```
Tópico + ano + duração + [maker]
  → 1. Architect      (DocSpec-AM: pedagogia, AE, MEM, SRTC-A)
  → 2. Designer       (design-spec: paleta OKLCH, tipografia, componentes)
  → 3. Builder        (HTML/CSS/JS interativo, self-contained)
  → 4. Proofreader    (revisão pt-PT AO90, adequação à faixa etária)
  → 5. Evaluator      (verificação no browser real, decisão pass/fail)
  → loop de reparação até passar ou esgotar iterações
```

O *spec* completo está em [`skills/openclaw/SKILL.md`](skills/openclaw/SKILL.md). Cada *run* deixa artefactos em `outputs/lessons/<slug>-*` (`docspec`, `design-spec`, `proofread`, `evaluation`, `iteration-log`, `run-manifest`).

## Estrutura

```text
pagecraft/
  index.html             # landing do catálogo público
  viewer.html            # visualizador genérico de atividade
  catalog.json           # índice das atividades publicadas
  activities/<slug>/     # cada atividade publicada
    index.html
    teacher.md
    docspec.json
    meta.json
  outputs/lessons/       # staging de runs do pipeline (pré-publicação)
    <slug>.html
    <slug>.md
    <slug>-docspec.json
    <slug>-design-spec.json
    <slug>-proofread-vN.json
    <slug>-evaluation-vN.json
    <slug>-iteration-log.md
    <slug>-run-manifest.json
  skills/
    openclaw/            # fonte canónica da skill
      SKILL.md
      identities/        # prompts dos agentes
      references/        # docspec-schema, age-adaptation, patterns, AE
      assets/template-base.html
      scripts/           # build_prompt, build_markdown, pagecraft, publish
    claude/              # variante para Claude Code (consome o canónico)
    codex/               # variante para Codex
    opencode/            # shim
    sync-from-canonical.sh   # propaga o canónico para os harnesses
  scripts/               # utilitários do catálogo
  ATTRIBUTION.md
  LICENSE
```

## Instalar e usar a skill

Para usar o *pipeline* a partir do Claude Code (ou variante):

```bash
# instalação no diretório atual (.claude/)
bash skills/claude/install.sh

# instalação no perfil do utilizador (~/.claude/)
bash skills/claude/install.sh --user
```

Depois, dentro de uma sessão Claude Code, invocar:

```
/pagecraft cria uma página de 30 minutos para o 3.º ano sobre verbos no indicativo
```

O `install.sh` corre primeiro `skills/sync-from-canonical.sh` para garantir que o *harness* recebe o conteúdo canónico do `openclaw/`.

Para verificar *drift* entre canónico e *harnesses* (útil em CI):

```bash
bash skills/sync-from-canonical.sh --check
```

## Publicar uma atividade no catálogo

Quando o Evaluator dá *pass* sem itens *critical*, o *orchestrator* publica via:

```bash
python3 skills/openclaw/scripts/publish_to_catalog.py \
  --slug <slug> \
  --html outputs/lessons/<slug>.html \
  --md outputs/lessons/<slug>.md \
  --docspec outputs/lessons/<slug>-docspec.json \
  --repo <caminho-do-repo-catalogo> \
  --maker minecraft|lego|none \
  --tags "tag1,tag2"
```

O script copia os artefactos para `activities/<slug>/`, gera/atualiza `meta.json` e `catalog.json`, e respeita `createdAt` quando o *slug* já existe.

## Princípios não negociáveis

- HTML *self-contained* (CSS + JS *inline*), sem CDN, sem fontes remotas, sem dependências externas.
- pt-PT (AO90).
- Diferenciação obrigatória em três níveis (apoio, intermédio, desafio), sem metáfora semáforo.
- *Constraint* pedagógico **descoberto** pela interação, nunca declarado em texto.
- *Feedback* não punitivo: âmbar e "Quase! Tenta de novo", nunca vermelho de erro.
- Áudio *opt-in*, nunca canal único de significado.
- Acessibilidade: `:focus-visible`, ARIA correto, `prefers-reduced-motion`, contraste AA/AAA.

Detalhe operacional em [`skills/openclaw/identities/builder.md`](skills/openclaw/identities/builder.md) e [`skills/openclaw/identities/designer.md`](skills/openclaw/identities/designer.md).

## Licença

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). Texto completo em [`LICENSE`](./LICENSE). Partilhar e adaptar são permitidos; atribuição obrigatória; derivados mantêm a mesma licença.
