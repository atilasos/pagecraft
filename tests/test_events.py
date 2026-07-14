import asyncio

from server.events import EventHub, EventLog
from server.storage import Storage


async def test_append_assigns_monotonic_seq(tmp_path):
    log = EventLog(Storage(tmp_path), tmp_path / "events.jsonl")
    r1 = await log.append({"type": "a"})
    r2 = await log.append({"type": "b"})
    assert (r1["seq"], r2["seq"]) == (1, 2)
    assert r1["ts"]


async def test_seq_continues_after_restart(tmp_path):
    storage = Storage(tmp_path)
    log = EventLog(storage, tmp_path / "events.jsonl")
    await log.append({"type": "a"})
    await log.append({"type": "b"})
    # novo processo: recarrega do ficheiro
    log2 = EventLog(storage, tmp_path / "events.jsonl")
    r3 = await log2.append({"type": "c"})
    assert r3["seq"] == 3


async def test_replay_after_seq(tmp_path):
    log = EventLog(Storage(tmp_path), tmp_path / "events.jsonl")
    for t in ("a", "b", "c"):
        await log.append({"type": t})
    records = await log.replay(after_seq=1)
    assert [r["type"] for r in records] == ["b", "c"]


async def test_subscribe_replays_then_streams_live(tmp_path):
    log = EventLog(Storage(tmp_path), tmp_path / "events.jsonl")
    await log.append({"type": "old"})

    received: list[str] = []

    async def consumer():
        async for record in log.subscribe(after_seq=0):
            received.append(record["type"])
            if record["type"] == "stop":
                break

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.05)
    await log.append({"type": "live"})
    await log.append({"type": "stop"})
    await asyncio.wait_for(task, timeout=2)
    assert received == ["old", "live", "stop"]


async def test_hub_returns_same_log_per_channel(tmp_path):
    hub = EventHub(Storage(tmp_path))
    assert hub.log_for("jobs", "x", "events.jsonl") is hub.log_for("jobs", "x", "events.jsonl")
