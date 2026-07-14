"""Aprendizagens Essenciais (documentos oficiais DGE) a partir do vault.

Os ficheiros vivem em documentos-oficiais/aprendizagens-essenciais/ com
frontmatter (disciplina, ciclo, ano, fonte). A pesquisa é por convenção de
nome de ficheiro (<disciplina>-<ano>-ano-1-ciclo.md) com fallbacks: documento
único de ciclo (<disciplina>-1-ciclo.md) e, em último recurso, a URL DGE do
frontmatter fica registada para consulta web.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

AE_REL = "documentos-oficiais/aprendizagens-essenciais"


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


@dataclass
class AEDocument:
    subject: str
    year: int | None
    path: str
    source_url: str
    body: str


class AEClient:
    def __init__(self, vault_path: Path):
        self.ae_dir = Path(vault_path) / AE_REL

    @property
    def available(self) -> bool:
        return self.ae_dir.is_dir()

    def _parse_frontmatter(self, text: str) -> tuple[dict, str]:
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) < 3:
            return {}, text
        meta: dict = {}
        for line in parts[1].splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip().strip('"')
        return meta, parts[2]

    def find(self, subject: str, year: int) -> AEDocument | None:
        """Documento AE para disciplina+ano do 1.º ciclo, com fallback de ciclo."""
        if not self.available:
            return None
        slug = _slugify(subject)
        candidates = [
            self.ae_dir / f"{slug}-{year}-ano-1-ciclo.md",
            self.ae_dir / f"{slug}-1-ciclo.md",
        ]
        # tolerância a variações de slug (ex.: "estudo do meio" vs "estudo-do-meio")
        if not any(c.exists() for c in candidates):
            matches = sorted(self.ae_dir.glob(f"*{slug.split('-')[0]}*-{year}-ano-1-ciclo.md"))
            candidates.extend(matches)
        for path in candidates:
            if path.exists():
                text = path.read_text("utf-8")
                meta, body = self._parse_frontmatter(text)
                year_match = re.search(r"\d+", meta.get("ano", ""))
                return AEDocument(
                    subject=meta.get("disciplina", subject),
                    year=int(year_match.group()) if year_match else None,
                    path=str(path),
                    source_url=meta.get("fonte", ""),
                    body=body.strip(),
                )
        return None

    def list_subjects(self) -> list[str]:
        if not self.available:
            return []
        subjects = set()
        for path in self.ae_dir.glob("*-1-ciclo.md"):
            stem = re.sub(r"-\d-ano-1-ciclo$|-1-ciclo$", "", path.stem)
            subjects.add(stem)
        return sorted(subjects)

    def context_for(self, subject: str, year: int, max_chars: int = 12000) -> tuple[str, str]:
        """(excerto, citação) para injetar no prompt do Architect."""
        doc = self.find(subject, year)
        if doc is None:
            return "", ""
        citation = f"AE {doc.subject} {year}.º ano (DGE). Fonte: {doc.source_url or doc.path}"
        return doc.body[:max_chars], citation
