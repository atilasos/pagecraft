#!/usr/bin/env python3
"""Verificações determinísticas do percurso PageCraft (sem IA).

Subcomandos:
  check <slug>   valida os artefactos de drafts/<slug>* contra os schemas do
                 Studio e o HTML contra os invariantes de validate_activity_html.
  lean <html>    imprime o HTML sem os blocos incorporados (fonte, componente
                 de apoio, data: URIs) para leitura económica por modelos.
  next <slug> <proofread|evaluation|repair-ticket>
                 imprime o caminho da próxima versão -vN.
  log <slug> --phase P --status S [--model M] [--artifact A] [--note N]
                 acrescenta uma entrada ao manifest drafts/<slug>-run-manifest.json.

Corre a partir da raiz do repositório: `uv run python <skill>/scripts/pagecraft_check.py ...`.
Saída JSON compacta; `check` termina com código 1 quando há erros.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_repo() -> Path:
    env = os.environ.get("PAGECRAFT_REPO")
    candidates = [Path(env)] if env else []
    candidates += [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]
    for path in candidates:
        if (path / "server/pipeline/validators.py").is_file():
            return path
    sys.exit("PageCraft não encontrado: corre na raiz do repositório ou define PAGECRAFT_REPO.")


REPO = find_repo()
sys.path.insert(0, str(REPO))

KINDS = ("proofread", "evaluation", "repair-ticket")
SCHEMAS = {
    "docspec": "docspec",
    "design-spec": "design-spec",
    "proofread": "proofread",
    "evaluation": "evaluation",
    "repair-ticket": "evaluation",
}


def versions(drafts: Path, slug: str, kind: str) -> list[tuple[int, Path]]:
    found = []
    for path in drafts.glob(f"{slug}-{kind}*.json"):
        match = re.fullmatch(rf"{re.escape(slug)}-{kind}(?:-v(\d+))?\.json", path.name)
        if match:
            found.append((int(match.group(1) or 0), path))
    return sorted(found)


def validate_json(path: Path, schema_name: str) -> list[str]:
    import jsonschema

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name}: JSON inválido ({exc.msg}, linha {exc.lineno})"]
    schema = json.loads((REPO / f"server/pipeline/schemas/{schema_name}.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{path.name}: {'/'.join(map(str, e.absolute_path)) or '(raiz)'}: {e.message}"
            for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))[:10]]


def cmd_check(args) -> int:
    from server.pipeline.validators import validate_activity_html

    drafts = Path(args.dir)
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    docspec_path = drafts / f"{args.slug}-docspec.json"
    docspec = {}
    if not docspec_path.is_file():
        errors.append(f"falta {docspec_path}")
    else:
        checked.append(docspec_path.name)
        errors += validate_json(docspec_path, "docspec")
        try:
            docspec = json.loads(docspec_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            docspec = {}
    design = drafts / f"{args.slug}-design-spec.json"
    if design.is_file():
        checked.append(design.name)
        errors += validate_json(design, "design-spec")
    for kind in KINDS:
        found = versions(drafts, args.slug, kind)
        if found:
            checked.append(found[-1][1].name)
            errors += validate_json(found[-1][1], SCHEMAS[kind])
            if found[-1][0] == 0:
                warnings.append(f"{found[-1][1].name}: sem versão -vN; a próxima iteração sobrescreve o histórico")
    html_path = drafts / f"{args.slug}.html"
    if html_path.is_file():
        checked.append(html_path.name)
        units = docspec.get("units") or []
        report = validate_activity_html(html_path.read_text(encoding="utf-8"), len(units),
                                        expected_support=bool(docspec.get("support")))
        errors += [f"{html_path.name}: {m}" for m in report.errors]
        warnings += [f"{html_path.name}: {m}" for m in report.warnings]
    print(json.dumps({"slug": args.slug, "passed": not errors, "checked": checked,
                      "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=1))
    return 1 if errors else 0


def lean_html(html: str) -> str:
    from server.activity_support import START as SUPPORT_START, END as SUPPORT_END
    from server.typography import START as FONT_START, END as FONT_END

    for start, end, label in ((FONT_START, FONT_END, "fonte incorporada"),
                              (SUPPORT_START, SUPPORT_END, "componente de apoio comum")):
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        html = pattern.sub(lambda m: f"{start} [{label}: {len(m.group(0))} caracteres omitidos] {end}", html)
    return re.sub(r"data:([\w/+.-]+);base64,[A-Za-z0-9+/=]{200,}",
                  lambda m: f"data:{m.group(1)};base64,[{len(m.group(0))} caracteres omitidos]", html)


def cmd_lean(args) -> int:
    sys.stdout.write(lean_html(Path(args.html).read_text(encoding="utf-8")))
    return 0


def cmd_next(args) -> int:
    found = versions(Path(args.dir), args.slug, args.kind)
    number = (found[-1][0] if found else 0) + 1
    print(Path(args.dir) / f"{args.slug}-{args.kind}-v{number}.json")
    return 0


def cmd_log(args) -> int:
    path = Path(args.dir) / f"{args.slug}-run-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"slug": args.slug}
    if not isinstance(manifest.get("runs"), list):
        manifest["runs"] = []
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "phase": args.phase, "status": args.status}
    for key in ("model", "artifact", "note"):
        if getattr(args, key):
            entry[key] = getattr(args, key)
    manifest["runs"].append(entry)
    manifest["status"] = args.status if args.phase == "orchestrator" else manifest.get("status", "running")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(entry, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default="drafts", help="pasta dos artefactos (por defeito drafts)")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("slug")
    lean = sub.add_parser("lean")
    lean.add_argument("html")
    nxt = sub.add_parser("next")
    nxt.add_argument("slug")
    nxt.add_argument("kind", choices=KINDS)
    log = sub.add_parser("log")
    log.add_argument("slug")
    log.add_argument("--phase", required=True,
                     choices=["orchestrator", "sources", "architect", "designer", "builder",
                              "proofreader", "evaluator", "repair", "teacher"])
    log.add_argument("--status", required=True)
    log.add_argument("--model")
    log.add_argument("--artifact")
    log.add_argument("--note")
    args = parser.parse_args(argv)
    return {"check": cmd_check, "lean": cmd_lean, "next": cmd_next, "log": cmd_log}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
