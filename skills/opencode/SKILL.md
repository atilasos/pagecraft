---
name: pagecraft
description: "Cria atividades PageCraft para o 1.º ciclo em OpenCode: páginas HTML interativas e self-contained em pt-PT, com diferenciação, apoio contextual, gates determinísticos, QA em browser e rascunho para aprovação do professor. Usar quando for pedida uma atividade, aula ou página interativa PageCraft, ou a reparação de um rascunho PageCraft."
---

# PageCraft em OpenCode

Esta variante não tem pedagogia nem percurso próprios. Usa o pacote `skills/claude/` do repositório, com `SKILL_DIR=skills/claude`.

1. Lê `skills/claude/SKILL.md` e segue-o integralmente: invariantes, percurso, gates e publicação.
2. Para cada fase, usa um subagente OpenCode que recebe como instrução o contrato `skills/claude/agents/pagecraft-<fase>.md`. Escolhe o modelo segundo `skills/claude/references/routing.md`. Quem avalia é de família diferente de quem construiu.
3. Se não houver subagentes, executa as fases em sequência. Antes de passar à fase seguinte, escreve o artefacto da fase e corre `uv run python skills/claude/scripts/pagecraft_check.py check <slug> --phase <fase>`. A mesma sessão não aprova o que produziu: sem revisão independente, o Evaluator não emite `pass:true`.
4. Para o browser, usa a skill `agent-browser-hub`. Se não estiver disponível, regista a limitação no `blocked_by` da avaliação.
