import pytest

from server.providers.base import AIProvider, ProviderFailure, SchemaError, parse_and_validate

SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}, "score": {"type": "integer"}},
    "required": ["answer"],
    "additionalProperties": False,
}


def test_parse_valid_json():
    data = parse_and_validate('{"answer": "olá", "score": 3}', SCHEMA)
    assert data == {"answer": "olá", "score": 3}


def test_parse_json_with_code_fence():
    text = '```json\n{"answer": "olá"}\n```'
    assert parse_and_validate(text, SCHEMA) == {"answer": "olá"}


def test_parse_invalid_json_raises_schema_error():
    with pytest.raises(SchemaError):
        parse_and_validate("isto não é json", SCHEMA)


def test_parse_schema_violation_raises():
    with pytest.raises(SchemaError):
        parse_and_validate('{"score": 3}', SCHEMA)


def test_parse_without_schema_returns_data():
    assert parse_and_validate('{"livre": true}', None) == {"livre": True}


def test_parse_validates_structured_objects():
    assert parse_and_validate({"answer": "olá"}, SCHEMA) == {"answer": "olá"}
    with pytest.raises(SchemaError):
        parse_and_validate({"score": 3}, SCHEMA)


class ScriptedProvider(AIProvider):
    """Transporte de teste: devolve (ou lança) as respostas por ordem."""

    name = "scripted"

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    async def _complete_once(self, prompt, *, system, timeout_s, schema):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


async def test_complete_retries_schema_error_with_warning():
    provider = ScriptedProvider(['{"score": 3}', '{"answer": "olá"}'])
    retries = []

    async def on_retry(attempt, error):
        retries.append((attempt, error))

    data = await provider.complete("pedido", schema=SCHEMA, attempts=2, on_retry=on_retry)
    assert data == {"answer": "olá"}
    assert len(retries) == 1 and isinstance(retries[0][1], SchemaError)
    # a segunda tentativa leva o aviso de schema acrescentado ao prompt
    assert "não cumpriu o schema" in provider.prompts[1]


async def test_complete_single_attempt_raises():
    provider = ScriptedProvider(['{"score": 3}'])
    with pytest.raises(SchemaError):
        await provider.complete("pedido", schema=SCHEMA)


async def test_complete_retries_provider_failure_without_prompt_change():
    provider = ScriptedProvider([ProviderFailure("exit 1"), '{"answer": "olá"}'])
    data = await provider.complete("pedido", schema=SCHEMA, attempts=2)
    assert data == {"answer": "olá"}
    assert provider.prompts == ["pedido", "pedido"]


async def test_complete_exhausts_attempts_and_raises_last_error():
    provider = ScriptedProvider([ProviderFailure("a"), ProviderFailure("b")])
    with pytest.raises(ProviderFailure, match="b"):
        await provider.complete("pedido", schema=SCHEMA, attempts=2)


async def test_complete_without_schema_returns_text():
    provider = ScriptedProvider(["texto livre"])
    assert await provider.complete("pedido") == "texto livre"


def test_available_defaults_to_true():
    assert ScriptedProvider([]).available is True
