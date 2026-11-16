import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "skills/shared/scripts/pagecraft_check.py"


def run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=cwd, capture_output=True, text=True)


SCORES = {k: 4 for k in ("factual_accuracy", "constraint_alignment", "differentiation_quality",
                          "ux_accessibility", "visual_design", "technical_quality")}
PASSING = {"pass": True, "severity": "low", "issues": [], "evidence": ["abri a página a 390px; sem erros"],
           "scores": SCORES}


def write_minimal(drafts: Path, slug: str, evaluation: dict) -> None:
    from test_schemas import MINIMAL_DOCSPEC

    spec = json.loads(json.dumps(MINIMAL_DOCSPEC))
    for unit in spec["units"]:
        unit.setdefault("interaction", {})["adjustment"] = "Retomar com material concreto em pequeno grupo."
    (drafts / f"{slug}-docspec.json").write_text(json.dumps(spec))
    (drafts / f"{slug}-evaluation-v1.json").write_text(json.dumps(evaluation))


def test_check_reports_schema_errors_and_exit_code(tmp_path):
    write_minimal(tmp_path, "demo", {"pass": True, "route": "none", "severity": "low", "issues": []})
    result = run("--dir", tmp_path, "check", "demo")
    report = json.loads(result.stdout)
    assert result.returncode == 1
    assert any("route" in error for error in report["errors"])


def test_check_passes_valid_artifacts_and_uses_latest_version(tmp_path):
    write_minimal(tmp_path, "demo", {"pass": False, "route": "none", "severity": "low", "issues": []})
    (tmp_path / "demo-evaluation-v2.json").write_text(json.dumps(PASSING))
    result = run("--dir", tmp_path, "check", "demo")
    assert result.returncode == 0, result.stdout
    assert "demo-evaluation-v2.json" in json.loads(result.stdout)["checked"]


def test_lean_omits_embedded_blocks_and_next_versions(tmp_path):
    from server.typography import START, END

    html = tmp_path / "demo.html"
    html.write_text(f"<style>{START}{'x' * 5000}{END}</style><img src=\"data:image/png;base64,{'A' * 900}\">")
    lean = run("lean", html).stdout
    assert "x" * 100 not in lean and "A" * 300 not in lean
    assert "omitidos" in lean
    assert run("--dir", tmp_path, "next", "demo", "proofread").stdout.strip().endswith("demo-proofread-v1.json")


def test_log_appends_runs_without_dropping_existing_fields(tmp_path):
    (tmp_path / "demo-run-manifest.json").write_text(json.dumps({"slug": "demo", "topic": "frações"}))
    assert run("--dir", tmp_path, "log", "demo", "--phase", "builder", "--status", "done",
               "--model", "codex/gpt").returncode == 0
    manifest = json.loads((tmp_path / "demo-run-manifest.json").read_text())
    assert manifest["topic"] == "frações"
    assert manifest["runs"][0]["model"] == "codex/gpt"


def errors_for(tmp_path, evaluation=None, proofread=None):
    write_minimal(tmp_path, "demo", evaluation or PASSING)
    if proofread:
        (tmp_path / "demo-proofread-v1.json").write_text(json.dumps(proofread))
    return json.loads(run("--dir", tmp_path, "check", "demo").stdout)["errors"]


def test_pass_requires_scores_evidence_and_no_blockers(tmp_path):
    bad = {"pass": True, "severity": "low", "issues": [{"severity": "critical"}],
           "scores": {"visual_design": 2}, "blocked_by": ["sem browser"]}
    joined = " | ".join(errors_for(tmp_path, bad))
    for expected in ("scores < 3", "sem scores de factual_accuracy", "issue critical", "sem evidence", "blocked_by"):
        assert expected in joined
    aggregate = dict(PASSING, severity="critical")
    assert any("issue critical" in e for e in errors_for(tmp_path, aggregate))


def test_docspec_units_need_duration_and_adjustment(tmp_path):
    write_minimal(tmp_path, "demo", PASSING)
    spec = json.loads((tmp_path / "demo-docspec.json").read_text())
    del spec["units"][0]["interaction"]["adjustment"]
    del spec["units"][0]["duration"]
    (tmp_path / "demo-docspec.json").write_text(json.dumps(spec))
    errors = " | ".join(json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "architect").stdout)["errors"])
    assert "sem duration" in errors and "sem interaction.adjustment" in errors


def test_proofread_pass_with_high_issue_and_overlong_units_fail(tmp_path):
    proofread = {"pass": True, "summary": "ok", "issues": [{"type": "grammar", "severity": "high"}]}
    assert any("high/critical" in e for e in errors_for(tmp_path, proofread=proofread))
    from test_schemas import MINIMAL_DOCSPEC
    spec = json.loads((tmp_path / "demo-docspec.json").read_text())
    spec["duration"] = 1
    spec["units"][0]["duration"] = 5
    (tmp_path / "demo-docspec.json").write_text(json.dumps(spec))
    result = json.loads(run("--dir", tmp_path, "check", "demo").stdout)
    assert any("acima da duração" in e for e in result["errors"])


def test_phase_scope_ignores_downstream_artifacts_and_requires_outputs(tmp_path):
    write_minimal(tmp_path, "demo", {"pass": True, "severity": "low", "issues": []})
    (tmp_path / "demo.html").write_text("<p>antigo</p>")
    architect = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "architect").stdout)
    assert architect["errors"] == [f"falta {tmp_path / 'demo-sources.md'}"]
    (tmp_path / "demo-sources.md").write_text("fontes")
    assert run("--dir", tmp_path, "check", "demo", "--phase", "architect").returncode == 0
    designer = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "designer").stdout)
    assert any("design-spec" in e for e in designer["errors"])
    delivery = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "delivery").stdout)
    assert any("demo.md" in e for e in delivery["errors"]) and any("sem evidence" in e for e in delivery["errors"])


def ready_for_delivery(tmp_path, builder="gpt/sol", evaluator="claude/opus"):
    import os

    write_minimal(tmp_path, "demo", PASSING)
    for name in ("demo-sources.md", "demo.md"):
        (tmp_path / name).write_text("x")
    (tmp_path / "demo-design-spec.json").write_text('{"palette": {}}')
    (tmp_path / "demo-activity.json").write_text(json.dumps(
        {"title": "Demo", "year": 3, "languages": ["pt"], "criteria": [{"id": "c1", "pt": "Consigo explicar."}]}))
    (tmp_path / "demo.html").write_text("<p>x</p>")
    (tmp_path / "demo-proofread-v1.json").write_text(json.dumps({"pass": True, "summary": "ok", "issues": []}))
    os.utime(tmp_path / "demo.html", (1, 1))
    for phase, model in (("builder", builder), ("evaluator", evaluator)):
        run("--dir", tmp_path, "log", "demo", "--phase", phase, "--status", "done", "--model", model)


def delivery_errors(tmp_path):
    report = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "delivery").stdout)
    return [e for e in report["errors"] if not e.startswith("demo.html:")]


def test_delivery_requires_independent_families_unless_teacher_decides(tmp_path):
    ready_for_delivery(tmp_path)
    assert delivery_errors(tmp_path) == []
    ready_for_delivery(tmp_path, builder="claude/sonnet", evaluator="claude/opus")
    assert any("mesma família (claude)" in e for e in delivery_errors(tmp_path))
    run("--dir", tmp_path, "log", "demo", "--phase", "teacher", "--status", "rejected", "--note", "não autorizo")
    assert any("mesma família" in e for e in delivery_errors(tmp_path))
    run("--dir", tmp_path, "log", "demo", "--phase", "teacher", "--status", "approved", "--note", "autorizo")
    assert any("mesma família" in e for e in delivery_errors(tmp_path))  # falta refazer a avaliação
    run("--dir", tmp_path, "log", "demo", "--phase", "evaluator", "--status", "failed", "--model", "claude/opus")
    assert any("mesma família" in e for e in delivery_errors(tmp_path))  # uma execução falhada não conta
    run("--dir", tmp_path, "log", "demo", "--phase", "evaluator", "--status", "done", "--model", "claude/opus",
        "--artifact", str(tmp_path / "demo-evaluation-v1.json"))
    assert any("mesma família" in e for e in delivery_errors(tmp_path))  # aponta para o relatório antigo
    (tmp_path / "demo-evaluation-v2.json").write_text(json.dumps(PASSING))
    run("--dir", tmp_path, "log", "demo", "--phase", "evaluator", "--status", "done", "--model", "claude/opus",
        "--artifact", str(tmp_path / "demo-evaluation-v2.json"))
    assert delivery_errors(tmp_path) == []
    run("--dir", tmp_path, "log", "demo", "--phase", "teacher", "--status", "rejected", "--note", "afinal não")
    (tmp_path / "demo-evaluation-v3.json").write_text(json.dumps(PASSING))
    run("--dir", tmp_path, "log", "demo", "--phase", "evaluator", "--status", "done", "--model", "claude/opus",
        "--artifact", str(tmp_path / "demo-evaluation-v3.json"))
    assert any("mesma família" in e for e in delivery_errors(tmp_path))  # a última decisão é uma recusa


def test_delivery_rejects_reviews_older_than_the_html(tmp_path):
    import os

    ready_for_delivery(tmp_path)
    os.utime(tmp_path / "demo-evaluation-v1.json", (1, 1))
    os.utime(tmp_path / "demo.html", (10, 10))
    assert any("o HTML mudou" in e for e in delivery_errors(tmp_path))
    evaluator = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "evaluator").stdout)
    assert any("o HTML mudou" in w for w in evaluator["warnings"])
    os.utime(tmp_path / "demo-evaluation-v1.json", (20, 20))
    (tmp_path / "demo-proofread-v2.json").write_text(json.dumps({"pass": False, "summary": "x", "issues": []}))
    os.utime(tmp_path / "demo-proofread-v2.json", (20, 20))
    assert any("revisão linguística não aprova" in e for e in delivery_errors(tmp_path))


def test_delivery_counts_html_repairs_as_builder_and_checks_activity(tmp_path):
    ready_for_delivery(tmp_path)
    run("--dir", tmp_path, "log", "demo", "--phase", "repair", "--status", "done",
        "--model", "claude/sonnet", "--artifact", str(tmp_path / "demo.html"))
    assert any("mesma família (claude)" in e for e in delivery_errors(tmp_path))
    (tmp_path / "demo-activity.json").write_text(json.dumps({"title": "", "year": "3", "criteria": []}))
    joined = " | ".join(delivery_errors(tmp_path))
    assert "falta title" in joined and "year" in joined and "criteria" in joined


def test_proofreader_warning_uses_html_repairs_as_builder(tmp_path):
    ready_for_delivery(tmp_path)
    for phase, model in (("repair", "claude/sonnet"), ("proofreader", "claude/haiku"), ("evaluator", "gpt/sol")):
        run("--dir", tmp_path, "log", "demo", "--phase", phase, "--status", "done", "--model", model,
            "--artifact", str(tmp_path / "demo.html"))
    report = json.loads(run("--dir", tmp_path, "check", "demo", "--phase", "delivery").stdout)
    assert any("Proofreader e Builder da mesma família (claude)" in w for w in report["warnings"])
