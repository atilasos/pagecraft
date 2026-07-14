"""Catálogo de atividades enriquecido (classificação) e estrutura de unidades.

A classificação junta o catalog.json com o docspec de cada atividade publicada
(disciplina real de curriculum.ae), com cache por mtime para não reler JSON
a cada pedido.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api", tags=["catalog"])

_cache: dict[str, tuple[float, dict]] = {}


def _read_json_cached(path: Path) -> dict | None:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return None
    key = str(path)
    hit = _cache.get(key)
    if hit and hit[0] == mtime:
        return hit[1]
    try:
        data = json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    _cache[key] = (mtime, data)
    return data


def _subject_from_docspec(docspec: dict | None) -> str:
    if not docspec:
        return ""
    ae = (docspec.get("curriculum") or {}).get("ae") or []
    if ae and isinstance(ae, list):
        return str(ae[0].get("subject", ""))
    return ""


def _parse_year(value) -> int | None:
    """Normaliza o ano de escolaridade a partir dos formatos históricos:
    3, "3", "3.º ano", "1.º ano (6-7 anos)", "9-10 anos (4.º ano do 1.º CEB)".
    Idades soltas ("6-8 anos, ajustável") ficam sem ano."""
    if isinstance(value, int):
        return value if 1 <= value <= 4 else None
    text = str(value or "")
    match = re.search(r"([1-4])\s*\.?\s*º?\s*ano", text) or re.fullmatch(r"\s*([1-4])\s*", text)
    return int(match.group(1)) if match else None


def list_activities(activities_dir: Path) -> list[dict]:
    items = []
    if not activities_dir.is_dir():
        return items
    for meta_path in sorted(activities_dir.glob("*/meta.json")):
        meta = _read_json_cached(meta_path)
        if not meta:
            continue
        subject = meta.get("subject") or _subject_from_docspec(
            _read_json_cached(meta_path.parent / "docspec.json")
        )
        items.append(
            {
                "slug": meta.get("slug", meta_path.parent.name),
                "title": meta.get("title", meta_path.parent.name),
                "year": _parse_year(meta.get("year")),
                "yearLabel": str(meta.get("year") or ""),
                "ageRange": meta.get("ageRange", ""),
                "duration": meta.get("duration"),
                "subject": subject,
                "maker": meta.get("maker"),
                "tags": meta.get("tags", []),
                "createdAt": meta.get("createdAt", ""),
            }
        )
    items.sort(key=lambda a: a.get("createdAt") or "", reverse=True)
    return items


@router.get("/activities")
async def activities(request: Request):
    config = request.app.state.config
    items = list_activities(config.activities_dir)
    subjects = sorted({a["subject"] for a in items if a["subject"]})
    years = sorted({a["year"] for a in items if a["year"]})
    return {"items": items, "subjects": subjects, "years": years}


@router.get("/activities/{slug}/units")
async def activity_units(slug: str, request: Request):
    """Estrutura da atividade para o controlo «chamar a atenção»: uma entrada
    por unidade, com o id estável do bridge (u1, u2, …)."""
    config = request.app.state.config
    docspec = _read_json_cached(config.activities_dir / slug / "docspec.json")
    if docspec is None:
        raise HTTPException(404, "atividade sem docspec")
    units = []
    for i, unit in enumerate(docspec.get("units") or []):
        units.append(
            {
                "id": f"u{i + 1}",
                "summary": unit.get("summary", f"Unidade {i + 1}"),
                "duration": unit.get("duration"),
            }
        )
    return {"slug": slug, "units": units}
