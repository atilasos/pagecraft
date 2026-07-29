from pathlib import Path
import subprocess

from scripts.generate_bridge_artifacts import find_drift
from server.classroom.event_types import SESSION_EVENT_TYPES


ROOT = Path(__file__).parent.parent


def test_bridge_artifacts_are_committed_and_distributions_are_synchronized():
    assert find_drift(ROOT) == []

    check = subprocess.run(
        ["bash", "skills/sync-from-canonical.sh", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert check.returncode == 0, check.stdout + check.stderr


def test_published_bridge_names_are_append_only():
    published = {
        "ai_feedback": "ai_feedback",
        "teacher_highlight": "highlight",
    }

    current = {
        event.name: event.bridge_name
        for event in SESSION_EVENT_TYPES.all()
        if event.bridge_name is not None
    }

    assert published.items() <= current.items()
