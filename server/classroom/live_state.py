"""Frames transitórios do estado vivo de uma Sessão de aula.

Estes frames são projeções do registo e nunca são Acontecimentos persistidos.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterable, Mapping
from datetime import datetime
from typing import Callable

from .session_state import reduce_session


_TICKS_CLOSED = object()


class LiveTickSubscription:
    def __init__(
        self,
        ticks: LiveSessionTicks,
        session_id: str,
        queue: asyncio.Queue,
    ):
        self._ticks = ticks
        self.session_id = session_id
        self._queue = queue
        self._closed = False

    def __aiter__(self) -> LiveTickSubscription:
        return self

    async def __anext__(self) -> datetime | str:
        instant = await self._queue.get()
        if instant is _TICKS_CLOSED:
            raise StopAsyncIteration
        return instant

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._ticks.unsubscribe(self.session_id, self._queue)


class LiveSessionTicks:
    """Um único relógio grosseiro por sessão com subscritores vivos."""

    def __init__(
        self,
        clock: Callable[[], datetime | str],
        *,
        interval_seconds: float = 30,
        sleep: Callable[[float], Awaitable[object]] = asyncio.sleep,
    ):
        self._clock = clock
        self._interval_seconds = interval_seconds
        self._sleep = sleep
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def subscribe(self, session_id: str) -> LiveTickSubscription:
        queue: asyncio.Queue = asyncio.Queue()
        subscribers = self._subscribers.setdefault(session_id, set())
        subscribers.add(queue)
        if session_id not in self._tasks:
            self._tasks[session_id] = asyncio.create_task(
                self._run(session_id)
            )
        return LiveTickSubscription(self, session_id, queue)

    def publish(
        self, session_id: str, *, now: datetime | str | None = None
    ) -> None:
        instant = self._clock() if now is None else now
        for queue in tuple(self._subscribers.get(session_id, ())):
            queue.put_nowait(instant)

    def session_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._subscribers))

    def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(session_id)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if subscribers:
            return
        self._subscribers.pop(session_id, None)
        task = self._tasks.pop(session_id, None)
        if task is not None and task is not asyncio.current_task():
            task.cancel()

    async def _run(self, session_id: str) -> None:
        try:
            while session_id in self._subscribers:
                await self._sleep(self._interval_seconds)
                self.publish(session_id)
        except asyncio.CancelledError:
            pass
        finally:
            if self._tasks.get(session_id) is asyncio.current_task():
                self._tasks.pop(session_id, None)

    async def stop(self) -> None:
        tasks = tuple(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        for subscribers in self._subscribers.values():
            for queue in subscribers:
                queue.put_nowait(_TICKS_CLOSED)
        self._subscribers.clear()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


def _session_projection(events: Iterable[Mapping], session: Mapping) -> dict:
    frozen = False
    status = str(session.get("status") or "live")
    for record in events:
        event_type = record.get("type")
        if event_type == "freeze_screens":
            frozen = True
        elif event_type == "unfreeze_screens":
            frozen = False
        elif event_type == "session_closed":
            status = "closed"
    return {
        "status": status,
        "closed": status == "closed",
        "frozen": frozen,
    }


def session_state_snapshot(
    events: list[Mapping],
    session: Mapping,
    *,
    now: datetime | str,
    role: str,
    student_id: str | None = None,
) -> dict:
    """Projeta o estado autorizado no instante pedido."""
    if role == "board":
        return {"session": _session_projection(events, session)}

    state = reduce_session(
        events,
        now=now,
        roster=session.get("roster", {}),
        started_at=session.get("started_at"),
    )
    students = state["students"]
    if role == "student":
        if student_id is None:
            raise ValueError("o instantâneo de aluno requer uma identidade")
        students = (
            {student_id: students[student_id]}
            if student_id in students
            else {}
        )
    elif role != "teacher":
        raise ValueError(f"papel desconhecido: {role}")

    snapshot = {
        "session": _session_projection(events, session),
        "students": students,
    }
    if role == "teacher":
        snapshot["numbers"] = state["numbers"]
    return snapshot


def changed_student_frames(previous: Mapping, current: Mapping) -> list[dict]:
    """Compara duas projeções autorizadas sem expor alunos fora delas."""
    before = previous.get("students", {})
    after = current.get("students", {})
    return [
        {"student_id": student_id, "student": student}
        for student_id, student in after.items()
        if before.get(student_id) != student
    ]


def changed_session_frame(
    previous: Mapping, current: Mapping
) -> dict | None:
    """Produz o delta global quando o controlo ou ciclo de vida mudou."""
    session = current.get("session", {})
    if previous.get("session") == session:
        return None
    return {"session": session}
