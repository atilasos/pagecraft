import json
import shutil
import subprocess
import sys
from pathlib import Path

from server.bridge_snippet import ensure_bridge_lite


ROOT = Path(__file__).parent.parent
CANONICAL_SLUGS = [
    "menina",
    "menino",
    "uva",
    "dedo",
    "sapato",
    "bota",
    "leque",
    "casa",
    "janela",
    "telhado",
    "escada",
    "chave",
    "galinha",
    "ovo",
    "rato",
    "cenoura",
    "girafa",
    "palhaco",
    "zebra",
    "bandeira",
    "funil",
    "arvore",
    "quadro",
    "passarinho",
    "peixe",
    "cigarra",
    "fogueira",
    "flor",
]


def _copy_script(repo: Path, name: str) -> Path:
    scripts = repo / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    destination = scripts / name
    shutil.copy2(ROOT / "scripts" / name, destination)
    return destination


def _meta(slug: str) -> dict:
    return {
        "slug": slug,
        "title": slug,
        "year": "1.º ano",
        "ageRange": "1.º ano",
        "duration": 30,
        "maker": "none",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "tags": [],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_m28p_generator_keeps_variants_and_delegates_canonical_catalog(
    tmp_path, install_publication_module
):
    repo = tmp_path / "pagecraft"
    shutil.copytree(ROOT / "activities" / "arvore", repo / "activities" / "arvore")
    _write_json(repo / "activities" / "aaa-fora-do-metodo" / "meta.json", _meta("aaa-fora-do-metodo"))
    install_publication_module(repo)
    script = _copy_script(repo, "generate_m28p_variants.py")
    real_catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    arvore = next(item for item in real_catalog["items"] if item["slug"] == "arvore")
    _write_json(
        repo / "catalog.json",
        {
            "generatedAt": None,
            "count": 2,
            "items": [arvore, {"slug": "fantasma", "tags": []}],
        },
    )

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (repo / "activities" / "arvore-cacador-silabas" / "meta.json").exists()
    assert (repo / "activities" / "arvore-frases-vivas" / "meta.json").exists()
    base_docspec = json.loads(
        (repo / "activities" / "arvore" / "docspec.json").read_text(
            encoding="utf-8"
        )
    )
    for slug in ("arvore-cacador-silabas", "arvore-frases-vivas"):
        generated = repo / "activities" / slug
        committed = ROOT / "activities" / slug
        for name in (
            "meta.json",
            "design-spec.json",
            "teacher.md",
            "proofread-v1.json",
            "evaluation-v1.json",
        ):
            assert (generated / name).read_bytes() == (committed / name).read_bytes()
        assert ensure_bridge_lite(
            (generated / "index.html").read_text(encoding="utf-8")
        ) == (committed / "index.html").read_text(encoding="utf-8")
        generated_docspec = json.loads(
            (generated / "docspec.json").read_text(encoding="utf-8")
        )
        committed_docspec = json.loads(
            (committed / "docspec.json").read_text(encoding="utf-8")
        )
        committed_docspec["m28pMethodAlignment"] = base_docspec[
            "m28pMethodAlignment"
        ]
        assert generated_docspec == committed_docspec
    catalog = json.loads((repo / "catalog.json").read_text(encoding="utf-8"))
    slugs = [item["slug"] for item in catalog["items"]]
    assert slugs == sorted(slugs)
    assert slugs == [
        "aaa-fora-do-metodo",
        "arvore",
        "arvore-cacador-silabas",
        "arvore-frases-vivas",
    ]


def test_m28p_repair_keeps_owned_fix_and_removes_stale_catalog_entry(
    tmp_path, install_publication_module
):
    repo = tmp_path / "pagecraft"
    for slug in CANONICAL_SLUGS:
        shutil.copytree(ROOT / "activities" / slug, repo / "activities" / slug)
    before = {
        path.relative_to(repo / "activities"): path.read_bytes()
        for slug in CANONICAL_SLUGS
        for path in (repo / "activities" / slug).iterdir()
        if path.is_file()
    }
    _write_json(repo / "activities" / "aaa-fora-do-metodo" / "meta.json", _meta("aaa-fora-do-metodo"))
    install_publication_module(repo)
    script = _copy_script(repo, "repair_m28p_main_pages.py")
    real_catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    items = [
        item for item in real_catalog["items"] if item["slug"] in CANONICAL_SLUGS
    ]
    items.extend(
        [
            {
                "slug": "aaa-fora-do-metodo",
                "tags": [],
            },
            {
                "slug": "fantasma",
                "tags": [],
            },
        ]
    )
    _write_json(
        repo / "catalog.json",
        {"generatedAt": None, "count": len(items), "items": items},
    )

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    after = {
        path.relative_to(repo / "activities"): path.read_bytes()
        for slug in CANONICAL_SLUGS
        for path in (repo / "activities" / slug).iterdir()
        if path.is_file()
    }
    assert after == before
    for slug in CANONICAL_SLUGS:
        activity = repo / "activities" / slug
        docspec = json.loads(
            (activity / "docspec.json").read_text(encoding="utf-8")
        )
        proof = json.loads(
            (activity / "proofread-v1.json").read_text(encoding="utf-8")
        )
        assert docspec["m28pMethodAlignment"]["principle"]
        assert "Princípio M28P — evitar uso puramente visual" in (
            activity / "teacher.md"
        ).read_text(encoding="utf-8")
        assert "m28p-method-check" in (activity / "index.html").read_text(
            encoding="utf-8"
        )
        assert proof["pass"] is True
    leque = json.loads(
        (repo / "activities" / "leque" / "meta.json").read_text(encoding="utf-8")
    )
    assert leque["duration"] == 45
    catalog = json.loads((repo / "catalog.json").read_text(encoding="utf-8"))
    slugs = [item["slug"] for item in catalog["items"]]
    assert slugs == sorted(slugs)
    assert "aaa-fora-do-metodo" in slugs
    assert "fantasma" not in slugs
