"""Emparelhamento duradouro do Quadro com confirmação pelo Professor."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .storage import Storage


PAIRING_TTL = timedelta(minutes=5)
BOARD_CREDENTIAL_TTL = timedelta(days=28)
_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


@dataclass
class _Challenge:
    pairing_id: str
    code: str
    expires_at: datetime
    confirmed: bool = False


class BoardPairings:
    """Mantém desafios efémeros e uma única credencial persistida por digest."""

    def __init__(self, storage: Storage, *, clock):
        self._storage = storage
        self._clock = clock
        self._challenges: dict[str, _Challenge] = {}
        self._lock = asyncio.Lock()

    def _now(self) -> datetime:
        value = self._clock()
        instant = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        )
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        return instant.astimezone(timezone.utc)

    @staticmethod
    def _digest(credential: str) -> str:
        return hashlib.sha256(credential.encode("utf-8")).hexdigest()

    def _state_path(self):
        return self._storage.path("board-pairing.json")

    def _discard_expired(self, now: datetime) -> None:
        self._challenges = {
            pairing_id: challenge
            for pairing_id, challenge in self._challenges.items()
            if challenge.expires_at > now
        }

    async def create_challenge(self) -> dict:
        async with self._lock:
            now = self._now()
            self._discard_expired(now)
            pairing_id = secrets.token_urlsafe(24)
            code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
            while any(
                hmac.compare_digest(challenge.code, code)
                for challenge in self._challenges.values()
            ):
                code = "".join(
                    secrets.choice(_CODE_ALPHABET) for _ in range(6)
                )
            challenge = _Challenge(
                pairing_id=pairing_id,
                code=code,
                expires_at=now + PAIRING_TTL,
            )
            self._challenges[pairing_id] = challenge
            return {
                "pairing_id": challenge.pairing_id,
                "code": challenge.code,
                "expires_at": challenge.expires_at.isoformat(),
            }

    async def confirm(self, code: str) -> bool:
        async with self._lock:
            now = self._now()
            self._discard_expired(now)
            for challenge in self._challenges.values():
                if hmac.compare_digest(challenge.code, code.upper()):
                    challenge.confirmed = True
                    return True
            return False

    async def complete(self, pairing_id: str) -> dict | None:
        """Devolve ``None`` enquanto pendente e levanta KeyError se inválido."""

        async with self._lock:
            now = self._now()
            self._discard_expired(now)
            challenge = self._challenges.get(pairing_id)
            if challenge is None:
                raise KeyError(pairing_id)
            if not challenge.confirmed:
                return None

            credential = secrets.token_urlsafe(32)
            expires_at = now + BOARD_CREDENTIAL_TTL
            await self._storage.write_json(
                self._state_path(),
                {
                    "credential_digest": self._digest(credential),
                    "paired_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                },
            )
            del self._challenges[pairing_id]
            return {
                "credential": credential,
                "expires_at": expires_at,
                "issued_at": now,
            }

    async def resolve(self, credential: str) -> bool:
        if not credential:
            return False
        state = await self._storage.read_json(self._state_path(), {})
        digest = str(state.get("credential_digest") or "")
        try:
            expires_at = datetime.fromisoformat(
                str(state["expires_at"]).replace("Z", "+00:00")
            )
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except (KeyError, TypeError, ValueError):
            return False
        return (
            self._now() < expires_at.astimezone(timezone.utc)
            and bool(digest)
            and hmac.compare_digest(digest, self._digest(credential))
        )

    async def state(self) -> dict:
        state = await self._storage.read_json(self._state_path(), {})
        expires_at = state.get("expires_at")
        paired = False
        if state.get("credential_digest") and expires_at:
            try:
                expiry = datetime.fromisoformat(
                    str(expires_at).replace("Z", "+00:00")
                )
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                paired = self._now() < expiry.astimezone(timezone.utc)
            except (TypeError, ValueError):
                pass
        return {
            "paired": paired,
            "expires_at": expires_at if paired else None,
        }

    async def revoke(self) -> None:
        async with self._lock:
            await self._storage.write_json(
                self._state_path(),
                {
                    "credential_digest": None,
                    "paired_at": None,
                    "expires_at": None,
                },
            )
