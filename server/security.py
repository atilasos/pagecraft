"""Credencial opaca persistida do Professor.

O módulo de Acesso transporta-a apenas num cookie HttpOnly, emitido pelo
bootstrap em loopback direto. Este módulo limita-se a carregar ou criar o
segredo que fica no servidor.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

TOKEN_FILE = "teacher-token.json"


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
