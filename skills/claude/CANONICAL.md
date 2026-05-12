# Fonte canónica

Os ficheiros partilhados desta skill (`assets/`, `references/`, `identities/`, `scripts/`)
**não devem ser editados directamente aqui**. A fonte de verdade está em
`skills/openclaw/`.

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
- `install.sh`
- `agents/*.md`
- `CANONICAL.md` (este ficheiro)
