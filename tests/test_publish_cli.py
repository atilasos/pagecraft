import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
COMMAND = ROOT / "skills" / "shared" / "scripts" / "publish_to_catalog.py"
SOURCE_ACTIVITY = ROOT / "activities" / "arvore-cacador-silabas"


def _copy_repository_publication_module(repo: Path) -> None:
    server = repo / "server"
    server.mkdir()
    for name in ("__init__.py", "publish.py", "bridge_snippet.py"):
        shutil.copy2(ROOT / "server" / name, server / name)


def _publication_command(repo: Path, inputs: Path) -> list[str]:
    return [
        sys.executable,
        str(COMMAND),
        "--slug",
        SOURCE_ACTIVITY.name,
        "--html",
        str(inputs / "index.html"),
        "--md",
        str(inputs / "teacher.md"),
        "--docspec",
        str(inputs / "docspec.json"),
        "--repo",
        str(repo),
    ]


def test_command_uses_repository_publication_act_and_preserves_omitted_tags(tmp_path):
    repo = tmp_path / "pagecraft"
    activity = repo / "activities" / SOURCE_ACTIVITY.name
    inputs = tmp_path / "inputs"
    shutil.copytree(SOURCE_ACTIVITY, activity)
    shutil.copytree(SOURCE_ACTIVITY, inputs)
    _copy_repository_publication_module(repo)
    before = json.loads((activity / "meta.json").read_text(encoding="utf-8"))

    result = subprocess.run(
        _publication_command(repo, inputs),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    published = json.loads((activity / "meta.json").read_text(encoding="utf-8"))
    assert published["tags"] == before["tags"]
    assert published["variantOf"] == before["variantOf"]
    assert "pagecraft-bridge-lite" in (activity / "index.html").read_text(
        encoding="utf-8"
    )


def test_command_fails_before_publishing_when_repository_module_is_missing(tmp_path):
    repo = tmp_path / "pagecraft"
    (repo / "activities").mkdir(parents=True)
    inputs = tmp_path / "inputs"
    shutil.copytree(SOURCE_ACTIVITY, inputs)

    result = subprocess.run(
        _publication_command(repo, inputs),
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "módulo de publicação" in result.stderr
    assert not (repo / "activities" / SOURCE_ACTIVITY.name).exists()
