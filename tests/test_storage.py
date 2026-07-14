import asyncio
import json

import pytest

from server.storage import Storage


@pytest.fixture
def storage(tmp_path):
    return Storage(tmp_path)


async def test_write_and_read_json_roundtrip(storage, tmp_path):
    path = tmp_path / "nested" / "doc.json"
    data = {"nome": "Turma do 3.º A", "alunos": ["Ana", "João"], "n": 3}
    await storage.write_json(path, data)
    assert await storage.read_json(path) == data


async def test_read_json_missing_returns_default(storage, tmp_path):
    assert await storage.read_json(tmp_path / "nope.json", default={}) == {}


async def test_write_json_is_atomic_no_tmp_left(storage, tmp_path):
    path = tmp_path / "doc.json"
    await storage.write_json(path, {"a": 1})
    await storage.write_json(path, {"a": 2})
    leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []
    assert (await storage.read_json(path))["a"] == 2


async def test_append_and_replay_jsonl(storage, tmp_path):
    path = tmp_path / "events.jsonl"
    for i in range(5):
        await storage.append_jsonl(path, {"seq": i, "type": "attempt"})
    records = await storage.read_jsonl(path)
    assert [r["seq"] for r in records] == [0, 1, 2, 3, 4]


async def test_read_jsonl_ignores_truncated_last_line(storage, tmp_path):
    path = tmp_path / "events.jsonl"
    await storage.append_jsonl(path, {"seq": 0})
    with open(path, "a", encoding="utf-8") as fh:
        fh.write('{"seq": 1, "type": "att')  # crash a meio da escrita
    records = await storage.read_jsonl(path)
    assert records == [{"seq": 0}]


async def test_concurrent_appends_do_not_interleave(storage, tmp_path):
    path = tmp_path / "events.jsonl"

    async def writer(n):
        for i in range(20):
            await storage.append_jsonl(path, {"w": n, "i": i, "pad": "x" * 200})

    await asyncio.gather(*(writer(n) for n in range(5)))
    records = await storage.read_jsonl(path)
    assert len(records) == 100
    for r in records:
        assert set(r) == {"w", "i", "pad"}
