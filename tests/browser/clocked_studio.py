"""Disposable browser server with an advancing clock away from school midnight.

Expiry boundaries are exercised by the service/API tests with injected clocks.
Browser journeys need stable credentials, including when CI crosses midnight.
"""
from datetime import datetime, timedelta, timezone
import time
from zoneinfo import ZoneInfo

from server.app import create_app


_started = time.monotonic()
_anchor = datetime(2026, 10, 22, 10, tzinfo=timezone.utc)


def classroom_clock():
    # Keep ordering of newly created sessions and claims, rather than freezing
    # every operation at the same timestamp. Cookies also carry relative Max-Age.
    return (_anchor + timedelta(seconds=time.monotonic() - _started)).isoformat()


app = create_app(
    classroom_clock=classroom_clock,
    school_timezone=ZoneInfo('Atlantic/Madeira'),
)
