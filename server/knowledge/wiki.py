"""Acesso ao conhecimento pedagógico da wiki (Sebenta / vault Obsidian).

Via preferida: a API HTTP local da Sebenta (serviço systemd `sebenta`,
por omissão em http://127.0.0.1:8765), que serve 20_Wiki/ com pesquisa
BM25 e leitura de páginas. Fallback: a ferramenta oficial do vault
(wiki_tool.py) por subprocess. Tudo apenas leitura.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import quote

import httpx

WIKI_TOOL_REL = "90_Meta/Agent/wiki-tools/wiki_tool.py"
DEFAULT_API_URL = "http://127.0.0.1:8765"

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


class WikiAPIError(RuntimeError):
    """A API Sebenta falhou, respondeu com erro ou devolveu um formato inesperado."""


class WikiClient:
    def __init__(
        self,
        vault_path: Path,
        api_url: str = DEFAULT_API_URL,
        timeout_s: float = 15.0,
    ):
        self.vault_path = Path(vault_path)
        self.tool = self.vault_path / WIKI_TOOL_REL
        self.api_url = api_url.rstrip("/")
        self.timeout_s = timeout_s
        self._api_ok: bool | None = None  # resultado do último contacto com a API

    @property
    def available(self) -> bool:
        if self._api_ok:
            return True
        return self.tool.exists()

    async def probe(self) -> bool:
        """Confirma se há alguma via utilizável (API Sebenta ou CLI do vault)."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.api_url}/api/health")
                self._api_ok = resp.status_code == 200
        except httpx.HTTPError:
            self._api_ok = False
        return self._api_ok or self.tool.exists()

    # ---- via API Sebenta ----

    async def _api_get(self, path: str, params: dict | None = None) -> dict:
        # circuit breaker: depois de uma falha de transporte, não voltar a
        # tentar a API (com timeout de 15 s por chamada) até novo probe()
        if self._api_ok is False:
            raise WikiAPIError("API Sebenta marcada como indisponível até novo probe")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                resp = await client.get(f"{self.api_url}{path}", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            # 4xx: a API está viva, só este recurso falhou — não disparar o breaker
            self._api_ok = exc.response.status_code < 500
            raise WikiAPIError(f"HTTP {exc.response.status_code} em {path}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            self._api_ok = False
            raise WikiAPIError(str(exc)) from exc
        if not isinstance(data, dict):
            raise WikiAPIError(f"resposta inesperada da API ({type(data).__name__})")
        self._api_ok = True
        return data

    async def search_pages(self, query: str, *, limit: int = 8) -> list[dict]:
        """Resultados estruturados da pesquisa BM25 na wiki (título, path, summary).

        API Sebenta primeiro; fallback para `wiki_tool.py bm25-search --json`,
        que devolve o mesmo formato. [] se nenhuma via estiver disponível.
        """
        try:
            data = await self._api_get(
                "/api/search", {"q": query, "kind": "wiki", "limit": limit}
            )
            results = data.get("results")
            if isinstance(results, list):
                return [r for r in results if isinstance(r, dict)]
        except WikiAPIError:
            pass
        if not self.tool.exists():
            return []
        try:
            out = await self._run("bm25-search", query, "--json", "--limit", str(limit))
            parsed = json.loads(out)
        except (RuntimeError, TimeoutError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        return [r for r in parsed if isinstance(r, dict)]

    # ---- via CLI do vault (fallback) ----

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

    # ---- operações com fallback automático API → CLI ----

    async def search(self, query: str, *, limit: int = 8) -> str:
        results = await self.search_pages(query, limit=limit)
        return "\n".join(
            f"- {r.get('title', '?')}: {(r.get('summary') or '').strip()}"
            for r in results
        )

    async def read_page(self, title: str) -> str:
        try:
            data = await self._api_get(f"/api/wiki/{quote(title, safe='')}")
            content = str(data.get("content") or "")
            if content.strip():
                return content
        except WikiAPIError:
            pass
        if not self.tool.exists():
            raise RuntimeError(
                f"página «{title}» indisponível: API Sebenta em baixo e CLI do vault ausente"
            )
        return await self._run("read", title)

    # ---- contexto para prompts ----

    async def mem_context(
        self, instruments: list[str] | None = None, max_chars_per_page: int = 3000
    ) -> str:
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

    async def topic_context(
        self,
        topic: str,
        subject: str = "",
        *,
        max_pages: int = 3,
        max_chars_per_page: int = 2500,
    ) -> str:
        """Excertos das páginas da wiki mais relevantes para o tema pedido.

        Pesquisa BM25 pelo tópico+disciplina e lê as melhores páginas,
        excluindo as MEM nucleares (já injetadas por mem_context).
        """
        query = f"{topic} {subject}".strip()
        if not query:
            return ""
        results = await self.search_pages(query, limit=max_pages * 3)
        mem_titles = set(MEM_CORE_PAGES)
        parts: list[str] = []
        seen: set[str] = set()
        for r in results:
            title = (r.get("title") or "").strip()
            if not title or title in seen or title in mem_titles:
                continue
            seen.add(title)
            try:
                body = await self.read_page(title)
            except (RuntimeError, TimeoutError):
                continue
            if not body.strip():
                continue
            parts.append(f"## {title}\n\n{body[:max_chars_per_page].strip()}\n")
            if len(parts) >= max_pages:
                break
        return "\n".join(parts)
