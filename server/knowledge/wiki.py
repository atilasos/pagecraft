"""Acesso ao conhecimento pedagógico da wiki (vault Obsidian).

Usa a ferramenta oficial do vault (wiki_tool.py) por subprocess — search e
bm25-search indexam 20_Wiki/. `read` devolve o corpo de uma página pelo
título. Tudo apenas leitura.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

WIKI_TOOL_REL = "90_Meta/Agent/wiki-tools/wiki_tool.py"

# Páginas nucleares para fundamentar geração MEM (existência verificada no vault)
MEM_CORE_PAGES = [
    "Modelo Pedagógico do MEM",
    "Plano Individual de Trabalho",
    "Tempo de Estudo Autónomo",
    "Conselho de Cooperação Educativa",
    "Circuitos de Comunicação",
    "Trabalho de Projeto",
    "Avaliação Formativa",
    "Avaliação Cooperada",
    "Diferenciação Pedagógica",
]


class WikiClient:
    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self.tool = self.vault_path / WIKI_TOOL_REL

    @property
    def available(self) -> bool:
        return self.tool.exists()

    async def _run(self, *args: str, timeout_s: int = 30) -> str:
        proc = await asyncio.create_subprocess_exec(
            "python3",
            str(self.tool),
            *args,
            cwd=str(self.vault_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"wiki_tool {' '.join(args)} excedeu {timeout_s}s")
        if proc.returncode != 0:
            raise RuntimeError(
                f"wiki_tool {' '.join(args)} falhou ({proc.returncode}): "
                + (stderr or b"").decode("utf-8", "replace")[-500:]
            )
        return (stdout or b"").decode("utf-8", "replace")

    async def search(self, query: str, *, bm25: bool = True) -> str:
        return await self._run("bm25-search" if bm25 else "search", query)

    async def read_page(self, title: str) -> str:
        return await self._run("read", title)

    async def mem_context(self, instruments: list[str] | None = None, max_chars_per_page: int = 3000) -> str:
        """Excertos das páginas MEM nucleares (ou das pedidas) para injetar em prompts."""
        titles = instruments or MEM_CORE_PAGES
        parts: list[str] = []
        for title in titles:
            try:
                body = await self.read_page(title)
            except (RuntimeError, TimeoutError):
                continue
            parts.append(f"## {title}\n\n{body[:max_chars_per_page].strip()}\n")
        return "\n".join(parts)
