"""Feedback IA em tempo útil às respostas dos alunos.

Fila assíncrona com 2 workers, cache por (unidade, resposta normalizada) e
orçamento de tempo: passado o timeout o aluno recebe uma mensagem pré-escrita
não punitiva e o professor vê o pedido pendente no dashboard. O feedback IA
é camada extra: o feedback determinista da atividade continua a mandar.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import unicodedata
from collections import Counter

from ..config import Config
from ..events import EventSubscription, utcnow
from ..providers import AIProvider, ProviderError
from ..storage import Storage
from .errors import SessionClosedError
from .service import ClassroomService

FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "feedback": {"type": "string", "maxLength": 400},
        "encoraja_tentar": {"type": "boolean"},
    },
    "required": ["feedback"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """És um assistente pedagógico numa sala de aula do 1.º ciclo em Portugal (Movimento da Escola Moderna).
Dás feedback formativo a respostas de crianças de 6-10 anos, em português europeu (AO90).
Regras absolutas:
- Máximo 2 frases curtas, vocabulário da idade, tratamento por tu.
- Nunca digas "errado", "mal", "falhaste" nem uses tom punitivo.
- Se a resposta está incompleta ou imprecisa: reconhece o que já está bem e dá UMA pista concreta para o próximo passo (nunca a solução).
- Se a resposta está certa: celebra a descoberta e nomeia o que a criança percebeu.
- Não uses emojis nem travessões."""

BANNED = re.compile(r"\berrado\b|\bwrong\b|\bfalhaste\b|\bmal\b[!.]", re.IGNORECASE)

TIMEOUT_MESSAGE = (
    "O assistente está a pensar mais devagar do que tu! "
    "Continua o teu trabalho, o professor já viu a tua resposta."
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().strip())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text)[:200]


class FeedbackService:
    def __init__(
        self,
        config: Config,
        storage: Storage,
        classroom: ClassroomService,
        provider: AIProvider,
        workers: int = 2,
    ):
        self.config = config
        self.storage = storage
        self.classroom = classroom
        self.provider = provider
        self.n_workers = workers
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._subscription: EventSubscription | None = None
        self._subscriber: asyncio.Task | None = None
        self._recovery: asyncio.Task | None = None
        self._caches: dict[str, dict] = {}
        self._pending: Counter[tuple[str, str]] = Counter()
        self._scheduled: set[tuple[str, int]] = set()
        self.max_pending_per_student = 3

    def start(self) -> None:
        if self._subscriber is None or self._subscriber.done():
            self._subscription = self.classroom.hub.subscribe("sessions")
            self._subscriber = asyncio.create_task(
                self._listen(self._subscription)
            )
        if self._recovery is None or self._recovery.done():
            self._recovery = asyncio.create_task(self._recover())
        while len([w for w in self._workers if not w.done()]) < self.n_workers:
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        if self._subscription is not None:
            self._subscription.close()
            self._subscription = None
        if self._subscriber is not None:
            self._subscriber.cancel()
            await asyncio.gather(self._subscriber, return_exceptions=True)
            self._subscriber = None
        if self._recovery is not None:
            self._recovery.cancel()
            await asyncio.gather(self._recovery, return_exceptions=True)
            self._recovery = None
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._queue = asyncio.Queue()
        self._pending.clear()
        self._scheduled.clear()

    async def _listen(self, subscription: EventSubscription) -> None:
        async for channel, record in subscription:
            if (
                len(channel) == 3
                and channel[2] == "events.jsonl"
                and record.get("type") == "feedback_request"
                and record.get("student_id")
            ):
                await self._schedule_record(channel[1], record)

    async def _recover(self) -> None:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return
        for path in sorted(sessions_dir.glob("*/events.jsonl")):
            records = await self.storage.read_jsonl(path)
            if any(record.get("type") == "session_closed" for record in records):
                continue
            for record in self._unprocessed_requests(records):
                await self._schedule_record(path.parent.name, record)

    @staticmethod
    def _unprocessed_requests(records: list[dict]) -> list[dict]:
        requests = [
            record
            for record in records
            if record.get("type") == "feedback_request"
            and record.get("student_id")
            and record.get("seq") is not None
        ]
        handled = {
            int(record["caused_by_seq"])
            for record in records
            if record.get("type")
            in {"ai_feedback", "feedback_error", "feedback_dropped"}
            and record.get("caused_by_seq") is not None
        }

        # Compatibilidade com respostas gravadas antes de existir causalidade
        # explícita: consome, por aluno/unidade, um pedido por desfecho legado.
        legacy_outcomes = Counter(
            (
                str(record.get("student_id")),
                (record.get("payload") or {}).get("unit_id"),
            )
            for record in records
            if record.get("type")
            in {"ai_feedback", "feedback_error", "feedback_dropped"}
            and record.get("caused_by_seq") is None
        )
        pending = []
        for record in requests:
            seq = int(record["seq"])
            if seq in handled:
                continue
            key = (str(record["student_id"]), record.get("unit_id"))
            if legacy_outcomes[key]:
                legacy_outcomes[key] -= 1
                continue
            pending.append(record)
        return pending

    async def _schedule_record(self, session_id: str, record: dict) -> None:
        request_seq = int(record["seq"])
        key = (session_id, request_seq)
        if key in self._scheduled:
            return
        self._scheduled.add(key)
        await self.request(
            session_id,
            record["student_id"],
            record.get("unit_id"),
            record.get("payload") or {},
            request_seq=request_seq,
        )

    async def _cache(self, session_id: str) -> dict:
        if session_id not in self._caches:
            path = self.storage.path("sessions", session_id, "feedback-cache.json")
            self._caches[session_id] = await self.storage.read_json(path, default={}) or {}
        return self._caches[session_id]

    async def _save_cache(self, session_id: str) -> None:
        path = self.storage.path("sessions", session_id, "feedback-cache.json")
        await self.storage.write_json(path, self._caches.get(session_id, {}))

    @staticmethod
    def _cache_key(unit_id: str | None, payload: dict) -> str:
        # inclui pergunta e resposta esperada: a mesma resposta a perguntas
        # diferentes da mesma unidade não pode partilhar feedback
        semantic = "|".join(
            (
                str(unit_id),
                _normalize(str(payload.get("question", ""))),
                _normalize(str(payload.get("expected", ""))),
                _normalize(str(payload.get("answer", ""))),
            )
        )
        return hashlib.sha256(semantic.encode("utf-8")).hexdigest()[:32]

    async def request(
        self,
        session_id: str,
        student_id: str,
        unit_id: str | None,
        payload: dict,
        *,
        request_seq: int | None = None,
    ) -> None:
        """Chamado quando chega um evento feedback_request; nunca bloqueia."""
        cache = await self._cache(session_id)
        cache_key = self._cache_key(unit_id, payload)
        cached = cache.get(cache_key)
        if cached:
            await self._deliver(
                session_id,
                student_id,
                unit_id,
                cached,
                source="cache",
                request_seq=request_seq,
            )
            return
        key = (session_id, student_id)
        if self._pending[key] >= self.max_pending_per_student:
            # não descartar em silêncio: o professor fica a saber
            await self.classroom.emit_event(
                session_id,
                "feedback_dropped",
                {"unit_id": unit_id, "reason": "demasiados pedidos seguidos"},
                author="assistant",
                student_id=student_id,
                caused_by_seq=request_seq,
            )
            return
        self._pending[key] += 1
        await self._queue.put(
            {
                "session_id": session_id,
                "student_id": student_id,
                "unit_id": unit_id,
                "payload": payload,
                "cache_key": cache_key,
                "request_seq": request_seq,
                "queued_at": utcnow(),
            }
        )
        self.start()

    async def _worker(self) -> None:
        while True:
            item = await self._queue.get()
            key = (item["session_id"], item["student_id"])
            try:
                await self._process(item)
            except asyncio.CancelledError:
                raise
            except SessionClosedError:
                # A resposta terminou depois do fecho: o registo já é imutável.
                pass
            except Exception as exc:  # noqa: BLE001 — worker nunca morre
                try:
                    await self.classroom.emit_event(
                        item["session_id"],
                        "feedback_error",
                        {"error": str(exc), "unit_id": item["unit_id"]},
                        author="assistant",
                        student_id=item["student_id"],
                        caused_by_seq=item["request_seq"],
                    )
                except SessionClosedError:
                    pass
            finally:
                self._pending[key] -= 1
                if self._pending[key] <= 0:
                    del self._pending[key]

    async def _process(self, item: dict) -> None:
        payload = item["payload"]
        prompt = (
            f"Pergunta ou tarefa: {payload.get('question', '')}\n"
            f"Resposta esperada (referência do professor): {payload.get('expected', '(não indicada)')}\n"
            f"Resposta da criança: {payload.get('answer', '')}\n\n"
            "Dá o teu feedback formativo."
        )
        try:
            result = await self.provider.complete(
                prompt,
                schema=FEEDBACK_SCHEMA,
                system=SYSTEM_PROMPT,
                timeout_s=self.config.feedback_timeout_s,
            )
            text = str(result.get("feedback", "")).strip()
            if not text or BANNED.search(text):
                text = "Boa tentativa! Volta a ler a pergunta com calma e experimenta outra vez."
            cache = await self._cache(item["session_id"])
            cache[item["cache_key"]] = text
            await self._save_cache(item["session_id"])
            await self._deliver(
                item["session_id"],
                item["student_id"],
                item["unit_id"],
                text,
                source="ai",
                request_seq=item["request_seq"],
            )
        except ProviderError as exc:
            await self._deliver(
                item["session_id"],
                item["student_id"],
                item["unit_id"],
                TIMEOUT_MESSAGE,
                source="timeout",
                request_seq=item["request_seq"],
            )
            await self.classroom.emit_event(
                item["session_id"],
                "feedback_timeout",
                {"unit_id": item["unit_id"], "error": str(exc), "payload": payload},
                author="assistant",
                student_id=item["student_id"],
                caused_by_seq=item["request_seq"],
            )

    async def _deliver(
        self,
        session_id: str,
        student_id: str,
        unit_id: str | None,
        text: str,
        source: str,
        *,
        request_seq: int | None,
    ) -> None:
        await self.classroom.emit_event(
            session_id,
            "ai_feedback",
            {"text": text, "unit_id": unit_id, "source": source},
            author="assistant",
            student_id=student_id,
            caused_by_seq=request_seq,
        )
