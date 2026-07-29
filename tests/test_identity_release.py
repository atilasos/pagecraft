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


async def _claimed_student(svc):
    cls = await svc.create_class("3.º A", 3, ["Ana"])
    session = await svc.create_session(cls["id"], "fracoes", "Frações")
    student_id = next(iter(session["roster"]))
    await svc.claim_identity(session["id"], student_id)
    return session, student_id


async def test_release_records_keep_by_default_and_an_explicit_reset(svc):
    session, student_id = await _claimed_student(svc)

    await svc.release_identity(session["id"], student_id)
    await svc.claim_identity(session["id"], student_id)
    await svc.release_identity(
        session["id"],
        student_id,
        reset_progress=True,
    )

    releases = [
        event
        for event in await svc.events_log(session["id"]).replay()
        if event["type"] == "identity_released"
    ]
    assert [event["payload"] for event in releases] == [
        {"reset_progress": False},
        {"reset_progress": True},
    ]
