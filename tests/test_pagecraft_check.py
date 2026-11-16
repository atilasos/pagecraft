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

    (drafts / f"{slug}-docspec.json").write_text(json.dumps(MINIMAL_DOCSPEC))
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


def test_proofread_pass_with_high_issue_and_overlong_units_fail(tmp_path):
    proofread = {"pass": True, "summary": "ok", "issues": [{"type": "grammar", "severity": "high"}]}
    assert any("high/critical" in e for e in errors_for(tmp_path, proofread=proofread))
    from test_schemas import MINIMAL_DOCSPEC
    spec = json.loads(json.dumps(MINIMAL_DOCSPEC))
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
