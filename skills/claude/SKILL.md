---
name: pagecraft-claude
description: "Criar páginas PageCraft em Claude Code: aulas HTML self-contained, interativas, pt-PT, acessíveis e verificadas no browser para crianças 4-10 anos, seguindo o fluxo multi-agente PageCraft (Architect → Designer → Builder → Proofreader → Evaluator) com subagentes dedicados do Claude Code (pagecraft-architect, pagecraft-designer, pagecraft-builder, pagecraft-proofreader, pagecraft-evaluator). Usa o vault pedagógico em ~/.openclaw/workspace/vault, DocSpec/SRTC-A, MEM, Aprendizagens Essenciais, Perfil do Aluno, diferenciação obrigatória e extensões Maker quando pedidas. Usar quando o utilizador pedir uma página/aula PageCraft, explorable explanation, atividade digital com sliders/drag/quiz, M28P, ou atividade maker com componente digital."
metadata:
  author: pagecraft
  version: "0.1.0"
---

# PageCraft para Claude Code

Esta skill é a versão Claude Code do pipeline PageCraft. Mantém o mesmo rigor da skill OpenClaw original e da skill `skills/codex/`: **papéis especializados, artefactos explícitos, QA real e iteração até qualidade suficiente**. A diferença é que cada fase especializada corre num **subagente nativo do Claude Code** (via tool `Agent` com `subagent_type`), não num agente ACP nem num subagente do Codex.

Ao invocar esta skill, o pedido do utilizador autoriza o uso dos seguintes subagentes:

- `pagecraft-architect`
- `pagecraft-designer`
- `pagecraft-builder`
- `pagecraft-proofreader`
- `pagecraft-evaluator`

O orquestrador (a sessão principal) coordena, valida artefactos e decide quando parar — não faz o trabalho dos subagentes.

## Fontes de verdade

1. Pedido explícito do utilizador/professor, desde que não viole acessibilidade/segurança.
2. Pedagogia canónica do vault: `~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md`.
3. Fontes oficiais no vault: `~/.openclaw/workspace/vault/documentos-oficiais/`.
4. Recursos desta skill: `identities/`, `references/`, `assets/`, `scripts/`, `agents/`.
5. `CLAUDE.md` do repo PageCraft (regras técnicas/design).
6. Skills irmãs (`skills/codex/`, `skills/openclaw/`) quando existirem no repo, como referência histórica se houver dúvida.

## Quando usar

Usa esta skill para:

- aulas/páginas PageCraft interativas;
- explicações exploráveis para crianças 4-10 anos;
- atividades com slider, drag/drop, matching, sorting, quiz, canvas ou simulação;
- atividades M28P/leitura-escrita inicial;
- páginas com diferenciação, MEM, Aprendizagens Essenciais ou maker.

Não usar para páginas HTML estáticas simples sem fluxo pedagógico/interativo.

## Regras absolutas

- HTML final único e self-contained: CSS+JS inline, sem CDN, imports externos, frameworks ou internet.
- `<html lang="pt-PT">`; português europeu AO90; linguagem adequada à idade.
- Touch-first: todos os controlos interativos com mínimo **48×48 px**.
- Acessibilidade: skip link, foco visível, labels/ARIA, contraste WCAG AA, alternativa a drag/drop por clique/teclado.
- Diferenciação obrigatória em três níveis: 🟢 Apoio, 🟡 Intermédio, 🔴 Desafio.
- O **Constraint** é descoberto pela interação; não entregar a regra como resposta pronta ao aluno.
- Assessment formativo, observável e ligado à interação principal.
- Maker é opcional, mas quando pedido é cooperativo, ligado ao digital e culmina em comunicação.
- QA real no browser antes de declarar concluído.
- Publicação/commit/push só com pedido explícito do utilizador.

## Papéis especializados Claude Code

O orquestrador não deve "fazer tudo sozinho". Cada fase usa um subagente dedicado com identidade própria. Os ficheiros estão em `agents/` e devem estar instalados em `.claude/agents/` (projeto) ou `~/.claude/agents/` (utilizador) para serem invocáveis via `Agent`.

| Fase | Subagente Claude Code | Identidade canónica | Output |
|---|---|---|---|
| Architect | `pagecraft-architect` | `identities/architect.md` | `<slug>-docspec.json` |
| Designer | `pagecraft-designer` | `identities/designer.md` | `<slug>-design-spec.json` |
| Builder | `pagecraft-builder` | `identities/builder.md` | `<slug>.html` |
| Proofreader | `pagecraft-proofreader` | `identities/proofreader.md` | `<slug>-proofread-vN.json` |
| Evaluator | `pagecraft-evaluator` | `identities/evaluator.md` | `<slug>-evaluation-vN.json` (+ `repair-ticket-vN.json` se reprovar) |

Se algum subagente não estiver disponível (ainda não copiado para `.claude/agents/`), o orquestrador deve copiá-lo de `skills/claude/agents/<nome>.md` antes de prosseguir, ou — em último recurso — manter a separação por artefactos e prompts e executar as fases sequencialmente sem misturar responsabilidades.

## Ambiente

Assumir `REPO_ROOT` como a raiz do repo PageCraft em uso (auto-detectada pelos scripts). Caso seja preciso forçar:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
export PAGECRAFT_WORKSPACE="$REPO_ROOT"
export PAGECRAFT_REPO="$REPO_ROOT"
# Vault é opcional. Definir só se existir uma pasta com pedagogia canónica:
# export PAGECRAFT_VAULT="$HOME/.openclaw/workspace/vault"
```

Os scripts em `skills/claude/scripts/` auto-detectam a raiz quando invocados de dentro do repo, e fazem fallback gracioso quando o vault não existe (a página continua a poder ser gerada, mas sem citações curriculares).

Artefactos de trabalho ficam em `outputs/lessons/`.

## Instalação

Ver `README.md` desta pasta para instruções completas. Resumo rápido:

```bash
# A partir da raiz do repo PageCraft:
bash skills/claude/install.sh           # instalação por projeto (.claude/)
bash skills/claude/install.sh --user    # instalação global (~/.claude/)
```

O script copia a skill para `.claude/skills/pagecraft/` e os subagentes para `.claude/agents/`. Os subagentes ficam imediatamente disponíveis para `Agent(subagent_type="pagecraft-architect", ...)`, etc. Cada agente já declara `tools` e `model` no frontmatter (Architect=opus, Proofreader=haiku, restantes=sonnet).

## Pipeline obrigatório

### 0. Orchestrator

Normalizar `topic`, `year`, `duration`, `maker`, restrições e `slug`. Para qualquer run não-trivial, criar:

- `outputs/lessons/<slug>-run-manifest.json`
- `outputs/lessons/<slug>-iteration-log.md`

Manifest mínimo:

```json
{
  "slug": "<slug>",
  "topic": "<tema>",
  "year": "<ano/faixa>",
  "duration": 45,
  "maker": "none|lego|minecraft|3d|robotics|whiteboard|...",
  "max_iterations": 3,
  "current_iteration": 0,
  "agents": {
    "architect": "pagecraft-architect",
    "designer": "pagecraft-designer",
    "builder": "pagecraft-builder",
    "proofreader": "pagecraft-proofreader",
    "evaluator": "pagecraft-evaluator"
  },
  "status": "planning|architect|designer|builder|proofreader|evaluator|repair|done|blocked",
  "artifacts": {}
}
```

### 1. Carregar pedagogia do vault

Antes do DocSpec, ler pelo menos:

- `~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md`
- documentos oficiais relevantes em `~/.openclaw/workspace/vault/documentos-oficiais/aprendizagens-essenciais/`
- Perfil dos Alunos em `~/.openclaw/workspace/vault/documentos-oficiais/`
- notas MEM/diferenciação/avaliação quando o tema o exigir.

O Architect deve distinguir evidência do vault de inferências próprias e deve citar ficheiros do vault no campo curricular sempre que útil.

### 2. Architect — DocSpec-AM

Gerar prompt base:

```bash
PAGECRAFT_WORKSPACE="$REPO_ROOT" PAGECRAFT_VAULT="$HOME/.openclaw/workspace/vault" \
python3 skills/claude/scripts/pagecraft.py \
  --topic "<tema>" --year "<ano>" --duration <min> --architect-only \
  --output-dir outputs/lessons
```

Lançar o subagente Architect:

```text
Agent(
  subagent_type="pagecraft-architect",
  description="Gerar DocSpec-AM",
  prompt="""
  Lê estes ficheiros antes de decidir:
  - skills/claude/identities/architect.md (a tua identidade)
  - outputs/lessons/_last_architect_prompt.md (prompt base)
  - skills/claude/references/docspec-schema.md (schema)
  - skills/claude/references/ae-index.md (AE/PA)
  - ~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md

  Pedido normalizado:
  - topic: <tema>
  - year: <ano>
  - duration: <min>
  - maker: <none|lego|...>
  - slug: <slug>

  Escreve APENAS JSON válido em outputs/lessons/<slug>-docspec.json com Write.
  """
)
```

Output: `outputs/lessons/<slug>-docspec.json`.

Critérios mínimos do DocSpec:

- SRTC-A completo por unidade: State, Render, Transition, Constraint, Assessment;
- duração das unidades compatível com a duração total;
- AE/Perfil do Aluno específicos quando existirem;
- MEM explícito;
- diferenciação real em três níveis;
- maker apenas quando pedido ou pedagogicamente justificado e aceite pelo pedido.

### 3. Designer — design-spec

Lançar:

```text
Agent(
  subagent_type="pagecraft-designer",
  description="Gerar design-spec",
  prompt="""
  Lê:
  - skills/claude/identities/designer.md
  - outputs/lessons/<slug>-docspec.json
  - CLAUDE.md
  Para M28P: respeita rigorosamente paleta e syllableColors do design-spec da palavra correspondente.

  Escreve APENAS JSON válido em outputs/lessons/<slug>-design-spec.json com Write.
  """
)
```

Output: `outputs/lessons/<slug>-design-spec.json`.

O design deve ser infantil, quente, legível, acessível e implementável sem dependências externas.

### 4. Builder — HTML

Gerar prompt base:

```bash
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/claude/scripts/build_prompt.py \
  outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>-builder-prompt.md
```

Lançar:

```text
Agent(
  subagent_type="pagecraft-builder",
  description="Construir HTML self-contained",
  prompt="""
  Lê:
  - skills/claude/identities/builder.md
  - outputs/lessons/<slug>-builder-prompt.md
  - outputs/lessons/<slug>-design-spec.json
  - skills/claude/assets/template-base.html
  - CLAUDE.md

  Escreve outputs/lessons/<slug>.html com Write.
  HTML único, CSS+JS inline, offline, touch-first, acessível.
  Implementa cada unit conforme SRTC-A. 3 níveis de diferenciação obrigatórios.
  """
)
```

Output: `outputs/lessons/<slug>.html`, offline, self-contained, com interações reais.

Em iterações de reparação, passar também o `outputs/lessons/<slug>-repair-ticket-vN.json` com routing `route:builder`.

### 5. Guia do professor

Gerar Markdown:

```bash
python3 skills/claude/scripts/build_markdown.py \
  outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>.md
```

### 6. Proofreader pt-PT AO90

Lançar:

```text
Agent(
  subagent_type="pagecraft-proofreader",
  description="Revisão pt-PT AO90",
  prompt="""
  Lê:
  - skills/claude/identities/proofreader.md
  - outputs/lessons/<slug>.html
  - outputs/lessons/<slug>-docspec.json

  Escreve APENAS JSON válido em outputs/lessons/<slug>-proofread-v1.json com Write.
  Não alteres o HTML; sinaliza issues e sugestões.
  """
)
```

Output: `outputs/lessons/<slug>-proofread-v1.json`.

Se houver problemas textuais, o orquestrador cria um ticket para o Builder corrigir o HTML. Se houver problema pedagógico estrutural, encaminha para o Architect.

### 7. Evaluator / QA real

Obrigatório antes de concluir.

Servir a página localmente (em background):

```bash
python3 -m http.server 8765 --directory "$REPO_ROOT" &
```

Lançar:

```text
Agent(
  subagent_type="pagecraft-evaluator",
  description="QA real no browser",
  prompt="""
  Lê:
  - skills/claude/identities/evaluator.md
  - outputs/lessons/<slug>.html
  - outputs/lessons/<slug>-docspec.json
  - outputs/lessons/<slug>-design-spec.json
  - outputs/lessons/<slug>-proofread-v1.json

  URL local: http://127.0.0.1:8765/outputs/lessons/<slug>.html

  Carrega ferramentas de browser via ToolSearch antes de chamar.
  Recolhe: snapshot, consola, pelo menos 1 interacção principal.
  Escreve outputs/lessons/<slug>-evaluation-vN.json com Write.
  Se reprovar, escreve outputs/lessons/<slug>-repair-ticket-vN.json com a route apropriada.
  """
)
```

Verificar pelo menos:

1. página abre sem erro fatal;
2. consola sem erros críticos;
3. pelo menos uma interação principal funciona;
4. layout mobile/tablet/desktop é utilizável;
5. texto pt-PT adequado à idade;
6. objetivo, exploração, feedback e assessment estão coerentes;
7. ficheiro não depende de internet;
8. resultados do Proofreader foram considerados.

Output esperado:

```json
{
  "pass": true,
  "route": "builder|designer|architect|proofreader|both|none",
  "severity": "low|medium|high|critical",
  "issues": [],
  "required_fixes": [],
  "evidence": [],
  "acceptance_checks": []
}
```

### 8. Loop de reparação

Iterar até `pass:true` sem `critical` ou até `max_iterations = 3`.

Routing:

- implementação/JS/CSS/layout/acessibilidade técnica → `pagecraft-builder`;
- sistema visual/paleta/tipografia/consistência gráfica → `pagecraft-designer` → `pagecraft-builder`;
- texto/semântica/pt-PT → ticket para `pagecraft-builder` com base no `proofread-vN.json`;
- conceção pedagógica/DocSpec/AE/MEM/diferenciação → `pagecraft-architect` → `pagecraft-designer`/`pagecraft-builder` se necessário;
- múltiplas falhas críticas → Architect primeiro, depois Builder, depois Evaluator.

Cada reprovação gera `outputs/lessons/<slug>-repair-ticket-vN.json` e entrada em `<slug>-iteration-log.md` com `issues → ações → evidência → decisão`.

## Critério de "funcional"

A página só é funcional se:

1. abre sem erro fatal;
2. não há erro JS crítico;
3. a interação principal funciona;
4. conteúdo principal é legível em tablet/desktop;
5. existe percurso completo para o nível 🟡 Intermédio;
6. a atividade conduz à descoberta do constraint;
7. mini-avaliação é observável;
8. não depende de internet.

Se restarem apenas melhorias não-críticas após 3 iterações, aceitar como versão final e listar riscos/melhorias futuras. Se falhar um mínimo funcional, marcar `blocked` e explicar objetivamente.

## Done

Uma página PageCraft está pronta apenas quando existem:

- `<slug>-docspec.json` válido;
- `<slug>-design-spec.json` quando houver design dedicado;
- `<slug>.html` self-contained e testado;
- `<slug>.md` guia do professor;
- `<slug>-proofread-vN.json`;
- `<slug>-evaluation-vN.json` ou evidência equivalente;
- nenhum erro crítico de consola, acessibilidade, layout, texto ou pedagogia.

## Publicação no catálogo

Só publicar com pedido explícito.

```bash
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/claude/scripts/publish_to_catalog.py \
  --slug <slug> \
  --html outputs/lessons/<slug>.html \
  --md outputs/lessons/<slug>.md \
  --docspec outputs/lessons/<slug>-docspec.json \
  --design-spec outputs/lessons/<slug>-design-spec.json \
  --maker <maker-ou-none> \
  --tags "tag1,tag2"
```

Depois validar `activities/<slug>/`, `catalog.json` e só fazer commit/push se o utilizador pedir explicitamente.

## Recursos incluídos

- `agents/pagecraft-architect.md` — subagente Claude Code (DocSpec-AM).
- `agents/pagecraft-designer.md` — subagente Claude Code (design-spec).
- `agents/pagecraft-builder.md` — subagente Claude Code (HTML self-contained).
- `agents/pagecraft-proofreader.md` — subagente Claude Code (revisão pt-PT AO90).
- `agents/pagecraft-evaluator.md` — subagente Claude Code (QA real no browser).
- `identities/*.md` — identidades canónicas (fonte de verdade dos prompts dos subagentes).
- `references/docspec-schema.md` — schema JSON completo.
- `references/interaction-patterns.md` — padrões de interação.
- `references/maker-patterns.md` — padrões maker/MEM.
- `references/ae-index.md` — índice operacional AE/PA.
- `references/age-adaptation.md` — fonte de verdade por faixa etária (tipografia, motricidade, patterns).
- `references/srtc-examples.md` — exemplos por idade.
- `assets/template-base.html` — base HTML.
- `scripts/*.py` — geração de prompts, markdown e publicação.
