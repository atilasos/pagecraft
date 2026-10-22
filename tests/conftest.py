import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent


@pytest.fixture
def install_publication_module():
    def install(repo: Path) -> None:
        server = repo / "server"
        server.mkdir(parents=True)
        for name in ("__init__.py", "publish.py", "bridge_snippet.py"):
            shutil.copy2(ROOT / "server" / name, server / name)

    return install


@pytest.fixture
def board_frame_received(monkeypatch):
    """Observe frames after the real SSE response consumer receives them."""
    import asyncio
    from server.api import board

    frames = asyncio.Queue()
    stream_session = board.stream_session

    async def observed_stream(session_id, request):
        response = await stream_session(session_id, request)
        source = response.body_iterator

        async def body():
            try:
                async for frame in source:
                    yield frame
                    frames.put_nowait(frame)
            finally:
                await source.aclose()

        response.body_iterator = body()
        return response

    monkeypatch.setattr(board, 'stream_session', observed_stream)

    async def received(event_name):
        async with asyncio.timeout(1):
            while True:
                frame = await frames.get()
                if f"event: {event_name}\n" in frame:
                    return frame

    return received
