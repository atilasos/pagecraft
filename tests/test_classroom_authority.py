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
