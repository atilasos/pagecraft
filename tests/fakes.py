"""Fakes partilhados de provider para testes.

`FakeProvider` subclassa `AIProvider`, por isso as respostas atravessam o
mesmo caminho de parse/validação/retry que os providers reais — os
fixtures têm de ser válidos contra o schema pedido.
"""

from __future__ import annotations

from server.providers import AIProvider


class FakeProvider(AIProvider):
    """Devolve `responses` por ordem de chamada; com `default`, repete-o
    quando a fila esvazia. Exceções na fila são lançadas em vez de
    devolvidas. `calls` regista cada pedido feito ao transporte."""

    name = "fake"

    def __init__(self, responses=(), *, default=None):
        self.responses = list(responses)
        self.default = default
        self.calls: list[dict] = []

    async def _complete_once(self, prompt, *, system, timeout_s, schema):
        self.calls.append(
            {"prompt": prompt, "system": system, "schema": schema, "timeout_s": timeout_s}
        )
        if self.responses:
            response = self.responses.pop(0)
        elif self.default is not None:
            response = self.default
        else:
            raise AssertionError("FakeProvider sem resposta programada")
        if isinstance(response, Exception):
            raise response
        return response
