"""EventLog: JSONL persistente + broadcast em memória com seq monotónico.

Cada canal (job de geração, sessão de aula) tem um EventLog. O `seq` é
atribuído no append e serve de SSE id para replay via Last-Event-ID.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Callable

from .storage import Storage


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventLog:
    def __init__(
        self,
        storage: Storage,
        path: Path,
        on_append: Callable[[dict], None] | None = None,
    ):
        self.storage = storage
        self.path = path
        self._on_append = on_append
        self._seq = 0
        self._loaded = False
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        records = await self.storage.read_jsonl(self.path)
        if records:
            self._seq = max(int(r.get("seq", 0)) for r in records)
        self._loaded = True

    async def append(self, record: dict) -> dict:
        async with self._lock:
            await self._ensure_loaded()
            self._seq += 1
            record = {**record, "seq": self._seq, "ts": record.get("ts") or utcnow()}
            await self.storage.append_jsonl(self.path, record)
        for queue in list(self._subscribers):
            queue.put_nowait(record)
        if self._on_append is not None:
            self._on_append(record)
        return record

    async def replay(self, after_seq: int = 0) -> list[dict]:
        await self._ensure_loaded()
        records = await self.storage.read_jsonl(self.path)
        return [r for r in records if int(r.get("seq", 0)) > after_seq]

    async def subscribe(self, after_seq: int = 0) -> AsyncIterator[dict]:
        """Replay do histórico seguido de eventos ao vivo, sem lacunas."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            backlog = await self.replay(after_seq)
            self._subscribers.add(queue)
        try:
            last = after_seq
            for record in backlog:
                yield record
                last = int(record.get("seq", last))
            while True:
                record = await queue.get()
                if int(record.get("seq", 0)) > last:
                    yield record
                    last = int(record.get("seq", last))
        finally:
            self._subscribers.discard(queue)


_SUBSCRIPTION_CLOSED = object()


class EventSubscription:
    """Subscrição ao vivo dos canais de um EventHub."""

    def __init__(self, hub: EventHub, prefix: tuple[str, ...]):
        self._hub = hub
        self.prefix = prefix
        self._queue: asyncio.Queue = asyncio.Queue()
        self._closed = False

    def __aiter__(self) -> EventSubscription:
        return self

    async def __anext__(self) -> tuple[tuple[str, ...], dict]:
        item = await self._queue.get()
        if item is _SUBSCRIPTION_CLOSED:
            raise StopAsyncIteration
        return item

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._hub._unsubscribe(self)
        self._queue.put_nowait(_SUBSCRIPTION_CLOSED)

    def _publish(self, channel: tuple[str, ...], record: dict) -> None:
        if not self._closed:
            self._queue.put_nowait((channel, record))


class EventHub:
    """Registo de EventLogs por canal, com criação preguiçosa."""

    def __init__(self, storage: Storage):
        self.storage = storage
        self._logs: dict[str, EventLog] = {}
        self._subscriptions: set[EventSubscription] = set()

    def log_for(self, *path_parts: str) -> EventLog:
        key = "/".join(path_parts)
        if key not in self._logs:
            channel = tuple(path_parts)
            self._logs[key] = EventLog(
                self.storage,
                self.storage.path(*path_parts),
                on_append=lambda record: self._publish(channel, record),
            )
        return self._logs[key]

    def subscribe(self, *prefix: str) -> EventSubscription:
        """Observa appends futuros nos canais que começam por ``prefix``."""
        subscription = EventSubscription(self, tuple(prefix))
        self._subscriptions.add(subscription)
        return subscription

    def _publish(self, channel: tuple[str, ...], record: dict) -> None:
        for subscription in list(self._subscriptions):
            if channel[: len(subscription.prefix)] == subscription.prefix:
                subscription._publish(channel, record)

    def _unsubscribe(self, subscription: EventSubscription) -> None:
        self._subscriptions.discard(subscription)
