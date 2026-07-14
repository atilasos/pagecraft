import pytest

from server.providers.base import SchemaError, parse_and_validate

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
