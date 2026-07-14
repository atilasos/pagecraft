"""Feedback IA em tempo útil às respostas dos alunos.

Fila assíncrona com 2 workers, cache por (unidade, resposta normalizada) e
orçamento de tempo: passado o timeout o aluno recebe uma mensagem pré-escrita
não punitiva e o professor vê o pedido pendente no dashboard. O feedback IA
é camada extra: o feedback determinista da atividade continua a mandar.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata

from ..config import Config
from ..events import utcnow
from ..providers import AIProvider, ProviderError
from ..storage import Storage
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
        self._caches: dict[str, dict] = {}
        self._in_flight: set[tuple[str, str]] = set()

    def start(self) -> None:
        while len([w for w in self._workers if not w.done()]) < self.n_workers:
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self) -> None:
        for w in self._workers:
            w.cancel()

    async def _cache(self, session_id: str) -> dict:
        if session_id not in self._caches:
            path = self.storage.path("sessions", session_id, "feedback-cache.json")
            self._caches[session_id] = await self.storage.read_json(path, default={}) or {}
        return self._caches[session_id]

    async def _save_cache(self, session_id: str) -> None:
        path = self.storage.path("sessions", session_id, "feedback-cache.json")
        await self.storage.write_json(path, self._caches.get(session_id, {}))

    async def request(self, session_id: str, student_id: str, unit_id: str | None, payload: dict) -> None:
        """Chamado quando chega um evento feedback_request; nunca bloqueia."""
        key = (session_id, student_id)
        if key in self._in_flight:
            return  # 1 pedido em voo por aluno
        cache = await self._cache(session_id)
        cache_key = f"{unit_id}|{_normalize(str(payload.get('answer', '')))}"
        cached = cache.get(cache_key)
        if cached:
            await self._deliver(session_id, student_id, unit_id, cached, source="cache")
            return
        self._in_flight.add(key)
        await self._queue.put(
            {
                "session_id": session_id,
                "student_id": student_id,
                "unit_id": unit_id,
                "payload": payload,
                "cache_key": cache_key,
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
            except Exception as exc:  # noqa: BLE001 — worker nunca morre
                await self.classroom.emit_teacher_event(
                    item["session_id"],
                    "feedback_error",
                    {"error": str(exc), "unit_id": item["unit_id"]},
                    student_id=item["student_id"],
                )
            finally:
                self._in_flight.discard(key)

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
            await self._deliver(item["session_id"], item["student_id"], item["unit_id"], text, source="ai")
        except ProviderError as exc:
            await self._deliver(
                item["session_id"], item["student_id"], item["unit_id"], TIMEOUT_MESSAGE, source="timeout"
            )
            await self.classroom.emit_teacher_event(
                item["session_id"],
                "feedback_timeout",
                {"unit_id": item["unit_id"], "error": str(exc), "payload": payload},
                student_id=item["student_id"],
            )

    async def _deliver(self, session_id: str, student_id: str, unit_id: str | None, text: str, source: str) -> None:
        await self.classroom.emit_teacher_event(
            session_id,
            "ai_feedback",
            {"text": text, "unit_id": unit_id, "source": source},
            student_id=student_id,
        )
