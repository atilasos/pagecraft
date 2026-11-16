#!/usr/bin/env python3
"""Verificações determinísticas do percurso PageCraft (sem IA).

Subcomandos:
  check <slug> [--phase F]
                 valida os artefactos de drafts/<slug>* contra os schemas do
                 Studio, as regras de aprovação e o HTML (validate_activity_html).
                 Com --phase, valida só até essa fase e exige as suas saídas;
                 --phase delivery exige tudo e uma avaliação aprovada.
                 Sem --phase é só auditoria do que existe; não serve de gate.
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
SCORE_KEYS = ("factual_accuracy", "constraint_alignment", "differentiation_quality",
              "ux_accessibility", "visual_design", "technical_quality")
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


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def severities(report: dict) -> set[str]:
    found = {i.get("severity") for i in report.get("issues") or [] if isinstance(i, dict)}
    if isinstance(report.get("severity"), str):
        found.add(report["severity"])
    return found | ({"critical"} if report.get("critical") else set())


def semantic_rules(kind: str, path: Path, html_path: Path) -> tuple[list[str], list[str]]:
    """Regras de aprovação que o schema não exprime (ver references/workflow.md)."""
    data, errors, warnings = load(path), [], []
    if not data:
        return errors, warnings
    name = path.name
    if kind == "evaluation" and data.get("pass") is True:
        scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
        missing = [k for k in SCORE_KEYS if k not in scores]
        if missing:
            errors.append(f"{name}: pass:true sem scores de {', '.join(missing)}")
        low = [k for k, v in scores.items() if not isinstance(v, (int, float)) or v < 3]
        if low:
            errors.append(f"{name}: pass:true com scores < 3 em {', '.join(low)}")
        if "critical" in severities(data):
            errors.append(f"{name}: pass:true com issue critical")
        if not data.get("evidence"):
            errors.append(f"{name}: pass:true sem evidence observada")
        if data.get("blocked_by"):
            errors.append(f"{name}: pass:true com blocked_by por resolver")
        if "route" in data:
            errors.append(f"{name}: pass:true não leva route")
    if kind == "proofread" and data.get("pass") is True and severities(data) & {"high", "critical"}:
        errors.append(f"{name}: pass:true com issues high/critical")
    if kind in ("proofread", "evaluation") and html_path.is_file() and path.stat().st_mtime < html_path.stat().st_mtime:
        warnings.append(f"{name}: mais antigo do que {html_path.name}; o HTML mudou depois desta revisão")
    return errors, warnings


def family(model: str | None) -> str | None:
    return model.split("/", 1)[0].strip().lower() if model and "/" in model else None


def role(run: dict) -> str | None:
    # uma reparação do HTML conta como trabalho do Builder
    if run.get("phase") == "repair" and str(run.get("artifact") or "").endswith(".html"):
        return "builder"
    return run.get("phase")


def last_models(manifest_path: Path) -> tuple[list[dict], dict]:
    runs = [r for r in load(manifest_path).get("runs") or [] if isinstance(r, dict)]
    return runs, {phase: next((r.get("model") for r in reversed(runs) if role(r) == phase and r.get("model")), None)
                  for phase in ("builder", "evaluator", "proofreader")}


def independence_errors(manifest_path: Path) -> list[str]:
    """Builder e Evaluator de famílias diferentes, salvo decisão do professor registada."""
    runs, last = last_models(manifest_path)
    missing = [p for p in ("builder", "evaluator") if not family(last[p])]
    if missing:
        return [f"{manifest_path.name}: falta o modelo <família>/<modelo> da fase {', '.join(missing)} (CHECK log --model)"]
    last_evaluation = max((i for i, r in enumerate(runs) if role(r) == "evaluator" and r.get("model")), default=-1)
    # a decisão do professor só vale se a avaliação tiver sido refeita depois dela
    if family(last["builder"]) == family(last["evaluator"]) and not any(
            r.get("phase") == "teacher" and r.get("status") == "approved" and r.get("note")
            for r in runs[:last_evaluation]):
        return [f"{manifest_path.name}: Builder e Evaluator da mesma família ({family(last['builder'])}) "
                "sem decisão do professor registada (CHECK log <slug> --phase teacher --status approved --note \"<decisão>\")"]
    return []


def activity_errors(path: Path) -> list[str]:
    """Mínimo dos metadados de registo (references/learning.md)."""
    if not path.is_file():
        return []
    data, name, errors = load(path), path.name, []
    if not data:
        return [f"{name}: JSON inválido"]
    if not str(data.get("title") or "").strip():
        errors.append(f"{name}: falta title")
    if not isinstance(data.get("year"), int):
        errors.append(f"{name}: year tem de ser um número inteiro")
    if not isinstance(data.get("languages"), list) or "pt" not in data["languages"]:
        errors.append(f"{name}: languages tem de incluir \"pt\"")
    criteria = data.get("criteria")
    if not isinstance(criteria, list) or not criteria or not all(
            isinstance(c, dict) and c.get("id") and c.get("pt") for c in criteria):
        errors.append(f"{name}: criteria precisa de pelo menos um critério com id e pt")
    return errors


PHASES = ("architect", "designer", "builder", "proofreader", "evaluator", "delivery")
# o que cada fase tem de ter produzido (cumulativo); validar só o que já se aplica
REQUIRED = {"architect": {"docspec", "sources"}, "designer": {"design-spec"}, "builder": {"html"},
            "proofreader": {"proofread"}, "evaluator": {"evaluation"}, "delivery": {"guide", "activity"}}


def cmd_check(args) -> int:
    from server.pipeline.validators import validate_activity_html

    drafts, slug = Path(args.dir), args.slug
    phase = args.phase
    scope = PHASES[:PHASES.index(phase) + 1] if phase else PHASES
    required = set().union(*(REQUIRED[p] for p in scope)) if phase else {"docspec"}
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    paths = {"docspec": drafts / f"{slug}-docspec.json", "sources": drafts / f"{slug}-sources.md",
             "design-spec": drafts / f"{slug}-design-spec.json", "html": drafts / f"{slug}.html",
             "guide": drafts / f"{slug}.md", "activity": drafts / f"{slug}-activity.json"}
    for name in paths:
        if name in required and not paths[name].is_file():
            errors.append(f"falta {paths[name]}")
    docspec = {}
    if paths["docspec"].is_file():
        checked.append(paths["docspec"].name)
        errors += validate_json(paths["docspec"], "docspec")
        docspec = load(paths["docspec"])
        units = [u for u in docspec.get("units") or [] if isinstance(u, dict)]
        planned = sum(u["duration"] for u in units if isinstance(u.get("duration"), (int, float)))
        for number, unit in enumerate(units, 1):
            if not isinstance(unit.get("duration"), (int, float)):
                errors.append(f"{paths['docspec'].name}: unidade u{number} sem duration numérica")
            interaction = unit.get("interaction") if isinstance(unit.get("interaction"), dict) else {}
            if not str(interaction.get("adjustment") or "").strip():
                errors.append(f"{paths['docspec'].name}: unidade u{number} sem interaction.adjustment (decisão de ajuste)")
        if isinstance(docspec.get("duration"), (int, float)) and planned > docspec["duration"]:
            errors.append(f"{paths['docspec'].name}: unidades somam {planned} min, acima da duração de {docspec['duration']} min")
    if "designer" in scope and paths["design-spec"].is_file():
        checked.append(paths["design-spec"].name)
        errors += validate_json(paths["design-spec"], "design-spec")
    html_path = paths["html"]
    if "builder" in scope and html_path.is_file():
        checked.append(html_path.name)
        report = validate_activity_html(html_path.read_text(encoding="utf-8"), len(docspec.get("units") or []),
                                        expected_support=bool(docspec.get("support")))
        errors += [f"{html_path.name}: {m}" for m in report.errors]
        warnings += [f"{html_path.name}: {m}" for m in report.warnings]
    kinds = {"proofread": "proofreader", "evaluation": "evaluator", "repair-ticket": "evaluator"}
    for kind in KINDS:
        found = versions(drafts, slug, kind)
        if kinds[kind] not in scope:
            continue
        if not found:
            if kind in required:
                errors.append(f"falta {drafts / f'{slug}-{kind}-v1.json'}")
            continue
        latest = found[-1][1]
        checked.append(latest.name)
        errors += validate_json(latest, SCHEMAS[kind])
        more_errors, more_warnings = semantic_rules(kind, latest, html_path)
        errors += more_errors
        warnings += more_warnings
        if found[-1][0] == 0:
            warnings.append(f"{latest.name}: sem versão -vN; a próxima iteração sobrescreve o histórico")
    if phase == "delivery":
        for kind, label in (("evaluation", "a última avaliação"), ("proofread", "a última revisão linguística")):
            found = versions(drafts, slug, kind)
            if found and load(found[-1][1]).get("pass") is not True:
                errors.append(f"{found[-1][1].name}: {label} não aprova a atividade")
        # na entrega, uma revisão mais antiga do que o HTML já não cobre a página
        stale = [w for w in warnings if "o HTML mudou depois desta revisão" in w]
        errors += stale
        warnings = [w for w in warnings if w not in stale]
        errors += independence_errors(drafts / f"{slug}-run-manifest.json")
        _, last = last_models(drafts / f"{slug}-run-manifest.json")
        builder, proofreader = last["builder"], last["proofreader"]
        if family(builder) and family(builder) == family(proofreader):
            warnings.append(f"Proofreader e Builder da mesma família ({family(builder)}); preferir outra família")
        errors += activity_errors(paths["activity"])
    print(json.dumps({"slug": slug, "phase": phase or "all", "passed": not errors, "checked": checked,
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
    check.add_argument("--phase", choices=PHASES,
                       help="valida só até esta fase e exige as suas saídas; delivery exige tudo e PASS")
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
