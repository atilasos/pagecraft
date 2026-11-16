# Fonte canónica

Os ficheiros partilhados desta skill (`assets/`, `references/`, `identities/`, `scripts/`, `agents/*.md`)
**não devem ser editados diretamente aqui**. As fontes de verdade são:

- `server/pipeline/prompts/` — identities, references e template-base
  (usadas pelo PageCraft Studio em runtime)
- `skills/shared/scripts/` — scripts CLI (pagecraft_check, activity, build_prompt,
  build_markdown, pagecraft, publish_to_catalog)
- `skills/shared/agents/` — contratos de fase (também copiados para `.claude/agents/`)
- `skills/shared/references/` — percurso, encaminhamento de modelos e integração com realizações

Para propagar mudanças:

```bash
bash skills/sync-from-canonical.sh
```

Para verificar drift no CI:

```bash
bash skills/sync-from-canonical.sh --check
```

Ficheiros específicos deste harness (não sincronizados), editáveis aqui:

- `SKILL.md`
- `install.py`
- `references/runtime.md`
- `agents/openai.yaml`
- `CANONICAL.md` (este ficheiro)
