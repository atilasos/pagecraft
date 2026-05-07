# PageCraft — Claude Code skill

Pipeline multi-agente para gerar **páginas PageCraft**: aulas HTML self-contained, interativas, em português europeu (AO90), acessíveis e verificadas no browser, para crianças dos 4 aos 10 anos.

Cada fase corre num subagente Claude Code dedicado:

| Fase | Subagente | Modelo | Output |
|------|-----------|--------|--------|
| 1. Architect | `pagecraft-architect` | **opus** | `<slug>-docspec.json` |
| 2. Designer | `pagecraft-designer` | sonnet | `<slug>-design-spec.json` |
| 3. Builder | `pagecraft-builder` | sonnet | `<slug>.html` (self-contained) |
| 4. Proofreader | `pagecraft-proofreader` | **haiku** | `<slug>-proofread-vN.json` |
| 5. Evaluator | `pagecraft-evaluator` | sonnet | `<slug>-evaluation-vN.json` |

A sessão principal (orquestrador) coordena, valida artefactos, despacha repair tickets — não faz o trabalho dos subagentes.

## Requisitos

- **Claude Code** (CLI, app desktop, ou extensão IDE) com acesso aos modelos Opus 4.7, Sonnet 4.6 e Haiku 4.5.
- **Python 3** disponível no PATH (usado pelos scripts de geração de prompts e markdown).
- **Repo PageCraft** clonado localmente. A skill assume a estrutura do repo (`outputs/lessons/`, `activities/`, `catalog.json`, `CLAUDE.md`).
- **Opcional — para QA real no browser:** Chrome com a extensão Claude in Chrome, expondo as tools `mcp__claude-in-chrome__*`.
- **Opcional — para citações curriculares:** uma pasta vault com pedagogia canónica (default: `~/.openclaw/workspace/vault/`). Se não existir, a página continua a ser gerada, mas o DocSpec não cita Aprendizagens Essenciais nem Perfil do Aluno.

## Instalação

A partir da raiz do repo PageCraft:

```bash
# Instalação por projeto — skill e subagentes ficam em .claude/ deste repo
bash skills/claude/install.sh

# Instalação global — disponível em todos os projetos
bash skills/claude/install.sh --user
```

O que o instalador faz:

1. Copia `SKILL.md` + restantes recursos (`identities/`, `references/`, `assets/`, `scripts/`) para `.claude/skills/pagecraft/` (ou `~/.claude/skills/pagecraft/` com `--user`).
2. Copia os 5 subagentes `pagecraft-*.md` para `.claude/agents/` (ou `~/.claude/agents/`).
3. Não toca em `~/.openclaw/` nem em qualquer outro caminho fora dos diretórios Claude Code.

Para desinstalar:

```bash
bash skills/claude/install.sh --uninstall          # ou
bash skills/claude/install.sh --uninstall --user
```

## Utilização

Abrir o Claude Code dentro do repo PageCraft e invocar a skill:

```
/pagecraft cria uma página de 30 minutos para o 3.º ano sobre verbos no indicativo
```

Ou, sem slash, descrever o pedido — a skill dispara automaticamente quando o pedido envolve "página PageCraft", "aula interativa", "explorable explanation", etc. (ver `description` em `SKILL.md`).

O orquestrador irá:

- normalizar `topic`/`year`/`duration`/`maker`/`slug`;
- consultar o vault pedagógico (se existir);
- delegar Architect → Designer → Builder via `Agent` com `subagent_type`;
- gerar guia do professor (markdown);
- correr Proofreader e Evaluator em paralelo;
- iterar repair tickets até passar (máx. 3 iterações).

Publicação em `activities/<slug>/` + `catalog.json` apenas com pedido explícito ("publica no catálogo").

## Estrutura desta skill

```
skills/claude/
├── SKILL.md                  # entry point da skill (frontmatter + pipeline)
├── README.md                 # este ficheiro
├── install.sh                # instalador
├── agents/                   # subagentes Claude Code (frontmatter + identidade)
│   ├── pagecraft-architect.md
│   ├── pagecraft-designer.md
│   ├── pagecraft-builder.md
│   ├── pagecraft-proofreader.md
│   └── pagecraft-evaluator.md
├── identities/               # identidades canónicas detalhadas
├── references/               # schemas, padrões, índices
├── assets/                   # template-base.html
└── scripts/                  # geração de prompts, markdown e publicação
    ├── pagecraft.py
    ├── build_prompt.py
    ├── build_markdown.py
    └── publish_to_catalog.py
```

## Notas operacionais

- **Limite de output do Builder:** páginas com 5+ unidades excedem 32k tokens num único `Write`. O subagente Builder está instruído a escrever um skeleton primeiro e depois expandir cada unit via `Edit` — não tentar reverter para um único Write.
- **Vault opcional:** se `~/.openclaw/workspace/vault/` não existir, definir `PAGECRAFT_VAULT` para outra pasta ou simplesmente correr sem ele. O Architect adapta-se.
- **Browser para Evaluator:** se as tools `mcp__claude-in-chrome__*` não estiverem disponíveis, o Evaluator falha. Nesse caso, executar QA manualmente e descrever as evidências ao orquestrador.
- **Override de modelo por chamada:** para Builds invulgarmente pesados, passar `model: "opus"` no `Agent` Builder. Para repairs triviais, `model: "haiku"`.

## Licença e fonte

Esta skill faz parte do projeto PageCraft. A pedagogia subjacente (DocSpec-AM, SRTC-A, MEM, diferenciação, Aprendizagens Essenciais) é específica do contexto educativo português (1.º ciclo).
