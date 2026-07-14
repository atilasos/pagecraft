import asyncio

import pytest

from server.classroom.feedback import TIMEOUT_MESSAGE, FeedbackService
from server.classroom.service import ClassroomService
from server.config import Config
from server.events import EventHub
from server.providers import ProviderTimeout
from server.storage import Storage


class GoodProvider:
    name = "fake"

    def __init__(self, text="Boa! Percebeste que as metades são iguais."):
        self.text = text
        self.calls = 0

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=20, workdir=None):
        self.calls += 1
        return {"feedback": self.text}


class SlowProvider:
    name = "fake"

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=20, workdir=None):
        raise ProviderTimeout("demorou demasiado")


@pytest.fixture
def env(tmp_path):
    config = Config(data_dir=tmp_path, feedback_timeout_s=1)
    storage = Storage(config.data_dir)
    hub = EventHub(storage)
    classroom = ClassroomService(config, storage, hub)
    return config, storage, hub, classroom


async def _session_with_student(classroom):
    cls = await classroom.create_class("2.º B", 2, ["Rita"])
    session = await classroom.create_session(cls["id"], "slug", "Atividade")
    student_id = next(iter(session["roster"]))
    await classroom.claim_identity(session["id"], student_id)
    return session, student_id


async def _wait_event(storage, session_id, type_, timeout=3.0):
    path = storage.path("sessions", session_id, "events.jsonl")

    async def poll():
        while True:
            for r in await storage.read_jsonl(path):
                if r["type"] == type_:
                    return r
            await asyncio.sleep(0.02)

    return await asyncio.wait_for(poll(), timeout)


async def test_feedback_delivered(env):
    config, storage, hub, classroom = env
    provider = GoodProvider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    await fb.request(session["id"], student_id, "u1", {"question": "2+2?", "answer": "4", "expected": "4"})
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert record["student_id"] == student_id
    assert "Percebeste" in record["payload"]["text"]
    assert record["payload"]["source"] == "ai"
    await fb.stop()


async def test_feedback_cache_hit(env):
    config, storage, hub, classroom = env
    provider = GoodProvider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    await fb.request(session["id"], student_id, "u1", {"question": "q", "answer": "quatro"})
    await _wait_event(storage, session["id"], "ai_feedback")
    # mesma resposta (normalizada) → cache, sem nova chamada
    await fb.request(session["id"], student_id, "u1", {"question": "q", "answer": "  QUATRO "})
    await asyncio.sleep(0.1)
    events = await storage.read_jsonl(storage.path("sessions", session["id"], "events.jsonl"))
    ai = [e for e in events if e["type"] == "ai_feedback"]
    assert len(ai) == 2
    assert ai[1]["payload"]["source"] == "cache"
    assert provider.calls == 1
    await fb.stop()


async def test_feedback_banned_words_replaced(env):
    config, storage, hub, classroom = env
    fb = FeedbackService(config, storage, classroom, GoodProvider("Está errado, tenta outra vez."))
    session, student_id = await _session_with_student(classroom)
    await fb.request(session["id"], student_id, "u1", {"question": "q", "answer": "x"})
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert "errado" not in record["payload"]["text"].lower()
    await fb.stop()


async def test_feedback_timeout_fallback(env):
    config, storage, hub, classroom = env
    fb = FeedbackService(config, storage, classroom, SlowProvider())
    session, student_id = await _session_with_student(classroom)
    await fb.request(session["id"], student_id, "u1", {"question": "q", "answer": "y"})
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert record["payload"]["text"] == TIMEOUT_MESSAGE
    assert record["payload"]["source"] == "timeout"
    timeout_alert = await _wait_event(storage, session["id"], "feedback_timeout")
    assert timeout_alert["student_id"] == student_id
    await fb.stop()
