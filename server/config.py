"""Configuração do servidor PageCraft.

Fonte de verdade: server/config.toml (opcional) com override por variáveis
de ambiente PAGECRAFT_*. Nenhum campo guarda segredos; a API key da
Anthropic vem sempre de ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Config:
    repo_root: Path = REPO_ROOT
    data_dir: Path = SERVER_ROOT / "data"
    outputs_dir: Path = REPO_ROOT / "outputs" / "lessons"
    activities_dir: Path = REPO_ROOT / "activities"
    catalog_path: Path = REPO_ROOT / "catalog.json"
    prompts_dir: Path = SERVER_ROOT / "pipeline" / "prompts"
    vault_path: Path = Path.home() / "vault"
    host: str = "127.0.0.1"
    port: int = 8777
    # provider de geração (pipeline completo) e de feedback (respostas rápidas)
    generation_provider: str = "codex"
    feedback_provider: str = "auto"  # auto: anthropic se houver key, senão codex
    codex_bin: str = "codex"
    anthropic_model: str = "claude-haiku-4-5-20251001"
    generation_timeout_s: int = 300
    builder_timeout_s: int = 900
    feedback_timeout_s: int = 20
    max_iterations: int = 3
    extra: dict = field(default_factory=dict)


def _coerce(value: str, target_type: type):
    if target_type is int:
        return int(value)
    if target_type is Path:
        return Path(value).expanduser()
    return value


def load_config(config_path: Path | None = None) -> Config:
    path = config_path or SERVER_ROOT / "config.toml"
    raw: dict = {}
    if path.exists():
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)

    kwargs: dict = {}
    for name, f in Config.__dataclass_fields__.items():
        if name == "extra":
            continue
        env_key = f"PAGECRAFT_{name.upper()}"
        if env_key in os.environ:
            kwargs[name] = _coerce(os.environ[env_key], f.type if isinstance(f.type, type) else type(f.default))
        elif name in raw:
            default = getattr(Config, name, None)
            target = type(default) if default is not None else str
            kwargs[name] = _coerce(str(raw[name]), target) if target in (int, Path) else raw[name]

    known = set(Config.__dataclass_fields__)
    extra = {k: v for k, v in raw.items() if k not in known}
    if extra:
        kwargs["extra"] = extra
    return Config(**kwargs)
