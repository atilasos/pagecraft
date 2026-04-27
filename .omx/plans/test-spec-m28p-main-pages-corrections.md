# Test Spec — Correção M28P

## Testes obrigatórios

1. Auditoria canónica:
```bash
python3 scripts/audit_m28p_alignment.py --format both
```
Esperado: zero priority issues nas 28 páginas principais.

2. Validação de `leque`:
- `catalog.json`: duration 45;
- `activities/leque/meta.json`: duration 45;
- `activities/leque/docspec.json`: duration 45 e soma das units 45;
- `activities/leque/teacher.md`: fluxo/total 45;
- `activities/leque/index.html`: duração visível 45.

3. Relatórios:
```bash
python3 - <<'PY'
import json
from pathlib import Path
slugs = [...]  # 28 canónicos
for slug in slugs:
  assert json.loads((Path('activities')/slug/'proofread-v1.json').read_text())['pass'] is True
  assert json.loads((Path('activities')/slug/'evaluation-v1.json').read_text())['pass'] is True
PY
```

4. Offline scan:
- sem `http://`, `https://`, `<script src`, `<link href`, `@import`, `googleapis`, `fontUrl` nos artefactos relevantes ou allowlist justificada.

5. pt-PT/AO90 scan:
- sem tokens pt-BR/pre-AO críticos não allowlisted.

6. HTTP local:
- abrir as 28 páginas principais via servidor local.
- se não houver consola browser disponível, não alegar “console clean”; registar limitação e compensar com sintaxe JS/HTML/offline scan.

7. Prova de scope:
```bash
git diff --name-only
```
Esperado: nenhum caminho `*-cacador-silabas`, `*-frases-vivas` ou `activities/menina-30min` alterado.

## Evidência esperada no relatório final
- caminhos alterados;
- resumo do audit antes/depois;
- resultado HTTP local;
- resultado offline/pt-PT;
- prova de variantes intocadas;
- riscos restantes.
