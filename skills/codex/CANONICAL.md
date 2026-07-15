# Fonte canónica

Os ficheiros partilhados desta skill (`assets/`, `references/`, `identities/`, `scripts/`)
**não devem ser editados directamente aqui**. As fontes de verdade são:

- `server/pipeline/prompts/` — identities, references e template-base
  (usadas pelo PageCraft Studio em runtime)
- `skills/shared/scripts/` — scripts CLI (build_prompt, build_markdown,
  pagecraft, publish_to_catalog)

Para propagar mudanças:

```bash
bash skills/sync-from-canonical.sh
```

Para verificar drift no CI:

```bash
bash skills/sync-from-canonical.sh --check
```

Ficheiros específicos deste harness (não sincronizados) e que podem ser editados aqui:

- `SKILL.md`
- `README.md`
- `install.sh` (quando exista)
- `agents/*.md`
- `CANONICAL.md` (este ficheiro)
