"""Contrato comum dos providers de IA.

`complete` recebe um prompt e um JSON Schema e devolve um dict validado.
Erros são sempre tipados para o runner decidir retry/reparação/abortar.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import jsonschema


class ProviderError(Exception):
    """Erro base de provider; `detail` transporta evidência para logs."""

    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


class ProviderTimeout(ProviderError):
    pass


class ProviderFailure(ProviderError):
    """Processo/HTTP falhou (exit != 0, status >= 400, stream cortado)."""


class SchemaError(ProviderError):
    """A resposta chegou mas não é JSON válido contra o schema pedido."""


def parse_and_validate(text: str, schema: dict[str, Any] | None) -> Any:
    """Extrai JSON de `text` e valida contra `schema` (se fornecido)."""
    candidate = text.strip()
    # tolera cercas de código à volta do JSON
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        candidate = "\n".join(lines).strip()
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise SchemaError("resposta não é JSON válido", detail=candidate[:2000]) from exc
    if schema is not None:
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            raise SchemaError(f"JSON não cumpre o schema: {exc.message}", detail=candidate[:2000]) from exc
    return data


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        timeout_s: int = 300,
        workdir: str | None = None,
    ) -> Any:
        """Devolve o JSON validado (ou texto, se schema=None)."""
