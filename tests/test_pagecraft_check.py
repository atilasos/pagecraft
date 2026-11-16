import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "skills/shared/scripts/pagecraft_check.py"


def run(*args, cwd=ROOT):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=cwd, capture_output=True, text=True)


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
    (tmp_path / "demo-evaluation-v2.json").write_text(json.dumps({"pass": True, "severity": "low", "issues": []}))
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
