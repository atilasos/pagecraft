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
