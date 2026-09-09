"""Atividades permanentes e realizações: ficheiros privados, um processo escritor."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from .events import utcnow


ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LEARNING_COOKIE = "pagecraft_realization"


def normalized_name(name: str) -> str:
    return " ".join(name.split()).casefold()


class Learning:
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config
        self.catalog_lock = asyncio.Lock()
        self.locks: dict[str, asyncio.Lock] = {}

    def lock(self, key):
        return self.locks.setdefault(key, asyncio.Lock())

    async def activities(self):
        return await self.storage.read_json(self.storage.path("learning", "activities.json"), {})

    async def activity(self, code):
        activity = (await self.activities()).get(code.upper())
        if activity is None:
            raise HTTPException(404, "Atividade não encontrada.")
        return activity

    async def register(self, data):
        # Slugs are validated by the HTTP boundary. Drafts are never static mounts.
        path = self.config.repo_root / "drafts" / f"{data['slug']}.html"
        published_path = self.config.activities_dir / data['slug'] / "index.html"
        if not path.is_file() and not published_path.is_file():
            raise HTTPException(422, "Falta o HTML em drafts/ ou activities/.")
        async with self.catalog_lock:
            activities = await self.activities()
            existing = next((a for a in activities.values() if a['slug'] == data['slug']), None)
            if existing:
                if not existing['published']:
                    existing.update(data)
                    activities[existing['code']] = existing
                    await self.storage.write_json(self.storage.path("learning", "activities.json"), activities)
                return existing
            code = "".join(secrets.choice(ALPHABET) for _ in range(6))
            while code in activities:
                code = "".join(secrets.choice(ALPHABET) for _ in range(6))
            activity = dict(data, code=code, published=False, created_at=utcnow())
            activities[code] = activity
            await self.storage.write_json(self.storage.path("learning", "activities.json"), activities)
            return activity

    async def publish(self, code):
        from .publish import publish_activity

        async with self.catalog_lock:
            activities = await self.activities()
            activity = await self.activity(code)
            if activity['published']:
                return activity
            drafts = self.config.repo_root / "drafts"
            html = drafts / f"{activity['slug']}.html"
            if html.is_file():
                spec = await self.storage.read_json(drafts / f"{activity['slug']}-docspec.json")
                guide = drafts / f"{activity['slug']}.md"
                if spec is None or not guide.is_file():
                    raise HTTPException(422, "Faltam o DocSpec ou o guia do professor.")
                design = await self.storage.read_json(drafts / f"{activity['slug']}-design-spec.json")
                await asyncio.to_thread(publish_activity, self.config.repo_root, activity['slug'], html,
                                        spec, guide.read_text('utf-8'), design)
            activity['published'] = True
            activity['published_at'] = utcnow()
            activities[activity['code']] = activity
            await self.storage.write_json(self.storage.path("learning", "activities.json"), activities)
            return activity

    def content_path(self, activity):
        if activity['published']:
            return self.config.activities_dir / activity['slug'] / "index.html"
        draft = self.config.repo_root / "drafts" / f"{activity['slug']}.html"
        return draft if draft.is_file() else self.config.activities_dir / activity['slug'] / "index.html"

    async def start(self, activity, data, *, preview=False):
        attempt_id, credential = secrets.token_hex(16), secrets.token_urlsafe(32)
        attempt = dict(
            id=attempt_id, code=activity['code'], title=activity['title'], year=activity['year'],
            criteria=activity['criteria'], name=" ".join(data['name'].split()),
            original_name=data['name'], group=data['group'] or activity.get('group', ''),
            mode=data['mode'], language=data['language'], level=data['level'],
            started_at=utcnow(), completed_at=None, preview=preview,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            credential_hash=hashlib.sha256(credential.encode()).hexdigest(),
            events=[], assessment=None, teacher_note="",
        )
        await self.storage.write_json(self.storage.path("learning", "realizations", f"{attempt_id}.json"), attempt)
        return attempt, f"{attempt_id}.{credential}"

    async def attempt(self, attempt_id):
        attempt = await self.storage.read_json(self.storage.path("learning", "realizations", f"{attempt_id}.json"))
        if attempt is None:
            raise HTTPException(404, "Realização não encontrada.")
        return attempt

    async def resolve(self, cookie):
        identifier, separator, credential = cookie.partition('.')
        if not separator or len(identifier) != 32 or any(c not in '0123456789abcdef' for c in identifier):
            return None
        try:
            attempt = await self.attempt(identifier)
        except HTTPException:
            return None
        if datetime.fromisoformat(attempt['expires_at']) <= datetime.now(timezone.utc):
            return None
        if not hmac.compare_digest(attempt['credential_hash'], hashlib.sha256(credential.encode()).hexdigest()):
            return None
        return identifier

    async def record(self, identifier, events):
        async with self.lock(identifier):
            attempt = await self.attempt(identifier)
            known = {e['id'] for e in attempt['events']}
            new = []
            for event in events:
                if event['id'] not in known:
                    known.add(event['id'])
                    new.append(dict(event, received_at=utcnow()))
            if new and attempt['completed_at']:
                raise HTTPException(409, "Esta realização já terminou.")
            if len(attempt['events']) + len(new) > 5000:
                raise HTTPException(409, "Limite de registos atingido; termina a realização.")
            attempt['events'].extend(new)
            for event in new:
                if event['type'] == 'language_changed' and event['payload'].get('language') in {'pt', 'en'}:
                    attempt['language'] = event['payload']['language']
                if event['type'] == 'level_changed' and event['payload'].get('level') in {'support', 'intermediate', 'challenge'}:
                    attempt['level'] = event['payload']['level']
            await self.storage.write_json(self.storage.path("learning", "realizations", f"{identifier}.json"), attempt)
            return len(new)

    async def finish(self, identifier, assessment):
        async with self.lock(identifier):
            attempt = await self.attempt(identifier)
            if attempt['completed_at']:
                return attempt
            criterion_ids = {c['id'] for c in attempt['criteria']}
            if set(assessment['answers']) - criterion_ids:
                raise HTTPException(422, "Critério desconhecido.")
            attempt['assessment'] = assessment
            attempt['language'] = assessment['language']
            attempt['level'] = assessment['level']
            attempt['completed_at'] = utcnow()
            await self.storage.write_json(self.storage.path("learning", "realizations", f"{identifier}.json"), attempt)
            return attempt

    async def annotate(self, identifier, data):
        async with self.lock(identifier):
            attempt = await self.attempt(identifier)
            attempt.update(data)
            await self.storage.write_json(self.storage.path("learning", "realizations", f"{identifier}.json"), attempt)
            return attempt

    async def reports(self):
        directory = self.storage.root / "learning" / "realizations"
        records = [await self.storage.read_json(p) for p in directory.glob('*.json')]
        return sorted((self.public_attempt(r, teacher=True) for r in records if not r['preview']),
                      key=lambda r: r['started_at'], reverse=True)

    @staticmethod
    def public_attempt(attempt, *, teacher=False):
        hidden = {"credential_hash", "expires_at"}
        if not teacher:
            hidden.add("teacher_note")
        result = {k: v for k, v in attempt.items() if k not in hidden}
        if teacher:
            from .learning_reports import describe_evidence
            result['evidence'] = [dict(type=e['type'], at=e['received_at'], text=describe_evidence(e)) for e in attempt['events']]
        return result

