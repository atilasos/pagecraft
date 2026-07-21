# PageCraft — instruções para agentes

## Commits

- Fazemos sempre commits **pequenos e incrementais**: cada passo lógico concluído (um ficheiro de config, uma correção, uma funcionalidade mínima) é commitado de imediato, sem esperar por aprovação.
- O objetivo é poder voltar atrás facilmente com `git revert`/`git reset` — nunca acumular um diff grande por commitar.
- Mensagens curtas e descritivas em português; um commit nunca mistura alterações não relacionadas.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`atilasos/pagecraft`, via the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary — the five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), each label equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
