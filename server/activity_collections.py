"""Coleções derivadas das declarações de cada atividade publicada.

O registo do Studio (learning/activities.json) conserva códigos e realizações;
o arquivo de uma coleção acontece no `meta.json` da própria atividade. Esta
camada junta as duas fontes para a preparação do professor: palavra e ordem no
método das 28 palavras e se o jogo foi substituído por uma coleção mais nova.
"""

from __future__ import annotations

import re
from pathlib import Path

from .api.catalog import _read_json_cached

M28P_SLUG = re.compile(
    r"^m28p-(?:v3|ciclo)-(?P<word>[a-z]+)-"
    r"(?P<kind>match|pairs|syllables|gap|recall|hunt|discover|listen-build|read-choose|sentence)$"
)
# Ordem pedagógica dentro da palavra (docs/m28p-ciclo-completo.md): ouvir e montar,
# ler e escolher, montar frases, descobrir. A coleção v3 arquivada fica antes.
KIND_ORDER = ["match", "pairs", "hunt", "syllables", "gap", "recall",
              "listen-build", "read-choose", "sentence", "discover"]


def m28p_word(slug: str) -> tuple[str, str] | None:
    match = M28P_SLUG.match(slug or "")
    return (match["word"], match["kind"]) if match else None


def describe(activity: dict, activities_dir: Path) -> dict:
    """Acrescenta `m28p` e `retired` sem alterar o registo guardado."""
    result = dict(activity)
    meta = _read_json_cached(activities_dir / activity["slug"] / "meta.json") or {}
    result["retired"] = meta.get("status") == "archived"
    word = m28p_word(activity["slug"])
    if word:
        label = str(activity.get("title", "")).split(" · ")[-1].strip() or word[0]
        order = meta.get("order")
        result["m28p"] = {
            "word": word[0],
            "label": label,
            "kind": word[1],
            "kind_order": KIND_ORDER.index(word[1]),
            "order": order if isinstance(order, int) else None,
        }
    return result


def describe_all(activities, activities_dir: Path) -> list[dict]:
    return [describe(activity, activities_dir) for activity in activities]


def sort_key(activity: dict):
    """Jogos de uma palavra pela ordem do ciclo; o resto mantém o título."""
    m28p = activity.get("m28p")
    if m28p:
        return (0, m28p["order"] or 99, m28p["kind_order"], activity["title"])
    return (1, 0, 0, activity["title"])
