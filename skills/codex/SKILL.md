---
name: pagecraft-codex
description: "Criar páginas PageCraft no Codex: aulas HTML self-contained, interativas, pt-PT, acessíveis e verificadas no browser para crianças 4-10 anos, seguindo o fluxo multi-agente da skill OpenClaw (Architect → Designer → Builder → Proofreader → Evaluator). Usa o vault pedagógico em ~/.openclaw/workspace/vault, DocSpec/SRTC-A, MEM, Aprendizagens Essenciais, Perfil do Aluno, diferenciação obrigatória e extensões Maker quando pedidas. Usar quando o utilizador pedir uma página/aula PageCraft, explorable explanation, atividade digital com sliders/drag/quiz, M28P, ou atividade maker com componente digital."
metadata:
  author: pagecraft
  version: "0.1.0"
---

# PageCraft para Codex

Esta skill adapta a skill OpenClaw `skills/openclaw/` para o Codex. O objetivo é produzir páginas pedagógicas PageCraft com o mesmo rigor: **papéis especializados, artefactos explícitos, QA real e iteração até qualidade suficiente**.

Ao invocar esta skill, o pedido do utilizador autoriza o uso de **Codex native subagents** para as fases especializadas abaixo. O orquestrador continua responsável pela integração e pela verificação final.

## Fontes de verdade

1. Pedido explícito do utilizador/professor, desde que não viole acessibilidade/segurança.
2. Regras técnicas do repo: `CLAUDE.md`.
3. Pedagogia canónica do vault: `~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md`.
4. Fontes oficiais no vault: `~/.openclaw/workspace/vault/documentos-oficiais/`.
5. Recursos desta skill: `identities/`, `references/`, `assets/`, `scripts/`.
6. Skill OpenClaw original (`skills/openclaw/`) como referência histórica se houver dúvida.

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

## Papéis especializados Codex

O orquestrador não deve “fazer tudo sozinho”. Cada fase usa uma identidade/prompt próprio e, quando possível, um subagente diferente:

| Fase | Subagente Codex recomendado | Identidade | Output |
|---|---|---|---|
| Architect | `architect` | `identities/architect.md` | `<slug>-docspec.json` |
| Designer | `designer` | `identities/designer.md` | `<slug>-design-spec.json` |
| Builder | `executor` | `identities/builder.md` | `<slug>.html` |
| Proofreader | `writer` | `identities/proofreader.md` | `<slug>-proofread-vN.json` |
| Evaluator | `verifier` (ou `vision` se houver screenshots) | `identities/evaluator.md` | `<slug>-evaluation-vN.json` / repair ticket |

Se subagentes não estiverem disponíveis, manter a separação por artefactos e prompts: executar as fases sequencialmente, sem misturar responsabilidades.

## Ambiente

Assumir `REPO_ROOT` como a raiz do repo PageCraft. Se necessário:

```bash
REPO_ROOT="/Users/igor/dev/pagecraft"
export PAGECRAFT_WORKSPACE="$REPO_ROOT"
export PAGECRAFT_REPO="$REPO_ROOT"
export PAGECRAFT_VAULT="$HOME/.openclaw/workspace/vault"
```

Artefactos de trabalho ficam em `outputs/lessons/`.

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
    "architect": "codex architect",
    "designer": "codex designer",
    "builder": "codex executor",
    "proofreader": "codex writer",
    "evaluator": "codex verifier"
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
python3 skills/codex/scripts/pagecraft.py \
  --topic "<tema>" --year "<ano>" --duration <min> --architect-only \
  --output-dir outputs/lessons
```

Dar ao subagente Architect:

- `identities/architect.md`;
- `outputs/lessons/_last_architect_prompt.md`;
- excertos relevantes do vault;
- `references/docspec-schema.md`, quando precisar do schema completo.

Output: JSON válido em `outputs/lessons/<slug>-docspec.json`.

Critérios mínimos do DocSpec:

- SRTC-A completo por unidade: State, Render, Transition, Constraint, Assessment;
- duração das unidades compatível com a duração total;
- AE/Perfil do Aluno específicos quando existirem;
- MEM explícito;
- diferenciação real em três níveis;
- maker apenas quando pedido ou pedagogicamente justificado e aceite pelo pedido.

### 3. Designer — design-spec

Dar ao subagente Designer:

- `identities/designer.md`;
- `outputs/lessons/<slug>-docspec.json`;
- `CLAUDE.md`;
- contexto visual/M28P relevante, se existir.

Output: `outputs/lessons/<slug>-design-spec.json`.

O design deve ser infantil, quente, legível, acessível e implementável sem dependências externas. Para M28P, respeitar rigorosamente a paleta e `syllableColors` quando definidos.

### 4. Builder — HTML

Gerar prompt base:

```bash
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/codex/scripts/build_prompt.py \
  outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>-builder-prompt.md
```

Dar ao subagente Builder (`executor`) ownership apenas de:

- `outputs/lessons/<slug>.html`;
- correções subsequentes no HTML quando houver repair ticket.

Contexto do Builder:

- `identities/builder.md`;
- `outputs/lessons/<slug>-builder-prompt.md`;
- `outputs/lessons/<slug>-design-spec.json`;
- `assets/template-base.html`;
- `CLAUDE.md`.

Output: `outputs/lessons/<slug>.html`, offline, self-contained, com interações reais.

### 5. Guia do professor

Gerar Markdown:

```bash
python3 skills/codex/scripts/build_markdown.py \
  outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>.md
```

### 6. Proofreader pt-PT AO90

Dar ao subagente Proofreader:

- `identities/proofreader.md`;
- HTML final;
- DocSpec;
- fontes do vault quando houver dúvida.

Output: `outputs/lessons/<slug>-proofread-v1.json`.

Se houver problemas textuais, criar ticket para o Builder corrigir o HTML. Se houver problema pedagógico estrutural, rotear para Architect.

### 7. Evaluator / QA real

Obrigatório antes de concluir. Verificar com browser local (Playwright, browser MCP ou método disponível):

1. página abre sem erro fatal;
2. consola sem erros críticos;
3. pelo menos uma interação principal funciona;
4. layout mobile/tablet/desktop é utilizável;
5. texto pt-PT adequado à idade;
6. objetivo, exploração, feedback e assessment estão coerentes;
7. ficheiro não depende de internet;
8. resultados do Proofreader foram considerados.

Dar ao Evaluator:

- `identities/evaluator.md`;
- DocSpec;
- design-spec;
- HTML/snapshot/evidência de browser;
- consola;
- interação testada;
- proofread report.

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

- implementação/JS/CSS/layout/acessibilidade técnica → Builder;
- sistema visual/paleta/tipografia/consistência gráfica → Designer → Builder;
- texto/semântica/pt-PT → Proofreader ticket → Builder;
- conceção pedagógica/DocSpec/AE/MEM/diferenciação → Architect → Designer/Builder se necessário;
- múltiplas falhas críticas → Architect primeiro, depois Builder, depois Evaluator.

Cada reprovação gera `outputs/lessons/<slug>-repair-ticket-vN.json` e entrada em `<slug>-iteration-log.md` com `issues → ações → evidência → decisão`.

## Critério de “funcional”

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
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/codex/scripts/publish_to_catalog.py \
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

- `identities/architect.md` — especialista curricular/DocSpec-AM.
- `identities/designer.md` — sistema visual pedagógico.
- `identities/builder.md` — implementação HTML/CSS/JS.
- `identities/proofreader.md` — revisão pt-PT AO90.
- `identities/evaluator.md` — QA pedagógico/técnico/visual.
- `references/docspec-schema.md` — schema JSON completo.
- `references/interaction-patterns.md` — padrões de interação.
- `references/maker-patterns.md` — padrões maker/MEM.
- `references/ae-index.md` — índice operacional AE/PA.
- `references/srtc-examples.md` — exemplos por idade.
- `assets/template-base.html` — base HTML.
- `scripts/*.py` — prompts, markdown e publicação.
