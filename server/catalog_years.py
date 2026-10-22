"""Anos destinatários declarados, comuns à publicação, índice e API.

``years`` é uma lista explícita de inteiros de 1 a 4. A ausência permite ler
escolaridade histórica de meta.year e depois DocSpec.ageRange. Idades,
etiquetas e referências curriculares nunca declaram destinatários.
"""

from __future__ import annotations

import re


# Listas e intervalos exigem ordinais para não confundir «3 e 4 anos» com
# escolaridade. O singular «3 ano» e o número isolado também são históricos.
_ORDINAL = r"[1-4]\s*\.?\s*[º°o]"
_SCHOOL_YEARS = re.compile(
    rf"(?<![\w.])(?:{_ORDINAL})(?:\s*(?:,|e|/|–|-|a|ao|até)\s*(?:{_ORDINAL}))*\s*anos?\b"
    r"|(?<![\w.\d–-])[1-4]\s*\.?\s*ano\b",
    re.IGNORECASE,
)


def validate_years(value: object) -> list[int]:
    """Valida a declaração explícita; devolve ordem canónica sem duplicados."""
    if not isinstance(value, list) or any(
        type(year) is not int or not 1 <= year <= 4 for year in value
    ):
        raise ValueError("years tem de ser uma lista de inteiros entre 1 e 4")
    return sorted(set(value))


def declared_years(value: object) -> list[int]:
    """Lê apenas escolaridade explícita nos formatos históricos portugueses."""
    if type(value) is int:
        return [value] if 1 <= value <= 4 else []
    if not isinstance(value, str):
        return []
    text = value.strip()
    if re.fullmatch(r"[1-4]", text):
        return [int(text)]
    years: set[int] = set()
    for match in _SCHOOL_YEARS.finditer(text):
        school_years = [int(number) for number in re.findall(r"[1-4]", match.group())]
        if len(school_years) == 2 and re.search(r"[–-]|\b(?:a|ao|até)\b", match.group()):
            years.update(range(min(school_years), max(school_years) + 1))
        else:
            years.update(school_years)
    return sorted(years)


def activity_years(meta: dict, docspec: dict | None = None) -> list[int]:
    """Metadados explícitos prevalecem, incluindo a declaração vazia []."""
    if "years" in meta:
        return validate_years(meta["years"])
    return declared_years(meta.get("year")) or declared_years(
        (docspec or {}).get("ageRange")
    )
