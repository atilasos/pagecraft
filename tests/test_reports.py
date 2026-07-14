import pytest

from server.classroom.reports import build_class_report, report_to_markdown
from server.classroom.service import ClassroomService
from server.config import Config
from server.events import EventHub
from server.storage import Storage


@pytest.fixture
def env(tmp_path):
    config = Config(data_dir=tmp_path)
    storage = Storage(config.data_dir)
    svc = ClassroomService(config, storage, EventHub(storage))
    return storage, svc


async def _session_with_activity(svc, cls, title):
    session = await svc.create_session(cls["id"], "slug", title)
    return session


async def test_report_aggregates_per_student_and_session(env):
    storage, svc = env
    cls = await svc.create_class("3.º A", 3, ["Ana", "Bruno"])
    session = await _session_with_activity(svc, cls, "Frações")
    ana_id = next(
        sid for sid, e in session["roster"].items() if e["display_name"] == "Ana"
    )
    await svc.claim_identity(session["id"], ana_id)
    await svc.ingest_events(
        session["id"],
        ana_id,
        [
            {"event_id": "e1", "type": "attempt", "payload": {"correct": True}},
            {"event_id": "e2", "type": "attempt", "payload": {"correct": False}},
            {"event_id": "e3", "type": "discovery", "payload": {"message": "!"}},
            {"event_id": "e4", "type": "help_needed", "payload": {}},
        ],
    )
    await svc.upsert_pit_item(session["id"], ana_id, "Ler texto", "done")
    await svc.upsert_pit_item(session["id"], ana_id, "Escrever frase", "planned")
    await svc.close_session(session["id"])

    report = await build_class_report(storage, cls, await svc.list_sessions())
    ana = next(s for s in report["students"] if s["display_name"] == "Ana")
    bruno = next(s for s in report["students"] if s["display_name"] == "Bruno")
    assert ana["sessions"] == 1
    assert ana["attempt"] == 2
    assert ana["correct"] == 1
    assert ana["discovery"] == 1
    assert ana["help_needed"] == 1
    assert ana["pit_done"] == 1 and ana["pit_total"] == 2
    assert bruno["sessions"] == 0
    assert len(report["sessions"]) == 1
    assert report["sessions"][0]["participants"] == 1


async def test_report_date_filter_excludes_sessions(env):
    storage, svc = env
    cls = await svc.create_class("1.º C", 1, ["Zé"])
    await _session_with_activity(svc, cls, "Sílabas")
    report = await build_class_report(
        storage, cls, await svc.list_sessions(), date_from="2099-01"
    )
    assert report["sessions"] == []
    assert report["students"][0]["sessions"] == 0


async def test_report_markdown_renders(env):
    storage, svc = env
    cls = await svc.create_class("2.º B", 2, ["Rita"])
    await _session_with_activity(svc, cls, "Dobros")
    report = await build_class_report(storage, cls, await svc.list_sessions())
    md = report_to_markdown(report)
    assert "Registo de trabalho — 2.º B" in md
    assert "| Rita |" in md
    assert "Dobros" in md
