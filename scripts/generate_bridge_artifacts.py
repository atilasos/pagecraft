#!/usr/bin/env python3
"""Gera os artefactos commitados da PageCraftBridge a partir do registo.

O pipeline e os harnesses continuam a consumir Markdown e HTML estáticos.
Este script é apenas uma ferramenta de desenvolvimento para os regenerar e
detetar drift; não é importado no caminho de execução do Builder.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from server.classroom.event_types import SESSION_EVENT_TYPES, SessionEventType


CONTRACT_PATH = Path("server/pipeline/prompts/references/bridge-contract.md")
TEMPLATE_PATH = Path("server/pipeline/prompts/template-base.html")
GENERATED_START = "      /* BEGIN GENERATED SESSION EVENT EMITTERS"
GENERATED_END = "      /* END GENERATED SESSION EVENT EMITTERS */"

# Compatibilidade pública: aliases existentes não seguem mecanicamente o nome
# interno. Esta política é explícita para que nunca mudem por acidente.
HELPER_ALIASES = {
    "assessment_result": "assessment",
    "feedback_request": "askForFeedback",
    "share_requested": "share",
}
AUTOMATIC_EMITTERS = frozenset({"activity_loaded", "heartbeat"})
EMPTY_STRING_DEFAULTS = frozenset(
    {
        ("attempt", "detail"),
        ("discovery", "message"),
        ("assessment_result", "detail"),
        ("feedback_request", "expected"),
        ("help_needed", "note"),
        ("share_requested", "what"),
    }
)
BRIDGE_RECEIVER_EFFECTS = {
    "ai_feedback": (
        "preenche `.ai-feedback` com `payload.text` "
        "(id `pagecraft-feedback` ou `targetId`)"
    ),
    "teacher_highlight": (
        "usa `unitId` do envelope para focar a unidade e aplicar "
        "`.pagecraft-attention` durante cerca de 6 s"
    ),
}


def _camel_case(name: str) -> str:
    first, *rest = name.split("_")
    return first + "".join(part.capitalize() for part in rest)


def _activity_events() -> tuple[SessionEventType, ...]:
    return SESSION_EVENT_TYPES.by_author("activity")


def _helper_name(event: SessionEventType) -> str:
    return HELPER_ALIASES.get(event.name, _camel_case(event.name))


def _parameter_name(field: str) -> str:
    return _camel_case(field)


def _payload_expression(event: SessionEventType) -> str:
    if not event.payload_fields:
        return "{}"
    values = []
    for field in event.payload_fields:
        parameter = _parameter_name(field)
        if (event.name, field) == ("attempt", "correct"):
            expression = f"!!{parameter}"
        elif (event.name, field) in EMPTY_STRING_DEFAULTS:
            expression = f"{parameter} || ''"
        else:
            expression = parameter
        values.append(f"{field}: {expression}")
    return "{ " + ", ".join(values) + " }"


def _helper_signature(event: SessionEventType) -> str:
    parameters = ["unitId", *map(_parameter_name, event.payload_fields)]
    return f"{_helper_name(event)}({', '.join(parameters)})"


def render_emitter_block() -> str:
    """Renderiza só o bloco substituível do template base."""
    by_name = {event.name: event for event in _activity_events()}
    missing = AUTOMATIC_EMITTERS - by_name.keys()
    if missing:
        raise ValueError(f"emissores automáticos sem declaração: {sorted(missing)}")

    helpers = [
        event for event in _activity_events() if event.name not in AUTOMATIC_EMITTERS
    ]
    lines = [
        f"{GENERATED_START} — do not edit by hand. */",
        "      /* presença: heartbeat de 30s enquanto a página está visível */",
        "      if (embedded) {",
        (
            f"        emit('{by_name['activity_loaded'].name}', null, "
            "{ title: document.title });"
        ),
        "        setInterval(function () {",
        (
            f"          if (!document.hidden) "
            f"emit('{by_name['heartbeat'].name}', null, {{}});"
        ),
        "        }, 30000);",
        "      }",
        "      return {",
        "        emit: emit,",
    ]
    for index, event in enumerate(helpers):
        parameters = ["unitId", *map(_parameter_name, event.payload_fields)]
        comma = "," if index < len(helpers) - 1 else ""
        lines.append(
            f"        {_helper_name(event)}: function ({', '.join(parameters)}) "
            f"{{ emit('{event.name}', unitId, {_payload_expression(event)}); }}{comma}"
        )
    lines.extend(["      };", GENERATED_END])
    return "\n".join(lines)


def _payload_documentation(event: SessionEventType) -> str:
    if not event.payload_fields:
        return "—"
    return "<br>".join(
        f"`{field}` — {description.strip()}"
        for field, description in event.payload_fields.items()
    )


def _markdown_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> str:
    header = tuple(headers)
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_contract() -> str:
    """Renderiza o contrato normativo que o Builder lê."""
    activity_events = _activity_events()
    incoming = tuple(
        event for event in SESSION_EVENT_TYPES.all() if event.bridge_name is not None
    )
    unknown_effects = {event.name for event in incoming} - BRIDGE_RECEIVER_EFFECTS.keys()
    if unknown_effects:
        raise ValueError(
            "acontecimentos recebidos sem política de apresentação: "
            f"{sorted(unknown_effects)}"
        )

    emitted_rows = []
    for event in activity_events:
        helper = (
            "automático pelo template"
            if event.name in AUTOMATIC_EMITTERS
            else f"`PageCraftBridge.{_helper_signature(event)}`"
        )
        emitted_rows.append(
            (
                f"`{event.name}`",
                f"`{event.name}`",
                helper,
                _payload_documentation(event),
            )
        )
    received_rows = [
        (
            f"`{event.name}`",
            f"`{event.bridge_name}`",
            _payload_documentation(event),
            BRIDGE_RECEIVER_EFFECTS[event.name],
        )
        for event in incoming
    ]

    return (
        "# PageCraftBridge — contrato gerado de acontecimentos de sessão\n\n"
        "<!-- Gerado por scripts/generate_bridge_artifacts.py a partir de "
        "SESSION_EVENT_TYPES. Não editar à mão. -->\n\n"
        "A atividade é **sempre** um HTML self-contained e offline. A ponte é "
        "opcional e degrada silenciosamente: usa apenas `postMessage` para "
        "`window.parent`; `fetch`, XHR e WebSocket são proibidos dentro da "
        "atividade. Quando a página é aberta diretamente, os acontecimentos "
        "não têm ouvinte e nada acontece.\n\n"
        "## Envelope\n\n"
        "```json\n"
        '{ "pagecraft": 1, "type": "<nome na ponte>", "unitId": "u1", '
        '"payload": {}, "ts": 1710000000000 }\n'
        "```\n\n"
        "O **nome interno** é o identificador canónico no servidor. O **nome "
        "na ponte** é o valor de `type` que fica incorporado nas atividades. "
        "Nos acontecimentos emitidos pela atividade os dois nomes coincidem. "
        "Nos recebidos, `bridge_name` é declarado separadamente no registo e "
        "é append-only: nunca se renomeia um nome publicado (ADR-0002), apenas "
        "se acrescenta outro durante uma migração deliberada.\n\n"
        "## Emitidos pela atividade\n\n"
        + _markdown_table(
            ("nome interno", "nome na ponte (`type`)", "emissor", "payload declarado"),
            emitted_rows,
        )
        + "\n\n"
        "`unitId` identifica a unidade no envelope e não faz parte de `payload`.\n\n"
        "## Recebidos pela atividade\n\n"
        + _markdown_table(
            ("nome interno", "nome na ponte (`type`)", "payload declarado", "efeito"),
            received_rows,
        )
        + "\n\n"
        "O host traduz o acontecimento interno para o envelope da ponte. Pode "
        "projetar apenas os campos necessários ao recetor; os campos acima "
        "documentam o payload canónico declarado no registo.\n\n"
        "## Regras para o Builder\n\n"
        "1. Usa os helpers listados na tabela e `PageCraftFeedback.show(...)` "
        "ou `showDiscovery(...)`; esses helpers já emitem os nomes normativos.\n"
        "2. Dá `unitId` estável a cada unidade (`u1`, `u2`, … pela ordem do "
        'docspec), põe `id="u1"` (ou `data-unit="u1"`) no contentor DOM e '
        "chama `PageCraftBridge.unitStarted(unitId)` quando a unidade fica "
        "visível ou ativa pela primeira vez.\n"
        "3. Em perguntas de texto livre, chama "
        "`PageCraftBridge.askForFeedback(unitId, pergunta, respostaDoAluno, "
        "respostaEsperada)` e inclui `<div class=\"ai-feedback\" "
        "id=\"pagecraft-feedback\"></div>` por baixo.\n"
        "4. Inclui um botão «Preciso de ajuda» (`help-button`) por unidade ou "
        "global que chama `PageCraftBridge.helpNeeded(unitId)`.\n"
        "5. O feedback local imediato continua a mandar; o feedback do "
        "assistente é uma camada extra e pode nunca chegar.\n"
        "6. Nunca uses rede. A ponte usa exclusivamente `postMessage`.\n"
    )


def _replace_emitter_block(template: str) -> str:
    pattern = re.compile(
        rf"{re.escape(GENERATED_START)}.*?{re.escape(GENERATED_END)}",
        re.DOTALL,
    )
    generated = render_emitter_block()
    updated, count = pattern.subn(generated, template)
    if count != 1:
        raise ValueError(
            "template-base.html precisa de exatamente um bloco de emissores gerado"
        )
    return updated


def expected_artifacts(root: Path) -> dict[Path, str]:
    root = Path(root)
    template = (root / TEMPLATE_PATH).read_text("utf-8")
    return {
        CONTRACT_PATH: render_contract(),
        TEMPLATE_PATH: _replace_emitter_block(template),
    }


def find_drift(root: Path) -> list[str]:
    root = Path(root)
    return [
        path.as_posix()
        for path, expected in expected_artifacts(root).items()
        if (root / path).read_text("utf-8") != expected
    ]


def write_artifacts(root: Path) -> None:
    root = Path(root)
    for path, content in expected_artifacts(root).items():
        destination = root / path
        if destination.read_text("utf-8") != content:
            destination.write_text(content, "utf-8")
            print(f"generated: {path}")


def _sync_distributions(root: Path, *, check: bool) -> int:
    command = ["bash", "skills/sync-from-canonical.sh"]
    if check:
        command.append("--check")
    return subprocess.run(command, cwd=root, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="falha se os artefactos commitados ou distribuídos tiverem drift",
    )
    args = parser.parse_args()
    root = REPO_ROOT

    if args.check:
        drift = find_drift(root)
        for path in drift:
            print(f"drift: {path}")
        sync_status = _sync_distributions(root, check=True)
        return 1 if drift or sync_status else 0

    write_artifacts(root)
    return _sync_distributions(root, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
