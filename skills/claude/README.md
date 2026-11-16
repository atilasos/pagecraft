# PageCraft — skill para Claude Code

Este ficheiro destina-se a pessoas. O agente lê `SKILL.md`.

- **Invocar:** `/pagecraft cria uma atividade de 45 minutos para o 3.º ano sobre frações`.
- **Instalação no projeto:** já vem versionada. `.claude/skills/pagecraft` é um link para `skills/claude`, e os subagentes estão em `.claude/agents/`. Se faltar algum, corre `bash skills/claude/install.sh`.
- **Instalação global:** `bash skills/claude/install.sh --user`, que cria links em `~/.claude/`.
- **Requisitos:**
  - `uv` e o ambiente do repositório, porque os scripts importam `server/`;
  - o serviço PageCraft em `127.0.0.1:8777`, para registar e publicar;
  - a skill `sebenta-wiki`;
  - um browser: `preview_*` no T3 ou `agent-browser-hub`.
- **Modelos:** cada subagente declara `model:`.

  | Subagente | Modelo |
  |---|---|
  | Architect | opus |
  | Designer | sonnet |
  | Builder | sonnet |
  | Proofreader | sonnet |
  | Evaluator | opus |

  No T3 Code, `references/routing.md` distribui as fases por vários fornecedores.
- **Manutenção:** estes ficheiros são próprios de cada harness e editam-se aqui: `SKILL.md`, `README.md`, `install.sh` e `CANONICAL.md`. O resto é sincronizado. Ver `CANONICAL.md`.
