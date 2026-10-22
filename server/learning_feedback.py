"""Feedback para realizações permanentes, com pedidos idempotentes e fila limitada."""
from __future__ import annotations

import asyncio

from fastapi import HTTPException

from .classroom.feedback import BANNED, FEEDBACK_SCHEMA
from .feedback_context import SYSTEM_PROMPT, TIMEOUT_MESSAGE, cache_key, feedback_prompt


class LearningFeedback:
    def __init__(self, learning, provider, timeout_s):
        self.learning = learning
        self.provider = provider
        self.timeout_s = timeout_s
        self.slots = asyncio.Semaphore(2)
        self.tasks: dict[tuple[str, str], asyncio.Task] = {}
        self.cache: dict[tuple[str, str], str] = {}

    async def stop(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def request(self, identifier, unit_id, payload):
        key = (identifier, payload['request_id'])
        # O lock só protege a criação do trabalho; nunca segura a escrita da realização.
        async with self.learning.lock('feedback:' + identifier):
            attempt = await self.learning.attempt(identifier)
            request = next((e for e in attempt['events'] if e['id'] == 'request:' + key[1]), None)
            if request and (request['payload'] != payload or request['unitId'] != unit_id):
                raise HTTPException(409, 'Este pedido já tem outro contexto.')
            result = next((e for e in attempt['events'] if e['id'] == 'feedback:' + key[1]), None)
            if result:
                return result['payload']
            if attempt['completed_at']:
                raise HTTPException(409, 'Esta realização já terminou.')
            task = self.tasks.get(key)
            if task is None:
                if any(owner == identifier for owner, _ in self.tasks):
                    raise HTTPException(429, 'Espera pela pista em curso ou usa as pistas do guião.')
                await self.learning.record(identifier, [{
                    'id': 'request:' + key[1], 'type': 'feedback_request', 'unitId': unit_id, 'payload': payload,
                }])
                task = asyncio.create_task(self._run(identifier, unit_id, payload))
                self.tasks[key] = task
                task.add_done_callback(lambda done: self.tasks.pop(key, None))
        return await asyncio.shield(task)

    async def _run(self, identifier, unit_id, payload):
        semantic = (identifier, cache_key(unit_id, payload))
        text = self.cache.get(semantic)
        source = 'cache' if text else 'ai'
        if not text:
            try:
                text = await asyncio.wait_for(self._generate(payload), timeout=self.timeout_s)
                self.cache[semantic] = text
            except Exception:
                text, source = TIMEOUT_MESSAGE, 'unavailable'
        result = {'request_id': payload['request_id'], 'unit_id': unit_id, 'text': text, 'source': source}
        # Uma resposta em curso pode terminar depois da autoavaliação. Mantém causalidade no registo.
        await self.learning.record(identifier, [{
            'id': 'feedback:' + payload['request_id'], 'type': 'ai_feedback', 'unitId': unit_id, 'payload': result,
        }], assistant=True)
        return result

    async def _generate(self, payload):
        async with self.slots:
            response = await self.provider.complete(feedback_prompt(payload), schema=FEEDBACK_SCHEMA,
                                                    system=SYSTEM_PROMPT, timeout_s=self.timeout_s)
        text = str(response.get('feedback', '')).strip()
        if not text or len(text) > 400 or BANNED.search(text):
            raise ValueError('Feedback sem uma pista utilizável')
        return text
