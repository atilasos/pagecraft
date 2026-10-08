"""Turmas, sessões de aula, identidades de alunos e eventos de progresso.

Sem dados sensíveis: alunos são apenas nome próprio/pseudónimo escolhido
pelo professor. A "autenticação" do aluno é um token opaco por sessão,
criado quando o aluno reclama a sua identidade no arranque da aula.
"""

from __future__ import annotations

import asyncio
import hmac
import os
import secrets
import uuid
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..config import Config
from ..events import EventHub, utcnow
from ..storage import Storage
from .errors import (
    ClassroomError,
    CompositionChangedError,
    InvalidPitItemError,
    InvalidSessionEventError,
    SessionClosedError,
    SessionNotFoundError,
    StudentNotInRosterError,
)
from .event_types import SESSION_EVENT_TYPES
from .live_state import LiveSessionTicks
from .lifecycle import session_lifecycle


_SESSION_MAX_AGE = timedelta(hours=8)


def _system_local_timezone() -> tzinfo:
    """Obtém o fuso local com regras DST, sem dependências externas."""

    candidates = [os.environ.get("TZ", "")]
    timezone_file = Path("/etc/timezone")
    try:
        candidates.append(timezone_file.read_text("utf-8").strip())
    except OSError:
        pass

    localtime_file = Path("/etc/localtime")
    try:
        resolved = localtime_file.resolve()
        if "zoneinfo" in resolved.parts:
            index = resolved.parts.index("zoneinfo")
            candidates.append("/".join(resolved.parts[index + 1 :]))
    except OSError:
        pass

    for name in candidates:
        if not name or name.startswith(("/", ":")):
            continue
        try:
            return ZoneInfo(name)
        except (ValueError, ZoneInfoNotFoundError):
            continue

    try:
        with localtime_file.open("rb") as localtime:
            return ZoneInfo.from_file(localtime)
    except (OSError, ValueError):
        return datetime.now().astimezone().tzinfo or timezone.utc


def _join_code(length: int = 6) -> str:
    # sem 0/O/1/I para ditar em voz alta sem ambiguidade
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class ClassroomService:
    def __init__(
        self,
        config: Config,
        storage: Storage,
        hub: EventHub,
        *,
        clock=utcnow,
        school_timezone: tzinfo | None = None,
        tick_interval_seconds: float = 30,
    ):
        self.config = config
        self.storage = storage
        self.hub = hub
        self._seen_event_ids: dict[str, set[str]] = {}
        # lock por sessão: torna atómicas as transações read-modify-write
        # (claim/release/PIT/close); um só processo, chega um asyncio.Lock
        self._session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._clock = clock
        self._school_timezone = school_timezone or _system_local_timezone()
        self.live_ticks = LiveSessionTicks(
            lambda: self._clock(),
            interval_seconds=tick_interval_seconds,
        )

    def now(self):
        return self._clock()

    def _now_as_datetime(self) -> datetime:
        value = self.now()
        if isinstance(value, datetime):
            instant = value
        else:
            instant = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        return instant

    def _student_credential_expires_at(self) -> str:
        """Meia-noite seguinte no fuso escolar, persistida como instante UTC."""

        local_now = self._now_as_datetime().astimezone(self._school_timezone)
        next_day = local_now.date() + timedelta(days=1)
        local_midnight = datetime.combine(
            next_day,
            time.min,
            tzinfo=self._school_timezone,
        )
        return local_midnight.astimezone(timezone.utc).isoformat()

    def tick_session(self, session_id: str, *, now=None) -> None:
        """Publica um tique controlado; útil também para testes do protocolo."""
        self.live_ticks.publish(session_id, now=now)

    def live_session_ids(self) -> tuple[str, ...]:
        """Sessões com streams vivos, cada uma servida por um só tique."""
        return self.live_ticks.session_ids()

    async def stop(self) -> None:
        await self.live_ticks.stop()

    # ---- turmas ----

    def _class_path(self, class_id: str):
        return self.storage.path("classes", f"{class_id}.json")

    async def create_class(self, name: str, year: int, students: list[str]) -> dict:
        cls = {
            "id": uuid.uuid4().hex[:10],
            "name": name,
            "year": year,
            "students": [
                {"id": uuid.uuid4().hex[:8], "display_name": s.strip()}
                for s in students
                if s.strip()
            ],
            "created_at": utcnow(),
        }
        await self.storage.write_json(self._class_path(cls["id"]), cls)
        return cls

    async def get_class(self, class_id: str) -> dict | None:
        return await self.storage.read_json(self._class_path(class_id))

    async def list_classes(self) -> list[dict]:
        classes_dir = self.storage.root / "classes"
        if not classes_dir.is_dir():
            return []
        out = []
        for path in sorted(classes_dir.glob("*.json")):
            data = await self.storage.read_json(path)
            if data:
                out.append(data)
        return out

    async def update_class_students(self, class_id: str, students: list[str]) -> dict | None:
        cls = await self.get_class(class_id)
        if not cls:
            return None
        existing = {s["display_name"]: s for s in cls["students"]}
        cls["students"] = [
            existing.get(name.strip()) or {"id": uuid.uuid4().hex[:8], "display_name": name.strip()}
            for name in students
            if name.strip()
        ]
        await self.storage.write_json(self._class_path(class_id), cls)
        return cls

    # ---- sessões ----

    def _session_path(self, session_id: str):
        return self.storage.path("sessions", session_id, "session.json")

    def events_log(self, session_id: str):
        return self.hub.log_for("sessions", session_id, "events.jsonl")

    async def _load_session_unlocked(self, session_id: str) -> dict | None:
        session = await self.storage.read_json(self._session_path(session_id))
        if not session:
            return None
        events = await self.events_log(session_id).replay()
        changed = False

        lifecycle = session_lifecycle(events, session)
        for key in ("status", "closed_at", "active_since"):
            if key == "active_since" and key not in session and not any(event.get("type") == "session_resumed" for event in events):
                continue
            if session.get(key) != lifecycle[key]:
                session[key] = lifecycle[key]
                changed = True

        pit_items: dict[str, dict] = {}
        last_identity_event: dict[str, str] = {}
        for event in events:
            event_type = event.get("type")
            student_id = event.get("student_id")
            if student_id and event_type in ("joined", "identity_released"):
                last_identity_event[str(student_id)] = str(event_type)
            if event_type != "pit_updated":
                continue
            item = dict(event.get("payload") or {})
            item_id = item.get("id")
            if not item_id:
                continue
            item.pop("previous_status", None)
            item["student_id"] = str(student_id or item.get("student_id") or "")
            pit_items[str(item_id)] = item
        expected_pit_items = list(pit_items.values())
        if session.get("pit_items") != expected_pit_items:
            session["pit_items"] = expected_pit_items
            changed = True

        for group in session.get("work_groups", {}).values():
            group.setdefault("device_id", group["id"])
            group.setdefault("composition_version", 1)
            group.setdefault("access_version", 1)
        for event in events:
            if event.get("type") != "work_group_changed":
                continue
            public = event["payload"]
            old = session["work_groups"][public["previous_work_group_id"]]
            if public["id"] not in session["work_groups"]:
                new = {**old, **{key:value for key,value in public.items() if key != "previous_work_group_id"}}
                session["work_groups"][new["id"]] = new
                old["token"] = None
                for sid in old["participant_ids"]:
                    if session["roster"][sid].get("work_group_id") == old["id"]:
                        session["roster"][sid].pop("work_group_id", None)
                for sid in new["participant_ids"]:
                    session["roster"][sid]["work_group_id"] = new["id"]
                changed = True

        for event in events:
            group = session.get("work_groups", {}).get(event.get("work_group_id"))
            if not group:
                continue
            if event.get("type") == "work_group_released" and group.get("token"):
                group["token"] = None
                for sid in group["participant_ids"]:
                    session["roster"][sid].pop("work_group_id", None)
                changed = True
            if event.get("type") == "level_changed":
                level = (event.get("payload") or {}).get("level")
                if level in {"support", "intermediate", "challenge"} and group["level"] != level:
                    group["level"] = level
                    changed = True

        for student_id, last_event in last_identity_event.items():
            if last_event != "identity_released":
                continue
            entry = session.get("roster", {}).get(student_id)
            if entry and (entry.get("token") is not None or entry.get("claimed_at") is not None or entry.get("resume_reserved")):
                entry["token"] = None
                entry["claimed_at"] = None
                entry["credential_expires_at"] = None
                entry["resume_reserved"] = False
                changed = True

        if session["status"] == "live" and self._session_has_expired(session):
            await self._close_session_unlocked(session_id, session)
            return session

        if changed:
            await self.storage.write_json(self._session_path(session_id), session)
        return session

    def _session_has_expired(self, session: dict) -> bool:
        try:
            started_at = datetime.fromisoformat(
                str(session.get("active_since", session["started_at"])).replace("Z", "+00:00")
            )
            now = datetime.fromisoformat(str(self.now()).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            return False
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if "active_since" in session and now.astimezone(self._school_timezone).date() != started_at.astimezone(self._school_timezone).date():
            return True
        return now.astimezone(timezone.utc) - started_at.astimezone(timezone.utc) >= (
            _SESSION_MAX_AGE
        )

    async def _require_writable_unlocked(
        self, session_id: str, student_id: str | None = None
    ) -> dict:
        session = await self._load_session_unlocked(session_id)
        if not session:
            raise SessionNotFoundError("sessão não encontrada")
        if session.get("status") != "live":
            raise SessionClosedError("a sessão já não está ativa")
        if student_id is not None and student_id not in session.get("roster", {}):
            raise StudentNotInRosterError("esse aluno não pertence à sessão")
        return session

    async def create_session(self, class_id: str, activity_slug: str, activity_title: str) -> dict | None:
        cls = await self.get_class(class_id)
        if not cls:
            return None
        session = {
            "id": uuid.uuid4().hex[:10],
            "class_id": class_id,
            "class_name": cls["name"],
            "activity_slug": activity_slug,
            "activity_title": activity_title,
            "status": "live",
            "join_code": _join_code(),
            "started_at": self.now(),
            "closed_at": None,
            "roster": {
                s["id"]: {
                    "display_name": s["display_name"],
                    "token": None,
                    "claimed_at": None,
                    "credential_expires_at": None,
                }
                for s in cls["students"]
            },
            "pit_items": [],
        }
        await self.storage.write_json(self._session_path(session["id"]), session)
        return session

    async def get_session(self, session_id: str) -> dict | None:
        async with self._session_locks[session_id]:
            return await self._load_session_unlocked(session_id)

    def project_session(self, session: dict, *, role: str) -> dict:
        """Produz a forma transportável da sessão sem expor tokens."""
        if role == "board":
            projection = {
                key: session[key]
                for key in (
                    "id",
                    "class_name",
                    "activity_slug",
                    "activity_title",
                    "join_code",
                    "status",
                    "started_at",
                )
            }
            if "group_codes_visible" in session:
                projection.update(group_codes=self.group_codes(session),
                                  group_codes_visible=session["group_codes_visible"])
            return projection
        if role == "student":
            return {
                "id": session["id"],
                "class_name": session["class_name"],
                "activity_slug": session["activity_slug"],
                "activity_title": session["activity_title"],
                "status": session["status"],
                "roster": [
                    {
                        "student_id": student_id,
                        "display_name": entry["display_name"],
                        "taken": self._identity_taken(entry),
                    }
                    for student_id, entry in session["roster"].items()
                ],
            }
        if role == "teacher":
            projection = {key: value for key, value in session.items() if key not in {"roster", "work_groups"}}
            projection["group_codes"] = self.group_codes(session)
            projection["roster"] = {
                student_id: {
                    key: value for key, value in entry.items() if key != "token"
                }
                | {"taken": self._identity_taken(entry)}
                for student_id, entry in session["roster"].items()
            }
            if session.get("work_groups"):
                projection["work_groups"] = {
                    group_id: self.project_work_group(group)
                    for group_id, group in session["work_groups"].items()
                }
            return projection
        raise ValueError(f"papel desconhecido: {role}")

    async def find_by_code(self, join_code: str) -> dict | None:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return None
        for path in sessions_dir.glob("*/session.json"):
            data = await self.get_session(path.parent.name)
            if data and data.get("join_code") == join_code.upper() and data.get("status") == "live":
                return data
        return None

    async def list_sessions(self) -> list[dict]:
        sessions_dir = self.storage.root / "sessions"
        if not sessions_dir.is_dir():
            return []
        out = []
        for path in sorted(sessions_dir.glob("*/session.json")):
            data = await self.get_session(path.parent.name)
            if data:
                out.append(data)
        out.sort(key=lambda s: s.get("active_since", s.get("started_at", "")), reverse=True)
        return out

    async def current_board_session(self) -> dict | None:
        """Projeta a Sessão de aula viva mais recente para o Quadro."""

        session = next(
            (
                candidate
                for candidate in await self.list_sessions()
                if candidate.get("status") == "live"
            ),
            None,
        )
        return (
            self.project_session(session, role="board")
            if session is not None
            else None
        )

    async def close_session(self, session_id: str) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            await self._close_session_unlocked(session_id, session)
        return session

    async def _close_session_unlocked(self, session_id: str, session: dict) -> None:
        record = await self._append_event_unlocked(
            session_id,
            "session_closed",
            {},
            author="session",
            ts=self.now(),
        )
        session["status"] = "closed"
        session["closed_at"] = record["ts"]
        await self.storage.write_json(self._session_path(session_id), session)

    @staticmethod
    def _current_groups(session: dict) -> list[dict]:
        current = {entry.get("work_group_id") for entry in session["roster"].values()}
        return [group for gid, group in session.get("work_groups", {}).items() if gid in current]

    @classmethod
    def group_codes(cls, session: dict) -> list[dict]:
        return [{"id": group["id"], "display_name": group["display_name"],
                 "code": group.get("access_code") if session["status"] == "live" else None}
                for group in cls._current_groups(session)]

    async def _publish_group_codes_unlocked(self, session: dict) -> None:
        await self._append_event_unlocked(
            session["id"], "group_codes_updated",
            {"groups": self.group_codes(session), "visible": session.get("group_codes_visible", False)},
            author="session", ts=self.now(),
        )

    async def resume_session(self, session_id: str) -> dict:
        async with self._session_locks[session_id]:
            session = await self._load_session_unlocked(session_id)
            if not session:
                raise SessionNotFoundError("sessão não encontrada")
            if session["status"] == "live":
                return session
            session.update(status="live", closed_at=None, active_since=self.now(), join_code=_join_code())
            for entry in session["roster"].values():
                # A public name claim must not inherit an earlier child's private work.
                entry["resume_reserved"] = bool(entry.get("token") or entry.get("resume_reserved"))
                entry.update(token=None, claimed_at=None, credential_expires_at=None)
            for group in session.get("work_groups", {}).values():
                group.update(token=None, access_code=None, access_version=group["access_version"] + 1)
            for group in self._current_groups(session):
                group["access_code"] = _join_code(8)
            session["group_codes_visible"] = bool(self._current_groups(session))
            await self.storage.write_json(self._session_path(session_id), session)
            await self._append_event_unlocked(session_id, "session_resumed", {}, author="session", ts=self.now())
            await self._publish_group_codes_unlocked(session)
            return session

    async def renew_group_code(self, session_id: str, group_id: str) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            group = next((group for group in self._current_groups(session) if group["id"] == group_id), None)
            if not group:
                raise StudentNotInRosterError("grupo não encontrado")
            group.update(token=None, access_code=_join_code(8), access_version=group["access_version"] + 1)
            await self.storage.write_json(self._session_path(session_id), session)
            await self._publish_group_codes_unlocked(session)
            return next(row for row in self.group_codes(session) if row["id"] == group_id)

    async def show_group_codes(self, session_id: str, visible: bool) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            session["group_codes_visible"] = visible
            await self.storage.write_json(self._session_path(session_id), session)
            await self._publish_group_codes_unlocked(session)
            return session

    async def enter_group(self, code: str) -> tuple[dict, dict] | None:
        for candidate in await self.list_sessions():
            session_id = candidate["id"]
            async with self._session_locks[session_id]:
                session = await self._load_session_unlocked(session_id)
                if not session or session["status"] != "live":
                    continue
                for group in self._current_groups(session):
                    if not group.get("access_code") or not hmac.compare_digest(group["access_code"], code):
                        continue
                    group.update(access_code=None, token=uuid.uuid4().hex, claimed_at=self.now(),
                                 credential_expires_at=self._student_credential_expires_at())
                    await self.storage.write_json(self._session_path(session_id), session)
                    await self._publish_group_codes_unlocked(session)
                    return session, group
        return None

    # ---- identidade do aluno ----

    @staticmethod
    def _identity_taken(entry: dict) -> bool:
        return bool(entry.get("token") or entry.get("work_group_id") or entry.get("resume_reserved"))

    @staticmethod
    def project_work_group(group: dict) -> dict:
        return {key: group[key] for key in ("id", "device_id", "composition_version", "access_version", "participant_ids", "members", "display_name", "mode", "level")}

    async def claim_work_group(self, session_id: str, participant_ids: list[str], mode: str, level: str) -> dict | None:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            if len(set(participant_ids)) != len(participant_ids) or not (
                mode == "pair" and len(participant_ids) == 2
                or mode == "group" and len(participant_ids) >= 3
            ):
                raise InvalidSessionEventError("Seleciona dois participantes para um par ou três ou mais para um grupo.")
            if any(sid not in session["roster"] for sid in participant_ids):
                raise StudentNotInRosterError("esse aluno não pertence à sessão")
            if any(self._identity_taken(session["roster"][sid]) for sid in participant_ids):
                return None
            group_id = uuid.uuid4().hex[:12]
            members = [{"student_id": sid, "display_name": session["roster"][sid]["display_name"]} for sid in participant_ids]
            group = {
                "id": group_id, "device_id": group_id, "composition_version": 1, "access_version": 1, "participant_ids": participant_ids, "members": members,
                "display_name": " + ".join(member["display_name"] for member in members),
                "mode": mode, "level": level, "token": uuid.uuid4().hex,
                "claimed_at": self.now(), "credential_expires_at": self._student_credential_expires_at(),
            }
            session.setdefault("work_groups", {})[group_id] = group
            for sid in participant_ids:
                session["roster"][sid]["work_group_id"] = group_id
            await self.events_log(session_id).append({
                "type": "work_group_joined", "work_group_id": group_id,
                "participant_ids": participant_ids, "payload": self.project_work_group(group),
            })
            await self.storage.write_json(self._session_path(session_id), session)
            return group

    async def change_work_group(self, session_id: str, group_id: str, participant_ids: list[str], mode: str) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            old = session.get("work_groups", {}).get(group_id)
            if not old or old not in self._current_groups(session):
                raise ClassroomError("Este grupo já foi alterado ou libertado. Atualiza a lista de grupos.")
            if len(set(participant_ids)) != len(participant_ids) or not (
                mode == "pair" and len(participant_ids) == 2
                or mode == "group" and len(participant_ids) >= 3
            ):
                raise InvalidSessionEventError("Seleciona dois participantes para um par ou três ou mais para um grupo.")
            if any(sid not in session["roster"] for sid in participant_ids):
                raise StudentNotInRosterError("Essa criança não pertence à sessão.")
            for sid in participant_ids:
                entry = session["roster"][sid]
                if entry.get("token") or entry.get("resume_reserved") or entry.get("work_group_id") not in (None, group_id):
                    raise ClassroomError("Um dos nomes está noutro dispositivo. Revê os participantes.")
            if participant_ids == old["participant_ids"] and mode == old["mode"]:
                return old
            new_id = uuid.uuid4().hex[:12]
            members = [{"student_id": sid, "display_name": session["roster"][sid]["display_name"]} for sid in participant_ids]
            new = {**old, "id": new_id, "participant_ids": participant_ids, "members": members,
                   "mode": mode, "display_name": " + ".join(member["display_name"] for member in members),
                   "composition_version": old["composition_version"] + 1}
            # One canonical change, recoverable using the existing private device credential.
            await self.events_log(session_id).append({
                "type": "work_group_changed", "work_group_id": new_id,
                "participant_ids": participant_ids,
                "payload": {**self.project_work_group(new), "previous_work_group_id": group_id},
            })
            session["work_groups"][new_id] = new
            old["token"] = None
            for sid in old["participant_ids"]:
                session["roster"][sid].pop("work_group_id", None)
            for sid in participant_ids:
                session["roster"][sid]["work_group_id"] = new_id
            await self.storage.write_json(self._session_path(session_id), session)
            if "group_codes_visible" in session:
                await self._publish_group_codes_unlocked(session)
            return new

    async def save_group_reflection(self, session_id: str, group_id: str, data: dict, criteria: list[dict]) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            group = session.get("work_groups", {}).get(group_id)
            if not group or not group.get("token") or data["student_id"] not in group["participant_ids"]:
                raise StudentNotInRosterError("Essa criança não pertence ao grupo deste computador.")
            records = await self.events_log(session_id).replay()
            voice = {key: data[key] for key in ("answers", "strategy", "next_step", "skipped")}
            voice["source_work_group_id"] = group_id
            voice["revision"] = data["expected_revision"] + 1
            previous = 0
            for record in records:
                if record.get("event_id") == data["event_id"]:
                    if (record.get("type") == "individual_reflection"
                        and record.get("student_id") == data["student_id"]
                        and all(record["payload"].get(key) == value for key, value in voice.items())):
                        return record
                    raise ClassroomError("Este envio já foi usado para outra resposta.")
                if (record.get("type") == "individual_reflection"
                    and record.get("student_id") == data["student_id"]
                    and session["work_groups"].get(record["payload"]["source_work_group_id"], {}).get("device_id") == group["device_id"]):
                    previous = record["payload"]["revision"]
            if ((data.get("composition_version") or 1) != group["composition_version"]
                or (data.get("access_version") or 1) != group["access_version"]):
                raise CompositionChangedError([data["event_id"]], self.project_work_group(group))
            if previous != data["expected_revision"]:
                raise ClassroomError("Há uma reflexão mais recente. Volta a abri-la antes de guardar.")
            if set(data["answers"]) - {c["id"] for c in criteria}:
                raise InvalidSessionEventError("Responde apenas aos critérios desta atividade.")
            if data["skipped"] and (data["answers"] or data["strategy"] or data["next_step"]):
                raise InvalidSessionEventError("Uma reflexão omitida não inclui respostas.")
            voice["criteria"] = criteria
            record = await self.events_log(session_id).append({
                "event_id": data["event_id"], "type": "individual_reflection",
                "student_id": data["student_id"], "payload": voice,
            })
            (await self._seen(session_id)).add(data["event_id"])
            return record

    async def work_group_for_token(self, session_id: str, token: str, *, require_live: bool = True) -> str | None:
        if not token:
            return None
        async with self._session_locks[session_id]:
            session = await self._load_session_unlocked(session_id)
            if not session or require_live and session.get("status") != "live":
                return None
            for group_id, group in session.get("work_groups", {}).items():
                if not group.get("token") or self._now_as_datetime() >= datetime.fromisoformat(group["credential_expires_at"]):
                    continue
                if hmac.compare_digest(group["token"], token):
                    return group_id
        return None

    async def claim_identity(self, session_id: str, student_id: str) -> dict | None:
        """Aluno escolhe quem é. Devolve token; None se já reclamado/inválido."""
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            entry = session["roster"][student_id]
            if self._identity_taken(entry):
                return None
            token = uuid.uuid4().hex
            claimed_at = self.now()
            expires_at = self._student_credential_expires_at()
            await self._append_event_unlocked(
                session_id,
                "joined",
                {"display_name": entry["display_name"]},
                author="session",
                student_id=student_id,
            )
            entry["token"] = token
            entry["claimed_at"] = claimed_at
            entry["credential_expires_at"] = expires_at
            await self.storage.write_json(self._session_path(session_id), session)
        return {
            "student_credential": token,
            "student_id": student_id,
            "display_name": entry["display_name"],
            "claimed_at": claimed_at,
            "credential_expires_at": expires_at,
        }

    async def release_identity(
        self,
        session_id: str,
        student_id: str,
        *,
        reset_progress: bool = False,
    ) -> bool:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            entry = session["roster"][student_id]
            if entry.get("work_group_id"):
                group = session["work_groups"][entry["work_group_id"]]
                await self.events_log(session_id).append({
                    "type": "work_group_released", "work_group_id": group["id"],
                    "participant_ids": list(group["participant_ids"]), "payload": {"reset_progress": reset_progress},
                })
                group["token"] = None
                for sid in group["participant_ids"]:
                    session["roster"][sid].pop("work_group_id", None)
                await self.storage.write_json(self._session_path(session_id), session)
                if "group_codes_visible" in session:
                    await self._publish_group_codes_unlocked(session)
                return True
            await self._append_event_unlocked(
                session_id,
                "identity_released",
                {"reset_progress": reset_progress},
                author="teacher",
                student_id=student_id,
            )
            entry["token"] = None
            entry["claimed_at"] = None
            entry["credential_expires_at"] = None
            entry["resume_reserved"] = False
            await self.storage.write_json(self._session_path(session_id), session)
        return True

    async def student_for_token(
        self, session_id: str, token: str, *, require_live: bool = True
    ) -> str | None:
        """Valida o token do aluno. Por omissão exige sessão viva — tokens
        deixam de servir para mutações depois do fecho ou do release."""
        if not token:
            return None
        async with self._session_locks[session_id]:
            session = await self._load_session_unlocked(session_id)
            if not session:
                return None
            if require_live and session.get("status") != "live":
                return None
            for student_id, entry in session["roster"].items():
                expires_at = entry.get("credential_expires_at")
                if not expires_at:
                    continue
                try:
                    expires = datetime.fromisoformat(
                        str(expires_at).replace("Z", "+00:00")
                    )
                    if expires.tzinfo is None:
                        expires = expires.replace(tzinfo=timezone.utc)
                except (TypeError, ValueError):
                    continue
                if self._now_as_datetime() >= expires.astimezone(timezone.utc):
                    continue
                if hmac.compare_digest(str(entry.get("token") or ""), token):
                    return student_id
        return None

    # ---- eventos ----

    async def _seen(self, session_id: str) -> set[str]:
        if session_id not in self._seen_event_ids:
            records = await self.storage.read_jsonl(
                self.storage.path("sessions", session_id, "events.jsonl")
            )
            self._seen_event_ids[session_id] = {
                r["event_id"] for r in records if r.get("event_id")
            }
        return self._seen_event_ids[session_id]

    async def ingest_events(self, session_id: str, student_id: str, events: list[dict]) -> list[dict]:
        """Aceita lote de eventos do aluno (at-least-once, dedup por event_id)."""
        async with self._session_locks[session_id]:
            await self._require_writable_unlocked(session_id, student_id)
            seen = await self._seen(session_id)
            accepted = []
            log = self.events_log(session_id)
            activity_types = {
                entry.name for entry in SESSION_EVENT_TYPES.by_author("activity")
            }
            for ev in events[:20]:
                event_id = str(ev.get("event_id") or uuid.uuid4().hex)
                ev_type = str(ev.get("type", ""))
                if event_id in seen or ev_type not in activity_types:
                    continue
                seen.add(event_id)
                record = await log.append(
                    {
                        "event_id": event_id,
                        "type": ev_type,
                        "student_id": student_id,
                        "unit_id": ev.get("unit_id"),
                        "payload": ev.get("payload") or {},
                    }
                )
                accepted.append(record)
            return accepted

    async def ingest_work_group_events(self, session_id: str, group_id: str, events: list[dict]) -> list[dict]:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id)
            group = session.get("work_groups", {}).get(group_id)
            if not group or not group.get("token"):
                raise InvalidSessionEventError("O grupo já não está disponível.")
            seen = await self._seen(session_id)
            activity_types = {entry.name for entry in SESSION_EVENT_TYPES.by_author("activity")}
            # Shared work declarations are saved; legacy joint self-assessment stays refused.
            events = [ev for ev in events if ev.get("type") != "assessment_result" or (
                isinstance((ev.get("payload") or {}).get("detail"), dict)
                and (ev["payload"]["detail"].get("field") or ev["payload"]["detail"].get("productChanged"))
                and ev["payload"]["detail"].get("activity") == session["activity_slug"]
            )]
            conflicts = [str(ev.get("event_id") or "") for ev in events[:20]
                         if ev.get("event_id") not in seen and ev.get("type") in activity_types
                         and (ev.get("composition_version", 1) != group["composition_version"]
                              or ev.get("access_version", 1) != group["access_version"])]
            if conflicts:
                raise CompositionChangedError(conflicts, self.project_work_group(group))
            accepted = []
            for ev in events[:20]:
                event_id = str(ev.get("event_id") or uuid.uuid4().hex)
                ev_type = str(ev.get("type", ""))
                if event_id in seen or ev_type not in activity_types:
                    continue
                seen.add(event_id)
                payload = ev.get("payload") or {}
                record = await self.events_log(session_id).append({
                    "event_id": event_id, "type": ev_type,
                    "work_group_id": group_id, "participant_ids": list(group["participant_ids"]),
                    "unit_id": ev.get("unit_id"), "payload": payload,
                })
                if ev_type == "level_changed" and payload.get("level") in {"support", "intermediate", "challenge"}:
                    group["level"] = payload["level"]
                accepted.append(record)
            await self.storage.write_json(self._session_path(session_id), session)
            return accepted

    async def send_teacher_message(
        self, session_id: str, text: str, *, student_id: str | None = None
    ) -> dict:
        return await self.emit_event(
            session_id,
            "teacher_message",
            {"text": text},
            author="teacher",
            student_id=student_id,
        )

    async def control_session(
        self,
        session_id: str,
        action: str,
        *,
        student_id: str | None = None,
        unit_id: str | None = None,
        unit_label: str = "",
    ) -> dict:
        if action == "highlight":
            return await self.emit_event(
                session_id,
                "teacher_highlight",
                {"unit_id": unit_id, "unit_label": unit_label},
                author="teacher",
                student_id=student_id,
            )
        type_ = {"freeze": "freeze_screens", "unfreeze": "unfreeze_screens"}[action]
        return await self.emit_event(
            session_id,
            type_,
            {},
            author="teacher",
        )

    async def emit_event(
        self,
        session_id: str,
        type_: str,
        payload: dict,
        *,
        author: str,
        student_id: str | None = None,
        caused_by_seq: int | None = None,
        work_group_id: str | None = None,
    ) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            participant_ids = None
            if work_group_id is not None:
                if student_id is not None:
                    raise ValueError('a autoria é individual ou conjunta')
                group = session.get('work_groups', {}).get(work_group_id)
                if group is None:
                    raise InvalidSessionEventError('grupo não pertence à sessão')
                participant_ids = list(group['participant_ids'])
            return await self._append_event_unlocked(
                session_id,
                type_,
                payload,
                author=author,
                student_id=student_id,
                caused_by_seq=caused_by_seq,
                work_group_id=work_group_id,
                participant_ids=participant_ids,
            )

    async def _append_event_unlocked(
        self,
        session_id: str,
        type_: str,
        payload: dict,
        *,
        author: str,
        student_id: str | None = None,
        caused_by_seq: int | None = None,
        ts: str | None = None,
        work_group_id: str | None = None,
        participant_ids: list[str] | None = None,
    ) -> dict:
        event_type = SESSION_EVENT_TYPES.get(type_)
        if event_type is None:
            raise ValueError(f"tipo de Acontecimento de sessão não declarado: {type_}")
        if author not in event_type.authors:
            raise ValueError(f"{author} não pode emitir o Acontecimento de sessão {type_}")
        record = {"type": type_, "student_id": student_id, "payload": payload}
        if work_group_id is not None:
            record['work_group_id'] = work_group_id
            record['participant_ids'] = participant_ids
        if caused_by_seq is not None:
            record["caused_by_seq"] = caused_by_seq
        if ts is not None:
            record["ts"] = ts
        return await self.events_log(session_id).append(record)

    # ---- PIT-lite ----

    async def create_pit_item(
        self, session_id: str, student_id: str, text: str
    ) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            clean_text = text.strip()[:280]
            if not clean_text:
                raise InvalidPitItemError("o item do plano precisa de texto")
            item = {
                "id": uuid.uuid4().hex[:8],
                "student_id": student_id,
                "text": clean_text,
                "status": "planned",
                "updated_at": utcnow(),
            }
            session["pit_items"].append(item)
            await self._append_event_unlocked(
                session_id,
                "pit_updated",
                {**item, "previous_status": None},
                author="student",
                student_id=student_id,
            )
            await self.storage.write_json(self._session_path(session_id), session)
        return item

    async def advance_pit_item(
        self, session_id: str, student_id: str, item_id: str
    ) -> dict:
        async with self._session_locks[session_id]:
            session = await self._require_writable_unlocked(session_id, student_id)
            item = next(
                (
                    candidate
                    for candidate in session["pit_items"]
                    if candidate["id"] == item_id
                ),
                None,
            )
            if item is None or item.get("student_id") != student_id:
                raise InvalidPitItemError("item do plano não encontrado")

            previous_status = item["status"]
            item["status"] = {
                "planned": "doing",
                "doing": "done",
                "done": "to_share",
                "to_share": "done",
            }[previous_status]
            item["updated_at"] = utcnow()
            await self._append_event_unlocked(
                session_id,
                "pit_updated",
                {**item, "previous_status": previous_status},
                author="student",
                student_id=student_id,
            )
            await self.storage.write_json(self._session_path(session_id), session)
        return item
