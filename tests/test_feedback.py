import asyncio

import pytest

from fakes import FakeProvider
from server.classroom.feedback import TIMEOUT_MESSAGE, FeedbackService
from server.classroom.service import ClassroomService
from server.config import Config
from server.events import EventHub
from server.providers import ProviderTimeout
from server.storage import Storage


def good_provider(text="Boa! Percebeste que as metades são iguais."):
    return FakeProvider(default={"feedback": text})


class BlockingProvider:
    name = "fake"

    def __init__(self):
        self.calls = 0
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=20):
        self.calls += 1
        self.started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            self.cancelled.set()
            raise


class PausingProvider:
    name = "fake"

    def __init__(self):
        self.calls = 0
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=20):
        self.calls += 1
        self.started.set()
        await self.release.wait()
        return {"feedback": "Boa! Continua assim."}


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


async def _register_feedback(
    classroom,
    session_id,
    student_id,
    event_id,
    payload,
    unit_id="u1",
):
    return await classroom.ingest_events(
        session_id,
        student_id,
        [
            {
                "event_id": event_id,
                "type": "feedback_request",
                "unit_id": unit_id,
                "payload": payload,
            }
        ],
    )


async def test_feedback_delivered(env):
    config, storage, hub, classroom = env
    provider = good_provider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    fb.start()
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-delivered",
        {"question": "2+2?", "answer": "4", "expected": "4"},
    )
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert record["student_id"] == student_id
    assert "Percebeste" in record["payload"]["text"]
    assert record["payload"]["source"] == "ai"
    await fb.stop()


async def test_feedback_request_from_another_authorized_path_delivers_feedback(env):
    config, storage, hub, classroom = env
    provider = good_provider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    fb.start()

    await classroom.emit_event(
        session["id"],
        "feedback_request",
        {
            "question": "2+2?",
            "answer": "4",
            "expected": "4",
        },
        author="activity",
        student_id=student_id,
    )

    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert record["student_id"] == student_id
    assert record["payload"]["source"] == "ai"
    assert len(provider.calls) == 1
    await fb.stop()


async def test_feedback_persisted_before_start_is_delivered_once_across_restart(env):
    config, storage, _, classroom = env
    provider = good_provider()
    session, student_id = await _session_with_student(classroom)
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-before-start",
        {"question": "2+3?", "answer": "5", "expected": "5"},
    )

    first = FeedbackService(config, storage, classroom, provider)
    first.start()
    await _wait_event(storage, session["id"], "ai_feedback")
    await first.stop()

    restarted_hub = EventHub(storage)
    restarted_classroom = ClassroomService(config, storage, restarted_hub)
    restarted = FeedbackService(
        config,
        storage,
        restarted_classroom,
        provider,
    )
    restarted.start()
    await asyncio.sleep(0.1)

    events = await storage.read_jsonl(
        storage.path("sessions", session["id"], "events.jsonl")
    )
    responses = [event for event in events if event["type"] == "ai_feedback"]
    assert len(responses) == 1
    assert responses[0]["student_id"] == student_id
    assert len(provider.calls) == 1
    await restarted.stop()


async def test_feedback_cache_hit(env):
    config, storage, hub, classroom = env
    provider = good_provider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-cache-1",
        {"question": "q", "answer": "quatro"},
    )
    await _wait_event(storage, session["id"], "ai_feedback")
    # mesma resposta (normalizada) → cache, sem nova chamada
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-cache-2",
        {"question": "q", "answer": "  QUATRO "},
    )
    await asyncio.sleep(0.1)
    events = await storage.read_jsonl(storage.path("sessions", session["id"], "events.jsonl"))
    ai = [e for e in events if e["type"] == "ai_feedback"]
    assert len(ai) == 2
    assert ai[1]["payload"]["source"] == "cache"
    assert len(provider.calls) == 1
    await fb.stop()


async def test_feedback_banned_words_replaced(env):
    config, storage, hub, classroom = env
    fb = FeedbackService(config, storage, classroom, good_provider("Está errado, tenta outra vez."))
    session, student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-banned",
        {"question": "q", "answer": "x"},
    )
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert "errado" not in record["payload"]["text"].lower()
    await fb.stop()


async def test_feedback_timeout_fallback(env):
    config, storage, hub, classroom = env
    fb = FeedbackService(config, storage, classroom, FakeProvider([ProviderTimeout("demorou demasiado")]))
    session, student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-timeout",
        {"question": "q", "answer": "y"},
    )
    record = await _wait_event(storage, session["id"], "ai_feedback")
    assert record["payload"]["text"] == TIMEOUT_MESSAGE
    assert record["payload"]["source"] == "timeout"
    timeout_alert = await _wait_event(storage, session["id"], "feedback_timeout")
    assert timeout_alert["student_id"] == student_id
    await fb.stop()


async def test_feedback_failure_is_registered(env):
    config, storage, hub, classroom = env
    fb = FeedbackService(config, storage, classroom, FakeProvider([RuntimeError("provider indisponível")]))
    session, student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-error",
        {"question": "q", "answer": "y"},
    )

    error = await _wait_event(storage, session["id"], "feedback_error")
    assert error["student_id"] == student_id
    assert error["payload"] == {
        "error": "provider indisponível",
        "unit_id": "u1",
    }
    await fb.stop()


async def test_feedback_excess_is_registered_as_dropped(env):
    config, storage, hub, classroom = env
    provider = BlockingProvider()
    fb = FeedbackService(config, storage, classroom, provider)
    session, student_id = await _session_with_student(classroom)
    fb.start()

    for number in range(4):
        await _register_feedback(
            classroom,
            session["id"],
            student_id,
            f"feedback-excess-{number}",
            {"question": f"pergunta {number}", "answer": "resposta"},
        )

    dropped = await _wait_event(
        storage,
        session["id"],
        "feedback_dropped",
    )
    assert dropped["student_id"] == student_id
    assert dropped["payload"] == {
        "unit_id": "u1",
        "reason": "demasiados pedidos seguidos",
    }
    await fb.stop()


async def test_feedback_stop_cancels_active_provider(env):
    config, storage, hub, classroom = env
    provider = BlockingProvider()
    fb = FeedbackService(config, storage, classroom, provider, workers=1)
    session, student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        session["id"],
        student_id,
        "feedback-blocked",
        {"question": "q", "answer": "a"},
    )
    await asyncio.wait_for(provider.started.wait(), timeout=1)

    await fb.stop()

    await asyncio.wait_for(provider.cancelled.wait(), timeout=1)
    assert provider.calls == 1


async def test_feedback_worker_survives_session_closing_during_response(env):
    config, storage, hub, classroom = env
    provider = PausingProvider()
    fb = FeedbackService(config, storage, classroom, provider, workers=1)
    first_session, first_student_id = await _session_with_student(classroom)
    fb.start()
    await _register_feedback(
        classroom,
        first_session["id"],
        first_student_id,
        "feedback-before-close",
        {"question": "q", "answer": "a"},
    )
    await asyncio.wait_for(provider.started.wait(), timeout=1)
    await classroom.close_session(first_session["id"])
    provider.release.set()

    second_session, second_student_id = await _session_with_student(classroom)
    await _register_feedback(
        classroom,
        second_session["id"],
        second_student_id,
        "feedback-after-close",
        {"question": "outra", "answer": "resposta"},
    )

    feedback = await _wait_event(storage, second_session["id"], "ai_feedback")
    assert feedback["student_id"] == second_student_id
    assert provider.calls == 2
    await fb.stop()
