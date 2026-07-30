"""Contrato comum dos providers de IA.

`complete` recebe um prompt e um JSON Schema e devolve um dict validado.
A classe base implementa o ciclo completo — retry com aviso de schema,
parse e validação num único sítio; os adaptadores implementam apenas o
transporte (`_complete_once`). Erros são sempre tipados para o chamador
decidir reparação/fallback/abortar.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

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


def parse_and_validate(payload: Any, schema: dict[str, Any] | None) -> Any:
    """Extrai JSON de `payload` (se texto) e valida contra `schema`."""
    if isinstance(payload, str):
        candidate = payload.strip()
        # tolera cercas de código à volta do JSON
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            candidate = "\n".join(lines).strip()
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise SchemaError("resposta não é JSON válido", detail=candidate[:2000]) from exc
    else:
        data = payload
    if schema is not None:
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            detail = json.dumps(data, ensure_ascii=False)[:2000]
            raise SchemaError(f"JSON não cumpre o schema: {exc.message}", detail=detail) from exc
    return data


_SCHEMA_RETRY_WARNING = (
    "\n\n---\n\nATENÇÃO: a tua resposta anterior não cumpriu o schema JSON "
    "({error}). Responde APENAS com JSON válido contra o schema."
)

OnRetry = Callable[[int, ProviderError], Awaitable[None]]


class AIProvider(ABC):
    name: str = "base"

    @property
    def available(self) -> bool:
        return True

    async def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        timeout_s: int = 300,
        attempts: int = 1,
        on_retry: OnRetry | None = None,
    ) -> Any:
        """Devolve o JSON validado (ou texto, se schema=None).

        Tenta até `attempts` vezes; entre tentativas, uma falha de schema
        acrescenta o aviso ao prompt e `on_retry(attempt, erro)` é notificado.
        """
        total = max(1, attempts)
        last_error: ProviderError | None = None
        for attempt in range(1, total + 1):
            try:
                raw = await self._complete_once(
                    prompt, system=system, timeout_s=timeout_s, schema=schema
                )
                if schema is None:
                    return raw
                return parse_and_validate(raw, schema)
            except ProviderError as exc:
                last_error = exc
                if attempt == total:
                    break
                if isinstance(exc, SchemaError):
                    prompt = prompt + _SCHEMA_RETRY_WARNING.format(error=exc)
                if on_retry is not None:
                    await on_retry(attempt, exc)
        raise last_error if last_error else RuntimeError("falha desconhecida do provider")

    @abstractmethod
    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        timeout_s: int,
        schema: dict[str, Any] | None,
    ) -> Any:
        """Transporte puro: uma chamada ao provider, sem retry nem validação.

        Devolve texto (a base faz parse) ou um objeto já estruturado
        (a base valida na mesma). `schema` serve apenas para o transporte
        moldar o pedido (schema no prompt, tool_use forçado, …).
        """
