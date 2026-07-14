"""Provider Anthropic (API direta via httpx).

Usado sobretudo para feedback rápido aos alunos (modelo Haiku). Quando há
schema, força a resposta através de tool-use com input_schema — o modelo
tem de devolver JSON válido contra o schema.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .base import AIProvider, ProviderFailure, ProviderTimeout, SchemaError, parse_and_validate

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-haiku-4-5-20251001", api_key: str | None = None, max_tokens: int = 4096):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.max_tokens = max_tokens

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        timeout_s: int = 300,
        workdir: str | None = None,
    ) -> Any:
        if not self.api_key:
            raise ProviderFailure("ANTHROPIC_API_KEY não definida")

        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        if schema is not None:
            body["tools"] = [
                {
                    "name": "emit_result",
                    "description": "Devolve o resultado estruturado pedido.",
                    "input_schema": schema,
                }
            ]
            body["tool_choice"] = {"type": "tool", "name": "emit_result"}

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(API_URL, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(f"API Anthropic excedeu {timeout_s}s") from exc
        except httpx.HTTPError as exc:
            raise ProviderFailure(f"erro HTTP na API Anthropic: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderFailure(f"API Anthropic devolveu {resp.status_code}", detail=resp.text[:2000])

        data = resp.json()
        content = data.get("content", [])
        if schema is not None:
            for block in content:
                if block.get("type") == "tool_use" and block.get("name") == "emit_result":
                    import jsonschema

                    try:
                        jsonschema.validate(block["input"], schema)
                    except jsonschema.ValidationError as exc:
                        raise SchemaError(f"JSON não cumpre o schema: {exc.message}") from exc
                    return block["input"]
            raise SchemaError("resposta sem bloco tool_use estruturado", detail=str(content)[:2000])

        text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
        return text
