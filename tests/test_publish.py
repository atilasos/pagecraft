import json
import shutil
from pathlib import Path

import pytest

from server.publish import build_catalog, publish_activity, regenerate_catalog


ROOT = Path(__file__).parent.parent

DOCSPEC = {
    "topic": "Estados físicos da água",
    "ageRange": "8-9 anos (3.º ano)",
    "duration": 40,
    "objectives": ["Identificar os estados da água", "Relacionar temperatura e estado"],
    "units": [
        {
            "summary": "Estados da água",
            "textDescription": "…",
            "maker": {"type": "minecraft", "challenge": "…", "connection": "…"},
        }
    ],
}

TEACHER_MD = "# Estados físicos da água\n\nVersão professor.\n"


@pytest.fixture
def repo(tmp_path):
    # Formato real do catalog.json do repo pagecraft
    (tmp_path / "catalog.json").write_text(
        json.dumps({"generatedAt": None, "count": 0, "items": []}), encoding="utf-8"
    )
    (tmp_path / "activities").mkdir()
    return tmp_path


@pytest.fixture
def html_file(tmp_path):
    path = tmp_path / "page.html"
    path.write_text(
        "<!doctype html><html><head><title>Estados da água</title></head>"
        "<body><h1>Olá</h1></body></html>",
        encoding="utf-8",
    )
    return path


def test_publish_writes_files_and_catalog_entry(repo, html_file):
    design_spec = {"palette": {"bg": "#ffffff", "ink": "#111111"}}
    meta = publish_activity(
        repo, "estados-agua", html_file, DOCSPEC, TEACHER_MD, design_spec
    )

    dst = repo / "activities" / "estados-agua"
    assert (dst / "index.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert (dst / "teacher.md").read_text(encoding="utf-8") == TEACHER_MD
    assert json.loads((dst / "docspec.json").read_text(encoding="utf-8")) == DOCSPEC
    assert json.loads((dst / "design-spec.json").read_text(encoding="utf-8")) == design_spec
    assert json.loads((dst / "meta.json").read_text(encoding="utf-8")) == meta

    assert meta["slug"] == "estados-agua"
    assert meta["title"] == "Estados físicos da água"
    assert meta["duration"] == 40
    assert meta["maker"] == "minecraft"  # derivado da unit
    assert meta["status"] == "published"
    assert meta["paths"]["designSpec"] == "./design-spec.json"

    catalog = json.loads((repo / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["count"] == 1
    assert catalog["generatedAt"] == meta["updatedAt"]
    (item,) = catalog["items"]
    assert item["slug"] == "estados-agua"
    assert item["url"] == "./activities/estados-agua/"
    assert item["teacherUrl"] == "./activities/estados-agua/teacher.md"
    assert item["createdAt"] == meta["createdAt"]


def test_republish_preserves_created_at(repo, html_file):
    meta1 = publish_activity(repo, "estados-agua", html_file, DOCSPEC, TEACHER_MD, None)

    # Força um createdAt antigo para garantir que a segunda publicação o preserva
    dst = repo / "activities" / "estados-agua"
    meta_path = dst / "meta.json"
    stored = json.loads(meta_path.read_text(encoding="utf-8"))
    stored["createdAt"] = "2026-01-01T00:00:00Z"
    meta_path.write_text(json.dumps(stored), encoding="utf-8")

    meta2 = publish_activity(repo, "estados-agua", html_file, DOCSPEC, TEACHER_MD, None)

    assert meta2["createdAt"] == "2026-01-01T00:00:00Z"
    assert meta2["paths"]["designSpec"] is None
    assert not (dst / "design-spec.json").exists()

    catalog = json.loads((repo / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["count"] == 1  # substitui, não duplica
    assert catalog["items"][0]["createdAt"] == "2026-01-01T00:00:00Z"
    assert meta1["slug"] == meta2["slug"] == "estados-agua"


def test_republish_real_activity_preserves_rich_metadata_and_complete_disk_state(
    tmp_path, html_file
):
    source = ROOT / "activities" / "arvore-cacador-silabas"
    repo = tmp_path / "pagecraft"
    activity = repo / "activities" / source.name
    shutil.copytree(source, activity)
    (repo / "catalog.json").write_text(
        json.dumps({"generatedAt": None, "count": 0, "items": []}),
        encoding="utf-8",
    )
    before = json.loads((activity / "meta.json").read_text(encoding="utf-8"))

    meta = publish_activity(
        repo,
        source.name,
        html_file,
        DOCSPEC,
        TEACHER_MD,
        None,
    )

    for field in (
        "createdAt",
        "tags",
        "order",
        "variantOf",
        "variantIndex",
        "variantTitle",
    ):
        assert meta[field] == before[field]
    assert meta["title"] == DOCSPEC["topic"]
    assert meta["duration"] == DOCSPEC["duration"]
    assert meta["paths"] == before["paths"]
    assert (activity / "design-spec.json").exists()
    assert "pagecraft-bridge-lite" in (activity / "index.html").read_text(
        encoding="utf-8"
    )

    catalog = json.loads((repo / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["count"] == 1
    assert [item["slug"] for item in catalog["items"]] == [source.name]
    assert catalog["items"][0]["tags"] == before["tags"]
    assert catalog["items"][0]["variantOf"] == before["variantOf"]


def test_explicit_republish_values_replace_existing_metadata(tmp_path, html_file):
    source = ROOT / "activities" / "arvore-cacador-silabas"
    repo = tmp_path / "pagecraft"
    shutil.copytree(source, repo / "activities" / source.name)

    meta = publish_activity(
        repo,
        source.name,
        html_file,
        DOCSPEC,
        TEACHER_MD,
        None,
        maker="lego",
        tags=["revista", "lego"],
    )

    assert meta["maker"] == "lego"
    assert meta["tags"] == ["revista", "lego"]


def test_regenerate_catalog_includes_only_metadata_and_removes_deleted_activity(
    tmp_path,
):
    repo = tmp_path / "pagecraft"
    activities = repo / "activities"
    shutil.copytree(
        ROOT / "activities" / "arvore-cacador-silabas",
        activities / "zeta",
    )
    shutil.copytree(
        ROOT / "activities" / "bota-cacador-silabas",
        activities / "alpha",
    )
    (activities / "sem-metadados").mkdir()

    first = regenerate_catalog(repo)

    assert [item["slug"] for item in first["items"]] == [
        "arvore-cacador-silabas",
        "bota-cacador-silabas",
    ]
    (activities / "zeta" / "meta.json").unlink()

    second = regenerate_catalog(repo)

    assert [item["slug"] for item in second["items"]] == [
        "bota-cacador-silabas"
    ]
    assert json.loads((repo / "catalog.json").read_text(encoding="utf-8")) == second


def test_committed_catalog_matches_activity_metadata():
    committed = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))

    assert committed == build_catalog(ROOT)


def test_publish_without_title_falls_back_to_html_title(repo, html_file):
    docspec = {"units": []}
    meta = publish_activity(repo, "sem-topico", html_file, docspec, "md", None)
    assert meta["title"] == "Estados da água"
    assert meta["maker"] == "none"
    assert meta["tags"] == []
