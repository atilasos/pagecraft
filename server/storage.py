"""Persistência em ficheiros: JSON atómico e JSONL append-only.

Um processo único; um asyncio.Lock por caminho evita escritas entrelaçadas.
Escrita JSON é sempre temp + os.replace para nunca deixar ficheiro truncado.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, AsyncIterator


class Storage:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _lock(self, path: Path) -> asyncio.Lock:
        return self._locks[str(path)]

    def path(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ---- JSON ----

    async def write_json(self, path: Path, data: Any) -> None:
        async with self._lock(path):
            await asyncio.to_thread(self._write_json_sync, path, data)

    @staticmethod
    def _write_json_sync(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise

    async def read_json(self, path: Path, default: Any = None) -> Any:
        try:
            text = await asyncio.to_thread(path.read_text, "utf-8")
        except FileNotFoundError:
            return default
        return json.loads(text)

    # ---- JSONL ----

    async def append_jsonl(self, path: Path, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False)
        async with self._lock(path):
            await asyncio.to_thread(self._append_line_sync, path, line)

    @staticmethod
    def _append_line_sync(path: Path, line: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    async def read_jsonl(self, path: Path) -> list[dict]:
        """Lê todos os registos; ignora uma última linha truncada (crash a meio)."""
        try:
            text = await asyncio.to_thread(path.read_text, "utf-8")
        except FileNotFoundError:
            return []
        records: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    async def iter_jsonl(self, path: Path) -> AsyncIterator[dict]:
        for record in await self.read_jsonl(path):
            yield record
