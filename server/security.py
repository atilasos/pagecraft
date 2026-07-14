"""Autenticação mínima do professor (single-teacher, servidor local).

Um token opaco é gerado no primeiro arranque e persistido em
data/teacher-token.json. As rotas de professor exigem o header
X-Teacher-Token (ou ?teacher_token= para SSE, onde não há headers).

O token é entregue ao browser do professor por /api/teacher-token, que só
responde a pedidos vindos de loopback SEM cabeçalhos de proxy — na máquina
do professor funciona; através de um tunnel (que injeta X-Forwarded-For)
ou da LAN, não. Alunos nunca conseguem obter o token.
"""

from __future__ import annotations

import hmac
import json
import secrets
from pathlib import Path

from fastapi import HTTPException, Request

TOKEN_FILE = "teacher-token.json"
PROXY_HEADERS = ("x-forwarded-for", "x-real-ip", "forwarded", "cf-connecting-ip")


def load_or_create_teacher_token(data_dir: Path) -> str:
    path = Path(data_dir) / TOKEN_FILE
    if path.exists():
        token = json.loads(path.read_text("utf-8")).get("token", "")
        if token:
            return token
    token = secrets.token_hex(24)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": token}), "utf-8")
    path.chmod(0o600)
    return token


def is_loopback_direct(request: Request) -> bool:
    client = request.client.host if request.client else ""
    if client not in ("127.0.0.1", "::1", "localhost"):
        return False
    return not any(h in request.headers for h in PROXY_HEADERS)


def provided_token(request: Request) -> str:
    return request.headers.get("x-teacher-token") or request.query_params.get("teacher_token", "")


def require_teacher(request: Request) -> None:
    expected = request.app.state.teacher_token
    given = provided_token(request)
    if not (given and hmac.compare_digest(given, expected)):
        raise HTTPException(401, "esta ação é só para o professor")
