---
name: pagecraft
description: Gerar páginas PageCraft em OpenCode/Oh My OpenAgents: aulas HTML self-contained, interativas, pt-PT, acessíveis e verificadas no browser. Usa a skill PageCraft original em `skills/openclaw/` como pacote operacional, mas consulta o conhecimento pedagógico canónico no vault `~/.openclaw/workspace/vault`.
metadata:
  author: pagecraft
  version: "0.2.0"
---

# PageCraft para OpenCode / Oh My OpenAgents

Esta skill é a camada OpenCode para gerar páginas PageCraft. Ela **não duplica a pedagogia**: reutiliza scripts, identidades e templates de `skills/openclaw/`, mas a fundamentação pedagógica deve ser consultada no vault.

## Quando usar

Usa esta skill quando o utilizador pedir:

- página/aula PageCraft;
- atividade digital interativa para crianças 4–10 anos;
- explorable explanation, quiz, drag/drop, sliders, recombinação, mini-avaliação;
- página M28P ou atividade de leitura/escrita inicial;
- atividade com extensão maker, MEM, diferenciação ou currículo português.

Não usar para páginas estáticas simples sem componente pedagógica/interativa.

## Fontes de verdade

1. **Regras técnicas e design do repo:** `CLAUDE.md`.
2. **Pacote operacional PageCraft:** `skills/openclaw/`.
3. **Conhecimento pedagógico canónico:** `~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md`.
4. **Fontes oficiais no vault:** `~/.openclaw/workspace/vault/documentos-oficiais/`.

Se houver conflito: pedido explícito válido do utilizador → `CLAUDE.md` → vault → identidades/referências de `skills/openclaw/`.

## Recursos reutilizados da skill PageCraft original

- `skills/openclaw/SKILL.md` — pipeline original e critérios.
- `skills/openclaw/identities/architect.md` — DocSpec/arquitetura pedagógica.
- `skills/openclaw/identities/designer.md` — design-spec.
- `skills/openclaw/identities/builder.md` — HTML/CSS/JS.
- `skills/openclaw/identities/proofreader.md` — revisão pt-PT AO90.
- `skills/openclaw/identities/evaluator.md` — avaliação final.
- `skills/openclaw/scripts/*.py` — geração de prompts, markdown e publicação.
- `skills/openclaw/assets/template-base.html` — base HTML.
- `skills/openclaw/references/*.md` — referências operacionais; usar como apoio, não como substituto do vault.

## Regras absolutas

- HTML final self-contained: sem CDN, frameworks, imports externos ou Google Fonts remotas.
- `<html lang="pt-PT">` e texto em português europeu/AO90.
- Touch-first: controlos interativos com mínimo 48×48 px.
- Acessibilidade: skip link, foco visível, labels/ARIA, alternativa a drag/drop por clique/teclado.
- Design infantil: quente, lúdico, legível, nunca corporativo/genérico.
- QA real no browser antes de declarar concluído.
- Git commit/push/publicação apenas com pedido explícito.

## Convenções OpenCode

- Criar `todos` para qualquer run com 2+ fases.
- Delegar fases especializadas quando fizer sentido:
  - Architect / Proofreader → `category="writing"`.
  - Designer / UI/UX / Builder visual → `category="visual-engineering"` com `frontend-ui-ux` se disponível.
  - Implementação ou iteração longa → `category="deep"`.
  - Dúvidas arquiteturais/QA pós-implementação significativa → Oracle.
- Para browser/QA visual, carregar `/playwright` quando disponível e usar verificação real.
- Não usar instruções específicas OpenClaw como requisito funcional: ACP/acpx, ações de browser próprias do OpenClaw, `agentId` ou runtime ACP.

## Ambiente

Assumir `REPO_ROOT` como a raiz do repo PageCraft. Se a skill for invocada fora do repo, usar:

```bash
REPO_ROOT="/Users/igor/dev/pagecraft"
```

Ao correr scripts, exportar:

```bash
PAGECRAFT_WORKSPACE="$REPO_ROOT"
PAGECRAFT_REPO="$REPO_ROOT"
PAGECRAFT_VAULT="$HOME/.openclaw/workspace/vault"
```

Artefactos temporários devem ficar em `outputs/lessons/` dentro do repo, salvo pedido contrário.

## Pipeline OpenCode

### 0. Orchestrator

Normalizar `topic`, `year`, `duration`, `maker`, constraints e `slug`. Se a run for mais que trivial, manter:

- `outputs/lessons/<slug>-run-manifest.json`
- `outputs/lessons/<slug>-iteration-log.md`

### 1. Carregar pedagogia do vault

Antes do DocSpec, consultar:

- `~/.openclaw/workspace/vault/Knowledge/PageCraft/PageCraft-pedagogia-vault.md`
- documentos oficiais relevantes em `~/.openclaw/workspace/vault/documentos-oficiais/`
- notas MEM/diferenciação/avaliação quando o tema o exigir.

O DocSpec deve citar fontes do vault no campo curricular sempre que possível.

### 2. Architect — DocSpec-AM

Gerar prompt base:

```bash
PAGECRAFT_WORKSPACE="$REPO_ROOT" PAGECRAFT_VAULT="$HOME/.openclaw/workspace/vault" \
python3 skills/openclaw/scripts/pagecraft.py --topic "<tema>" --year "<ano>" --duration <min> --architect-only
```

Ler:

- `skills/openclaw/identities/architect.md`
- `outputs/lessons/_last_architect_prompt.md`
- nota pedagógica PageCraft no vault.

Produzir JSON válido em `outputs/lessons/<slug>-docspec.json`.

### 3. Designer — design-spec

Ler:

- `skills/openclaw/identities/designer.md`
- `outputs/lessons/<slug>-docspec.json`
- `CLAUDE.md`

Produzir `outputs/lessons/<slug>-design-spec.json`. Para M28P, usar rigorosamente a paleta e `syllableColors` do `design-spec.json` da palavra quando existirem.

### 4. Builder — HTML

Gerar prompt base:

```bash
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/openclaw/scripts/build_prompt.py \
  outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>-builder-prompt.md
```

Ler:

- `skills/openclaw/identities/builder.md`
- `outputs/lessons/<slug>-builder-prompt.md`
- `outputs/lessons/<slug>-design-spec.json`
- `skills/openclaw/assets/template-base.html`
- `CLAUDE.md`

Produzir `outputs/lessons/<slug>.html`. O HTML deve abrir offline e conter CSS/JS inline.

### 5. Guia do professor

Gerar markdown:

```bash
python3 skills/openclaw/scripts/build_markdown.py outputs/lessons/<slug>-docspec.json > outputs/lessons/<slug>.md
```

### 6. Proofreader pt-PT AO90

Ler:

- `skills/openclaw/identities/proofreader.md`
- HTML final;
- DocSpec;
- fontes pedagógicas do vault quando houver dúvida.

Produzir `outputs/lessons/<slug>-proofread-v1.json`. Corrigir problemas textuais no HTML sem regredir a intenção pedagógica.

### 7. Evaluator / QA real

Obrigatório antes de concluir.

Verificar pelo menos:

- página abre sem erro fatal;
- consola sem erros críticos;
- uma interação principal funciona;
- layout mobile/tablet/desktop utilizável;
- texto pt-PT adequado à idade;
- coerência entre objetivo, exploração, feedback e mini-avaliação;
- ficheiro não depende de internet.

Se falhar, criar repair ticket e rotear:

- pedagógico/estrutura → Architect;
- sistema visual → Designer;
- HTML/CSS/JS/UX/acessibilidade → Builder;
- texto → Builder com base no Proofreader.

## Done

Uma página PageCraft está pronta apenas quando existem:

1. `outputs/lessons/<slug>-docspec.json` válido;
2. `outputs/lessons/<slug>-design-spec.json` quando houver design dedicado;
3. `outputs/lessons/<slug>.html` self-contained;
4. `outputs/lessons/<slug>.md` se pedido ou se a run for publicável;
5. prova de QA real no browser;
6. nenhum erro crítico de acessibilidade, consola, layout ou texto.

## Publicação no catálogo

Só publicar com pedido explícito do utilizador.

```bash
PAGECRAFT_REPO="$REPO_ROOT" python3 skills/openclaw/scripts/publish_to_catalog.py \
  --slug <slug> \
  --html outputs/lessons/<slug>.html \
  --md outputs/lessons/<slug>.md \
  --docspec outputs/lessons/<slug>-docspec.json \
  --design-spec outputs/lessons/<slug>-design-spec.json
```

Depois validar `activities/<slug>/`, `catalog.json` e só fazer commit/push se o utilizador pedir explicitamente.
