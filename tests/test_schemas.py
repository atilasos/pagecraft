import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "server" / "pipeline" / "schemas"

SCHEMA_FILES = [
    "docspec.schema.json",
    "design-spec.schema.json",
    "builder-output.schema.json",
    "proofread.schema.json",
    "evaluation.schema.json",
]

MINIMAL_DOCSPEC = {
    "topic": "Estados físicos da água",
    "ageRange": "8-9 anos (3.º ano)",
    "duration": 40,
    "objectives": [
        "Identificar os três estados físicos da água",
        "Relacionar a temperatura com as mudanças de estado",
    ],
    "curriculum": {
        "ae": [
            {
                "subject": "Estudo do Meio",
                "year": "3.º ano",
                "descriptor": "Identificar propriedades físicas da água",
            }
        ],
        "competencies": ["PA-I: Saber científico, técnico e tecnológico"],
    },
    "units": [
        {
            "summary": "Os três estados da água dependem da temperatura",
            "textDescription": "O aluno deve compreender que a temperatura determina o estado da água.",
            "interaction": {
                "state": [
                    {
                        "name": "temperatura",
                        "type": "slider",
                        "range": [-20, 120],
                        "step": 1,
                        "default": 20,
                        "unit": "°C",
                    }
                ],
                "render": "Termómetro e moléculas animadas",
                "transition": "Arrastar o slider ajusta velocidade das moléculas",
                "constraint": "A água muda de estado a 0°C e 100°C",
                "assessment": "O aluno encontra e regista as temperaturas de mudança",
            },
            "differentiation": {
                "support": "Slider com 3 posições fixas",
                "standard": "Slider contínuo, descoberta livre",
                "challenge": "Gráfico de energia das moléculas",
            },
            "duration": 20,
        }
    ],
}


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", SCHEMA_FILES)
def test_schema_is_valid_draft_2020_12(name):
    schema = load_schema(name)
    Draft202012Validator.check_schema(schema)


def test_minimal_docspec_validates():
    validator = Draft202012Validator(load_schema("docspec.schema.json"))
    validator.validate(MINIMAL_DOCSPEC)


def test_docspec_unit_without_interaction_fails():
    docspec = copy.deepcopy(MINIMAL_DOCSPEC)
    del docspec["units"][0]["interaction"]
    validator = Draft202012Validator(load_schema("docspec.schema.json"))
    with pytest.raises(ValidationError):
        validator.validate(docspec)


def test_builder_output_rejects_short_html_and_extra_keys():
    validator = Draft202012Validator(load_schema("builder-output.schema.json"))
    validator.validate({"html": "<!doctype html>" + "x" * 600, "notes": "ok"})
    with pytest.raises(ValidationError):
        validator.validate({"html": "<p>curto</p>"})
    with pytest.raises(ValidationError):
        validator.validate({"html": "x" * 600, "extra": 1})


def test_evaluation_fail_requires_route():
    validator = Draft202012Validator(load_schema("evaluation.schema.json"))
    validator.validate(
        {"pass": False, "severity": "high", "issues": ["layout partido"], "route": "builder"}
    )
    validator.validate({"pass": True, "severity": "low", "issues": []})
    with pytest.raises(ValidationError):
        validator.validate({"pass": False, "severity": "high", "issues": []})
