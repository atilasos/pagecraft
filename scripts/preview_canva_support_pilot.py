"""Servidor de ensaio isolado. Não usa dados da turma nem chama um fornecedor de IA.

Executar: uv run python -m scripts.preview_canva_support_pilot
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import tempfile

import uvicorn

from fastapi.responses import HTMLResponse
from server.access import RoutePolicy, access_policy
from server.api.learning import ACTIVITY_CONTENT_HEADERS
from server.app import create_app
from server.providers import AIProvider


class PreviewProvider(AIProvider):
    name = 'ensaio-local'

    async def _complete_once(self, prompt, *, schema, system, timeout_s):
        await asyncio.sleep(.5)
        context = json.loads(prompt.split('\n', 1)[1])
        text = ('Aponta no teu esboço a zona de cada animal. Qual queres organizar primeiro?'
                if context.get('participant_count') == 1 else
                'Apontem no vosso esboço a zona de cada animal. Qual querem organizar primeiro?')
        return {'feedback': text}


def create_preview():
    root = Path(__file__).resolve().parents[1]
    # Fica separado dos dados reais e é removido ao fechar o servidor.
    directory = tempfile.TemporaryDirectory(prefix='pagecraft-canva-pilot-')
    os.environ['PAGECRAFT_DATA_DIR'] = directory.name
    def demo_route(app):
        @app.get('/pilot-demo', response_class=HTMLResponse)
        @access_policy(RoutePolicy.PUBLIC)
        async def demo():
            return HTMLResponse((root / 'drafts/canva-animais-autonomia-piloto.html').read_text(),
                                headers=ACTIVITY_CONTENT_HEADERS)
    app = create_app(route_extensions=[demo_route])
    lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def preview_lifespan(app):
        async with lifespan(app):
            app.state.feedback.provider = PreviewProvider()
            app.state.learning_feedback.provider = PreviewProvider()
            registration = json.loads((root / 'drafts/canva-animais-autonomia-piloto-registration.json').read_text())
            activity = await app.state.learning.register(registration)
            cls = await app.state.classroom.create_class('Ensaio Canva', 4, ['Ana de teste', 'Bruno de teste', 'Carla de teste'])
            session = await app.state.classroom.create_session(cls['id'], registration['slug'], registration['title'])
            print("\nEnsaio isolado: IA simulada, alunos fictícios e armazenamento temporário.", flush=True)
            print("Guião sem entrada ou gravações: http://127.0.0.1:18877/pilot-demo", flush=True)
            print(f"Pré-visualização permanente: http://127.0.0.1:18877/{activity['code']}", flush=True)
            print(f"Studio: http://127.0.0.1:18877/student/ · código {session['join_code']}", flush=True)
            print(f"Painel: http://127.0.0.1:18877/teacher/class.html · sessão {session['id']}\n", flush=True)
            try:
                yield
            finally:
                directory.cleanup()
    app.router.lifespan_context = preview_lifespan
    return app


if __name__ == '__main__':
    uvicorn.run(create_preview(), host='127.0.0.1', port=18877)
