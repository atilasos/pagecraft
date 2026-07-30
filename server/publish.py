"""Ato único de publicação e regeneração do Catálogo PageCraft."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bridge_snippet import ensure_bridge_lite


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _replace_json(path: Path, obj: Any) -> None:
    """Escreve JSON fora do destino e publica-o com uma substituição atómica."""
    content = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _infer_title_from_html(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    start = text.find("<title>")
    end = text.find("</title>")
    if start != -1 and end != -1 and end > start:
        return text[start + 7 : end].strip()
    return html_path.stem


def _infer_maker(docspec: dict) -> str | None:
    """Deriva o recurso maker principal a partir das units do DocSpec."""
    for unit in docspec.get("units", []):
        maker = unit.get("maker")
        if isinstance(maker, dict) and maker.get("type"):
            return maker["type"]
    return None


def _catalog_item(meta: dict[str, Any]) -> dict[str, Any]:
    slug = meta["slug"]
    item = {
        "slug": slug,
        "title": meta.get("title", slug),
        "year": meta.get("year"),
        "ageRange": meta.get("ageRange"),
        "duration": meta.get("duration"),
        "maker": meta.get("maker", "none"),
    }
    if meta.get("order"):
        item["order"] = meta["order"]
    if meta.get("variantOf"):
        item["variantOf"] = meta["variantOf"]
    if meta.get("variantIndex") is not None:
        item["variantIndex"] = meta["variantIndex"]
    if meta.get("variantTitle"):
        item["variantTitle"] = meta["variantTitle"]
    item.update(
        {
            "tags": meta.get("tags", []),
            "createdAt": meta.get("createdAt"),
            "url": f"./activities/{slug}/",
            "teacherUrl": f"./activities/{slug}/teacher.md",
            "docspecUrl": f"./activities/{slug}/docspec.json",
        }
    )
    return item


def build_catalog(repo_root: Path) -> dict[str, Any]:
    """Projeta em memória o Catálogo a partir dos ``meta.json`` publicados."""
    activities = Path(repo_root) / "activities"
    metadata = [
        _load_json(meta_path, {})
        for meta_path in sorted(activities.glob("*/meta.json"))
    ]
    items = sorted((_catalog_item(meta) for meta in metadata), key=lambda item: item["slug"])
    updated_at = [meta["updatedAt"] for meta in metadata if meta.get("updatedAt")]
    return {
        "generatedAt": max(updated_at, default=None),
        "count": len(items),
        "items": items,
    }


def regenerate_catalog(repo_root: Path) -> dict[str, Any]:
    """Reconstrói e substitui atomicamente ``catalog.json``."""
    repo_root = Path(repo_root)
    catalog = build_catalog(repo_root)
    _replace_json(repo_root / "catalog.json", catalog)
    return catalog


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
    """Publica uma atividade e regenera o Catálogo num único ato.

    Escreve index.html, teacher.md, docspec.json, meta.json (+ design-spec.json
    se fornecido). Metadados existentes que não sejam fornecidos sobrevivem.
    Devolve o meta dict escrito em meta.json.
    """
    repo_root = Path(repo_root)
    activities = repo_root / "activities"
    dst = activities / slug
    dst.mkdir(parents=True, exist_ok=True)

    html_path = Path(html_path)
    html = ensure_bridge_lite(html_path.read_text(encoding="utf-8"))
    (dst / "index.html").write_text(html, encoding="utf-8")
    (dst / "teacher.md").write_text(teacher_md, encoding="utf-8")
    _save_json(dst / "docspec.json", docspec)
    if design_spec is not None:
        _save_json(dst / "design-spec.json", design_spec)

    meta_path = dst / "meta.json"
    existing_meta = _load_json(meta_path, {})
    created = existing_meta.get("createdAt") or _now_iso()
    updated = _now_iso()
    title = docspec.get("topic") or _infer_title_from_html(html_path)
    updates: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "createdAt": created,
        "updatedAt": updated,
        "status": "published",
    }
    if "ageRange" in docspec:
        updates["year"] = docspec["ageRange"]
        updates["ageRange"] = docspec["ageRange"]
    if "duration" in docspec:
        updates["duration"] = docspec["duration"]
    if "topic" in docspec:
        updates["topic"] = docspec["topic"]
    ae_refs = (docspec.get("curriculum") or {}).get("ae") or []
    if ae_refs:
        updates["subject"] = str(ae_refs[0].get("subject", ""))
    supplied_maker = maker if maker is not None else _infer_maker(docspec)
    if supplied_maker is not None:
        updates["maker"] = supplied_maker
    if tags is not None:
        updates["tags"] = tags

    existing_paths = existing_meta.get("paths")
    paths = dict(existing_paths) if isinstance(existing_paths, dict) else {}
    paths.update(
        {
            "activity": "./index.html",
            "teacher": "./teacher.md",
            "docspec": "./docspec.json",
        }
    )
    if design_spec is not None:
        paths["designSpec"] = "./design-spec.json"
    elif not existing_meta:
        paths["designSpec"] = None
    updates["paths"] = paths

    meta = {
        **existing_meta,
        **updates,
    }
    meta.setdefault("year", "")
    meta.setdefault("ageRange", "")
    meta.setdefault("duration", None)
    meta.setdefault("topic", title)
    meta.setdefault("subject", "")
    meta.setdefault("maker", "none")
    meta.setdefault("tags", [])
    _save_json(meta_path, meta)
    regenerate_catalog(repo_root)
    return meta
