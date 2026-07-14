"""Publicação de uma atividade PageCraft aprovada no catálogo do repo.

Port de skills/openclaw/scripts/publish_to_catalog.py sem a parte de
git commit/push (isso era responsabilidade do script antigo).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _infer_title_from_html(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    start = text.find("<title>")
    end = text.find("</title>")
    if start != -1 and end != -1 and end > start:
        return text[start + 7 : end].strip()
    return html_path.stem


def _infer_maker(docspec: dict) -> str:
    """Deriva o recurso maker principal a partir das units do DocSpec."""
    for unit in docspec.get("units", []):
        maker = unit.get("maker")
        if isinstance(maker, dict) and maker.get("type"):
            return maker["type"]
    return "none"


def publish_activity(
    repo_root: Path,
    slug: str,
    html_path: Path,
    docspec: dict,
    teacher_md: str,
    design_spec: dict | None = None,
    *,
    maker: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Publica uma atividade em activities/<slug>/ e atualiza catalog.json.

    Escreve index.html, teacher.md, docspec.json, meta.json (+ design-spec.json
    se existir), preservando o createdAt de entradas já publicadas.
    Devolve o meta dict escrito em meta.json.
    """
    repo_root = Path(repo_root)
    activities = repo_root / "activities"
    dst = activities / slug
    dst.mkdir(parents=True, exist_ok=True)

    html_path = Path(html_path)
    shutil.copy2(html_path, dst / "index.html")
    (dst / "teacher.md").write_text(teacher_md, encoding="utf-8")
    _save_json(dst / "docspec.json", docspec)
    if design_spec is not None:
        _save_json(dst / "design-spec.json", design_spec)

    title = docspec.get("topic") or _infer_title_from_html(html_path)
    year = docspec.get("ageRange") or ""
    duration = docspec.get("duration")
    topic = docspec.get("topic") or title
    age_range = docspec.get("ageRange", "")

    if maker is None:
        maker = _infer_maker(docspec)
    if tags is None:
        tags = [maker] if maker and maker != "none" else []

    meta_path = dst / "meta.json"
    existing_meta = _load_json(meta_path, {})
    created = existing_meta.get("createdAt") or _now_iso()
    updated = _now_iso()

    meta = {
        "slug": slug,
        "title": title,
        "year": year,
        "ageRange": age_range,
        "duration": duration,
        "topic": topic,
        "maker": maker,
        "createdAt": created,
        "updatedAt": updated,
        "status": "published",
        "tags": tags,
        "paths": {
            "activity": "./index.html",
            "teacher": "./teacher.md",
            "docspec": "./docspec.json",
            "designSpec": "./design-spec.json" if design_spec is not None else None,
        },
    }
    _save_json(meta_path, meta)

    catalog_path = repo_root / "catalog.json"
    catalog = _load_json(catalog_path, {"generatedAt": None, "count": 0, "items": []})
    items = catalog.get("items", [])
    item = {
        "slug": slug,
        "title": title,
        "year": year,
        "ageRange": age_range,
        "duration": duration,
        "maker": maker,
        "tags": tags,
        "createdAt": created,
        "url": f"./activities/{slug}/",
        "teacherUrl": f"./activities/{slug}/teacher.md",
        "docspecUrl": f"./activities/{slug}/docspec.json",
    }

    replaced = False
    for i, it in enumerate(items):
        if it.get("slug") == slug:
            items[i] = item
            replaced = True
            break
    if not replaced:
        items.append(item)

    catalog["items"] = sorted(items, key=lambda x: x.get("slug", ""))
    catalog["count"] = len(catalog["items"])
    catalog["generatedAt"] = updated
    _save_json(catalog_path, catalog)

    return meta
