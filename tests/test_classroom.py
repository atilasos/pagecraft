import asyncio

import pytest

from server.classroom.service import ClassroomService
from server.config import Config
from server.events import EventHub
from server.storage import Storage


@pytest.fixture
def svc(tmp_path):
    config = Config(data_dir=tmp_path)
    storage = Storage(config.data_dir)
    return ClassroomService(config, storage, EventHub(storage))


async def _session(svc):
    cls = await svc.create_class("3.º A", 3, ["Ana", "Bruno", "Carla"])
    return await svc.create_session(cls["id"], "3ano-fracoes", "Frações")


async def test_create_class_and_session(svc):
    session = await _session(svc)
    assert session["status"] == "live"
    assert len(session["join_code"]) == 6
    assert len(session["roster"]) == 3
    found = await svc.find_by_code(session["join_code"].lower())
    assert found and found["id"] == session["id"]


async def test_claim_identity_once(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    claim = await svc.claim_identity(session["id"], student_id)
    assert claim and claim["student_token"]
    # segunda tentativa com a mesma identidade falha
    assert await svc.claim_identity(session["id"], student_id) is None
    # release liberta
    assert await svc.release_identity(session["id"], student_id)
    assert await svc.claim_identity(session["id"], student_id)


async def test_token_lookup(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    claim = await svc.claim_identity(session["id"], student_id)
    assert await svc.student_for_token(session["id"], claim["student_token"]) == student_id
    assert await svc.student_for_token(session["id"], "tokeninventado") is None


async def test_ingest_dedup_and_type_filter(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    await svc.claim_identity(session["id"], student_id)
    events = [
        {"event_id": "e1", "type": "attempt", "unit_id": "u1", "payload": {"correct": True}},
        {"event_id": "e1", "type": "attempt", "unit_id": "u1", "payload": {"correct": True}},  # duplicado
        {"event_id": "e2", "type": "tipo_desconhecido", "payload": {}},  # rejeitado
        {"event_id": "e3", "type": "discovery", "unit_id": "u1", "payload": {"message": "!"}},
    ]
    accepted = await svc.ingest_events(session["id"], student_id, events)
    assert [r["event_id"] for r in accepted] == ["e1", "e3"]
    # replay não readmite duplicados (novo serviço, mesmo storage)
    svc2 = ClassroomService(svc.config, svc.storage, EventHub(svc.storage))
    again = await svc2.ingest_events(session["id"], student_id, events)
    assert again == []


async def test_events_have_monotonic_seq_with_join(svc):
    session = await _session(svc)
    ids = list(session["roster"])
    await svc.claim_identity(session["id"], ids[0])  # emite "joined" (seq 1)
    accepted = await svc.ingest_events(
        session["id"], ids[0], [{"event_id": "x", "type": "heartbeat", "payload": {}}]
    )
    assert accepted[0]["seq"] == 2


async def test_pit_upsert(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    item = await svc.upsert_pit_item(session["id"], student_id, "Ler o texto das frações", "planned")
    assert item["status"] == "planned"
    updated = await svc.upsert_pit_item(session["id"], student_id, item["text"], "done", item["id"])
    assert updated["id"] == item["id"]
    assert updated["status"] == "done"
    fresh = await svc.get_session(session["id"])
    assert len(fresh["pit_items"]) == 1


async def test_concurrent_claims_only_one_wins(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    results = await asyncio.gather(
        *(svc.claim_identity(session["id"], student_id) for _ in range(8))
    )
    wins = [r for r in results if r]
    assert len(wins) == 1
    # o token que ficou persistido é o do vencedor
    assert await svc.student_for_token(session["id"], wins[0]["student_token"]) == student_id


async def test_token_invalid_after_close_for_mutations(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    claim = await svc.claim_identity(session["id"], student_id)
    await svc.close_session(session["id"])
    assert await svc.student_for_token(session["id"], claim["student_token"]) is None
    assert (
        await svc.student_for_token(session["id"], claim["student_token"], require_live=False)
        == student_id
    )


async def test_close_session(svc):
    session = await _session(svc)
    closed = await svc.close_session(session["id"])
    assert closed["status"] == "closed"
    assert await svc.find_by_code(session["join_code"]) is None
