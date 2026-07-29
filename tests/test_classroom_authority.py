import json

import pytest

from server.classroom.errors import SessionClosedError, StudentNotInRosterError
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
    cls = await svc.create_class("3.º A", 3, ["Ana", "Bruno"])
    return await svc.create_session(cls["id"], "3ano-fracoes", "Frações")


async def test_loading_repairs_a_close_recorded_before_the_state_write(svc, monkeypatch):
    session = await _session(svc)
    original_write = svc.storage.write_json
    failed = False

    async def fail_first_session_write(path, data):
        nonlocal failed
        if path == svc._session_path(session["id"]) and not failed:
            failed = True
            raise OSError("falha injetada depois do append")
        await original_write(path, data)

    monkeypatch.setattr(svc.storage, "write_json", fail_first_session_write)

    with pytest.raises(OSError, match="falha injetada"):
        await svc.close_session(session["id"])

    persisted = await svc.storage.read_json(svc._session_path(session["id"]))
    assert persisted["status"] == "live"

    restarted = ClassroomService(svc.config, svc.storage, EventHub(svc.storage))
    repaired = await restarted.get_session(session["id"])

    assert repaired["status"] == "closed"
    assert repaired["closed_at"]
    assert (
        await restarted.storage.read_json(restarted._session_path(session["id"]))
    )["status"] == "closed"


async def test_module_refuses_commands_after_the_session_is_closed(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    await svc.close_session(session["id"])

    with pytest.raises(SessionClosedError):
        await svc.send_teacher_message(session["id"], "Terminámos")
    with pytest.raises(SessionClosedError):
        await svc.ingest_events(
            session["id"],
            student_id,
            [{"event_id": "late", "type": "attempt", "payload": {}}],
        )


async def test_module_refuses_a_message_to_someone_outside_the_roster(svc):
    session = await _session(svc)

    with pytest.raises(StudentNotInRosterError):
        await svc.send_teacher_message(session["id"], "Olá", student_id="intruso")


async def test_loading_rebuilds_pit_items_from_the_log(svc, monkeypatch):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    original_write = svc.storage.write_json

    async def fail_state_write(path, data):
        if path == svc._session_path(session["id"]):
            raise OSError("estado PIT não persistido")
        await original_write(path, data)

    monkeypatch.setattr(svc.storage, "write_json", fail_state_write)

    with pytest.raises(OSError, match="estado PIT"):
        await svc.upsert_pit_item(
            session["id"], student_id, "Ler as frações", "planned"
        )

    monkeypatch.setattr(svc.storage, "write_json", original_write)
    restarted = ClassroomService(svc.config, svc.storage, EventHub(svc.storage))
    repaired = await restarted.get_session(session["id"])

    assert [
        (item["student_id"], item["text"], item["status"])
        for item in repaired["pit_items"]
    ] == [(student_id, "Ler as frações", "planned")]


async def test_loading_applies_a_recorded_release_to_the_protected_token(svc, monkeypatch):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    claim = await svc.claim_identity(session["id"], student_id)
    original_write = svc.storage.write_json

    async def fail_state_write(path, data):
        if path == svc._session_path(session["id"]):
            raise OSError("token ainda persistido")
        await original_write(path, data)

    monkeypatch.setattr(svc.storage, "write_json", fail_state_write)

    with pytest.raises(OSError, match="token ainda"):
        await svc.release_identity(session["id"], student_id)

    monkeypatch.setattr(svc.storage, "write_json", original_write)
    restarted = ClassroomService(svc.config, svc.storage, EventHub(svc.storage))

    assert (
        await restarted.student_for_token(
            session["id"], claim["student_token"], require_live=False
        )
        is None
    )


async def test_session_projections_are_role_specific_and_never_include_tokens(svc):
    session = await _session(svc)
    student_id = next(iter(session["roster"]))
    claim = await svc.claim_identity(session["id"], student_id)
    session = await svc.get_session(session["id"])

    teacher = svc.project_session(session, role="teacher")
    student = svc.project_session(session, role="student")

    assert teacher["roster"][student_id]["taken"] is True
    assert student["roster"][0] == {
        "student_id": student_id,
        "display_name": "Ana",
        "taken": True,
    }
    assert claim["student_token"] not in json.dumps([teacher, student])
    assert '"token"' not in json.dumps([teacher, student])
