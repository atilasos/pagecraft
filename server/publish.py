"""Ato único de publicação e regeneração do Catálogo PageCraft."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bridge_snippet import ensure_bridge_lite
from .catalog_years import activity_years, validate_years


_publication_lock = threading.RLock()


def _serialized_publication(function):
    @wraps(function)
    def publish(*args, **kwargs):
        # O servidor tem um processo e vários jobs podem aprovar em paralelo.
        with _publication_lock:
            return function(*args, **kwargs)
    return publish


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


def _infer_title_from_html(text: str, fallback: str) -> str:
    start = text.find("<title>")
    end = text.find("</title>")
    if start != -1 and end != -1 and end > start:
        return text[start + 7 : end].strip()
    return fallback


def _infer_maker(docspec: dict) -> str | None:
    """Deriva o recurso maker principal a partir das units do DocSpec."""
    for unit in docspec.get("units", []):
        maker = unit.get("maker")
        if isinstance(maker, dict) and maker.get("type"):
            return maker["type"]
    return None


def _catalog_item(meta: dict[str, Any], docspec: dict | None = None) -> dict[str, Any]:
    slug = meta["slug"]
    item = {
        "slug": slug,
        "title": meta.get("title", slug),
        "year": meta.get("year"),
        "yearLabel": str(meta.get("year") or ""),
        "years": activity_years(meta, docspec),
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
    metadata = []
    items = []
    for meta_path in sorted(activities.glob("*/meta.json")):
        meta = _load_json(meta_path, {})
        metadata.append(meta)
        docspec = _load_json(meta_path.parent / "docspec.json", {})
        items.append(_catalog_item(meta, docspec))
    items.sort(key=lambda item: item["slug"])
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


@_serialized_publication
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
    generation_id: str | None = None,
    review_id: str | None = None,
    html_content: str | None = None,
) -> dict:
    """Publica uma atividade e regenera o Catálogo num único ato.

    Escreve index.html, teacher.md, docspec.json, meta.json (+ design-spec.json
    se fornecido). Metadados existentes que não sejam fornecidos sobrevivem.
    Gerações do Studio são imutáveis: só se repete o mesmo job, revisão e
    conteúdo. O diretório completo é instalado atomicamente antes do catálogo.
    Devolve o meta dict escrito em meta.json.
    """
    repo_root = Path(repo_root)
    activities = repo_root / "activities"
    dst = activities / slug
    html_path = Path(html_path)
    html = ensure_bridge_lite(html_content if html_content is not None else html_path.read_text(encoding="utf-8"))
    content = {"index.html": html.encode("utf-8"), "teacher.md": teacher_md.encode("utf-8"),
               "docspec.json": (json.dumps(docspec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")}
    if design_spec is not None:
        content["design-spec.json"] = (json.dumps(design_spec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    meta_path = dst / "meta.json"
    existing_meta = _load_json(meta_path, {})
    generation = {"job_id": generation_id, "review_id": review_id}
    if generation_id and not review_id:
        raise ValueError("Publicação de geração exige revisão identificada.")
    if dst.exists() and (generation_id or existing_meta.get("generation")):
        if not generation_id or existing_meta.get("generation") != generation:
            raise ValueError("Slug já publicado por outra geração. Usa um novo slug.")
        expected = set(content) | {"meta.json"}
        if set(p.name for p in dst.iterdir()) != expected or any(
            not (dst / name).is_file() or (dst / name).read_bytes() != data
            for name, data in content.items()
        ):
            raise ValueError("O conteúdo da publicação difere da versão revista. Usa um novo slug.")
        # Recupera também um crash entre instalar a atividade e atualizar o índice.
        regenerate_catalog(repo_root)
        return existing_meta
    created = existing_meta.get("createdAt") or _now_iso()
    updated = _now_iso()
    title = docspec.get("topic") or _infer_title_from_html(html, html_path.stem)
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
    if "years" in docspec:
        meta["years"] = validate_years(docspec["years"])
    else:
        meta["years"] = activity_years(existing_meta, docspec)

    activities.mkdir(parents=True, exist_ok=True)
    if generation_id:
        meta["generation"] = generation
        staging = Path(tempfile.mkdtemp(prefix=".publish-", dir=repo_root))
        try:
            for name, data in content.items():
                (staging / name).write_bytes(data)
            _save_json(staging / "meta.json", meta)
            os.rename(staging, dst)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    else:
        dst.mkdir(parents=True, exist_ok=True)
        for name, data in content.items():
            (dst / name).write_bytes(data)
        _save_json(meta_path, meta)
    regenerate_catalog(repo_root)
    return meta
