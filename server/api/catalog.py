"""Catálogo de atividades enriquecido (classificação) e estrutura de unidades.

A classificação junta os metadados com o docspec de cada atividade publicada
(disciplina real de curriculum.ae), com cache por mtime para não reler JSON
a cada pedido.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from ..access import RoutePolicy, access_policy
from ..catalog_years import activity_years

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


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")


def list_activities(activities_dir: Path) -> list[dict]:
    items = []
    if not activities_dir.is_dir():
        return items
    for meta_path in sorted(activities_dir.glob("*/meta.json")):
        meta = _read_json_cached(meta_path)
        if not meta or meta.get("status") == "archived":
            continue
        docspec = _read_json_cached(meta_path.parent / "docspec.json")
        subject = meta.get("subject") or _subject_from_docspec(docspec)
        years = activity_years(meta, docspec)
        items.append(
            {
                # o nome do diretório é a verdade (o slug do meta pode divergir)
                "slug": meta_path.parent.name,
                "title": meta.get("title", meta_path.parent.name),
                "years": years,
                "year": years[0] if len(years) == 1 else None,
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
@access_policy(RoutePolicy.TEACHER)
async def activities(request: Request):
    config = request.app.state.config
    items = list_activities(config.activities_dir)
    subjects = sorted({a["subject"] for a in items if a["subject"]})
    years = sorted({year for activity in items for year in activity["years"]})
    return {"items": items, "subjects": subjects, "years": years}


@router.get("/activities/{slug}/units")
@access_policy(RoutePolicy.TEACHER)
async def activity_units(slug: str, request: Request):
    """Estrutura da atividade para o controlo «chamar a atenção»: uma entrada
    por unidade, com o id estável do bridge (u1, u2, …)."""
    config = request.app.state.config
    if not SLUG_RE.match(slug):
        raise HTTPException(404, "atividade não encontrada")
    activities_root = config.activities_dir.resolve()
    docspec_path = (activities_root / slug / "docspec.json").resolve()
    if not docspec_path.is_relative_to(activities_root):
        raise HTTPException(404, "atividade não encontrada")
    docspec = _read_json_cached(docspec_path)
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
